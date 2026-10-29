from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# The only allowed values for a source's status.
SourceStatus = Literal["Processing", "Processed", "Failed"]


class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str
    size: int
    uploaded_at: datetime
    timestamp_is_estimated: bool
    status: SourceStatus


class SourceListResponse(BaseModel):
    sources: list[SourceMetadata]