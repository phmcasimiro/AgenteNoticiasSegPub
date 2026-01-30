from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NewsItem(BaseModel):
    id: str
    title: str
    url: str
    publishedAt: datetime
    source: str
    snippet: str
    language: str = "pt"
