# 明示した終価翌期FCFFをDCFへ渡す最小仕様案

本書は保存原典の点検と最小実装の仕様である。後続実装で[valuation.py](../src/ir_agent/valuation.py)に新methodを追加し、[専用テスト](../tests/test_explicit_terminal_valuation.py)で算術と旧契約の回帰を確認した。既存原典、実DB、金融入力を変更せず、新GETも行っていない。

**終価分子の算術差分だけなら翌期FCFFの追加で足りるが、旧保存版とIR契約の互換のため、明示的に選ぶ別methodを実装した。** method名は `dcf_explicit_terminal`、追加金額は `terminal_fcff_jpy`。現在の `dcf` の意味・結果を変更せず、既存と同じ単一割引率rに限定する。入力・出力構造はprojectの契約であり、原典のAPIではない。

## 保存原典と式の根拠

すべて[保存済みsources.json](../research/valuation-model-routing-2026-10-15/sources.json)の原PDFと抽出本文を使用した。頁はPDF先頭を1とする。若い企業論文p39–40はPDF画像でも式・Table 18を確認した。

| source ID / 著者原典 | 保存PDF SHA-256 | 今回の用途 |
|---|---|---|
| `damodaran.young-growth.2009` / Aswath Damodaran, *Valuing Young, Start-up and Growth Companies*, May 2009 | `0e45bb889ca2a6148f21a41070b7e9a15294e86be2a63c72f5627e26f9675782` | p38–40、特にn期末終価にn+1期FCFFを使う式と割引時点。 |
| `damodaran.cyclical-commodity.2009` / *Ups and Downs: Valuing Cyclical and Commodity Companies*, September 2009 | `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40` | p17/21の安定期FCFF分子、p23–25の移行期と安定期の区別、単一WACC例。 |
| `damodaran.financial-services.2009` / *Valuing Financial Service Firms*, April 2009 | `2e1b2d45a8d04ab14b8ed48825b64e7765dd896d59e1db34cce32ded23d07472` | p14–15、firm cash flowとequity/DPSの範囲・割引率の区別。FCFF終価へDDMをそのまま転用しない。 |

以下の短い引用は、指定頁の保存本文と空白正規化後に逐語一致する。式は原式を読み下し、API・機能制限はproject adaptationとして分ける。

| ID / source・頁 | 原文 | 確認範囲 |
|---|---|---|
| ET-Q01 / young-growth p39 | “We estimate the terminal value for Secure Mail at the end of year 10” | 終価は予測最終年10の末。 |
| ET-Q02 / young-growth p39 | “Free Cash flow to the firm11= After-tax Operating income11* (1-Reinvestment Rate)” | 終価分子は次期11年目の税・再投資後FCFF。最終予測CFそのものではない。 |
| ET-Q03 / young-growth p40 | “discounting back at the year-specific costs of capital (from table 16)” | 終価を予測CFに組み込み、各年の資本コストで現在へ割り引く。 |
| ET-Q04 / young-growth p40 | “Note that the cost of capital is cumulated to reflect the changes in the cost over time.” | 原典のこの例は期ごとの割引率を累積しており、単一率の再現例ではない。 |
| ET-Q05 / cyclical p25 | “We keep the cost of capital unchanged at 5.09% over the period” | 循環企業の別例は単一率。今回この数値を既定にせず、単一rという機能範囲のみを維持する。 |
| ET-Q06 / financial-services p14 | “We value firms by discounting expected after tax cash flows prior to debt payments at the weighted average cost of capital.” | 会社全体FCFFの範囲。株主CFや配当を同じ金額へ混ぜない。 |
| ET-Q07 / financial-services p15 | “DPS1 is the expected dividends per share next year.” | DDMも翌期分子を区別するが、DPS/株とFCFF/会社は別。FCFF式の直接根拠はyoung-growth p39。 |
| ET-Q08 / young-growth p38 | “If the assumption of cash flows continuing in perpetuity is too radical for the firm” | 永続成長の適否は別判断。有限寿命・清算モデルは今回の追加に含めない。 |

