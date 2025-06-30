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

def cluster_and_summarize_comments(comments: List[str], num_clusters: int = 7) -> List[Dict[str, Any]]:
    """
    コメントのリストを受け取り、似た内容でグルーピングして要約する。
    """
    if not comments or len(comments) < num_clusters:
        # コメントが少ない場合は単純なリストとして返す
        return [{"theme": comment, "count": 1, "representative_comment": comment} for comment in comments]

    # プロンプトが長くなりすぎないように、最大500件程度に絞る
    comments_to_process = comments[:500]
    
    formatted_comments = "\n".join([f"- {comment}" for comment in comments_to_process])

    prompt = f"""
    以下のコメントリストを分析し、内容が類似するコメントを{num_clusters}個の主要なテーマに分類・集約してください。

    コメントリスト:
    {formatted_comments}

    各テーマについて、以下の情報を含むJSONオブジェクトの配列を生成してください。
    1. "theme": そのテーマを表す簡潔なタイトル（例：「資料の分かりやすさ」「課題の難易度」）。
    2. "count": そのテーマに合致するコメントのおおよその件数。
    3. "representative_comment": そのテーマを最もよく表している代表的なコメントを一つ選んでください。

    出力はJSONオブジェクトの配列のみとしてください。
    例: [{{ "theme": "...", "count": ..., "representative_comment": "..." }}, ...]
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error during comment clustering: {e}")
        return []

def generate_narrative_report(dashboard_data: Dict[str, Any]) -> str:
    """
    ダッシュボードデータを受け取り、自然言語のレポートを生成する。
    """
    # LLMに渡すために、データを簡潔なテキスト形式に変換
    summary = dashboard_data.get('summary', {})
    report_text = f"""
分析サマリー:
- 総コメント数: {summary.get('totalComments', 0)}件
- ポジティブな意見: {summary.get('positiveCount', 0)}件
- ネガティブな意見: {summary.get('negativeCount', 0)}件

ポジティブな意見の主なテーマ:
{ "、".join([t['theme'] for t in dashboard_data.get('topPositiveThemes', [])]) }

改善に関する意見の主なテーマ:
{ "、".join([t['theme'] for t in dashboard_data.get('topNegativeThemes', [])]) }
    """

    prompt = f"""
あなたは大学の講義改善を支援する優秀なアシスタントです。
以下のアンケート分析のサマリーデータを基に、講義の担当者へ報告するための簡潔なレポートを作成してください。

レポートには、以下の3つの要素を必ず含めてください。
1. **全体的な傾向**: 講義に対する受講生の全体的な満足度や反応について1〜2文で要約してください。
2. **賞賛すべき点**: ポジティブな意見のテーマを基に、特に評価されている点を2〜3点、箇条書きで挙げてください。
3. **今後の改善点**: ネガティブな意見のテーマを基に、今後改善が期待される点を2〜3点、箇条書きで挙げてください。各々の箇条書きの下に具体的な改善策を上げてください。

# 分析サマリーデータ
{report_text}

# 出力形式
## 講義アンケート分析レポート

### 全体的な傾向
（ここに要約を記述）

### 賞賛すべき点
- （ここに良かった点を記述）
- （ここに良かった点を記述）

### 今後の改善点
- （ここに改善点を記述）
- （ここに改善点を記述）
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error during report generation: {e}")
        return "レポートの生成中にエラーが発生しました。"