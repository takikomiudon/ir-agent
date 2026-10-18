# 循環企業の正常化：保存原典から確認できる式と最小実装の範囲

本書は原典点検と最小算術の仕様である。既存の金融モデル、DB、実企業の仮説を変更していない。1332ニッスイ、5480日本冶金工業の単期利益を正常利益へ変換したものでもない。

後続の最小実装として、[純粋計算器](../src/ir_agent/cyclical_margin.py)の `calculate_cyclical_margin(request)` と[対象テスト](../tests/test_cyclical_margin.py)を追加した。実装済みなのは原年次金額からの等重み利益率算術と宣言の構造点検であり、正常化の採用は常に `unresolved`、状態は `intermediate_only` である。下記のROC・再投資・financing・金融モデル接続案は実装していない。[原典照合artifact](../research/cyclical-normalization-2026-10-15/source-audit.json)に13引用、元表12行、独立算術結果と原文不一致を保存している。

初回実装は、**明示された比較可能な年次入力について、利益率の単純平均と指定売上への適用を再現する純粋な中間計算器**に限定する。正常な景気局面、完全なサイクル、将来の持続可能利益を自動認定する計算器にはしない。ROC、再投資、financingを揃えた循環DCFへの接続は別の入力・意味点検が残る。以下の仕様に未確認と記す式は実装しない。

## 原典と確認範囲

- Aswath Damodaran, *Ups and Downs: Valuing Cyclical and Commodity Companies*, September 2009。保存ID `damodaran.cyclical-commodity.2009`。
- [著者のNYU PDF](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/commodity.pdf)。保存先は [sources.json](../research/valuation-model-routing-2026-10-15/sources.json) の当該source内 `raw_pdf_base64` / `extracted_text`。この調査で新GETは行っていない。
- 原PDF SHA-256: `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`、670,511 bytes、40 PDF pages。保存取得時刻 `2026-10-15T01:26:14.401821+00:00`。
- 保存バイトを復元してSHAを照合し、`pdftotext -layout` の再抽出が保存textとバイト一致することを確認。保存text SHA-256: `bc0de814b9bac9a6923a09919084071f4342e1fbfe5f9665c678d32ce096ea5b`。
- 以下のpはPDF先頭を1とするページ位置。p6–25の関連本文・表・式を読み、p15–17、21–22、24はPDF画像でも照合した。本文全体の関連語も検索したが、未発見の一般規則を「存在しない」と証明するものではない。別途リンクされたspreadsheetは取得・検証していない。

既存の[研究用routing](../research/valuation-model-routing-2026-10-15/routing.json)が採用した「循環正常化の点検が必要」という原則と、以下の計算API案は別である。後者は本プロジェクトの適応で、著者の完成済みソフトウェア契約ではない。

## 原典の逐語引用と、支持される範囲

改行と連続空白だけを正規化し、各引用が指定ページの保存本文に存在することを確認した。引用IDは本仕様内の識別子である。

