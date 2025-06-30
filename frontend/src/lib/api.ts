// frontend/lib/api.ts

import { CommentAnalysis } from "./types";

// バックエンドのURL (環境変数から取得するのが望ましいが、ここでは直接記述)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function analyzeCsvFile(file: File): Promise<CommentAnalysis[]> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/analysis/analyze`, {
    method: "POST",
    body: formData,
    // headers: { 'Content-Type': 'multipart/form-data' } // fetchが自動で設定するため不要
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "分析中にエラーが発生しました。");
  }

  return response.json();
}
