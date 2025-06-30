# backend/app/api/endpoints/report.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
from app.services import llm_service

router = APIRouter()

# フロントエンドから受け取るダッシュボードデータの型を定義
class DashboardData(BaseModel):
    summary: Dict[str, Any]
    categoryDistribution: Dict[str, Any]
    topPositiveThemes: List[Any]
    topNegativeThemes: List[Any]
    criticalComments: List[Any]
    topRankedComments: List[Any]

class ReportResponse(BaseModel):
    report_text: str

@router.post("/generate", response_model=ReportResponse)
async def generate_report_endpoint(dashboard_data: DashboardData):
    """ダッシュボードデータを受け取り、要約レポートを生成する"""
    try:
        # Pydanticモデルを辞書に変換してサービスに渡す
        report_text = llm_service.generate_narrative_report(dashboard_data.model_dump())
        return {"report_text": report_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レポート生成中にエラーが発生しました: {str(e)}")