# ir-agent

日本株の数カ月〜1年の投資仮説を、公開情報とIRへの質問で検証するCodex用ベースライン。

Anthropicの金融技能を参考にした [Codexスキル](.agents/skills/jp-equity-ir/SKILL.md) と、Python／SQLiteのハーネスを組み合わせる。仮説・質問・回答は履歴を残し、評価額は明示した入力からプログラムで計算する。

## 起動

Python 3.11以上と [uv](https://docs.astral.sh/uv/) を使う。

```bash
uv sync --frozen
.venv/bin/python scripts/demo.py
.venv/bin/python -m unittest discover -s tests -v
```

デモは架空企業・架空資料・架空回答だけを使い、一時DBで「開示→日次調査→仮説更新→質問→返信→評価更新」を実行する。ネットワークやAPIキーは不要。期待評価額が1,278.75円から1,328.75円へ変わり、仮説がv1→v2→v3になる例を確認できる。数値は動作例で、投資推奨ではない。

API接続用の任意SDKとそのオフラインテストも使う場合：

```bash
uv sync --frozen --extra data
```

uvを使わない場合は `python3 -m venv .venv` と `.venv/bin/python -m pip install -e .`、SDKを加えるなら `-e '.[data]'` で導入できる。

## Codexから使う

このリポジトリで `$jp-equity-ir` を指定する。スキルは主担当と反証担当の分担、質問前の仮説・回答分岐、返信の原文引用を案内する。CLIはJSONを返す。

```bash
.venv/bin/ir-agent --db data/research.sqlite3 init
.venv/bin/ir-agent --db data/research.sqlite3 ingest examples/demo.json
.venv/bin/ir-agent --db data/research.sqlite3 daily --limit 5
.venv/bin/ir-agent --db data/research.sqlite3 claim --worker analyst-1 --measurement-kind synthetic
```

`claim` の `id` を使って `packet JOB_ID` で固定入力を読み、Codexが調査・反証レビューを行う。claimで返る `attempts` を保存し、`complete JOB_ID --worker analyst-1 --expected-attempt ATTEMPT --result FILE` で結果と次の仮説版を保存する。長い調査は `renew JOB_ID --worker analyst-1 --expected-attempt ATTEMPT` でleaseを延長する。再確保後に古い世代の処理を更新へ使わない。

通信再送を扱う場合は[要求ID付きclaim/renew](docs/idempotent-job-requests.md)を使う。同じ要求の再送ではleaseを増やさず、元応答と現在の有効性を分けて返す。IDなし旧呼出とは戻り値の形が異なる。

`daily` は調査キューを作る処理、`inbox` はIR質問候補・返信待ち・未評価返信を読む処理。モデルの呼び出しはこのスキルを実行するCodexが担う。日次の起動にはCodexのタスク実行基盤など外部のスケジューラを接続する。

## 実装した範囲

- 選別済み対象の管理。`active`で仮説が保存されている会社について、新着資料と点検期限から調査対象を選ぶ。保有銘柄を優先する。
- SQLiteに仮説の版・資料原文・固定入力・質問分岐・返信原文・判断履歴を保存。既存版の上書きや同じ論点の重複質問を拒否する。
- 複数workerの原子的なjob確保、同じ会社の同時処理防止、lease切れの回収、古い仮説への更新の拒否。
- EPS×PER、年末FCFFのDCF（明示終価・株主価値調整を含む）、2段階DDMのJPY評価。明示した確率による加重、上昇余地・提示シナリオの下落幅を計算し、入力を検証する。
- 質問前に回答分岐を固定。返信の引用と分類を保存し、明確な分岐を適用する場合だけ次の仮説版を追加する。曖昧な回答や無回答は価格を変えない。
- J-Quants日足・[既存会社向け財務summary](docs/jquants-financial-summary.md)・EDINET提出一覧の読み取りアダプター、保存済みEDINET XBRLの解析。SDK返却値と原資料の範囲を区別し、取得時刻・欠損を保持する。

企業へのメール／フォーム送信、証券注文、継続するモデル実行のスケジュール設定は含まない。`question mark-sent` は外部で送信済みの事実を記録するコマンド。APIのライブ接続とデータ利用条件はまだ検証していない。

## 入力と運用

[入力仕様・実行例](docs/workflow.md)、[データ接続](docs/data-sources.md)、[構成](docs/architecture.md)、[既存実装の採用境界と帰属](docs/upstream.md) を参照する。入力例は [examples](examples/) にある。公表値の明示換算は金額・比率に加え[株数単位](docs/disclosed-share-units.md)にも対応し、発行済・期中平均・自己株控除後の定義は別に保持する。

初回調査で会社、公開資料、仮説をJSONに保存する。`schema_version=1` のbundleを `ingest` してから運用する。対象がまだ選別されていない場合は `watch`、専用モデルが必要なら `special_model`、除外する場合は理由付きの `excluded` を使う。SDKの会社一覧取得だけでは調査jobは作られない。

`sync --provider jquants --date YYYY-MM-DD` と `sync --provider edinet --date YYYY-MM-DD` は、任意SDKとそれぞれの `JQUANTS_API_KEY` / `EDINET_API_KEY` がある場合に使う。キーはGitへ保存しない。DBは `data/` に置き、資料・返信・秘密情報がGitへ入らないようにする。

このベースラインは投資仮説の正しさや超過収益を実証したものではない。現在価格は仮説保存時点の入力であり、新しい相場を確認して更新する。対象社数は[全工程の計測](docs/capacity-measurement.md)と予算、決算集中日の滞留から決める。実測が不足する現時点では、運用できる社数の上限は未推定である。

## 調査したIR窓口

[2026年10月11日の窓口調査](research/ir-contacts-2026-10-11/README.md) に、公式メール・フォーム、受付条件、個人の利用条件と確認根拠を保存した。49社を調べ、37社の窓口案内を確認。個別返信なし・受付対象の制限を除いた窓口候補は35社で、29社はIRメールまたは入力項目まで確認、6社は公式案内・リンク確認の段階。株価・流動性・財務での選別は次の工程で行う。

[全社へ拡大した窓口調査](research/ir-intake-completion-2026-10-12/README.md) は、種類株の除外と10月11日までの上場変更を反映した東証国内普通株3,686社を対象にする。取得資料のある3,529社を点検し、既知の取得・解析エラー157社は保留した。未点検だった保存資料884社と追加938URLをすべて点検。IRメール・フォームの確認済み候補は1,808社で、うち個人受付の明示は341社。[全社CSV](research/ir-intake-completion-2026-10-12/all-companies.csv)、受付条件・引用、エラー保留一覧、URLごとの試行結果を保存した。IR送信は行っていない。

[保留157社の再調査](research/ir-recovery-2026-10-13/README.md)では全157社を再確認し、未試行は0社。27社の公式企業本文を復旧し、11社のIRメール・フォームを追加確認した。残る16社は本文復旧・受付未確認、130社は取得エラーで保留。累計の窓口候補は1,819社、うち個人受付の明示は343社。[今回157社の結果](research/ir-recovery-2026-10-13/recovery-companies.csv)、[更新した全社一覧](research/ir-recovery-2026-10-13/all-companies.csv)、引用・条件・試行結果を保存した。IR送信は行っていない。

## IR回答と投資判断のロジック

[判断方針](docs/decision-policy.md)は、固定版Anthropicの仮説・反証・決算シナリオ管理を基礎にする。Damodaranの評価手順とBaioらの情報価値を組み合わせ、著者の原則とプロジェクト独自の契約を分ける。具体的な株価条件・確率・将来利益の既定値は持たず、根拠が不足する判断は保留する。出力は売買の点検候補であり、外部送信・発注は行わない。

流れは、公開資料の分類、仮説と反証の記録、評価入力の確認、質問前の回答分岐の固定、返信原文の点検、許された入力だけの再評価、別途確認した価格・方針との比較である。公開資料で答えがある質問は除き、曖昧・無回答で評価額を自動変更しない。[操作手順](docs/workflow.md)と[全体の流れ](docs/ir-decision-flow.md)を参照する。

[最初の研究ベースライン](docs/research-baseline.md)では、JPXの公表選別結果を保存済み窓口台帳と照合し、受付候補121社・個人受付明示23社を抽出した。公表一覧の適用予定日と窓口の確認日を保持し、1975の既存資料で評価入力と質問の必要性を検証する。指数採用を買い推奨にせず、会社EPS・評価方法・投資家側の条件を分けて既存実装へ接続する。

| 機能 | 現在できることと境界 |
|---|---|
| `intake` | 数値仮説を作る前の公開資料分類。分類完了は金融入力や投資適格性の検証ではない。 |
| `normalize-facts` / `model-inputs` | 公表値の引用・単位・期間と実績/会社予想/外部予測の区分を保持し、モデルが使う数値の出所を点検する。予測や評価法の採用は別に記録する。 |
| `value` | EPS倍率、企業全体FCFのDCF、明示n+1期FCFFのDCF、2段階DDMを計算する。[株主価値調整](docs/explicit-equity-bridge-spec.md)では現金・非営業資産・負債・少数持分を分ける。確率なしは`aggregation: unweighted`で個別評価を保持し、平均や期待値を補わない。 |
| `cycle-margin` / `stable-reinvestment` | 著者式に沿う利益率・再投資の中間計算。全サイクル・将来予測・税や期間の適合を認定せず、評価へ自動採用しない。 |
| `regulatory-fcfe` | 明示年次NI−規制資本再投資の中間計算。必要資本や将来再投資を作らず、終価・株価へ変換しない。 |
| `research-decision-review` | [返信を必須としない価格判断](docs/research-decision-reviews.md)を、既存仮説・固定方針・価格根拠・明示保有と結び付けて保存する。過去の結果と現在の再点検を分け、公開資料だけのbaselineも区別する。 |
| `decision` / `ir-plan` | 出典付き方針・価格・回答別入力から判断候補と質問の影響を比較する。未設定の費用・リスク・鮮度・確率を独自に埋めない。 |
| `observations` / `predictions` | 観測・訂正・予測を不変の版で保存する。確率採点や根拠照合の成功を、校正や投資成績の実証としない。 |
| 読み取り専用レポート | 保存来歴、根拠、資料不足、試行計測、決算予定に加え、数値仮説前の新保存・未確認資料・研究管理日を点検する。予定を実施済み・時刻確定・自動ジョブと扱わない。 |

質問前の方針と仮説版、元返信、入力変更、判断履歴を保持する。ジョブは再確保の世代と要求ID付き再送を照合し、古いworkerの更新や二重処理を防ぐ。[保存来歴](docs/historical-availability-design.md)では申告日時と実保存を分け、後着情報を過去の入力へ混ぜない。過去時点の再研究は明示したretrospective表示を使う。

[依存返信の公開性が訂正された場合](docs/reply-dependency-holds.md)は、次の質問の事前確認と新しい金融入力の適用も保留する。当該新返信の公開性と依存側の保留を区別し、原文・過去版を維持する。

[保有情報の申告](docs/position-declarations.md)は、窓口台帳のheld既定値と分けて保存する。新しい実判断では明示申告の記録を使い、来歴不明の観測で保有確認の保留を解除しない。

数値評価が未完成でも、外部著者の条件と新しい公開事実を会社別に照合できる。[実企業の研究例](research/ir-case-studies-2026-10-15/README.md)では、公開で解ける問いと条件付きで残る定義を分けた。[外部目標株価の点検例](research/ir-author-valuation-example-2026-10-15/README.md)では、目標値を読めても算式が未確認ならIR後の再評価を再現できないことを記録する。通常dailyは数値thesisを前提とするため、会社別研究ファイルが自動スケジュール済みとは扱わない。

[既存3問のDD準備票](research/ir-dd-question-application-2026-10-15/README.md)では、Anthropicの質問準備手順を顧客数・製品比率・受注取消の定義確認へ適用した。元の回答分岐を保持し、定義の解消と価格判断を分ける。独立点検済みだが正式登録・送信は未準備。

[質問準備](docs/ir-question-preparation.md)には日本IR協議会の公開指針も参照し、公表済み業績の変動理由や計画の前提を質問対象として整理する。企業側への当時の推奨を投資家用に適応した手順で、個別の返信や価格判断を保証するものではない。

現在の実台帳は窓口1,819社のうち公開資料あり37社・財務内容あり32社、216資料（公開215・市場1）・分類215。全126job完了（intake100・定性26）、attempt123/event246/request receipt123・pending/leased0、source来歴はlegacy28/trusted188。native監視は28case・55版・165既読、内部管理日はJan15が12case・Jan16が16case。[1975・3817の年次入力接続](research/ir-graham-number-two-company-input-connection-2026-10-16/README.md)を受入済み。[公表数値索引v38](research/ir-case-studies-2026-10-15/disclosed-fact-index-v38.json)は29社230項目・43親entry・45派生source・会社/原典36組で、実台帳には223項目を派生43件として保存した。対象外8331/9702の2派生7項目はfile-only。

[日本電設工業の原4資料と推奨9値](research/ir-1950-initial-with-facts-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native case v1・既読5](research/ir-case-studies-2026-10-15/1950/native-case-setup-2026-10-16/parent-acceptance.json)と[索引の受入](research/ir-case-studies-2026-10-15/1950/disclosed-facts-2026-10-16/context-reference-only/index-connection/parent-acceptance.json)まで完了。推奨参照表現だけを採用し、旧full-context版85fe…は実台帳へ投入していない。Q1/当時FY予想・EPS/DPS、季節性と利益/NCIの区別を保持し、金融入力へは未採用。[大成温調の配当表示と追補の比較](research/ir-case-studies-2026-10-15/1904/split-dividend-composite-facts-2026-10-16/qualitative-review/parent-acceptance.json)も完了済みで、後続p10読解はfile-onlyのまま。金融仮説・実policy・正式質問・返信・送信・注文は0件。最新状態と未解決の入力は[継続作業の記録](docs/ongoing-work.md)へまとめた。

[日揮HDの原5資料と派生1資料・9表示値](research/ir-1963-initial-with-facts-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native case v1・既読6](research/ir-case-studies-2026-10-15/1963/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。公開既答9群と残余6を分け、Indonesiaの6か月混在を全社Q1と同一視せず、水ingのQ2譲渡/利益段階・当時会社予想・基本/希薄化後EPS・DPS未確認境界を保持する。旧初期file-only表示は当時の履歴で、現在は実台帳へ登録済み。金融入力・IR判断への採用は0。

[朝日工業社の初回原3資料と派生1資料・9表示値](research/ir-1975-initial-with-facts-intake-2026-10-16/parent-acceptance.json)によるnative v1・既読4の後、[カレンダーと8月6日説明会資料を保存・分類・比較](research/ir-case-studies-2026-10-15/1975/public-source-calendar-and-presentation-connection-2026-10-16/qualitative-review/actual-verification.json)し、native v2・既読6へ進めた。連結繰越高117,864百万円と施設別110,795百万円の範囲を混同せず、旧p10/13読解も手動文脈として引き継いだ。[予定4件の実DBレポート](research/ir-case-studies-2026-10-15/1975/catalyst-schedule-connection-2026-10-16/actual-report/report.stdout.json)は時刻/timezone・実施未確認を保持する。[保存会計値のNCAV研究計算](research/ir-case-studies-2026-10-15/1975/ncav-accounting-input-review-2026-10-16/README.md)は別の限定screenで、金融thesisや利確条件へは採用していない。 [通期原本を追加保存・比較](research/ir-case-studies-2026-10-15/1975/annual-earnings-book-input-discovery-2026-10-16/actual-connection/actual-verification.json)し、その時点でnative v3・既読7。年次EPS/BPSの派生sourceも比較し、現在はnative v4・既読8。実績EPS358.13円/BPS1,965.51円による[Graham Number式の参考計算](research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/README.md)は3,979.69円で、NCAVとは別の方法として保持する。

[アルトナーの原4資料と派生1資料・10表示値](research/ir-2163-initial-with-facts-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native case v1・3条件・既読5](research/ir-case-studies-2026-10-15/2163/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。[索引v34受入](research/ir-case-studies-2026-10-15/2163/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)まで完了。公開既知10群/残余7、FAQ選定5scope、単体の平均/期末・費用季節性、利益/営業CF調整/投資cashを分ける。EPSは会社の分割調整済み、中間43pre/期末21.50postは年間非合算で、金融入力・将来DPS列・IR判断へ採用していない。

CAICA DIGITALの[初期6source](research/ir-2315-initial-with-facts-intake-2026-10-16/parent-acceptance.json)と[補足1source](research/ir-2315-supplement-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native v1・3論点・既読7](research/ir-case-studies-2026-10-15/2315/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。[12表示値とv35](research/ir-case-studies-2026-10-15/2315/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)は営業黒字/経常・親会社赤字/会社nonGAAP EBITDA/当時会社予想を分離。金融外部売上の負値のgross/net・実現/評価は確認範囲で未解決、[評価法は未選択・needs_data](research/ir-case-studies-2026-10-15/2315/model-scope-review-2026-10-16/parent-acceptance.json)のまま。[公表箇所案内を求める研究票1問](research/ir-case-studies-2026-10-15/2315/question-residual-review-2026-10-16/parent-acceptance.json)は未正式・送信不可で、金融入力や価格判断へ採用していない。

2315の[年次原典1sourceを保存・分類](research/ir-2315-annual-accounting-intake-2026-10-16/parent-acceptance.json)し、[正当な定性jobでcase v2/config1・既読8へ更新](research/ir-case-studies-2026-10-15/2315/annual-accounting-qualitative-review-2026-10-16/parent-acceptance.json)した。限定1/66/67/71/72/87/88頁の過去の売買差額・約定日認識、市場有無別評価、B/S scope・P/L非区分・非活発市場原価注記・年次分解を既答へ移し、旧一般定義問の一部削減をsummaryとcase observation双方へ保存。旧7bootstrap/config/研究票は保持し、Jan16管理日維持・再queue0。現Q3の取引別適用と金融モデルはunresolved/IR価値未立証で、金融採用・新質問登録・送信は0。

[アルバイトタイムスの原短信と派生12値](research/ir-2341-disclosed-facts-intake-2026-10-16/parent-acceptance.json)を保存・分類し、[native v1・既読2](research/ir-case-studies-2026-10-15/2341/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。公開注記で商品認識売上/ARR、セグメント・全社費用/OP、特益/親会社利益予想、消却/自己株処分・cash・平均株数を分け、[公開既答と残余](research/ir-case-studies-2026-10-15/2341/question-residual-review-2026-10-16/parent-acceptance.json)へ整理した。正常利益や現在EPSは作らず、金融入力・質問は未採用。公開KPI入口の別補足はfile-only。

キャリアデザインセンターは原短信・10/1通知・10/15結果・公開QAと派生12値の5sourceを保存・分類し、[native v1・既読5](research/ir-case-studies-2026-10-15/2410/native-case-setup-2026-10-16/actual-inputs/parent-acceptance.json)を登録、初回queue0。[会社公表のPrime継続結果](research/ir-2410-listing-result-intake-2026-10-16/parent-acceptance.json)と[QA/12値](research/ir-2410-facts-with-qa-intake-2026-10-16/parent-acceptance.json)は公開既答へ移したが、独立した取下完了・取引保証とは分ける。非連結Q3/終了年度向け7月会社予想、普通/特別配当、内定承諾と辞退取消の認識を区別し、会社3,000円目標を投資家の評価額にしない。[v37受入](research/ir-case-studies-2026-10-15/2410/disclosed-facts-2026-10-16/index-connection/parent-acceptance.json)の210資料・25case/47版/144既読は登録前の歴史snapshotで、現在の28caseと混同しない。具体的な著者予測・評価法/売買閾値は未採用、正式質問・送信は0。

2163の[公式スポンサーindex](research/ir-case-studies-2026-10-15/2163/external-research-entry-followup-2026-10-16/parent-acceptance.json)と[ActionLearning原本の限定4頁](research/ir-case-studies-2026-10-15/2163/actionlearning-report-review-2026-10-16/parent-acceptance.json)は受入済みfile-onlyで、実台帳へ未算入。作成日/掲載日と旧株式基準を分け、会社由来の配当86やEPS×PERの図凡例を現在予測・公正倍率・目標株価にしない。独自予測の認定・金融採用は0。 [同原本の追加2頁](research/ir-case-studies-2026-10-15/2163/actionlearning-authorship-saved-pages-2026-10-16/parent-acceptance.json)で著者の事実整理という目的と会社中計の転載帰属を確認した補足もfile-onlyで、外部独自予測や売買規則にはしない。

[2327の静的入口](research/ir-case-studies-2026-10-15/2327/initial-public-review-2026-10-16/parent-acceptance.json)は本文未確認のfile-only、[2445の初回](research/ir-case-studies-2026-10-15/2445/initial-public-review-2026-10-16/parent-acceptance.json)はrobots HTTP302で規則未確認のため1GET停止・財務source0。資料不存在や投資除外を意味せず、実台帳へ加算していない。2459の新資料候補もfile-only・DB外で未算入。

日揮HDの[概要p6/8追補](research/ir-case-studies-2026-10-15/1963/segment-explanation-followup-2026-10-16/parent-acceptance.json)と[残余票v2](research/ir-case-studies-2026-10-15/1963/question-residual-review-v2-2026-10-16/parent-acceptance.json)は受入済みのfile-only補足で、新source/jobを作らず旧native v1を維持する。

任意の[公開情報レビュー参照](docs/workflow.md#出典付き方針で判断を点検する)で、確認範囲・時点・source ID/native SHA・逐語引用を固定し、実保存来歴と公開性訂正を照合できる。[受入済み](research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)だが、引用一致は回答不存在やIR価値・送信準備・金融採用の認証ではない。[1963のbinding-only probe](research/ir-case-studies-2026-10-15/1963/public-review-binding-probe-2026-10-16/README.md)も参照点検だけで、質問や投資判断を作成していない。

[定性レビューjob](docs/qualitative-research-jobs.md)は新資料/管理日に対応する明示opt-inで、数値thesis前の監視を扱う。外部scheduler・定時Web取得・LLMの定時実行は未設置。分類や定性jobの件数を、全研究工程の日次能力へ換算しない。

検証の最新チェックポイントは[全1,585テスト成功・37.349秒](research/ir-reference-value-integration-2026-10-16/parent-acceptance.json)。[価格なしの参考計算](docs/reference-value-spec.md)を追加し、既存6方式を価格・比率・売買判断なしで使える。旧価格付きAPIの111ケースは結果/エラーが一致し、独立レビューの必須指摘0。従前の[1,573件・38.890秒](research/ir-graham-number-valuation-integration-2026-10-16/parent-acceptance.json)では、[Graham Number](docs/graham-number-valuation-spec.md)を既存評価器へ追加し、旧5methodの24ケースは出力JSON同値、資源guardの独立指摘を修正した。従前の[1,558件・公開確認参照の固定](research/ir-public-information-review-binding-integration-2026-10-16/parent-acceptance.json)では独立2指摘を修正し、旧5planの出力はbyte同値。従来の[全1,534テスト成功・円銭の明示変換](research/ir-yen-sen-normalization-integration-2026-10-16/parent-acceptance.json)も保持する。旧33資料・143項目の全出力を維持し、原表示と数値の再現確認を金融的な採用と区別する。[存在確認後の定性レビュー](research/ir-qualitative-known-by-availability-2026-10-15/parent-acceptance.json)も含む。[新規窓口取得の元bytes保存](research/ir-contact-raw-entity-preservation-2026-10-15/parent-acceptance.json)も含む。[明示ゼロ成長の算術境界](research/ir-explicit-zero-growth-boundary-2026-10-15/parent-acceptance.json)も含む。[質問前のbaseline固定](research/ir-question-baseline-binding-integration-2026-10-15/README.md)も含む。[返信不要の研究判断保存](research/ir-research-decision-review-integration-2026-10-15/README.md)も含む。[未送信質問の閉鎖修正](research/ir-decision-logic-gap-review-2026-10-15/README.md)も含む。[財務summary日次連携](research/ir-jquants-financial-summary-integration-2026-10-15/README.md)も含む。[根拠復旧後の監視再開](research/ir-qualitative-independent-code-review-2026-10-15/README.md)も含む。[規制資本FCFEの中間計算](research/ir-regulatory-fcfe-integration-2026-10-15/README.md)も含む。[前回観測の引継ぎ](research/ir-qualitative-prior-review-2026-10-15/README.md)も含む。[定性worker向け表示](research/ir-qualitative-worker-view-2026-10-15/README.md)も利用できる。[新規だけの起票](research/ir-new-only-queue-integration-2026-10-15/README.md)、[定性job接続](research/ir-qualitative-job-integration-2026-10-15/README.md)、[株数単位](research/ir-disclosed-share-unit-integration-2026-10-15/README.md)、[保有申告](research/ir-catalog-position-boundary-review-2026-10-15/README-v3.md)の検証を含む。実企業の推奨や運用成績を検証したものではない。架空の操作例は `.venv/bin/python scripts/demo_ir_policy_workflow.py`、実運用用の未設定方針は[template](examples/decision-policy.template.json)を使う。