| ID / 頁 | 原文 | 支持する範囲・残る点 |
|---|---|---|
| CYC-Q01 / p10 | “we also have to normalize return on capital, reinvestment and cost of financing” | 利益だけを正常化し、他を不況年のまま組み合わせることへの警告。各要素の一意な自動推定式ではない。 |
| CYC-Q02 / p11 | “we are double counting growth, once by normalizing earnings and again by using a higher growth rate.” | 正常利益への置換と、同じ景気回復を含む高成長率の重複を避ける。回復期間や正常成長率の数値指定ではない。 |
| CYC-Q03 / p14 | “the averaging should occur over a period long enough to cover an entire cycle.” | full-cycleを覆う期間を選ぶ。本文の景気循環年数の例は固定窓ではない。 |
| CYC-Q04 / p14 | “we can average profit margins over time, instead of net profits” | 絶対利益の平均に代わり、規模で割った変数を平均する。一般的な重みの式はこの文にない。 |
| CYC-Q05 / p14 | “apply the average profit margin to revenues in the most recent period to estimate normalized earnings.” | 平均利益率×直近売上という規模調整。四半期の自動年率化や将来売上の自動生成は指定しない。 |
| CYC-Q06 / p14 | “by looking at ratios of revenue or book capital over time, rather than the absolute values.” | capex・working capitalも売上または簿価資本に対する比率で考える。gross/net capex、working-capital残高/増分の一意な選択式は未指定。 |
| CYC-Q07 / p15 | “this approach will also fail to incorporate the characteristics (operating efficiencies or inefficiencies) that may lead a firm to be different from the rest of the sector.” | sector平均は企業固有差を失う。自社historyがない場合の無条件代入ではない。 |
| CYC-Q08 / p16 | “Averaging the pre-tax operating margin from 1998 to 2009 yields an average operating margin of 7.33%.” | Toyota例の対象は税引前営業利益率。平均法の再現は下表参照。数値は当時の例であり既定値にしない。 |
| CYC-Q09 / p17 | “since neither the debt ratio nor the cost of capital has moved substantially over time, we will use this as the normalized cost of capital.” | 履歴点検後、当時の資本コストを正常値として採った例。資本コストを常にそのまま使う規則ではない。 |
| CYC-Q10 / p17 | “We will also assume that the firm will be able to generate a return on capital equal to its cost of capital on its investments.” | Toyota固有の将来投資ROC仮定。全循環企業のROCをWACCへ等置する一般規則ではない。 |
| CYC-Q11 / p21, 注5 | “Return on capital = Operating Income (1-tax rate)/ Invested Capital” | 正常化営業利益から税引後ROCを計算する例。分母の会計定義・時点と税の適用は別途明示が必要。 |
| CYC-Q12 / p18–19 | “With reinvestment and cost of financing, it will require some subjective judgments” | commodityの正常価格で再投資と資金調達がどう変わるかには判断が必要。p19の続きと併せて確認。 |
| CYC-Q13 / p23 | “allow earnings to follow the current cycle for the short term” | 長期正常値へ即時移行する方式とは別に、短期の悪化・回復経路を明示する。即時正常化を翌期予想と同一視しない。 |

著者はp14でnormal yearの判断に主観性があると説明する。単に平均を計算できたことは、「その期間が一サイクルである」「その利益率が現在にも適切」という証明ではない。

## 平均法：確認できる式と未指定事項

`S_i`を各対象期の売上、`OI_i`を同じ期・範囲の税引前営業利益とする。Toyota例の利益概念を採用する場合、`m_i = OI_i / S_i` は営業利益率であり、純利益率・EBITDA率・EPSとは区別する。

原典p14が支持する関係は次である。

```text
normalized operating income candidate = chosen average operating margin × current-scale revenue
```

原典は一般論として「average」の重みを式で指定していない。p15 Table 2の年次行を独立計算すると、下記の**等しい年次観測に対する単純算術平均**が掲載平均に整合する。一方、売上加重平均は別の値になる。

```text
m_equal = (Σ_i (OI_i / S_i)) / n
OI_candidate = m_equal × S_current

# 比較用の別計算。m_equalと同じ方法ではない。
m_sales_weighted = (Σ_i OI_i) / (Σ_i S_i)
```

最初の式は著者例を再現するために採るプロジェクト側の明示methodとし、すべての企業・サイクルへ著者が一律に要求した重みだとはしない。売上加重、期間日数加重、直近重視、winsorize、極端値除外、幾何平均へ黙って切り替えない。

