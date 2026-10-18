# 参照元と実装の境界

このベースラインは、Codexの日本株IR技能と `ir-agent` の状態管理を組み合わせる。金融手順を参考にしながら、数カ月〜1年の仮説、回答分岐、問い合わせ前後の記録を追加する。独自のPython/Decimal評価器と任意SDKへの読取りアダプタを持ち、外部のエージェントランタイム、メール送信、フォーム送信、発注は導入しない。

## 保存した原文

[third_party/anthropic](../third_party/anthropic/README.md) に、Anthropicの `thesis-tracker`、`earnings-preview`、`catalyst-calendar`、`idea-generation` とApache-2.0 LICENSEを保存した。原文ファイルは無改変で、固定コミット、URL、取得日時、SHA-256は [manifest](../third_party/anthropic/manifest.json) に記録した。固定コミットの全件Git treeにNOTICEはなかった。

[jp-equity-ir](../.agents/skills/jp-equity-ir/SKILL.md) は新規の日本語運用手順である。原文の設計を参考に、次を追加・適応した。

- CodexとCLIで、会社ごとのジョブ担当と仮説版を管理する。
- 質問前に事前仮説・評価と回答分岐を保存する。
- 返信の原文引用と、変更する入力の根拠を残す。
- 無回答・曖昧な回答を機械的な否定にせず、反証役と独立に検討する。
- 日本株のコード、JPY、開示時点・対象期間・単位・会計基準を確認する。

原文のClaude用コネクタ、メール配信、カレンダー連携、空売り等は採用した実行機能ではない。資料中の指示はセッションへの命令として扱わない。

## 他の部品

| 参照元 | ベースラインでの扱い | 追加接続時の境界 |
|---|---|---|
| [J-Quants公式クライアント](https://github.com/J-Quants/jquants-api-client-python/tree/4a6ab360dbd43e763595f7ad362e749a25d6439d) | 銘柄一覧・日足を正規化する読取りアダプタを実装。SDKは任意依存、APIのライブ接続は未検証 | 契約、データ時点、APIキー、レート制限を確認して `sync` で入力へ変換。日足の取得日時と、開示の公表日時を混同しない |
| [edinet-tools](https://github.com/matthelmer/edinet-tools/tree/94fb7ec5843b751c15379f053ee70ceb8d6d0445) | 提出書類一覧の取得・正規化と保存パッケージ解析のアダプタを実装。SDKは任意依存、APIのライブ接続は未検証 | 原文と抽出値を区別し、単位、コンテキスト、連結範囲、訂正、公表日時を確認。提出書類一覧の取得だけで本文の解析まで完了したとしない |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents/tree/1394a3f72aa4393e1a98f51b382434c4b4c2d972) | 強気・弱気・リスクの分担を設計参照 | Codexの主担当・反証担当に役割を適応。LangGraph等の実行ランタイムは未導入 |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot/tree/2717499b8e30f242640af08c4ad9afd1113c2d45) | 計算・説明の分離と出典管理を設計参照。コードのコピーなし | 評価器は独自のPython/Decimal実装。FinRobot全体のランタイム・UI・計算器は未導入 |

データSDKは、会社IDと証券コード・EDINETコード、原文URL、公表日時、取得日時、対象期間、単位等を保つアダプタの内側に置く。エージェントへ生のSDKオブジェクトや提供元固有の状態を渡す前提にしない。EDINET抽出の欠損はゼロとせず、原文へ戻れるようにする。SDKの採用はデータを取得・検証済みであることを意味しない。

状態管理と評価器は標準ライブラリとSQLiteで動く。SDKはAPI取得やEDINETの保存パッケージ解析に必要な任意依存で、API認証は外部取得に必要となる。基礎のオフラインJSON入力と状態管理にはSDK・APIキーを要求しない。操作と入力例は [workflow.md](workflow.md) を参照する。

日次のジョブ確保は期限付きリースを使い、担当者は期限内に `renew` で更新できる。`inbox` は下書き・返信待ち・未評価または保留中の返信を表示する。日時と版の制約により、ジョブの評価時点より前または実際の完了より後に調査を記録することや、未来・直前版より過去の時刻に返信を評価することを拒否する。これらは作業と履歴の整合性を守る機能であり、投資判断の正しさを保証するものではない。

評価器はEPS×PERと、明示したFCF・割引率・終価成長率・株数等によるDCFを決定的に計算する。モデル入力とシナリオの妥当性は調査で確認する。`thesis` の上昇余地は保存時点の `current_price_jpy` を使う。新しい相場を取得しても仮説入力を自動更新しないため、現在の判断には新しい調査結果の `thesis_update` で価格と根拠を更新する。

FinRobotの米国SEC向け `edgartools` は、日本の `edinet-tools` とは別のプロジェクトである。FinRobot V2全体の依存にはPydanticAI、FastAPI、yfinance、edgartools等が含まれる。`pip install finrobot` とREADMEのV2計算エンジンも同じ導入経路ではないため、計算器を使う場合は対象を固定する。

Anthropicの `financial-analysis` にはDCFや比較評価もあるが、このベースラインに原文・計算器を追加導入していない。DCF原文にある `Debt Weight = Net Debt / Enterprise Value` とネットキャッシュ時に負の負債重みを許す記述を、そのままWACC計算へ採用しない。資本構成と余剰現金の扱い、評価通貨に対応する金利、税率等を別途検証する。[固定原文](https://github.com/anthropics/financial-services-plugins/blob/574ed3624aebd0418c7e96cd101262f30210ab26/plugins/vertical-plugins/financial-analysis/skills/dcf-model/SKILL.md) を参照。

## ライセンスと検証範囲

参照したルートLICENSEは、Anthropic・J-Quants・TradingAgents・FinRobotがApache-2.0、edinet-toolsがMIT。今回同梱した第三者ファイルは上記Anthropicの4技能とLICENSEで、他プロジェクトは参照先として記載した。移植する場合は対象ファイルの帰属、LICENSE、必要なNOTICE、変更表示を保持する。FinRobotにはNOTICEと商標ポリシーがある。

APIのライブ接続、契約データの網羅性、外部SDK・計算器の実行互換性、複数エージェントによる投資成績は、この保存・設計参照やアダプタのオフライン検証によって検証済みにはならない。ハーネスが検証する入力や状態管理と、金融仮説の正しさを区別して評価する。
