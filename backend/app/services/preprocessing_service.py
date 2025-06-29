# backend/app/services/preprocessing_service.py

import pandas as pd
from typing import IO

def preprocess_csv(file: IO[bytes], column_name: str) -> pd.DataFrame:
    """
    アップロードされたCSVファイルを読み込む。
    複数の文字コードを試し、最適なもので読み込む。
    """
    # 試行する文字コードのリスト
    encodings_to_try = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis']
    df = None

    for encoding in encodings_to_try:
        try:
            # ファイルの読み取り位置を毎回先頭に戻すことが重要
            file.seek(0)
            
            # 指定した文字コードで読み込みを試行
            df = pd.read_csv(file, encoding=encoding)
            
            # 成功したら、どの文字コードで成功したかターミナルに表示
            print(f"Successfully read CSV with encoding: '{encoding}'")
            break  # 読み込みに成功したらループを抜ける

        except (UnicodeDecodeError, pd.errors.ParserError):
            # 読み込みに失敗した場合は、次の文字コードを試す
            print(f"Failed to read with encoding: '{encoding}'. Trying next...")
            continue
    
    # すべての文字コードで読み込みに失敗した場合
    if df is None:
        raise ValueError("サポートされている文字コード（UTF-8, CP932, Shift_JIS）でファイルを読み込めませんでした。ファイルの形式を確認してください。")

    # --- 以下は、ファイル読み込み成功後の共通処理 ---
    if column_name not in df.columns:
        raise ValueError(f"指定された列'{column_name}'がCSVに見つかりません。")
    
    # コメントが空の行を削除
    df.dropna(subset=[column_name], inplace=True)
    df = df[df[column_name].str.strip() != '']
    
    print(f"CSVファイルを読み込み、'{column_name}'列から{len(df)}件のコメントを前処理しました。")
    return df