
シリコンバレーのハッカソンでは生成 AI 関連テーマが急増し ─ スタートアップは入賞プロジェクトの分析を採用・投資判断にも活用しています  ￼。しかし Devpost など主要プラットフォームは公式 API を提供しておらず（後述）、手作業での情報収集は煩雑です。本アプリケーションは 「Pythonスクリプト実行で自動収集 → LLM で審査ポイントと再利用アイデアを抽出 → Markdownレポートをローカル生成」 を一気通貫で行い、開発者が次のハッカソンで"刺さる"テーマを素早く選定できるよう支援します。

※ 個人利用向けのスタンドアロンアプリケーションとして開発。将来的にはクラウドへのデプロイと定期実行を想定。

⸻

1. 目的 (Purpose)

ID	内容
P-1	生成 AI ハッカソンの入賞アイデア・審査観点を週次で可視化し、再利用可能なテーマバンクを構築する。
P-2	手動リサーチ負荷を削減し、開発者・企業内イノベーション担当・投資家が 24 h 以内に実行可能な MVP を発案できる状態を作る。
P-3	法令・利用規約を順守しつつ、分析レポートを Markdown 形式でローカル出力し、履歴をデータベースに蓄積する。


⸻

2. サービス概要 (Overview)

項目	詳細
名称	Hackathon Insight Automator（仮）
データ源	Devpost (RSS + スクレイピング)  ￼ ￼ ／ HackerEarth API  ￼ ￼ ／ その他大学・企業ハッカソン RSS
出力	① Markdown レポート（ローカル保存）② Web ダッシュボード (Next.js) ※将来実装
実行方法	手動実行（Python スクリプト）※将来的に GitHub Actions による定期実行を検討
想定ユーザー	個人開発者／社内新規事業チーム／VC スカウト部門


⸻

3. 機能一覧 (Major Features)

#	機能	説明
F-1	データ収集	Devpost は公式 API がないためスクレイパで受賞ページを取得  ￼ ￼。RSS から募集・結果を差分監視。
F-2	メタデータ正規化	events / projects / awards / tech_tags テーブル構造で PostgreSQL に保存。Supabase でスキーマ即 API 化  ￼ ￼。
F-3	LLM 分析パイプライン	LangChain で・テーマ分類・ジャッジコメントから審査キーフレーズ抽出・「他ドメイン転用アイデア」生成  ￼ ￼
F-4	レポート生成	上記分析結果をテンプレに差し込み、Markdown + フロント Matter を自動出力。
F-5	レポート出力	生成したレポートをローカルに保存。将来的に通知機能を追加予定。
F-6	トレンド可視化	タグ出現頻度を 4 週移動平均で表示。（Dashboard にラインチャート）
F-7	コンプライアンス管理	Devpost 利用規約順守・Rate-Limit 設定  ￼。


⸻

4. システム構成 (System Architecture)

graph TD
A[Python Script<br>Manual Execution] --> B{Scraper<br>(Playwright/Python)}
B --> C[(Supabase<br>Postgres)]
C --> D[LangChain<br>LLM Worker]
D --> E[Markdown Report]
E --> F[Local File System]
E --> G[Next.js Dashboard<br>(Future)]

	•	Scraper: Playwright で動的ページをレンダリングし JSON 化  ￼
	•	LLM Worker: OpenAI o3 もしくは OpenLLM エンドポイント経由  ￼
	•	将来的な CI/CD: GitHub Actions + Fly.io / Vercel で自動デプロイ。

⸻

5. データフロー (Data Flow)
	1.	Fetch Stage – RSS 取得 → 新規 URL 判定 → 取得キューへ。
	2.	Scrape Stage – Playwright が HTML → JSON へ。画像は Storage へ保存。
	3.	Store Stage – Supabase へ INSERT／UPSERT。
	4.	Process Stage – LangChain Pipeline が  a) タグ付け b) 審査要因抽出 c) 転用案生成。
	5.	Publish Stage – テンプレに差し込み Markdown 化 →
a) ローカルファイルシステムに保存 / b) 将来: GitHub Pages へ push / c) 将来: Dashboard 更新。

⸻

6. 非機能要件 (Non-functional Requirements)

カテゴリ	要件
パフォーマンス	手動実行時は 30 分以内、同時スクレイプ 5 並列以下。
セキュリティ	API キーは環境変数または設定ファイルで管理。PII は取得しない。
法令順守	robots.txt チェックと Devpost TOS に従い、商用利用時は別途許諾取得  ￼。
可観測性	ログ出力によりジョブ状態を可視化。
可用性	失敗時は再実行可能。DB は WAL でバックアップ。


⸻

7. 使用技術スタック (Tech Stack)

レイヤ	技術候補
フロント	Next.js + Tailwind CSS（将来実装）
バックエンド	Python (FastAPI), Playwright, LangChain
DB & Auth	Supabase (PostgreSQL, Row-Level Security)  ￼
通知	将来実装予定（SendGrid / Slack / Discord）
MLOps	OpenAI o3 / OpenLLM + LangChain Integrations  ￼
実行環境	ローカル Python 環境 → 将来: GitHub Actions による定期実行


⸻

8. ロードマップ (6 週間 MVP)

週	目標
1	DB スキーマ & RSS 取得モジュール
2	Playwright Scraper + 重複排除
3	LangChain Pipeline（分類 & 抽出）
4	Markdown レポートテンプレート
5	レポート出力 & 将来のDashboard設計
6	βテスト → ドキュメント整備


⸻

9. リスクと対策 (Risks & Mitigations)

リスク	対策
Devpost 側 UI 変更 → スクレイパ故障	E2E テスト＋Playwright Selectors のバージョン管理
利用規約変更	毎月 TOS 差分チェック & 法務レビュー
LLM 出力の誤情報	Chain 段階で URL バリデーション & Fact-check フラグ


⸻

10. 付録 (Appendix)
	•	参考実装リポジトリ – Unofficial Devpost API  ￼
	•	LLM パイプライン詳細 – LangChain チュートリアル & パイプライン構築例  ￼ ￼

⸻

この仕様をベースに MVP を組み、実データでパイプラインの精度とレポート品質を検証していくことを推奨します。