| 論点 | 原典で確認した内容 | 最小実装の境界 |
|---|---|---|
| サイクル範囲 | p14はfull-cycle。長短さまざまな年数の例を挙げ、一定年数を固定しない。 | 選定期間・景気/価格driver・根拠・採否理由を外部入力に残す。年数だけでcompleteとしない。底/天井の機械検出・回復確率は実装しない。 |
| 期間の重み | Toyotaは年次行。一般的な期間加重式は未確認。 | 第一段階は比較可能な通期行の等重みと明示する。四半期/YTD/通期や変則決算を自動混合しない。 |
| 年率化 | p14は直近期の売上への適用。四半期利益率×4、売上×4、日数比例の式は示されない。 | 年率化しない。別期間の資料が必要なら不足を残す。 |
| 規模変化 | p14は売上倍増時の絶対平均の過小評価を指摘し、relative averageを提案。 | 売上規模の違いに対処するが、買収・事業売却・事業構成・会計基準・価格/為替変化まで自動修復しない。過去の率の適合を点検する。 |
| 赤字・負利益 | p15はoperating income or lossを参照し、p23–24は負利益を含む回復経路を扱う。Table 2の掲載年次利益はすべて正で、四半期損失の記述とは別。 | 入力された負の営業利益を勝手に除外・0化しない、という保存・算術上の扱いはプロジェクト契約。負平均から正の正常利益を作らない。 |
| 予想の混在 | Table 2には `FY 2009 (Est)` が含まれる。 | 著者例は「実績のみ」の例ではない。企業への適用で実績と予想を混ぜる場合は各区分と採用理由を明示し、予想を実績へ変えない。 |
| 利益率の丸め | Table 2の年次率と平均率は表示精度が限られる。 | 原金額からの率、表示率の平均、表示平均率の適用を区別する。中間値の黙った丸めや、原文値へ合わせる補正はしない。 |
| sector平均 | p15は自社history不足/事業変更時の選択肢と、企業固有差を失う注意を示す。 | sectorの選定、企業/年次の二段階の重み、欠損企業、生存者偏りの処理は未指定。第一段階にsector平均自動生成を含めない。 |

## 著者の算術例を独立照合した結果

ここに出す値は**著者の2009年の例の再現・差分**で、採用パラメータではない。保存表の数値文字列をDecimalで独立計算した。後続の実装テストには元の行と計算式をfixtureとして保持し、以下の表示値だけから逆算しない。

### Toyota：Table 2（p15）と本文（p16–18）

Table 2の単位はmillion JPY。対象12行の営業利益率は次のとおり。

```text
1998  6.68%     1999  6.08%     2000  6.02%     2001  6.48%
2002  7.44%     2003  8.49%     2004  9.64%     2005  9.01%
2006  8.93%     2007  9.35%     2008  8.64%     2009 (Est) 1.18%
```

最終行の売上は `22,661,325 million JPY`。本文冒頭の1998–2008という説明だけで行を切らず、表とp16の1998–2009という説明も照合した。

| 計算 | 独立結果 | 原文との関係 |
|---|---|---|
| 12個の表示利益率の等重み平均 | `7.328333333…%` | 表示7.33%に整合。 |
| 各年の原営業利益÷原売上を未丸めで計算した率の等重み平均 | `7.3283985287…%` | 同じく表示7.33%に整合。著者が内部でどちらを使ったかまでは確定できない。 |
| 営業利益合計÷売上合計 | `7.4087569680…%` | 売上加重なら掲載7.33%を再現しない。 |
| 表示年次率の平均×最終行売上 | `1,660,697.43375 million JPY` | 約1,660.7 billion JPYで本文に整合。 |
| 未丸めの年次比率平均×最終行売上 | `1,660,712.207887… million JPY` | 同じ表示桁では約1,660.7 billion JPY。 |
| 表示平均7.33%そのもの×最終行売上 | `1,661,075.1225 million JPY` | 表示平均をそのまま使うと本文の1,660.7とは完全一致しない。 |
| 営業利益12行の絶対平均 | `1,306,866.666… million JPY` | Table 2の平均 `¥1,306,867` に整合。p16本文は `1,332.9 billion yen` と記し不一致。勝手にどちらかへ修正しない。 |