### 直接確認できる終価式

young-growth p39、Secure Mail例は次を表示する。

```text
Terminal Value_10 = FCFF_11 / (Cost of capital_stable − stable growth rate)
```

p40 Table 18では10年目のFCFFと終価を同じ予測最終年の欄に置き、その年までの累積割引係数で割り引く。一般に原典の年別率を使うなら次の形となる。

```text
TV_n     = FCFF_(n+1) / (r_stable − g)
PV_TV    = TV_n / product_(t=1..n)(1 + r_t)
PV_FCFF  = sum_(t=1..n)[FCFF_t / product_(j=1..t)(1 + r_j)]
```

若い企業論文p34/36は資本コストの時間変化を明示し、Table 16では予測期と安定期の値が異なる。**原典に相違が示されていない、として単一率を正当化しない。** 今回は既存DCF互換のため `r_t=r_stable=r` と限定するproject scopeを優先する。この限定形は次である。

```text
n        = len(explicit_forecast_fcff)
TV_n     = explicit_terminal_FCFF_(n+1) / (r − g)
PV_TV    = TV_n / (1 + r)^n
EV_0     = sum_(t=1..n)[FCFF_t / (1 + r)^t] + PV_TV
Equity_0 = EV_0 + cash − debt
Value_per_share = Equity_0 / shares
```

単一rが適合しない企業へ、年別WACCや別のstable WACCを推測して足さない。年別率の原典が存在することと、その拡張を今回実装することは別である。金融原典p15の高成長/安定期のequity costも、別のWACC入力を無条件に輸入する根拠にはしない。

## 既存DCFの契約と、任意fieldだけでは残る問題

[valuation.py](../src/ir_agent/valuation.py)の現行 `dcf` は次の6項目を消費する。

```text
discount_rate, terminal_growth_rate, fcf_jpy,
cash_jpy, debt_jpy, shares_outstanding
```

`fcf_jpy`は1〜n期の会社全体・JPY・年末アンレバードFCF。現行の終価分子は `fcf_jpy[-1] × (1+g)` である。`stable-reinvestment`の結果は既に次期NOPATから税・再投資を反映したflowなので、そのまま末尾へ置くとさらに成長が掛かる。また配列へ追加すればn自体が増え、そのCFを予測CFと終価の双方へ含める危険がある。

現行 `_prepare` のDCF分岐は必要な数値を抽出し、raw inputsの未知fieldを一般には拒否しない。従って過去に未使用の `terminal_fcff_jpy` などが保存されていた場合、同じ `method:dcf` に任意fieldを追加するだけで、**同一保存JSONの再計算が突然別の値になる**可能性がある。今回、実DBを全件監査してそのようなfieldが存在しないと確認したわけではない。

| 案 | 算術・互換上の評価 |
|---|---|
| 既存dcfへoptional `terminal_fcff_jpy` | 内部算術の変更は小さい。省略時legacy、present時explicitとすれば新しい値の区別は可能。ただし過去の未使用fieldの有効化、null時のfallback、IR canonical pathの増減、表示の意味が変わる。旧版全件監査/明示移行なしでは保存互換を保証できない。 |
| 既存dcfへmode+optional金額 | 意図は明確になるが、以前の未知modeを有効化する問題と、分岐/任意fieldの組合せが増える。全旧資料の互換を自動証明しない。 |
| 別method `dcf_explicit_terminal` | **推奨。** 現行dcfは従来どおり。新methodは終価翌期FCFFを必須とする。旧methodでは以前認められなかった新名を明示選択するため、未使用fieldだけで旧版が新計算へ変わることを避けられる。 |

新methodも会社全体FCFFのDCFであり、別の投資戦略ではない。共通の予測CF割引・株主価値変換を内部で再利用し、計算分子の選択を明示する最小差分に留めた。旧dcfの未知field許容を変更して既存の入力受理範囲を狭める作業は含めていない。

