# 日本株IRリサーチのベースラインと組合せ方針

設計決定日：2026-10-11（日本時間）。投資期間は数カ月〜1年。Codexスキル、SQLiteの状態管理、日次キュー、独自のEPS×PER／DCF計算器、読み取り用SDKアダプターをベースラインとして実装した。入力・実行手順は [workflow.md](workflow.md) を参照する。契約APIのライブ接続、外部送信、常時稼働するスケジューラは未設定。

## ベースライン

金融調査の手順と記録形式には、Anthropicの `equity-research` と `financial-analysis` の技能を採用する。Codexの技能として使えるように、日本株の資料・通貨・会計・企業コード・利用ツールへ適応する。日次の実行と状態保存を担うハーネスは、この手順を呼び出す薄い構成にする。

| 部品 | 採用方針 | 役割 |
|---|---|---|
| Anthropic金融スキル | 調査手順・記録形式の土台として適応 | 候補抽出、仮説・反証条件、決算シナリオ、イベント管理、評価手順 |
| J-Quants公式Pythonクライアント | 銘柄一覧・日足取得アダプターを実装 | 株価、売買代金の原値を保持。財務APIは今後の接続対象 |
| edinet-tools | 提出一覧の取得と保存済みXBRLの解析アダプターを実装 | 単位・会計基準・訂正を保持。書類ダウンロードの運用は今後の接続対象 |
| TradingAgents | 強気・弱気・リスクの役割設計をCodexのサブエージェントへ移植 | 仮説に対する反証と判断レビュー |
| FinRobot | 計算と説明の分離、出典管理を参考に採用。評価器は独自実装 | 決定的な評価計算と数値の追跡 |
| IR案件管理 | このプロジェクトで追加 | 質問の選別、回答分岐、問い合わせ・返信の状態、仮説と評価額の更新 |

技能の主な対応は `idea-generation` → 候補抽出、`thesis-tracker` → 仮説管理、`earnings-preview` / `earnings-analysis` → 決算前後の比較、`catalyst-calendar` → 調査時期の管理。評価は `comps-analysis` / `dcf-model` の手順を参考にする。方法・入力・計算式は日本株の対象事業に合わせて検証する。

各部品は共通の会社・開示・仮説記録を通じて接続する。Codexが調査とレビューを担当し、データ取得・金額計算・状態更新は明確な入力と出力を持つプログラムで処理する。SDKや計算器を交換しても仮説・質問履歴を保持できる境界にする。

## 既存のIR対応と追加する範囲

公開されたIR資料・決算説明会を読む機能は既存プロジェクトにある。AnthropicのEarnings Reviewerは会社開示や決算説明会の全文を扱う。FinRobotにも決算説明会全文の取得機能や公開資料を検索する例がある。ただし、確認したソースの範囲では、こちらから企業へメール／フォームで問い合わせ、返信に応じて事前仮説を更新する一連の案件管理は揃っていない。

追加する流れは以下とする。

`公開情報 → 事前仮説・評価 → 未解決点 → 質問と回答分岐 → 質問の選別 → 返信の記録 → 仮説・評価・判断の更新`

質問候補は、回答が買い・見送り・保有・売却の判断や評価額を変える見込みで選ぶ。問い合わせ本数を日次目標にしない。質問を作る前に、どの回答がどの仮説・モデル入力を変えるか記録する。

例えば「利益率低下は一時的な採用費が原因」という仮説なら、公開資料を示して費用の性質・継続性の説明を求める。一時費用との整合性、恒常費用であること、説明だけでは判断不能であることを分岐として保持し、収益予想への影響を評価する。返答の好意的な語調や無回答そのものを、機械的な売買シグナルにしない。

## 共通記録と日次運用

少なくとも次の情報を継続して保存する。

- **会社・開示**：安定した会社ID、証券コード、EDINETコード、資料URL、公表日時、取得日時、対象期間、単位、連結範囲、会計基準、訂正との関係。
- **投資仮説**：仮説の版、根拠、反証条件、強気・基本・弱気のモデル入力と評価額、次の材料、再評価日、判断履歴。
- **IR案件**：質問ID、問い合わせ先の確認日、質問の前提資料、変えるモデル入力、回答別の扱い、質問・返信の原文、送信・返信・追加質問の日時と状態。

実装済みのIR状態は、下書き、返信待ち、回答済み、回答拒否、期限切れ、取消。追加質問は別IDと論点を使って保存する。同じ会社の同じ未解決点を重複して問い合わせない。送信する前の仮説・回答分岐は保存し、後の解釈と区別する。

