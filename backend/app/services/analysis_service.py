# backend/app/services/analysis_service.py
from typing import List, IO, Dict, Any
from pathlib import Path
from collections import Counter
from . import preprocessing_service, llm_service

# 引数を file: IO[bytes] から file_path: Path に変更
def analyze_comments_from_file(file_path: Path, column_name: str, batch_size: int) -> Dict[str, Any]:
    """
    CSVファイルを分析し、サマリーダッシュボード用のデータを生成する。
    """
    # この関数内でファイルを開いて、すぐに閉じるように変更
    with open(file_path, "rb") as f:
        df = preprocessing_service.preprocess_csv(f, column_name)
    
    comments = df[column_name].astype(str).tolist()

    # --- 個別コメントの分析（バッチ処理） ---
    all_results_dicts = []
    for i in range(0, len(comments), batch_size):
        batch_comments = comments[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch_comments)} comments)...")
        
        batch_results = llm_service.analyze_comments_in_batch(batch_comments)
        
        for original_comment, result_dict in zip(batch_comments, batch_results):
            if result_dict:
                result_dict['original_text'] = original_comment
                all_results_dicts.append(result_dict)

    # --- ここからが集計・サマリー処理 ---
    total_comments = len(all_results_dicts)
    sentiment_counts = Counter(r.get('sentiment') for r in all_results_dicts)
    category_counts = Counter(r.get('category') for r in all_results_dicts)
    critical_comments = [r for r in all_results_dicts if r.get('is_critical')]
    sorted_by_score = sorted(all_results_dicts, key=lambda r: r.get('score', 0), reverse=True)
    top_ranked_comments = sorted_by_score[:10]
    positive_comments = [r['original_text'] for r in all_results_dicts if r.get('sentiment') == 'positive']
    negative_comments = [r['original_text'] for r in all_results_dicts if r.get('sentiment') == 'negative']

    # LLMによるテーマ集約
    top_positive_themes = llm_service.cluster_and_summarize_comments(positive_comments, num_clusters=5)
    top_negative_themes = llm_service.cluster_and_summarize_comments(negative_comments, num_clusters=7)

    # 最終的なダッシュボード用データを構築
    dashboard_data = {
        "summary": { "totalComments": total_comments, "positiveCount": sentiment_counts.get('positive', 0), "negativeCount": sentiment_counts.get('negative', 0), "neutralCount": sentiment_counts.get('neutral', 0), },
        "categoryDistribution": dict(category_counts), "topPositiveThemes": top_positive_themes, "topNegativeThemes": top_negative_themes,
        "criticalComments": critical_comments, "topRankedComments": top_ranked_comments,
    }
    
    print(f"Dashboard data successfully generated for {total_comments} comments.")
    return dashboard_data