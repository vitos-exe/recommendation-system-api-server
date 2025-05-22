from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class MoodBase(BaseModel):
    happy: float
    sad: float
    angry: float
    relaxed: float
    notes: Optional[str] = None


class MoodCreate(MoodBase):
    pass


class MoodRecord(MoodBase):
    id: int
    user_id: int
    recorded_at: datetime

    class Config:
        orm_mode = True


class MoodStatistics(BaseModel):
    start_date: datetime
    end_date: datetime
    records: List[MoodRecord]
