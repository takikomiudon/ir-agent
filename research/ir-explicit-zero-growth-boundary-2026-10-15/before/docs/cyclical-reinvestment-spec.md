# 循環正常化後のROC・再投資・FCFF接続仕様案

本書は保存原典に基づく設計と最小実装の仕様である。後続実装として[純計算器](../src/ir_agent/stable_reinvestment.py)と[対象テスト](../tests/test_stable_reinvestment.py)を追加した。既存資料、実DB、1332/5480の正常利益・税・ROC・成長・再投資を変更せず、新GETも行っていない。

実装した最小計算は、**明示された次期安定期間の税引後営業利益（NOPAT）、同じ安定期の営業利益成長率g、将来新規投資のROCから、再投資率・再投資額・FCFFを分解する純計算**である。歴史的資本から将来ROCを作る機能、税/NOL計算、capex・D&A・運転資本から再投資を推定する機能は分ける。以下の原典確認だけでは、これらを自動的に一本へ接続できない。

現在の計算結果は `intermediate_only / adoption:unresolved` とし、循環DCF、終価、株価、売買条件へつながったことにはしない。以下の資本stock・税/NOL・会計部品・経済的適合の検証は未実装のままである。

## 保存原典と照合範囲

Aswath Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies*, September 2009、保存source ID `damodaran.cyclical-commodity.2009`。[著者NYU PDF](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/commodity.pdf)の保存原バイト・抽出本文は[既存sources.json](../research/valuation-model-routing-2026-10-15/sources.json)にある。

- 原PDF SHA-256: `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`。
- 保存text SHA-256: `bc0de814b9bac9a6923a09919084071f4342e1fbfe5f9665c678d32ce096ea5b`。
- 頁はPDF先頭を1とする位置。p7–8、10–11、16–18、20–25の関連本文・式・表を再確認した。
- [既存source-audit.json](../research/cyclical-normalization-2026-10-15/source-audit.json)の原典SHA、13引用、Toyota元表、独立算術、不一致記録を再利用した。元資料・同artifactは変更していない。
- 既存の[利益率仕様](cyclical-normalization-spec.md)と[純計算器](../src/ir_agent/cyclical_margin.py)は、年次OI/Sの等重み平均と指定売上への適用まで。税引後利益・再投資の入力を準備済みにしない。

以下の引用は、指定頁の保存本文と空白正規化後に逐語一致を確認した。式は改行された表示式を読み下したもの、API・定義域・記録方法は本プロジェクトの設計として区別する。

| ID / PDF頁 | 原文 | 本設計で支持される範囲 |
|---|---|---|
| CR-Q01 / p10 | “we also have to normalize return on capital, reinvestment and cost of financing” | 正常化は利益だけで完結しない。残る各入力を不況年のまま置く一般手順にはしない。 |
| CR-Q02 / p11 | “we are double counting growth, once by normalizing earnings and again by using a higher growth rate.” | 正常化と同じ回復を成長率へ再び含める二重計上を避ける。 |
| CR-Q03 / p17 | “Stable period reinvestment rate” | g/ROCはここでは安定期の関係。短期赤字・回復各年の同率投資ではない。 |
| CR-Q04 / p17 | “We will also assume that the firm will be able to generate a return on capital equal to its cost of capital on its investments.” | Toyotaに置いた将来投資ROC=WACCという仮定。全社共通ルールではない。 |
| CR-Q05 / p21 | “New investments are expected to generate a return on capital that reflects the normalized operating income and current capital invested” | Exxonでは、正常利益/資本で求める率が新規投資でも得られると別途仮定している。単なる過去ROCの算術からは導けない。 |
| CR-Q06 / p21, 注5 | “Return on capital = Operating Income (1-tax rate)/ Invested Capital” | 当該例の税引後ROCの式。利益のflow期間と資本のstock時点を残す必要がある。 |
| CR-Q07 / p21 | “Using a marginal tax rate of 38% (rather than the effective tax rate)” | 当該正常化例が採った税率の種類。日本の現行税率やNOLの既定値ではない。 |
| CR-Q08 / p24 | “Capital investedt = Capital investedt-1 + Reinvestmentt” | Table 3のpro forma資本推移の関係。実際の貸借対照表を完全に再構成する共通式とはしない。 |
| CR-Q09 / p24 | “creates a Net Operating Loss (NOL) carry forward that shelters the firm entirely from taxes in year 2 and partially in year 3” | 回復経路では損失繰越と税の時点を別に扱う。赤字×税率から即時還付を作らない。 |
| CR-Q10 / p14 | “by looking at ratios of revenue or book capital over time, rather than the absolute values.” | 設備支出・working capitalにも規模調整という方向を示す。会計部品の一意な再投資式ではない。 |