## 新methodの最小入力契約

新methodのinputsは**以下7キーのみ**で、終価翌期FCFFは必須である。

| field | 意味・検証 |
|---|---|
| `fcf_jpy` | 空でない1〜n期末FCFF配列。会社全体JPY、税・営業再投資後、負債支払前。負額を許容。terminal翌期を追加しない。 |
| `terminal_fcff_jpy` | **n+1期の明示FCFF金額**、会社全体JPY。0・負額も有限数値として許容する。欠損/nullはエラーでlegacy式へ戻さない。 |
| `discount_rate` | 予測期と安定期に共通の年率r、小数比率、正。別の金利仮定を追加しない。 |
| `terminal_growth_rate` | n+1期以後の安定FCFF成長率g。現行の `−1 < g < r` を維持し、既定値なし。 |
| `cash_jpy` | 現行と同じ非負の会社全体JPY調整額。キャッシュフローと混ぜない。 |
| `debt_jpy` | 現行と同じ非負の会社全体JPY調整額。FCFFから借入返済を再控除しない。 |
| `shares_outstanding` | 同じ株式/持分基準の正の株数。現行の株主価値変換の機能範囲を維持。 |

新fieldの数値受理は既存valuationと同じfinite Decimal変換を再利用する。bool、非数、Infinity等を拒否し、明示0と欠損を区別する。厳密decimal文字列で入力することを推奨し、private context・input依存精度・非丸め計算・最後の表示丸めを維持する。

新methodの計算では、`terminal_fcff_jpy`へ **税率、再投資率、(1+g)のいずれも再適用しない**。gを使うのは終価分母であり、分子が既にn+1期であることを変えない。終価はn期末、割引はn期分。FCFF_(n+1)をもう一度独立の予測CFとして現在価値へ足さない。

配列が空の場合のn=0純Gordonは今回対象外とする。予測期間を水増しして空配列を埋めることも、n+1期を配列へ詰めることもしない。

### 出力と既存値の互換

- 旧 `dcf` の受理済み入力・計算結果・既存出力キー・丸めを維持する。旧保存JSONを自動書換えしない。
- 新methodもscenario価格、enterprise/equity value、集計・unweighted・`include_unrounded`の既存構造を再利用する。method名は新名のまま返す。
- 新methodのscenario出力だけに `terminal_fcff_jpy / forecast_periods / terminal_value_jpy / present_value_of_terminal_value_jpy / present_value_of_forecast_fcf_jpy` を追加した。最初は入力精度を保持した正規化decimal文字列、次は整数n、残り3額は既存と同じ2桁表示である。古いsnapshotへfieldを後付け保存しない。
- `terminal_fcff_jpy = last_forecast_fcf×(1+g)`を明示した新methodなら、同じr・g・cash/debt/sharesの旧dcfと算術上等しくなることを確認する。ただし計算一致から前提妥当性を保証しない。

新methodで負terminal FCFFは負TVとなり得る。負予測CFも現行どおり保持し、0へclampしない。EVが負であること自体を新しい企業除外条件にしない。**現行の負equity valueエラー・0 equity有効・正sharesという株価変換の制限は維持する**。負FCFFを許すことと、負の将来CFが永続する経済仮定を採用することは別である。

## stable-reinvestmentとの接続と出典不足

[stable-reinvestment仕様](cyclical-reinvestment-spec.md)の中間量は、明示NOPAT_nextと同じ安定期のg・ROC_newから得たFCFFである。接続前に次が必要になる。

