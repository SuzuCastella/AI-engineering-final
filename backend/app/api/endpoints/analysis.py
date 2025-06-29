# backend/app/api/endpoints/analysis.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.schemas.comment import CommentAnalysis
from app.services import analysis_service

router = APIRouter()

@router.post("/analyze", response_model=List[CommentAnalysis])
async def analyze_csv_file(file: UploadFile = File(...)):
    """
    CSVファイルをアップロードして、自由記述コメントを分析するエンドポイント。
    """
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="無効なファイル形式です。CSVファイルをアップロードしてください。")

    try:
        # サービス層の分析関数を呼び出す
        results = analysis_service.analyze_comments_from_csv(file.file)
        return results
    except Exception as e:
        # エラーハンドリング
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")