## 原典に明示された関係と、代数的分解

記号は `OI` が税引前営業利益、`τ` が明示税率、`IC` が定義・時点を指定した投下資本stock、`ROC` が当該定義での資本収益率、`g` が安定期の営業利益成長率。`r` を再投資率とする。率は小数比率であり、金額ではない。

| 関係 | 確認箇所・意味 |
|---|---|
| `ROC = OI_normalized × (1−τ) / IC` | p21注5。正常化営業利益の税引後額を、指定した簿価資本で割る例。 |
| `r = g / ROC` | p17、21、25の表示式。安定成長と将来投資ROCの仮定を置いて使用する。 |
| `Value_operating_assets = OI_base × (1+g) × (1−τ) × (1−r) / (WACC−g)` | p17。p21も同じ分子で `r=g/ROC` と表示する。今回は価値の分母やDCFを実装候補に含めない。 |
| `FCFF_t = after-tax operating income_t − reinvestment_t` | p24 Table 3の行の関係。p8はworking capitalがnegligibleの例で税引後OIからnet capexを控除する。 |

価値式の分子を分解すると、同じ安定期の次期flowについて次を得る。最後の二式は掲載式の**代数的な分解**であり、capexや運転資本の内訳からRを推定したという主張ではない。

```text
OI_next       = OI_base × (1 + g)
NOPAT_next    = OI_next × (1 − τ)       # 単純税率を使える前提が必要
r             = g / ROC_new
R_next        = NOPAT_next × r
FCFF_next     = NOPAT_next − R_next
              = NOPAT_next × (1 − r)
```

`ROC_new`という添字は、新規投資にも当該収益率が得られるという条件を見失わないための本プロジェクトの表記である。原典p21の分母は `ROC`。`g = r×ROC`への並べ替えは代数上可能でも、任意の過去ROICと任意の投資率から利益成長が必ず生じるという実証法則ではない。

最小候補では**NOPAT_nextを明示入力にする**。したがって計算器内で `×(1+g)` や `×(1−τ)` を再度行わない。基準年OIからNOPAT_nextを作る場合は、外側に別の根拠・税処理・時点の記録が必要である。基準年の税引後利益と次期税引後利益を同じfieldへ曖昧に入れない。

## ROC/ROIC：資本stockの定義と時点

この原典の式はROCである。別資料・企業の「ROIC」という名称だけで、cash控除、税、資本平均、リース・無形資産等の定義が同じだとはしない。

Exxon p21注5の資本は、2007年末の `book equity 126,044 + book debt 9,566 − cash 33,981 = 101,629 million USD`。分子は正常化OIの税引後額である。現在のmarket capitalizationをbook equityへ代入しない。価値のequity bridgeで用いるdebt 9,400 million USDも、このstockのbook debt 9,566とは別の入力である。

最低限、次をそれぞれ保持する必要がある。

| 項目 | 必要な記録・未確定事項 |
|---|---|
| 利益flow | 対象start/end、通期のラベル、正常化/実績/会社予想/仮定、税引前/後、連結範囲、通貨・金額単位、原典と計算来歴。 |
| 資本stock | as-of日、book/marketの区別、equity/debt/cash等の構成、cash控除範囲、会計基準、連結範囲、原典。 |
| flowとstockの対応 | 期首、期末、平均、別のnormalization基準日など、採用した関係と理由。原典一例からいずれかを共通既定にしない。 |
| 調整 | 買収・売却、為替、減損/再評価、非営業資産、リース・無形資産等で分母が変わる場合、必要な調整の根拠。未確認調整を作って差額を埋めない。 |
| 将来投資への適合 | 既存資産の平均収益率を、新しい投資の収益率として使う理由と対象期間。計算済みROCをそのままROC_newへコピーしない。 |

