// frontend/src/lib/types.ts

export type Sentiment = "positive" | "negative" | "neutral";
export type Category = "講義内容" | "講義資料" | "運営" | "その他";

export interface CommentAnalysis {
  id: number;
  original_text: string;
  sentiment: Sentiment;
  category: Category;
  is_critical: boolean;
  total_score: number;
  summary: string | null;
}