本文の正常営業利益と平均表の小差は、丸めた率を再入力することの限界を示す。平均絶対利益の不一致は単なる単位変換では解けない。数値を元のsourceごと保持し、機械式が原文すべてを完全再現したとは報告しない。

p17の後続例も表示入力をliteralに計算すると次のようになる。

| 著者式の表示入力 | 独立結果 | 確認できること |
|---|---|---|
| `g / ROC = .015 / .0509` | `.2946954813…` | 本文の `.2946` / `29.46%` とは厳密一致しない。未表示の精度を推測して合わせない。 |
| `WACC = .0865×.471 + .0325×(1−.407)×.529` | `.0509366525` | 表示5.09%に整合。 |
| `1660.7×1.015×(1−.407)×(1−.2946)/(.0509−.015)` | `19,640.517562… billion JPY` | 著者のoperating-assets表示19,640に近いが丸め処理の完全再現ではない。 |

ここでの税率、成長率、ROC、WACC、利益率、窓年数はすべて当時の例である。

### Exxon：ROCと再投資の整合（p20–22、注5）

p20の営業利益と原油価格の回帰、p21の例では次を用いる。

```text
OI = -6,395 + 911.32 × average oil price
IC = book equity + book debt − cash
ROC = OI × (1 − tax rate) / IC
stable reinvestment rate = g / ROC
```

回帰係数を他社へ移植しない。p20注4はExxonが大規模で安定していたため関係が強く、小規模・変化中の企業では弱くなり得ると説明している。

| 保存例の入力 | 独立結果・注意 |
|---|---|
| `-6395 + 911.32×45` | `34,614.40`。本文の34,614は表示丸めと整合。 |
| `126044 + 9566 − 33981` | `101,629 million USD`。注5は2007年末の資本要素を使用。 |
| `34614×(1−.38)/101629` | `21.116689134…%`。注5の21.1%に整合。 |
| `.02/.21` | `9.523809523…%`。本文の9.52%に整合。注5から再計算した未丸めROCを使うと `9.471181714…%` となり、使用したROCの精度は区別が必要。 |
| `34614×1.02×(1−.38)×(1−.02/.21)/(.0818−.02)` | `320,471.550624… million USD`。本文320,472に整合。 |

p21本文には営業利益を `$34,614 billion` と記す一方、後続式・注5・価値式はmillionベースである。またp22本文は固定資本を `$10,629 million` と記す一方、p21注5の構成要素合計は101,629である。PDF画像でも文字を確認した。これらの不一致をOCR誤読と片付けたり、黙って修正して他社の式へ採用したりしない。上表は使用した式と単位を明示した算術照合に限る。

## ROC・再投資・financingで、今後揃える必要がある入力

### ROC

p21注5の計算は、正常化した税引前営業利益、明示税率、簿価equity・debt・cashから定義した資本を使う。一般形は次の関係として確認できる。

```text
after-tax normalized operating income = OI_normalized × (1 − chosen tax rate)
ROC_normalized = after-tax normalized operating income / chosen invested capital
```

ただし、これは税を一律乗算してよい条件が明示された例の関係である。赤字・税損失繰越・実効税率/限界税率の移行を扱う一般税計算器ではない。p24は赤字年のNOLが後年の税を抑える別の経路を示す。

資本の時点は元例では2007年末と明示される。「常に期首」「常に期末」「期首期末平均」という共通規則をこの例だけから作らない。資本の会計範囲、cashの控除範囲、リース・無形資産・少数株主持分等の調整も、日本企業へ適用する前に追加確認が必要である。

Toyotaのp17は将来投資ROCをWACCへ等置する仮定を置く。注2の別計算では、正常利益と2008年末資本によるROCが4.98%で、採用5.09%に近いと説明する。**正常化ROCの計算、将来の新規投資ROCの仮定、WACCは別の入力**であり、同じものとして自動設定しない。

