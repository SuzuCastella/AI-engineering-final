# backend/app/services/analysis_service.py

from typing import List, IO
from app.schemas.comment import CommentAnalysis
from . import preprocessing_service, llm_service

# 引数に batch_size を追加
def analyze_comments_from_file(file: IO[bytes], column_name: str, batch_size: int) -> List[CommentAnalysis]:
    """CSVファイルを指定されたバッチサイズで分析する"""
    df = preprocessing_service.preprocess_csv(file, column_name)
    
    comments = df[column_name].astype(str).tolist()
    all_results_dicts = []
    
    # 引数で受け取ったbatch_sizeを使用
    for i in range(0, len(comments), batch_size):
        batch_comments = comments[i:i + batch_size]
        print(f"Processing batch {i // batch_size + 1} ({len(batch_comments)} comments)...")
        
        batch_results = llm_service.analyze_comments_in_batch(batch_comments)
        
        for original_comment, result_dict in zip(batch_comments, batch_results):
            if result_dict:
                result_dict['original_text'] = original_comment
                all_results_dicts.append(result_dict)

    final_results = []
    for i, res_dict in enumerate(all_results_dicts):
        final_results.append(
            CommentAnalysis(
                id=i + 1,
                original_text=res_dict.get('original_text', ''),
                sentiment=res_dict.get('sentiment', 'neutral'),
                category=res_dict.get('category', 'その他'),
                is_critical=res_dict.get('is_critical', False),
                total_score=res_dict.get('score', 0),
                summary=res_dict.get('summary', '')
            )
        )

    print(f"Analysis complete. Total {len(final_results)} comments processed.")
    return final_results