資本stockの単位は金額、分子NOPATは一期間の金額flow、結果ROCはその期間に対応した率である。期・通貨・価格基準を揃えず、四半期flowを年次率と呼んだり日数で機械的に年率化したりしない。小さい/負の資本の解釈や定義変更をこの式だけで解決しない。

### Toyota Table 3は税引後ROCの共通定義を確定する根拠にしない

p24 Table 3を表示数値から独立計算すると、次の違いがある。

| Table 3表示値 | 表示金額による独立計算 | 残る問題 |
|---|---|---|
| Current ROC `1.79%`、OI `268`、after-tax OI `175`、IC `14,945` | `268/14945 = 1.7932418869…%`、`175/14945 = 1.1709601873…%` | 表示ROCは税引前の比率には整合し、p21注5と同じ税引後式には整合しない。 |
| Year 3 ROC `5.93%`、OI `916`、after-tax OI `714`、IC `15,445` | `916/15445 = 5.9307219164…%`、`714/15445 = 4.6228552929…%` | 同様に、同じ税引後ROCの行として一律に解釈できない。 |
| Year 1 ROC `−4.15%`、OI/after-tax OI `−612`、IC `14,745` | `−612/14745 = −4.1505595116…%`、前列IC14,945なら `−4.0950150552…%` | 表示は当該列の資本と整合するが、これだけで期首/期末の一般規約を決めない。 |

ここで金額の相互比率だけを計算しており、新しい企業入力を作っていない。Table 3の未表示調整・意図を推測して補正しない。p21の明示された税引後ROC式と、Table 3の定義上の不整合/未確認を分離する。実装に都合のよい列を選び、全表が同一ROC定義で再現したとは報告しない。

Table 3の `IC_t = IC_(t−1) + R_t` は、当該予測表の資本推移である。実際の帳簿資本の増減には別要因が入り得るため、これをあらゆる実企業の完全な会計恒等式として使ったり、残差を架空の再投資へしたりしない。

## 税率、税額、NOLは別工程

正常化利益に税率を掛ける式は、税率と税ベースがその状況に適するという前提を必要とする。原典p8の直近Exxon例は実効税率、p21の正常化例は限界税率を使用しており、混ぜて一つの実績税率と扱えない。いずれも2009年の例で、現行日本の税率・控除・損失繰越規則ではない。

p24は、赤字年にNOLが生じ、翌期の税を全額、続く期の税を一部抑え、その後限界税率へ移る例を明示する。これにより必要な区別は確認できるが、各国の期限・控除上限・税額控除・連結納税/通算・繰延税金などを実装できる一般規則は確認していない。

- NOPATに使うtax expense/税額/仮定税率の概念、利益ベースと期間、資金流出との対応を明示する。
- 負OIに `(1−τ)` を掛けるだけで即時の税還付を生成しない。NOLを同額の現金や確実な将来便益にしない。
- 利息控除後のnet incomeや、財務活動の税効果を含んだcash taxを、説明なしに負債支払前の営業NOPATへ置かない。
- NOLが残る移行期のNOPATと、NOL消化後の安定期NOPATを区別する。次の安定期を「直近の次年度」と自動決定しない。

最小候補は外側で作られた **明示NOPAT_next** を受け取り、その税計算の適合を未検証として保持する。数値と説明が揃ったことだけで税/NOLレビュー済みを生成しない。

## WC、設備支出、D&Aと再投資

原典p7は設備支出とworking-capital投資が景気とともに変動すること、p14は売上/簿価資本比率による正常化を説明する。p8の例は **net capital expenditures** を控除し、working-capital investmentをnegligibleとする。

これだけでは、gross capexとD&Aの対応、資産売却、非現金取引、どのWC勘定を含むか、cash/debtの除外、WC残高と期間増分などの一般的な部品規約は確定しない。設備投資・減価償却・運転資本からFCFFを組み立てる関数は、今回の設計対象外とする。