1. そのnextが、DCFの最後の予測期nの直後のn+1期であることを確認する。「次期安定期間」を直近の翌年度と自動解釈しない。
2. 同じ企業・連結/会計/利益範囲・通貨・金額単位・年次期間・名目/実質の基準を揃える。中間量のbillions/millionsを無換算でJPYへ入れない。USDの著者例をJPYの値としない。為替を自動生成しない。
3. 中間計算のgとDCFの安定gを一致させるか、異なる意味ならその橋渡しを別途検証する。意味不明の率を黙って差し替えない。
4. 税/NOL、将来新規投資ROC、成長と再投資、安定期移行、資金調達/存続の根拠を保持する。中間量の `adoption:unresolved` がDCFへ数値転記しただけで消えたことにしない。
5. 入力request/hash・計算器版・元数値/資料の来歴を保持した派生計算として追跡する。公表実績・会社予想へ分類を上げず、原典を参照しただけで独立検証済みにしない。

この追加は自動importerでも金融前提の採用器でもない。源泉不明・期間不明・通貨不明・意味未確認のterminal FCFFは**金融入力としての採用を保留**する。純計算のプレビューが可能でも、その数値を無条件に仮説・売買条件へ採用しない。

現在の `decision` は `model-inputs`実行を全経路で強制する仕組みではない。この設計だけで源泉不明入力がすべてのCLIから拒否されるとは主張しない。次の有限実装は算術とcanonical監査path・IR変更制約の維持までとし、意味レビューの強制接続が必要なら独立した要件として扱う。新しい自己承認フラグでこの不足を解消しない。

## model-inputsとIR回答分岐への影響

[decision.py](../src/ir_agent/decision.py)の `_flatten` は `_prepare` が消費するcanonical inputsだけをpathへ変換する。[model_inputs.py](../src/ir_agent/model_inputs.py)も同じpathを監査するため、新fieldをraw JSONから取り出すだけで終わらせない。

| 箇所 | 最小変更時の確認事項 |
|---|---|
| `_prepare` | 新methodと必須7項目を検証し、terminal金額をcanonical inputsに保持する。raw fieldだけを読んでcanonicalへ入れない実装は不可。 |
| `_precision` | 新しいterminal金額も精度計算に含む。callerのDecimal contextに左右されない。 |
| `model-inputs` | `scenarios.<name>.inputs.terminal_fcff_jpy` をrequired pathへ含める。provenanceなしはmissing/needs_review。数値一致してもperiod/unit/definitionは未レビューのまま。 |
| provenance | 企業・期・単位・税/再投資後の定義、actual/guidance/estimate/assumptionを残す。派生計算なら全原典と計算来歴が必要。`external_estimate`等の既存監査kindと中間計算のkind名は別契約で、名前だけで自動変換しない。 |
| IR `parameter_paths` | 新fieldは質問時のbaselineに実在するcanonical pathとして固定する。答えを見て初めて追加するpathは、旧質問の許可済み変更にしない。 |
| method変更 | old dcf→新methodは `scenarios.<name>.method` と入力集合の変更。旧baselineにないterminal pathは現行 `parameter_paths`で指定できないため、新仮説版・新質問として設計し直す。旧質問の分岐・履歴を更新しない。 |
| 新methodを既に使うbaseline | 質問前にterminal金額と対応pathを保存していれば、明示的に許可したそのpathの変更を比較できる。曖昧/無回答分岐は従来どおり評価維持。 |

IRの返信が明るいという理由でterminal FCFF、安定g、WACCをまとめて変更する入口にはしない。各変更は既存の固定方針・出典・価格条件と独立に追跡する。この文書で新しいIR送信・注文を行わない。

## 有限の算術例

### 原典が示す「最終予測CF」と「終価翌期CF」の違い

young-growth p40の10年目FCFFは `109.67 million USD`、p39の11年目安定FCFFは `112.57 million USD` と表示される。単に `109.67×1.03` とすると `112.9601` で同じにならない。安定期の利益/再投資前提を明示して翌期CFを作る必要がある例である。

表示値をliteralに使うと `112.57/(.10−.03)=1608.142857… million USD`、最終予測CFの機械成長なら `1613.715714… million USD`。原文の終価表示は `1608.13` で、小差を未表示精度の推測で埋めない。年別割引率を持つこの例全体を、単一rの今回候補で177.56という企業価値まで再現したとはしない。

