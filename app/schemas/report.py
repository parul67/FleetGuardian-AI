from datetime import datetime
from pydantic import BaseModel

class ReportCreate(BaseModel):
    name: str
    type: str  # pdf, csv

class ReportResponse(BaseModel):
    id: int
    name: str
    type: str
    file_path: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