| 混同を避ける対象 | 最低限必要な点検 |
|---|---|
| gross設備支出とnet設備支出 | D&A、売却、買収、リース等をどこに含めるか、出典・cash/noncash・期間・符号。netという名称だけで同じ式とはしない。 |
| D&Aとcash flow | 税引前営業利益はD&A控除後の利益概念であることを確認する。EBITDAを同じNOPAT入力へ変えず、D&Aを二重に処理しない。 |
| WC残高とWC投資flow | 残高はas-of stock、投資flowは対応した期間の変化。残高比率×現在売上をそのまま毎年のcash outflowにしない。 |
| CFOとFCFF | 会社のcash-flow区分、利息/税/設備/借入等の範囲が異なり得る。営業CFを同じNOPATまたはFCFFと自動分類しない。 |
| g/ROCによるRと会計部品によるR | どちらの推計経路かを明示する。g/ROCからRを算出済みなのにcapexやWCを再度控除しない。 |

将来、会計部品から再投資を作るなら、それぞれの控除・加算を支持する別の原典確認と、同じ企業・期・範囲の出典が必要になる。今回の保存原典で明示確認できた安定期関係を、未確認の部品定義を埋める道具にしない。

## g/ROCの適用範囲と符号

著者のToyota/Exxon安定期例では、正の税引後営業利益、正の成長率、正の将来投資ROCを用いる。短期の赤字・悪化・回復はp23–25で別の明示経路を置き、終盤から安定期の再投資率へ移る。景気回復を表す高いEPS成長率、売上だけの成長率、株価上昇率を同じgへ転用しない。

| 入力・結果 | 数式上の性質 | 初回実装を検討する場合の提案 |
|---|---|---|
| `ROC=0` | 除算できない。`g=0`でも0/0は未定義。 | 数式上の入力エラー。代替ROCや再投資率0を補わない。 |
| 正NOPAT・正g・正ROC_new | 保存例にある安定期の符号範囲。 | 外部の適合は未検証のまま、実装済みの純算術範囲とする。 |
| `g=0`, `ROC≠0` | 代数上は `r=0`。式そのもののエラーではない。 | 当該原典でゼロ成長時の再投資・資本維持の適用説明を確認していないため、初回APIでは未対応scopeの検証エラーを返す。代数境界と経済的適用の拡張は未実装。gross capexや維持投資が0との意味にしない。 |
| 負g | 代数上は符号付き比率を計算できる。 | 縮小・資本回収の持続性を当例から確定できず、初回APIでは対象外。勝手な負額/clampや除外銘柄判定へ変えない。 |
| 負/0 NOPAT、負ROC_new | 数値の掛算・除算が可能な場合はある。 | 赤字回復/NOLと安定期の式の意味を確認できないため、初回対象外。赤字だけで企業を投資対象外にしない。 |
| `r>1`, `FCFF<0` | 正g・正ROCでも起こり得る。数式は定義される。 | 金融上の上限を新設して1へclampしない。符号を保存し、資金調達・成長持続の外部点検を未解決として残す。 |

正の符号への限定は**当初の著者例再現というプロジェクトの機能範囲**であり、原典が指定した万能の金融閾値でも、成長0の企業の価値否定でもない。ROC0の分母未定義と、g0の未確認の経済的適用は別の理由で返す。g0かつROC0は分母未定義を先に返す。

## 著者例の単位・算術・不一致

以下は当時の著者例の検証用。利益・税率・g・ROCを既定値にしたり現在企業へ移植したりしない。原source-auditの結果に加え、下記のNOPAT/FCFF分解を独立Decimal算術で確認した。

