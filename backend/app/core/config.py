# backend/app/core/config.py

import os
from dotenv import load_dotenv

# パスの指定を削除。これで、実行時のカレントディレクトリにある .env を自動で探してくれる。
load_dotenv()

class Settings:
    """アプリケーションの設定を管理するクラス"""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
    PROJECT_NAME: str = "講義アンケート分析アプリ"
    API_V1_STR: str = "/api/v1"

settings = Settings()

# --- ↓↓↓ 正しく読み込めたか確認するためのデバッグ用コードです ↓↓↓ ---
print("--- 起動時のAPIキー読み込みチェック ---")
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    # キーの全体が表示されないように、安全な形で末尾4文字だけ表示します
    print(f"✅ APIキーが.envファイルから読み込まれました。(キーの末尾: ...{settings.GEMINI_API_KEY[-4:]})")
else:
    print("❌ 警告: APIキーが.envファイルから読み込めていません。.envファイルの場所と内容を確認してください。")
print("------------------------------------")