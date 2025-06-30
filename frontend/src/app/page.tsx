"use client";

import { useState, useMemo } from "react";
import type { ChangeEvent } from "react";
import { Chart as ChartJS, ArcElement, Tooltip, Legend, Title } from "chart.js";
import { Doughnut } from "react-chartjs-2";
import ReactMarkdown from "react-markdown";

// Chart.jsに必要なコンポーネントを登録
ChartJS.register(ArcElement, Tooltip, Legend, Title);

// ========== 型定義 ==========
interface CommentInfo {
  id?: number;
  original_text: string;
  sentiment?: string;
  category?: string;
  is_critical?: boolean;
  score?: number;
  summary?: string;
}

interface ThemeInfo {
  theme: string;
  count: number;
  representative_comment: string;
}

interface DashboardData {
  summary: {
    totalComments: number;
    positiveCount: number;
    negativeCount: number;
    neutralCount: number;
  };
  categoryDistribution: { [key: string]: number };
  topPositiveThemes: ThemeInfo[];
  topNegativeThemes: ThemeInfo[];
  criticalComments: CommentInfo[];
  topRankedComments: CommentInfo[];
}

// ========== ダッシュボード用UIコンポーネント群 ==========

// 1. 全体サマリー
const OverallSummary = ({ data }: { data: DashboardData["summary"] }) => (
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
    <div className="p-4 bg-gray-100 rounded-lg">
      <p className="text-sm text-gray-600">総コメント数</p>
      <p className="text-3xl font-bold">{data.totalComments}</p>
    </div>
    <div className="p-4 bg-green-50 rounded-lg">
      <p className="text-sm text-green-800">ポジティブ</p>
      <p className="text-3xl font-bold text-green-600">{data.positiveCount}</p>
    </div>
    <div className="p-4 bg-red-50 rounded-lg">
      <p className="text-sm text-red-800">ネガティブ</p>
      <p className="text-3xl font-bold text-red-600">{data.negativeCount}</p>
    </div>
  </div>
);