| 例 | 使用する表示入力と単位 | 分解・残る点 |
|---|---|---|
| Toyota p17 | `OI_base=1660.7 billion JPY`, `g=.015`, `τ=.407`, `ROC_new=.0509` | `NOPAT_next=999.5670265 billion JPY`。literal `g/ROC=.2946954813…`、`R_next=294.5678860019646…`、`FCFF_next=704.999140498035… billion JPY`。本文再投資率`.2946`とは厳密一致しないので、原文の価値へ合わせる補正をしない。 |
| ToyotaのROC仮定 | p17はROC_new=WACCと仮定。注2の正常化利益/2008年末資本によるROCは4.98%との別記述。 | 計算された正常化ROC、将来の投資ROC仮定、WACCを別々に残す。WACCへ自動等置しない。 |
| Exxon p21 | `OI_base=34614 million USD`, `g=.02`, `τ=.38`, `ROC_new=.21` | `NOPAT_next=21889.8936 million USD`、`r=.0952380952…`、`R_next=2084.75177142857…`、`FCFF_next=19805.1418285714… million USD`。これらは表示21%を使った経路である。 |
| Exxon注5のROC | `34614×(1−.38)/101629` | `21.116689134…%`。この未丸めROCでg/ROCを再計算すると`9.471181714…%`で、本文の丸めた21%を使う9.52%とは異なる。どちらを使ったかを黙って入れ替えない。 |

Exxon原典はp21本文で営業利益を `$34,614 billion`、後続式・注5・価値式ではmillionベースと記し、p22本文の固定資本は `$10,629 million`、p21注5の構成要素合計は101,629である。これらは[保存artifactのdiscrepancies](../research/cyclical-normalization-2026-10-15/source-audit.json)に記録済み。Table 3のROC差分も含め、原典の不一致・定義未確認を残し、既存資料を黙って「訂正」しない。

## 最小純計算の実装契約

公開APIは `calculate_stable_reinvestment(request) -> dict`。DB schemaや自動接続は追加しない。入力は以下の意味を持ち、全数値があっても適合は未検証のままとする。

| 入力 | 必要な意味と来歴 |
|---|---|
| 計算方法 | `stable_growth_new_investment_roc`の明示method。暗黙defaultや、会計部品方式との自動切替はしない。名称はプロジェクト契約。 |
| `NOPAT_next` | 対象となる最初の安定期の**次期・税引後・負債支払前営業利益flow**。会社、利益概念、期間start/endとラベル、通貨・金額単位、scope/会計基準、実績/予想/仮定区分、出典、税/NOL処理の根拠。 |
| `g` | 同じ安定期の年次営業利益成長率、小数比率。正常化の回復を再計上せず、NOPAT_nextを作るとき既に掛けた成長との関係を残す。 |
| `ROC_new` | 同じ安定期の将来新規投資に想定する税引後資本収益率、小数比率。歴史的ROCから採るなら、その橋渡しの根拠を別途残す。 |
| 安定期・整合の根拠 | いつ安定期へ入るか、利益率・税・資本投資の持続、年次期間の比較可能性、名目/実質など率とflowの基準。全数値があっても主張は未検証。 |

最小計算器は3個の数値と必要metadataを受け、`r=g/ROC_new`、`R_next=NOPAT_next×r`、`FCFF_next=NOPAT_next−R_next`を同じ金額単位で返す。ROC計算やstock会計を一緒に実装しておらず、資本残高や税率から欠けた数値を補う入口は持たない。

厳密decimal文字列、private高精度context、丸め方式の記録、元requestと参照、全結果の符号、不足/対象外理由を保持する。数学的に成功したことと、source存在・quote・意味・当時利用可能性・新規投資ROC・安定期の適合の検証を別にする。`approved:true`やcallerの「検証済み」だけから採用をtrueへする入口は持たない。

JSONのtopは `method / basis / nopat_next / growth / roc_new / assessment` の固定キー。basisは `company_id / currency / amount_unit / scope / accounting_basis`、金額unitは `units / thousands / millions / billions`、通貨は大文字3字を明示する。各descriptorのbasisはtopと一致させ、変換は行わない。

`nopat_next`は `value / concept / timing / period / basis / data_kind / source_refs / rationale` を持ち、conceptは `aftertax_operating_income_before_financing`、timingは `next_stable_period`。growthとroc_newはtimingに代えて `unit:annual_decimal_ratio` を持ち、conceptは各 `stable_operating_income_growth` と `aftertax_return_on_new_investment` を必須とする。税引前OIや歴史ROCを同じfieldへ置く入力は拒否するが、callerが誤って意味ラベルを付けたことまで機械検証したとはしない。

