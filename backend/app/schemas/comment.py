from pydantic import BaseModel
from typing import Literal, Optional

class CommentAnalysis(BaseModel):
    """分析結果の単一コメントデータモデル"""
    id: int
    original_text: str
    sentiment: Literal['positive', 'negative', 'neutral']
    category: Literal['講義内容', '講義資料', '運営', 'その他']
    is_critical: bool = False
    total_score: int
    summary: Optional[str] = None