### 再投資

p17・21・25には安定成長期の関係 `reinvestment rate = g / ROC` が明示される。p17の価値式から、当該安定成長仮定のもとで次の分解が読み取れる。

```text
normalized OI_next = normalized OI_base × (1 + g)
NOPAT_next = normalized OI_next × (1 − tax rate)
reinvestment_next = NOPAT_next × (g / ROC)
FCFF_next = NOPAT_next × (1 − g / ROC)
```

最終2行は掲載価値式の代数的な分解であり、歴史的capexやworking capitalから再投資を自動推定する新しい著者式ではない。`g`と`ROC`の対象期間・利益基準が揃い、ROCが将来投資にも適切という前提が必要になる。gを株価上昇率や過去EPS回復率へ置き換えない。

p14はcapex・working capitalの売上/簿価資本比率の正常化を提案するが、そこだけではgross/net capex、減価償却、運転資本残高/増分、基準売上、負額、投資時点を一意に決められない。`平均WC比率×現在売上`をそのまま年次cash outflowとして控除する実装はしない。売上高成長のΔから投資CFへ結ぶ式も本資料の確認済み箇所から勝手に補わない。

p24の `Capital invested_t = Capital invested_(t−1) + Reinvestment_t` とTable 3では、負の再投資と後年の正の再投資があり、短期は一定再投資率ではない。安定期の `g/ROC` を赤字・回復年へ一律適用しない。ROCが0なら除算できず、負ROCや負成長を入れた比率の経済的意味も別点検となる。負額を0化・正値化したり、原典未指定の範囲へclampしたりしない。

### Financing

p7はriskfree rate、risk premium、負債比率、負債/株主資本コストが景気とともに変化し、方向も一意でないと説明する。p16–17の例の式は次である。

```text
cost of equity = riskfree rate + beta × equity risk premium
debt weight = D / (D + E)
WACC = cost of equity × E/(D+E) + pretax cost of debt × (1 − tax rate) × D/(D+E)
```

Toyotaでは資本構成・資本コスト履歴を点検したうえで現在値を正常値として使い、業界bottom-up beta、当時の金利・ERP・rating/default spread・税率・市場equityを明示した。**WACCの歴史平均、通常年riskfree rate、beta、ERP、default spread、負債目標を自動生成する一般手順は、この例から確定できない。** p18–19も商品正常価格の下での再投資・financingに主観判断が残るとする。

最終DCFには通貨・時点・cash flowの名目/実質・税・資本構成・成長の整合、低迷期の資金繰り/借換/存続制約、commodityなら資源寿命等の点検が必要になる。正常利益率だけを求めて、足元の再投資・借入コストを黙って組み合わせない。上記の算術式を示したことは、これらの推定法や金融モデル実装の採用完了ではない。

## 最小中間計算器の入力・出力契約

金融モデル本体へ新しいvaluation methodを加えるより、まず単独の純粋関数に限定する判断材料は次のとおり。full-cycle選定、当期への利益率適合、税、再投資、financing、回復経路の証拠が独立しており、利益率算術だけでは埋まらないためである。

| 入力 | 必要な内容 |
|---|---|
| 方法 | `arithmetic_equal_annual_periods` を明示。既定methodや重みは置かない。これは著者例に整合するプロジェクト契約。 |
| 年次行 | 同一企業・比較可能な範囲の期start/end、通期の識別、税引前営業利益と売上の明示decimal文字列、通貨・単位、連結範囲・会計/概念、実績/予想の区別、source ID/版/hash/引用参照。 |
| 採用集合 | 使用行の全件と選択期間、完全サイクルと考えるdriver/公開根拠・理由、除外行と理由。存在しない年を補完せず、好都合な年だけを落とした集合を完全履歴としない。 |
| 適用売上 | current-scale revenueの数値、期・範囲・単位・実績/予想区分と出所、なぜ当該売上へ歴史的率を適用するか。現在の株価とは別。 |
| 精度 | 原数値と表示率のどちらを使うか明示。第一段階の本APIは原OI/売上から率を計算し、表示率入力・金額の表示quantizeは受け付けない。繰返し除算等は返却するworking precisionで丸める。表示率を使う著者例再現は原典監査artifact内の別算術に限る。 |

