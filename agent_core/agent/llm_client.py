"""Client for NVIDIA Nemotron models on Nebius Token Factory (OpenAI-compatible API).

Every answer must be valid JSON for a Pydantic schema. The schema is written into the
prompt; if the answer does not validate, the error is sent back to the model and it is
asked to correct it. Rate limits (429) and connection errors are retried with back-off.
Token counts are collected for the cost estimate.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError

THINK_TAG = re.compile(r"<think>.*?</think>", re.DOTALL)


@dataclass
class CallResult:
    ok: bool
    parsed: BaseModel | None
    error: str | None
    prompt_tokens: int = 0
    completion_tokens: int = 0


def extract_json(text: str) -> dict:
    """Returns the first JSON object in a model answer, skipping <think> blocks and code fences."""
    text = THINK_TAG.sub("", text or "").strip()
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text[i:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON object found in the answer")


class LLMClient:
    """One model from config.yaml ('filter' or 'analysis')."""

    def __init__(self, config: dict, model_key: str, mock: bool = False):
        self.model_key = model_key
        self.model_cfg = config["models"][model_key]
        self.defaults = config.get("defaults", {})
        self.mock = mock
        provider = config["provider"]
        self.client = None
        if not mock:
            api_key = os.environ.get(provider["api_key_env"])
            if not api_key:
                raise RuntimeError(f"{provider['api_key_env']} is not set (see .env.example)")
            self.client = OpenAI(
                base_url=provider["base_url"],
                api_key=api_key,
                timeout=self.defaults.get("timeout_s", 180),
                max_retries=0,  # retries are handled below
            )

    def _request(self, messages: list[dict]):
        params = dict(self.model_cfg.get("params", {}))
        extra_body = params.pop("extra_body", None)
        kwargs = dict(model=self.model_cfg["model_id"], messages=messages, **params)
        if extra_body:
            kwargs["extra_body"] = extra_body

        for wait_round in range(self.defaults.get("rate_limit_retries", 5) + 1):
            try:
                return self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                retry_after = None
                if e.response is not None:
                    retry_after = e.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else min(60, 5 * 2 ** wait_round)
                print(f"    [{self.model_key}] rate limited, waiting {delay:.0f} s...")
                time.sleep(delay)
            except (APITimeoutError, APIConnectionError) as e:
                delay = min(60, 5 * 2 ** wait_round)
                print(f"    [{self.model_key}] {e.__class__.__name__}, retrying in {delay} s...")
                time.sleep(delay)
        raise RuntimeError("request failed after repeated rate-limit or connection errors")

    def call(
        self,
        system: str,
        user: str,
        schema_model: type[BaseModel],
        mock_response: dict | None = None,
    ) -> CallResult:
        if self.mock:
            parsed = schema_model.model_validate(mock_response)
            return CallResult(True, parsed, None)

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        max_attempts = self.defaults.get("max_retries", 3)
        totals = {"prompt": 0, "completion": 0}
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                resp = self._request(messages)
            except APIStatusError as e:
                # 4xx errors (wrong model id, unsupported parameter) will not fix themselves
                last_error = f"API {e.status_code}: {str(e)[:300]}"
                break
            except RuntimeError as e:
                last_error = str(e)
                break

            usage = getattr(resp, "usage", None)
            if usage:
                totals["prompt"] += usage.prompt_tokens or 0
                totals["completion"] += usage.completion_tokens or 0

            raw_text = resp.choices[0].message.content or ""
            try:
                parsed = schema_model.model_validate(extract_json(raw_text))
                return CallResult(True, parsed, None, totals["prompt"], totals["completion"])
            except (ValueError, ValidationError) as e:
                last_error = f"invalid JSON: {str(e)[:300]}"
                # Show the model its own answer and the validation error, then ask again
                messages = messages[:2] + [
                    {"role": "assistant", "content": raw_text[:4000]},
                    {"role": "user", "content": "Your previous answer was not valid JSON for the "
                     f"required schema. Error: {str(e)[:500]}. Return ONLY the corrected JSON object."},
                ]

        return CallResult(False, None, last_error, totals["prompt"], totals["completion"])