// 2. カテゴリ別円グラフ
const CategoryPieChart = ({
  data,
}: {
  data: DashboardData["categoryDistribution"];
}) => {
  const chartData = {
    labels: Object.keys(data),
    datasets: [
      {
        data: Object.values(data),
        backgroundColor: [
          "#4ade80",
          "#f87171",
          "#60a5fa",
          "#a78bfa",
          "#facc15",
          "#fb923c",
        ],
        borderColor: "#ffffff",
        borderWidth: 2,
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" as const },
      title: {
        display: true,
        text: "コメントカテゴリの割合",
        font: { size: 16 },
      },
    },
  };
  return (
    <div className="md:w-3/4 lg:w-1/2 mx-auto p-4 border rounded-lg">
      <Doughnut data={chartData} options={options} />
    </div>
  );
};

// 3. テーマ別コメントリスト
const ThemedComments = ({
  title,
  themes,
}: {
  title: string;
  themes: ThemeInfo[];
}) => (
  <div>
    <h3 className="text-lg font-semibold mb-2">{title}</h3>
    <ul className="space-y-3">
      {themes &&
        themes.map((item, index) => (
          <li
            key={index}
            className="p-3 bg-gray-50 rounded-md border border-gray-200"
          >
            <p className="font-bold">
              ▶ {item.theme} ({item.count}件)
            </p>
            <p className="text-sm text-gray-600 pl-4 mt-1 whitespace-pre-wrap">
              代表的なコメント: 「{item.representative_comment}」
            </p>
          </li>
        ))}
    </ul>
  </div>
);

// 4. 危険コメントのアラート
const CriticalCommentsAlert = ({ comments }: { comments: CommentInfo[] }) => {
  if (!comments || comments.length === 0) return null;
  return (
    <div className="p-4 bg-red-100 border-l-4 border-red-500 text-red-800 rounded">
      <h3 className="font-bold">🚨 要対応コメント ({comments.length}件)</h3>
      <ul className="list-disc list-inside mt-2 space-y-1">
        {comments.map((comment, index) => (
          <li key={index} className="whitespace-pre-wrap">
            {comment.original_text}
          </li>
        ))}
      </ul>
    </div>
  );
};

// 5. 重要度ランキング
const TopRankedComments = ({ comments }: { comments: CommentInfo[] }) => (
  <div>
    <h3 className="text-lg font-semibold mb-2">重要度の高いコメント Top 10</h3>
    <ol className="list-decimal list-inside space-y-2">
      {comments.map((comment, index) => (
        <li key={index} className="p-3 border-b last:border-b-0">
          <span className="font-bold text-blue-600">
            (スコア: {comment.score})
          </span>
          <p className="mt-1 whitespace-pre-wrap">{comment.original_text}</p>
        </li>
      ))}
    </ol>
  </div>
);

// ========== メインのページコンポーネント ==========
export default function HomePage() {
  // --- State管理 ---
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [selectedColumn, setSelectedColumn] = useState<string>("");
  const [batchSize, setBatchSize] = useState(50);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportText, setReportText] = useState<string>("");
  const [isReportLoading, setIsReportLoading] = useState(false);

  // --- コスト計算 ---
  const { estimatedCost, apiCallCount } = useMemo(() => {
    if (totalRows === 0) return { estimatedCost: 0, apiCallCount: 0 };
    const AVG_TOKENS_PER_COMMENT = 150;
    const GEMINI_FLASH_PRICE_PER_MILLION_TOKENS = 0.1875;
    const totalTokens = totalRows * AVG_TOKENS_PER_COMMENT;
    const costInUSD =
      (totalTokens / 1_000_000) * GEMINI_FLASH_PRICE_PER_MILLION_TOKENS;
    const calls = batchSize > 0 ? Math.ceil(totalRows / batchSize) : 0;
    return { estimatedCost: costInUSD, apiCallCount: calls };
  }, [totalRows, batchSize]);

  // --- イベントハンドラ ---
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setFileId(null);
      setHeaders([]);
      setTotalRows(0);
      setSelectedColumn("");
      setDashboardData(null);
      setError(null);
      setReportText("");
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError(null);
    try {
      const { file_id, headers, total_rows } = await uploadCsv(selectedFile);
      setFileId(file_id);
      setHeaders(headers);
      setTotalRows(total_rows);
      if (headers.length > 0) setSelectedColumn(headers[0]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!fileId || !selectedColumn) return;
    setIsLoading(true);
    setError(null);
    setDashboardData(null);
    setReportText("");
    try {
      const data = await startAnalysis(fileId, selectedColumn, batchSize);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!dashboardData) return;
    setIsReportLoading(true);
    setError(null);
    try {
      const result = await getReport(dashboardData);
      setReportText(result.report_text);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsReportLoading(false);
    }
  };

  // --- API呼び出し関数 ---
  async function uploadCsv(
    file: File
  ): Promise<{ file_id: string; headers: string[]; total_rows: number }> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("http://localhost:8000/api/v1/files/upload", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "アップロードに失敗しました。");
    }
    return response.json();
  }
  async function startAnalysis(
    fileId: string,
    columnName: string,
    batchSize: number
  ): Promise<DashboardData> {
    const response = await fetch("http://localhost:8000/api/v1/files/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_id: fileId,
        column_name: columnName,
        batch_size: batchSize,
      }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "分析中にエラーが発生しました。");
    }
    return response.json();
  }
  async function getReport(
    data: DashboardData
  ): Promise<{ report_text: string }> {
    const response = await fetch(
      "http://localhost:8000/api/v1/report/generate",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "レポート生成に失敗しました。");
    }
    return response.json();
  }

  // --- レンダリング ---
  return (
    <main className="container mx-auto p-4 sm:p-6 lg:p-8">
      <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
        講義アンケート コメント分析ダッシュボード
      </h1>
      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium leading-6 text-gray-900">
          1. 分析するCSVファイルを選択
        </label>
        <div className="mt-2 flex items-center space-x-4">
          <input type="file" accept=".csv" onChange={handleFileChange} />
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isLoading || !!fileId}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white enabled:hover:bg-blue-500 disabled:opacity-50"
          >
            {isLoading && !fileId ? "アップロード中..." : "アップロード"}
          </button>
        </div>
      </div>
      {fileId && (
        <div className="mt-8 bg-white p-6 rounded-lg shadow space-y-6">
          <div>
            <h2 className="text-lg font-bold">2. 分析設定</h2>
            <p className="text-sm text-gray-600 mt-1">
              ファイルから{totalRows}件の有効なコメントが検出されました。
            </p>
          </div>
          <div>
            <label
              htmlFor="column-select"
              className="block text-sm font-medium"
            >
              分析対象の列
            </label>
            <select
              id="column-select"
              value={selectedColumn}
              onChange={(e) => setSelectedColumn(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm"
            >
              {headers.map((header, index) => (
                <option key={`${header}-${index}`} value={header}>
                  {header}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="batch-size" className="block text-sm font-medium">
              バッチサイズ
            </label>
            <input
              type="number"
              id="batch-size"
              value={batchSize}
              onChange={(e) => setBatchSize(Number(e.target.value))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm"
              step="10"
              min="10"
            />
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-gray-900">概算コスト</h3>
              <p className="text-2xl font-bold text-green-600 mt-1">
                約 ${estimatedCost.toFixed(4)} USD
              </p>
              <div className="text-right">
                <h3 className="font-semibold text-gray-900">API呼び出し回数</h3>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {apiCallCount} 回
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              ※ コストは総トークン数に基づく概算値です。
            </p>
          </div>
          <div>
            <button
              onClick={handleAnalyze}
              disabled={isLoading}
              className="w-full rounded-md bg-green-600 px-4 py-3 text-base font-semibold text-white enabled:hover:bg-green-500 disabled:opacity-50"
            >
              {isLoading ? "分析中..." : `分析を開始する`}
            </button>
          </div>
        </div>
      )}

      {error && <p className="mt-4 text-sm text-red-600">エラー: {error}</p>}
      {(isLoading || isReportLoading) && (
        <div className="text-center p-8">
          <p>処理中です... 少々お待ちください。</p>
        </div>
      )}

      {dashboardData && !isLoading && (
        <div className="mt-8 space-y-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-2xl font-bold border-b pb-2">分析結果サマリー</h2>
          <OverallSummary data={dashboardData.summary} /> <hr />
          <CategoryPieChart data={dashboardData.categoryDistribution} /> <hr />
          <CriticalCommentsAlert comments={dashboardData.criticalComments} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <ThemedComments
              title="👍 ポジティブなご意見の要点"
              themes={dashboardData.topPositiveThemes}
            />
            <ThemedComments
              title="💡 改善に関するご意見の要点"
              themes={dashboardData.topNegativeThemes}
            />
          </div>{" "}
          <hr />
          <TopRankedComments comments={dashboardData.topRankedComments} />{" "}
          <hr />
          <div className="text-center space-y-4">
            <button
              onClick={handleGenerateReport}
              disabled={isReportLoading}
              className="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white enabled:hover:bg-purple-500 disabled:opacity-50"
            >
              {isReportLoading
                ? "レポートを生成中..."
                : "改善傾向レポートを生成"}
            </button>
            {reportText && (
              <div className="p-4 bg-gray-50 rounded-lg text-left border mt-4">
                <div className="prose prose-sm sm:prose-base max-w-none">
                  <ReactMarkdown>{reportText}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