これらの文言やsource参照を受け取っただけで、資料の意味やfull-cycleを検証済みにしない。単期しかない場合、算術としての単一比率は得られても、full-cycle正常化の入力が揃ったことにならない。

出力候補は各行の `OI/S`、等重み平均、指定売上への適用額、全入力と式・精度来歴、および不足/意味点検事項である。`intermediate_only` とし、算術再現と正常値採用の意味確認を分ける。full-cycle/期間・範囲の根拠が不足する場合は正常化の採用をunresolvedとし、数値補完や `inputs_verified:true` を生成しない。

この段階ではROIC自動推定、再投資額、FCFF列、WACC、DCF/目標株価、EPS/PER、売買判断、IR送信、確率、重みを出力しない。現在の[source正常化](../src/ir_agent/disclosed_facts.py)も原数値・引用の再現と意味の採用を分けているため、派生平均は公表実績そのものへ分類しない。

## 有限の実装受入条件

等重み年次金額の純粋計算と入力構造の条件を[対象テスト](../tests/test_cyclical_margin.py)で確認している。表の意味、サイクル範囲、会計上の比較可能性を機械検証したという報告ではなく、後段モデルに関する条件は依然として接続を保留するための境界である。

| ケース | 必要な結果 |
|---|---|
| Toyota掲載12行をそのまま使用 | 原比率の等重み平均と指定売上への適用を再現。表示率平均、表示平均7.33%、売上加重を同一経路にしない。 |
| Table 2の絶対平均と本文の値が不一致 | 両原典記述と算術差分を残し、1,332.9へ合わせる補正や成功判定をしない。 |
| full-cycle根拠なし・単期のみ・窓年数のみ申告 | 必要な採用点検をunresolvedとし、固定年数や自己申告completeから正常化済みへ昇格しない。 |
| 年次行の重複/期間重複、四半期/YTD/変則決算混在 | 比較可能性の不足を返す。足し合わせ・年率化・日数加重を黙って行わない。 |
| 別企業・会計範囲・利益概念・通貨/単位の混在 | 拒否または意味点検の保留。営業利益、純利益、EBITDA、EPSを混ぜない。 |
| 欠損、dash、売上0、非有限値 | 補完やゼロ利益化をせず通常の入力エラー/不足。売上が正という当計算の定義域を明示する。 |
| 売上が正で営業利益が負 | signed marginを保持。正の年だけ選択する処理、clamp、税還付の自動付与をしない。 |
| 実績と会社予想/著者推計の混在 | 区分と採用理由を保持し、実績だけの検証とは報告しない。 |
| 買収・売却・事業構成変更で歴史比率の意味が変わる | 規模調整だけで解消したとしない。未調整historyの正常利益採用を保留する。 |
| mean method未指定、売上加重指定、未対応の期間重み | 等重みを既定補完しない。第一段階の非対応methodは明示拒否する。 |
| 未丸め入力と表示率で結果が異なる | 使用した経路・decimal精度を残し、原文値一致のため途中丸めしない。 |
| 将来のROC/再投資/WACC/回復期間がない | 中間計算までに止め、既存DCFや退出条件へ自動接続しない。 |
| 元の入力や返却値を後で変更 | 純粋計算は元入力を書き換えない。採用・保存を後で作る場合も元sourceと派生計算を別ID/不変版で保持する。 |

原典の方法を実装することと、その方法が実企業に適合することは別の課題である。今回確認したのは、規模調整した利益率平均の算術、例示されたROC/安定再投資/financingの関係、およびそれだけでは埋まらない条件である。
