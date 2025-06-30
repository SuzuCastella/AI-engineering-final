from fastapi import APIRouter
from .endpoints import files, report # analysis から files に変更

api_router = APIRouter()
# prefixを/filesに変更し、新しいルーターを登録
api_router.include_router(files.router, prefix="/files", tags=["File Analysis"])
api_router.include_router(report.router, prefix="/report", tags=["Report Generation"])