```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd frontend
npm run dev
```

エラー: 分析中にエラーが発生しました: module 'app.services.llm_service' has no attribute 'analyze_comments_in_batch'
