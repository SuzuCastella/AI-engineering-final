# backend/app/api/endpoints/files.py

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid
from pathlib import Path
from typing import List
from app.schemas.comment import CommentAnalysis
from app.services import analysis_service
import csv

router = APIRouter()
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

class UploadResponse(BaseModel):
    file_id: str
    headers: List[str]
    total_rows: int

class AnalyzeRequest(BaseModel):
    file_id: str
    column_name: str
    batch_size: int = 50

@router.post("/upload", response_model=UploadResponse)
async def upload_csv_for_preview(file: UploadFile = File(...)):
    """CSVをアップロードし、ファイルID、ヘッダー、総行数を返す"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルをアップロードしてください。")
    
    file_id = str(uuid.uuid4())
    file_path = TEMP_DIR / f"{file_id}.csv"

    # まずファイル内容をメモリに読み込む
    file_content = await file.read()
    
    # ファイルを一時保存
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ↓↓↓ 文字コード自動判定ロジックをここに追加しました ↓↓↓
    encodings_to_try = ['utf-8-sig', 'utf-8', 'cp932', 'shift_jis']
    decoded_content = None
    
    for encoding in encodings_to_try:
        try:
            decoded_content = file_content.decode(encoding)
            print(f"Successfully decoded upload preview with encoding: '{encoding}'")
            break
        except UnicodeDecodeError:
            print(f"Failed to decode with encoding: '{encoding}'. Trying next...")
            continue
    
    if decoded_content is None:
        raise HTTPException(status_code=400, detail="サポートされている文字コードでファイルを読み込めませんでした。")
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

    headers = []
    total_rows = 0
    try:
        # デコード済みの内容からヘッダーと行数を取得
        lines = decoded_content.splitlines()
        if lines:
            reader = csv.reader(lines)
            headers = next(reader)
            # コメント列だけでなく、いずれかの列にデータがあればカウントする
            total_rows = sum(1 for row in reader if any(field.strip() for field in row))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSVの解析に失敗しました: {e}")
    
    return {"file_id": file_id, "headers": headers, "total_rows": total_rows}


@router.post("/analyze", response_model=List[CommentAnalysis])
async def analyze_uploaded_file(request: AnalyzeRequest):
    """ファイルID、列名、バッチサイズを使って分析を実行する"""
    file_path = TEMP_DIR / f"{request.file_id}.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="指定されたファイルが見つかりません。再度アップロードしてください。")

    try:
        with open(file_path, "rb") as f:
            results = analysis_service.analyze_comments_from_file(
                f, request.column_name, request.batch_size
            )
        file_path.unlink()
        return results
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"分析中にエラーが発生しました: {str(e)}")