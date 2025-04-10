from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class SourcesExecute(BaseModel):
    plugin_name: str
    method_name: str
    args: List[Any]

class QACache(BaseModel):
    question: str
    answer: str
    similarity_score: Optional[float] = None
    llm_provider: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None