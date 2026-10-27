
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    size: int
    uploaded_at: datetime
    timestamp_is_estimated: bool
    status: str


class SourceListResponse(BaseModel):
    sources: list[SourceMetadata]
