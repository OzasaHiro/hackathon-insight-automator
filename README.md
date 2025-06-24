# Hackathon Insight Automator 🚀

AI関連ハッカソンの入賞プロジェクトを自動収集・分析し、技術トレンドレポートを生成するPythonアプリケーション。Google Gemini AIによる詳細分析機能付き。

## 主な機能 ✨

- 🔍 **AI関連ハッカソンの自動検索**: Devpostから最新のAI/MLハッカソンを自動検出
- 🤖 **LLM分析**: Google Gemini 2.5 Flashによるプロジェクト詳細分析
- 🎯 **AI自動選択**: LLMが最適なハッカソンを自動選択（--auto-select）
- 📊 **技術トレンド分析**: 使用技術の統計と人気度ランキング
- 💡 **AIアイデア生成**: トレンド分析から新しいMVPアイデアを生成（--generate-ideas）
- 📝 **自動レポート生成**: Markdownフォーマットの包括的なレポート
- 🎯 **インタラクティブ選択**: 複数のハッカソンから分析対象を選択可能

## 必要要件

- Python 3.8以上
- Google Gemini API キー（[取得方法](https://makersuite.google.com/app/apikey)）

## セットアップ

### クイックスタート（推奨）
```bash
# セットアップスクリプトを実行
./setup.sh

# 仮想環境を有効化
source venv/bin/activate

# Gemini API キーを設定（LLM分析用）
export GOOGLE_API_KEY="your_gemini_api_key_here"

# スクレイピング実行（検索モード）
cd src
python main.py --search
```

### 手動セットアップ

#### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd HackathonReport
```

#### 2. 仮想環境の作成と有効化
```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

#### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

#### 4. Playwrightのセットアップ
```bash
playwright install
```

#### 5. 環境変数の設定
```bash
cp .env.example .env
# 必要に応じて.envファイルを編集
```

## 使用方法

### 基本的な使用方法（推奨）

#### 🔍 検索モード - 最近のAIハッカソンから選択
```bash
cd src
# 手動選択
python main.py --search

# AI自動選択（新機能！）
python main.py --search --auto-select

# AI自動選択 + アイデア生成（新機能！）
python main.py --search --auto-select --generate-ideas
```

実行すると以下のような画面が表示されます：
```
Recent AI Hackathons
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ No.┃ Name                    ┃ Participants┃ URL                 ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ UC Berkeley AI Hackathon│ 1037        │ https://...         │
│ 2  │ AI Innovation Challenge │ 89          │ https://...         │
└────┴─────────────────────────┴─────────────┴─────────────────────┘

# 手動選択の場合
Select hackathon (1-2) or 'q' to quit: 

# AI自動選択の場合
Using AI to select the best hackathon...

🤖 AI Selection: UC Berkeley AI Hackathon

📊 Selection Scores:
- Participant Count: 9/10
- Recency: 8/10
- AI Relevance: 10/10
- Overall: 9/10

💡 Reasoning: This hackathon has the highest participant count indicating strong competition and quality projects.

✓ AI Selected: UC Berkeley AI Hackathon
Proceed with this selection? (Y/n):
```

#### プロジェクトをスクレイピング
```bash
cd src
python main.py https://devpost.com/software/example-project
```

#### ハッカソンをスクレイピング（複数プロジェクト）
```bash
cd src
python main.py https://example-hackathon.devpost.com/project-gallery
```

#### オプション付きで実行
```bash
cd src
# ヘッドレスモードで実行（ブラウザ非表示）
python main.py --search --headless

# リクエスト間隔を変更
python main.py --search --delay 3

# 出力ディレクトリを指定
python main.py --search --output-dir ../custom_data --reports-dir ../custom_reports

# LLM分析を無効化（高速化したい場合）
python main.py --search --no-llm

# URLを直接指定してヘッドレスモード
python main.py https://devpost.com/software/example --headless

# ヘルプを表示
python main.py --help
```

### 出力ファイル

実行後、以下のファイルが生成されます：

#### 📁 生データ（JSON形式）
`data/raw/hackathon_YYYYMMDD_HHMMSS.json`
- プロジェクト詳細
- 技術タグ
- GitHubリンク
- LLM分析結果

#### 📄 分析レポート（Markdown形式）
`reports/HackathonName_YYYYMMDD_HHMMSS.md`
- プロジェクト一覧と詳細
- 技術トレンド統計
- LLMによる要約と分析
- 商業的可能性の評価

### 出力例

```markdown
## Top Technologies/Tags
- **gemini**: 3 project(s)
- **flask**: 3 project(s)
- **python**: 3 project(s)

## Projects

### ASSIST
**Summary**: An AI-powered mobile application that helps users with daily tasks

**Detailed Description**: ASSIST leverages cutting-edge AI technology to provide personalized assistance for elderly users. The application uses voice recognition and natural language processing to understand user needs and provide contextual help. Built with a mobile-first approach, it integrates with smart home devices and healthcare systems. The backend uses Flask for API services and Gemini for intelligent response generation.

**Problem Addressed**: Elderly individuals face significant challenges in using modern technology and managing daily tasks independently. This leads to reduced quality of life and increased dependence on caregivers.

**Target Audience**: Adults aged 65+ who live independently but need occasional assistance with technology and daily activities

**Commercial Potential**: High

**Technical Architecture**:
  - Frontend: React Native for cross-platform mobile development
  - Backend: Flask REST API with JWT authentication
  - Database: PostgreSQL for user data and Firebase for real-time features
  - Deployment: Docker containers on Google Cloud Platform
  - External Services: Google Speech-to-Text API, Gemini AI, Twilio for notifications

**Key Features**:
  - Voice-activated assistance
  - Medication reminders
  - Emergency contact system
  - Simplified UI with large buttons
  - Integration with smart home devices

**Technical Complexity**: Medium

**Innovation Level**: High

**Unique Value**: Unlike generic voice assistants, ASSIST is specifically designed for elderly users with cognitive considerations and simplified interactions

**SWOT Analysis**:
  **Strengths**:
    - User-centric design for elderly
    - Strong AI integration
    - Cross-platform compatibility
  **Weaknesses**:
    - Requires internet connectivity
    - Initial setup complexity
  **Opportunities**:
    - Growing elderly population
    - Healthcare system integration
  **Threats**:
    - Competition from tech giants
    - Privacy concerns

**Categories**: healthcare, accessibility, ai

---

## 🚀 AI-Generated MVP Ideas

Based on the analysis of winning projects and emerging trends, here are innovative MVP ideas:

### 1. MindMesh - Collaborative AI Brain Network
**Connecting human creativity with AI intelligence for breakthrough innovations**

**Description**: MindMesh creates a neural network of human experts and AI agents working together on complex problems. It uses advanced prompt engineering to facilitate human-AI collaboration sessions where multiple specialists can brainstorm with AI assistance in real-time.

**Problem**: Complex problems require diverse expertise, but coordinating experts is difficult and AI alone lacks human intuition and creativity.

**Target Users**: Research teams, innovation labs, startup incubators

**Key Features**:
- Real-time collaborative AI workspace
- Expert matching algorithm
- AI-moderated brainstorming sessions
- Knowledge graph visualization
- Automated insight synthesis

**Tech Stack**: Python, LangChain, Neo4j, WebRTC, React, Gemini API

**AI Integration**: Uses multiple AI agents with different expertise areas to provide specialized insights during collaboration sessions

**MVP Scope**: Basic collaborative workspace with 2-3 AI agents and simple brainstorming features

**Revenue Model**: SaaS subscription for teams, premium AI agent marketplace

**Growth Potential**: Can expand to become the go-to platform for human-AI collaborative problem solving across industries
```

## プロジェクト構造

```
HackathonReport/
├── src/                    # ソースコード
│   ├── scraper/           # スクレイピングモジュール
│   ├── models/            # データモデル
│   ├── report/            # レポート生成
│   └── main.py            # エントリーポイント
├── data/                  # データ保存ディレクトリ
│   └── raw/              # 生データ
├── reports/               # 生成されたレポート
├── requirements.txt       # Python依存関係
└── .env.example          # 環境変数のサンプル
```

## 環境変数

`.env`ファイルまたは環境変数で以下を設定：

```bash
# Google Gemini API キー（必須）
GOOGLE_API_KEY=your_gemini_api_key_here

# オプション設定
SCRAPING_DELAY=2  # リクエスト間隔（秒）
MAX_CONCURRENT_REQUESTS=3  # 最大同時リクエスト数
LOG_LEVEL=INFO  # ログレベル
```

## トラブルシューティング

### よくある問題

#### 1. Playwrightエラー
```bash
# Playwrightブラウザを再インストール
playwright install
```

#### 2. 依存関係エラー
```bash
# 仮想環境を再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. スクレイピングが失敗する
- DevpostのURLが正しいか確認
- インターネット接続を確認
- `--no-headless`オプションでブラウザの動作を確認
- `--delay`オプションで間隔を長くする

#### 4. メモリ不足
- 大規模なハッカソンの場合、プロジェクト数を制限
- 十分なメモリがあるマシンで実行

### ログの確認

詳細なログを表示する場合：
```bash
cd src
python main.py <url> --log-level DEBUG
```

## 技術スタック

- **スクレイピング**: Playwright (Chromium/Firefox対応)
- **データ処理**: Pandas, Pydantic
- **LLM**: Google Generative AI (Gemini 2.5 Flash)
- **CLI**: Rich (美しいターミナルUI)
- **レポート**: Jinja2, Markdown

## パフォーマンス

- 平均処理時間: 約3-5分/ハッカソン（5プロジェクト）
- LLM分析: 約5-10秒/プロジェクト
- 同時処理: 最大3プロジェクト

## 開発状況

詳細は[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)と[DEVLOG.md](DEVLOG.md)を参照してください。

### 実装済み機能
- ✅ Devpostプロジェクトページのスクレイピング
- ✅ 基本的なハッカソンページのスクレイピング
- ✅ **AI関連ハッカソンの自動検索・選択機能**
- ✅ **LLMによる最適ハッカソン自動選択**
- ✅ **LLM分析機能（Gemini 2.5 Flash）- 詳細な技術・市場分析**
- ✅ **AIアイデア生成機能 - トレンドベースのMVP提案**
- ✅ データモデルの定義
- ✅ Markdownレポートの生成
- ✅ CLI インターフェース
- ✅ 技術トレンド分析
- ✅ GitHubリンク自動抽出

### 今後の予定
- 🔄 データベース連携（Supabase）
- 🔄 Webダッシュボード
- 🔄 定期実行機能
- 🔄 複数LLMプロバイダー対応
- 🔄 Slack/Discord通知
- 🔄 PDFエクスポート

## 貢献

プルリクエストを歓迎します！バグ報告や機能リクエストは[Issues](https://github.com/your-repo/issues)にお願いします。

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 作者

Hackathon Insight Automator Team

---

⭐ このプロジェクトが役に立ったら、スターをお願いします！