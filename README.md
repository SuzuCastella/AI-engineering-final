講義アンケートを自動集計・分析するアプリです。

起動方法は以下の通りです。

①gemini api key を取得し、backend/.env に記入

```env
GEMINI_API_KEY=XXXXXXXXXXXXXX
```

②bash にて、以下を実行

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd frontend
npm run dev
```

③http://localhost:3000 にアクセス