periodは `kind / label / start / end`、kindは `full_fiscal_year` の宣言。start/endは各日付またはnullで、3 descriptorが同じperiodを明示する。既知の逆転・異期間・四半期/YTDは拒否し、未知日付、年次性、52/53週の適合を自動認定しない。source refは `id / version / sha256 / location / quote`（versionとSHAはnull可）、資料の取得・引用照合は行わない。

data_kindは `reported_fact / issuer_guidance / author_estimate / explicit_assumption / synthetic_example` の申告を保持する。assessmentは `tax_and_nol_rationale / stable_growth_rationale / new_investment_roc_rationale / comparability_rationale / source_refs` を持ち、前4項目の未設定はnullで残せる。未知fieldは拒否する。

返値の `arithmetic.reinvestment_rate / reinvestment_amount / fcff` が中間計算値、`calculation`が精度・式・p17/p21の著者参照とproject adaptation、`verification`はすべてunverifiedである。`period_dates_incomplete`と`assessment_fields_unset`は不足の場所を示す。上流cycle-margin結果の税引前利益を自動取り込みする機能はない。

金融モデルへ組み込む前には、回復期間の明示cash-flow列、WACCと資本構成の正常化、通貨/名目実質/時点、低迷期の資金繰り・借換・存続、commodityの資源寿命、企業価値から株主価値への範囲の橋渡しが別途必要である。FCFFに利息・借入返済を重ねたり、FCFE/配当と取り違えたりしない。

## 有限の受入条件

対象21テストで、著者例と合成入力の算術、厳格入力、符号範囲、Decimal ambient設定からの独立性、精度、入力不変を確認した。実企業への適用や税/NOL・資本/将来投資ROIのレビューを完了したという報告ではない。

| ケース | 必要な結果 |
|---|---|
| 著者例の明示NOPAT_next・g・ROC_new | 表示入力のliteral分解を再現し、単位・計算精度・式を返す。原文丸め値へ合うように補正しない。 |
| NOPATが基準年、税引前OI、純利益、EBITDA、CFO | 同じ入力として受け付けない。次期営業NOPATへの変換を勝手に行わない。 |
| NOPATに既に成長が入っている | 計算器内で`×(1+g)`を繰り返さない。gは再投資率の計算にのみ使用する。 |
| 別会社・期間・scope・通貨/単位、ROCとgの年次基準が不一致 | 拒否/対象外または整合保留。日数による年率化やFX変換を自動実行しない。 |
| ROC0、欠損、非有限値、bool、率とpercentの混同 | 通常の入力エラー。0/0の0化、率の既定補完、暗黙percent変換をしない。 |
| g0・負g、非正NOPAT/ROC | 上記初期範囲では対象外。g0を除算未定義と誤説明せず、未確認の経済的範囲として区別する。 |
| 正入力でr>1/負FCFF | 数式結果の符号を保持。1/0へのclampや、存続/調達可能性を検証済みとする処理をしない。 |
| 税/NOL根拠が未解決 | 税引後入力が数値として存在しても、その意味の適合は未検証のまま。税率・税損失の便益を補わない。 |
| 過去の平均ROC、またはWACCだけがある | ROC_newへ自動コピーしない。明示された仮定とその未検証性を保つ。 |
| Table 3のROCやExxonの資本記述が不一致 | 原文と独立算術の差分を残す。都合のよい定義/単位へ黙って統一しない。 |
| g/ROCによるRに加えcapex/WC控除を要求 | 最小methodの対象外。二重再投資や会計部品の推測をしない。 |
| 計算成功・完全なmetadata・原典ID/hashが揃う | `intermediate_only / adoption:unresolved`を維持。循環DCF/終価/価格/売買の自動解放は行わない。 |

純算術を実装したことと、実企業の税・新規投資収益性・正常成長・資金調達を採用する判断は分離する。今回の実装は後者の不足を消したものではない。
