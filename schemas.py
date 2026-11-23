from pydantic import BaseModel, Field
from typing import Optional, List


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="User search query"
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results"
    )

    doc_type: Optional[str] = None
    source: Optional[str] = None
    min_score: float = Field(default=0.0, ge=-1.0, le=1.0)


class SearchResult(BaseModel):
    source: str
    page: int
    section: str
    score: float
    text: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int