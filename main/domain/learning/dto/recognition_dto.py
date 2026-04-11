from typing import List, Optional
from pydantic import BaseModel


class PredictionItem(BaseModel):
    label: str
    prob: float


class RecognitionResultDto(BaseModel):
    type: str = "prediction"
    hand_detected: bool
    top3: List[PredictionItem]
    target: Optional[str] = None
    score: float = 0.0
    is_passed: bool = False