日次スケジューラは共通データを取得し、重要な変更や点検期限の会社を調査待ちに入れる。保有銘柄、反証となる開示、期限の近い材料を優先する。対象社数は詳細調査の全工程の利用量、予算、決算集中日の滞留を計測して決める。固定の初期社数やworker数からの上限を推定せず、[実測の不足](capacity-measurement.md)を明示する。企業ごとの更新担当を決め、共通資料を再利用する。

## 移植・接続で確認する点

Anthropicの技能にはClaudeのツールや米国市場を前提とする部分がある。例えばManaged AgentのTranscript Readerは英字中心の銘柄コードとASCIIのガイダンスを想定している。日本株の数値コード・日本語・JPY・日本の決算期に適応する。日次運用では、利用できないコンセンサスや資料を推測で補わず、取得状態と不足を記録する。

評価手順も検証対象とする。AnthropicのDCF原文には `Debt Weight = Net Debt / Enterprise Value` と負のDebt Weightを許す記述がある。WACCの資本構成や余剰現金の扱いは採用する評価手法に沿って定義し、この既定手順を自動採用しない。通貨に対応する無リスク金利、税率、成長率等も記録する。

FinRobotのDCF演算子には独立利用できる余地がある。静的な依存確認では、DCFは内部の金融モデル・閾値・WACCに依存し、金融モデルの外部依存はPydantic。計算器を移植する場合は入力・出力の型、既定値、独自の補正まで確認する。V2全体のインストールはデータ・UI・別のエージェントランタイムも導入するため、必要な演算子と依存ファイルを選んで接続する。JPYデータをUSDへ正規化する既存の取得処理は、今回のJPY評価には移植しない。

FinRobotの仮説管理技能にはAnthropic由来のものがあるため、同じ技能は一つに集約する。FinRobot側の米国SEC向け `edgartools` と、日本の `edinet-tools` は別プロジェクトとして扱う。

Anthropic・TradingAgents・FinRobot・J-Quantsは確認したルートLICENSEがApache-2.0、edinet-toolsはMIT。実際にファイルを移植するときは対象ファイルのライセンスを確認し、帰属・LICENSE・必要なNOTICE・変更表示を保持する。取得データの利用条件はSDKのライセンスと別に確認する。

## 固定した参照先と確認範囲

公開README、技能、関連するソースを静的に確認し、独自ハーネス・評価器と任意SDKのオフライン動作を検証した。原文を保存したのはAnthropicの4技能。全参照プロジェクトの実行監査、契約APIへのライブ接続、送信機能やスケジューラの設定は行っていない。

- Anthropic [`thesis-tracker`](https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md)、[`dcf-model`](https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/vertical-plugins/financial-analysis/skills/dcf-model/SKILL.md)、[Earnings Reviewer](https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md)、[Transcript Reader](https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/managed-agent-cookbooks/earnings-reviewer/subagents/transcript-reader.yaml)。コミット `574ed3624aebd0418c7e96cd101262f30210ab26`。
- TradingAgents [状態定義](https://github.com/TauricResearch/TradingAgents/blob/1394a3f72aa4393e1a98f51b382434c4b4c2d972/tradingagents/agents/state.py)、[実行処理](https://github.com/TauricResearch/TradingAgents/blob/1394a3f72aa4393e1a98f51b382434c4b4c2d972/tradingagents/graph/trading_graph.py)。コミット `1394a3f72aa4393e1a98f51b382434c4b4c2d972`。
- FinRobot [DCF演算子](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/compute/operators/dcf.py)、[WACC演算子](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/engine/compute/operators/wacc.py)、[決算説明会取得](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/finrobot_desktop/finrobot/routes/data.py)、[NOTICE](https://github.com/AI4Finance-Foundation/FinRobot/blob/2717499b8e30f242640af08c4ad9afd1113c2d45/NOTICE)。コミット `2717499b8e30f242640af08c4ad9afd1113c2d45`。
- [J-Quants公式クライアント](https://github.com/J-Quants/jquants-api-client-python/tree/4a6ab360dbd43e763595f7ad362e749a25d6439d)。コミット `4a6ab360dbd43e763595f7ad362e749a25d6439d`。
- [edinet-tools](https://github.com/matthelmer/edinet-tools/tree/94fb7ec5843b751c15379f053ee70ceb8d6d0445)。コミット `94fb7ec5843b751c15379f053ee70ceb8d6d0445`。
