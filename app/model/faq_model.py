from pydantic import BaseModel
from typing import Optional

class FAQ(BaseModel):
    question: str
    answer: str

class FAQInDB(FAQ):
    id: Optional[str]
