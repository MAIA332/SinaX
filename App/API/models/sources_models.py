from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SourcesExecute(BaseModel):
    plugin_name:str
    method_name:str
    args:Optional[list]