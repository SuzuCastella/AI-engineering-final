# backend/app/services/llm_service.py

import google.generativeai as genai
from app.core.config import settings
import json
import time
from typing import List, Dict, Any

# APIキーの設定
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def analyze_comments_in_batch(comments: List[str]) -> List[Dict[str, Any]]:
    """
    複数のコメントをバッチ処理で分析し、結果の辞書のリストを返す。
    """
    if not comments:
        return []

    # LLMに入力するコメントリストを整形
    formatted_comments = "\n".join([f'{i+1}. 「{comment}」' for i, comment in enumerate(comments)])

    # バッチ処理用の新しいプロンプト
    prompt = f"""
    以下のカスタマーレビューのリストを分析し、各レビューに対する分析結果をJSONオブジェクトの配列（リスト）として返してください。

    レビューリスト:
    {formatted_comments}

    各レビューについて、以下の項目を分析してください:
    1. sentiment: レビューの感情を "positive", "negative", "neutral" のいずれかで分類。
    2. category: レビューの主題を "講義内容", "講義資料", "運営", "その他" のいずれかで分類。
    3. score: フィードバックの重要度を1から10の整数で評価（10が最も重要）。
    4. summary: レビューの要点を日本語20字以内で簡潔に要約。
    5. is_critical: 誹謗中傷、個人攻撃、緊急対応が必要な内容が含まれる場合はtrue、そうでなければfalse。

    出力は必ず、入力されたレビューリストの順番に対応したJSONオブジェクトの配列のみとしてください。
    例: [{{ "sentiment": "...", "category": "...", ... }}, {{ "sentiment": "...", "category": "...", ... }}]
    """

    for i in range(3):  # 3回までリトライ
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
            )
            # JSON文字列をPythonのリストに変換
            results_list = json.loads(response.text)
            
            # 結果の件数が入力と一致するか確認
            if isinstance(results_list, list) and len(results_list) == len(comments):
                return results_list
            else:
                print(f"Warning: LLM response count mismatch. Expected {len(comments)}, got {len(results_list)}. Retrying...")
        
        except Exception as e:
            print(f"LLM API batch call failed (Attempt {i+1}/3): {e}")
            time.sleep(2) # 2秒待ってリトライ
    
    # すべてのリトライが失敗した場合
    print("Error: LLM batch analysis failed after all retries.")
    # 後続の処理でエラーが出ないように、入力と同じ数の空の辞書を返す
    return [{} for _ in comments]