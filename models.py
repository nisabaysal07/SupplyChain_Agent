"""
Data Models Schema Module:
Defines structured dataclasses for news source items, supplier news reports, 
and the final consolidated supply chain report schema.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NewsSourceItem:
    """Represents a validated and filtered individual news source item."""
    news_id: str
    title: str
    published_date: Optional[str]
    date_verified: bool
    effective_date: Optional[str]
    source_name: str
    source_type: str            
    url: str
    relevance: str             
    summary: str


@dataclass
class SupplierNewsReport:
    """Represents aggregated news and status reports for a specific supplier query."""
    query_id: str
    query: str
    query_type: str             
    priority: Optional[str]
    company_country: str
    supplier_country: Optional[str]
    logistics_point: Optional[str]
    location_country: Optional[str]
    supplier_names: List[str]
    products: List[str]
    status: str                 
    search_errors: List[str] = field(default_factory=list)
    sources_found: List[NewsSourceItem] = field(default_factory=list)


@dataclass
class FinalCleanSupplyReport:
    generated_at: str
    plan_generated_at: Optional[str]
    reports: List[SupplierNewsReport]