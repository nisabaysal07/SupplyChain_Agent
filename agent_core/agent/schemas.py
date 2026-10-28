"""Structured outputs expected from the models.

Each Pydantic model is used twice: written into the prompt as a JSON Schema, and used
to validate the answer. Field descriptions are part of the prompt, so they are written
as instructions to the model.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Same values as article_analyses.event_type in the database
EventType = Literal[
    "tariff_increase",
    "tariff_decrease",
    "trade_restriction",
    "transport_disruption",
    "price_change",
    "other",
    "not_relevant",
]


# Shared by both stages so the filter and the analysis classify events the same way
EVENT_TYPE_HELP = (
    "tariff_increase / tariff_decrease = Turkish customs duty or other Turkish tax on the product (VAT, "
    "special consumption tax, Culture Fund), including trade agreements that change duties; "
    "trade_restriction = ban, quota, licence, sanction or new mandatory certificate needed to export or "
    "import; transport_disruption = problem at a departure or arrival point; price_change = market "
    "price of a part; other = affects a supplier but none of these; not_relevant for 'none'."
)


# Stage 1: screening filter

ImpactLevel = Literal["direct", "none"]


class FilterItem(BaseModel):
    news_id: str
    impact_level: ImpactLevel = Field(
        description="direct = relevant, changes cost, availability or delivery of what we buy from a "
        "supplier (alert); none = not relevant."
    )
    affected_supplier_ids: list[str] = Field(
        description="Affected supplier IDs copied exactly from the list. Empty if impact_level is 'none'."
    )
    event_type: EventType = Field(description=EVENT_TYPE_HELP)
    reason: str = Field(description="One short sentence: why this level, and why it matters to us.")


class FilterBatch(BaseModel):
    results: list[FilterItem] = Field(description="Exactly one entry per input news item.")



# Stage 2: impact analysis

class AffectedSupplier(BaseModel):
    supplier_id: str = Field(description="ID copied exactly from the supplier list.")
    why: str = Field(description="One sentence: why this supplier is affected.")


class ImpactAnalysis(BaseModel):
    affected_suppliers: list[AffectedSupplier]
    event_type: EventType = Field(description=EVENT_TYPE_HELP)
    status: Literal["enacted", "proposed", "ongoing_event", "unclear"] = Field(
        description="enacted = adopted measure or price change that happened; proposed = draft or planned; "
        "ongoing_event = transport disruption happening now; unclear = the text does not say, or a forecast "
        "price change.")
    country: Optional[str] = Field(description="Country the measure or event concerns, or null.")
    affected_locations: list[str] = Field(
        description="For transport disruptions: the departure or arrival points from the supplier "
        "list that the event hits, copied exactly as written there. Empty list for other event types."
    )
    rate_type: Optional[Literal["gv", "igv", "kultur_fonu", "kdv", "otv"]] = Field(
        description="Which Turkish tax the rates are: gv = customs duty (gumruk vergisi), igv = additional "
        "customs duty (ilave gumruk vergisi), kultur_fonu = Culture Fund, kdv = VAT, otv = special consumption "
        "tax. Null if the news is not about a tax or the text does not say which one."
    )
    old_rate_pct: Optional[float] = Field(
        description="Previous tax rate in percent ONLY if stated in the text, else null."
    )
    new_rate_pct: Optional[float] = Field(
        description="New tax rate in percent ONLY if stated in the text, else null."
    )
    effective_date: Optional[str] = Field(
        description="YYYY-MM-DD date a regulatory measure enters into force, ONLY if the text states it. "
        "Never use the article's publication date instead. Null if no date is stated, for proposals without "
        "a date and for ongoing events."
    )
    expected_delay_days: Optional[int] = Field(
        description="For transport disruptions (strikes, disasters, closures at a port or airport): how many "
        "days shipments are expected to be delayed or stopped, ONLY if the text states it, "
        "else null. Convert to days (2 weeks = 14, 72 hours = 3). For a range or 'at least' / 'up to', "
        "use the LARGEST number stated. Null for tariffs and other regulatory measures."
    )
    price_change_pct: Optional[float] = Field(
        description="For price changes: how much the market price of the part changed, in percent, with a "
        "sign (+40 = up 40 percent, -5 = down 5 percent), ONLY if the text states it, else null. For a range "
        "use the largest number. Null for other event types."
    )
    summary: str = Field(description="2-3 sentence summary for a procurement manager, in English.")
    evidence_quote: str = Field(
        description="Short exact quote from the article supporting the key facts, "
        "kept in the article's ORIGINAL language so a user can find it in the source."
    )


def prompt_schema(model: type[BaseModel]) -> dict:
    """Simplifies a Pydantic JSON Schema for the prompt.

    Every field is required and extra fields are not allowed, so the model always
    returns the full structure and writes null for unknown values.
    """
    schema = model.model_json_schema()

    def fix(node):
        if isinstance(node, dict):
            node.pop("title", None)
            node.pop("default", None)
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"].keys())
                for sub in node["properties"].values():
                    fix(sub)
            for key, value in node.items():
                if key != "properties":
                    fix(value)
        elif isinstance(node, list):
            for item in node:
                fix(item)

    fix(schema)
    return schema