循環論文Table 3のROC/税引前後の不整合、Toyota/Exxonの表示精度や単位差は[既存仕様](cyclical-reinvestment-spec.md)と[source-audit](../research/cyclical-normalization-2026-10-15/source-audit.json)に残す。Table 3を訂正済みの正解表として新契約の根拠にしない。

### 年末・n期割引・二重成長を区別する合成例

次は算術検証専用の合成値であり、金融既定値や投資条件ではない。

```text
forecast FCFF = [-110, 121] JPY       # n=2
terminal FCFF_3 = 200 JPY
r=.10, g=.02, cash=0, debt=0, shares=10

PV_forecast = -110/1.1 + 121/1.1^2 = 0
TV_2        = 200/(.10-.02) = 2500
PV_TV       = 2500/1.1^2 = 2066.115702479338…
value/share = 206.611570247933… JPY   # 表示206.61
```

旧式の `121×1.02` を分子に使えば価格127.50。明示200へさらに1.02を掛ける誤実装なら210.743801652892…となる。n+1期分割り引くのも別の誤りである。

明示terminal FCFFを0にすれば、この例のTV/価格は0。欠損を0にした例ではない。terminalを−200とするとcash0ではequityが負となり現行制限上エラー。cashを明示3000にした別の合成ケースでは、equity `933.884297520661… JPY`、価格 `93.3884297520661… JPY`となり、負のterminal CF自体をclampしないことを確認できる。

## 最小受入条件と実装範囲

専用17テストで新methodの算術、旧dcf/EPS/DDMの回帰、exact7項目、負/0CFとequity制限、二重成長/割引時点、Decimal ambient非依存、入力不変を確認した。model-inputs/IR/CLIからの統合確認は別であり、この単体テストの件数へ含めていない。年別WACC・税・再投資推定・意味検証・自動取込は未実装のままである。

| ケース | 必要な結果 |
|---|---|
| 既存dcfの旧fixture/保存JSON | method・値・既存出力を維持。従来未消費のfieldだけで新modeへ切り替わらない。 |
| explicit terminal金額が最後の予測CFと異なる | その明示金額を1回だけ使用。最終予測CFを置換せず、配列長nも変えない。 |
| 上の合成例 | PV_forecast0、TV2500、n=2の割引、価格206.61を再現。税・再投資・成長を追加適用しない。 |
| terminalがlegacy式と同じ値 | 同条件の旧dcfと丸め前の結果が一致する。 |
| terminal欠損/null/bool/NaN/Infinity、未知input key | 明示エラー。legacy fallback・0補完なし。 |
| 空予測配列 | n=0未対応として拒否。架空の年を追加しない。 |
| 負予測CF/負terminal/terminal0 | 符号と明示0を保持。equity負は現行エラー、equity0は有効。 |
| `r≤0`、`g≤−1`、`g≥r`、不正shares/cash/debt | 現行の数値定義域を維持。新しい金利・成長の既定値を挿入しない。 |
| terminal金額の大きさ・桁差、hostile Decimal context | 精度に含め、外部contextの精度/丸め/trapに依存せず、計算資源限界は通常エラー。 |
| model-inputsでterminal provenanceがない/数値が違う | required pathとして不足/mismatchを返し、入力を確認済みとしない。意味検証は別保留。 |
| IR枝が無許可でterminal/g/methodを変更 | canonical比較でunmappedとして保留。旧質問を新methodへ自動移行しない。 |
| 中間計算の通貨/単位/期/g/意味が未解決 | 単体数値の計算成功と採用保留を分け、自動的に金融モデル・判断へ解放しない。 |

この最小追加で解消するのは「終価翌期CFの明示」とその算術・path上の区別である。安定期の成立、終価前提、税、ROC、資金調達、存続、投資判断の正しさを保証する機能は含まない。
