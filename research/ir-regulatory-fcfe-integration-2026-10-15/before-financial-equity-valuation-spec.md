# 金融株主価値評価の実装仕様案

**実装済みは、原典に明示された将来DPSの配当割引モデル（DDM）。規制資本再投資FCFEは確認式と入力仕様だけを記録し、計算器はまだ実装していない。FCFEの終価・株価換算・自動希薄化は対象にしない。** 会社予測や金融係数を作る仕様ではなく、明示入力を再現する計算器の仕様である。

採用元はAswath Damodaran, *Valuing Financial Service Firms*, April 2009、出典ID `damodaran.financial-services.2009`。[NYU原典PDF](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf)は[保存済みsources.json](../research/valuation-model-routing-2026-10-15/sources.json)の原バイトと抽出本文から確認した。新規GETは行っていない。以下の頁番号はPDF物理頁と印字頁が一致する。DDMの式は保存PDF15頁を画像でも照合した。

## 原典で確認したDDM

14頁は、企業全体の税引後・負債支払前CFをWACCで割り引く企業価値評価と、株主CFを株主資本コストで割り引く株主価値評価を区別する（引用F01）。金融機関については後者を選ぶ理由を説明している。

15頁の一般式と、安定期Gordon式は次のとおり。

```text
Value_per_share = Σ_(t=1..∞) DPS_t / (1 + k_e)^t
Stable_value_per_share = DPS_1 / (k_e − g)
```

`DPS_t` は各期の予想1株当たり配当、`k_e` は株主資本コスト。`DPS_1` は**翌期**の予想配当、`g` は安定期の永久配当成長率（引用F02・F03）。直近の実績配当を自動成長させる入力契約ではない。

同頁の予測期間n年を持つ原式は、予測期の株主資本コスト `k_e,hg` と安定期のコスト `k_e,st` を分けている。

```text
P_0 = Σ_(t=1..n) DPS_t / (1 + k_e,hg)^t
      + DPS_(n+1) / [(k_e,st − g_n) × (1 + k_e,hg)^n]
```

したがって実装では、まずn期末時点の終価を計算し、それを予測期コストでn期分割り引く。

```text
TV_n      = DPS_(n+1) / (k_e,st − g_n)
PV_DPS    = Σ_(t=1..n) DPS_t / (1 + k_e,hg)^t
PV_TV     = TV_n / (1 + k_e,hg)^n
P_0       = PV_DPS + PV_TV
```

終価はn期末にあり、分子はn+1期の配当。終価をn+1期分割り引いたり、分子へもう一度 `(1+g)` を掛けたりしない。n期の配当は予測配列、n+1期以降の配当は終価に含まれ、重複させない。

## DDMの5フィールド入力契約

以下は**projectで採用する計算入力契約**であり、原典にJSONの仕様があるわけではない。金額はすべて同じ株式単位のJPY/株、配列は年末支払・年単位、率は年率の小数比率で入力する。株主資本コストは予測期間内で一定、安定期内で一定とし、両期の値は別々に必須とする。

| フィールド | 型と意味 |
|---|---|
| `dividends_per_share_jpy` | **空でない**有限Decimal配列。t=1からnまでの各年末予想DPS。nは配列長。数値文字列も同じ値へ正確に変換する。 |
| `cost_of_equity` | 予測期の `k_e,hg`。明示入力、正。 |
| `terminal_cost_of_equity` | 安定期の `k_e,st`。明示入力、正。予測期の値から自動補完しない。 |
| `terminal_dividend_per_share_jpy` | 明示した `DPS_(n+1)`。最後の予測配当から自動計算しない。 |
| `terminal_growth_rate` | `g_n`。安定期の永久**配当**成長率。`-1 < g_n < terminal_cost_of_equity`。会社のEPS成長率をそのまま流用しない。 |

両期のコストを同じにしたい場合も、同値を両フィールドに入力する。16頁はリスクや成長を含む入力間の整合を求め、18〜19頁は成長・ROE・分配の関係を扱う。原典の企業例の金利、ベータ、成長率、利益率等を既定値にしていない。

未入力の形を表す下記は**計算可能な入力例ではない**。nullを数値や0へ補わない。

```json
{
  "dividends_per_share_jpy": [null],
  "cost_of_equity": null,
  "terminal_cost_of_equity": null,
  "terminal_dividend_per_share_jpy": null,
  "terminal_growth_rate": null
}
```

取得・予測の根拠は計算入力の外側で、評価時点、株式種類、株式分割等の基準、各期の日付、実績/会社予想/独自仮定、原文と出典ID、入力を作った者、安定期へ移る根拠として保存する。5フィールドが形式上正しくても、その予測の妥当性や金融業種の適合まで確認済みにはならない。

## DDMの定義域と結果

以下は計算器の検証規則であり、買い条件・投資の推奨値ではない。

- 5フィールドを必須にし、null、非数、無限値、boolを数値として受け取らない。
- DPS配列はn>=1。空配列はエラー。原典の安定期式はn=0の純Gordonに相当するが、**今回の入力契約では未対応**とする。架空の予測年やDPSを補って配列を作らない。
- 配列の各DPSと終価翌期DPSは0以上。明示された0は有効だが、未確認配当を0にしない。
- `cost_of_equity > 0`、`terminal_cost_of_equity > 0`、`-1 < terminal_growth_rate < terminal_cost_of_equity`。両コストを正とする条件はprojectの限定した入力定義域である。成長率条件はこのGordon式の持続的な配当成長と収束に対応する。
- 丸め前のDecimalでPVを計算し、最終表示等の丸めは既存評価器と整合させる。分母が小さい場合に恣意的な安全率や上限価格を挿入しない。計算精度・資源の限界に達する入力は明示エラーにする。

結果は予測配当PV合計、n期末の終価、終価PV、合計の**1株当たり株主価値**を区別して返す。各年のDPS・期間・根拠は入力と付随記録で追跡する。これを企業価値と呼ばない。現在株価や買い・利確条件はこの計算とは別の根拠付き入力であり、このモデルの5フィールドに含めない。

安定期へ移る時点の配当性向・利益成長・ROE・資本要件が整合しているかは外部の研究レビューが必要。19頁の関係 `Payout ratio in stable growth = 1 − g / ROE_stable` はその確認根拠（引用F05）だが、ROEを推測して配当を自動作成する機能は今回実装しない。

## 実際の配当と配当可能額、0配当の解釈

10〜11頁は、利益を留保して資本比率を厚くするために配当可能額より少なく支払う銀行と、過大な配当を新株発行で補う銀行の両方を説明する（引用F11・F08）。**実際の配当額は、配当可能利益・持続可能な株主CFと同義ではない。** 低配当や無配だけで価値が低いと結論せず、成長に必要な規制資本と資本政策を先に確認する。

16頁は、直近配当を起点に過去やアナリストの成長率を機械的に使う危険を指摘し、成長・配当・リスクの内部整合を求める（引用F12・F04）。DPS配列と終価翌期DPSには、分配の持続性、配当性向の変化、規制資本への留保、買戻し・希薄化の扱いを外部の根拠付き前提として反映する。直近配当だけの永続外挿、配当予想の欠損を実績値で埋める処理は行わない。

すべての予測DPSと終価翌期DPSを明示的に0と入力すれば、この式のモデル値は0になる。ただし、これは**その分配前提の下でDDMが表す価値が0**という計算結果であり、企業全体の価値や配当可能利益が0との断定ではない。11頁も、無配企業を実際の配当だけで評価するとゼロ株主価値に至る問題を説明する（引用F13）。将来の分配変更、留保資本、買戻し等を入力が表現できているかを確認し、0を自動的な除外や売却条件へ変換しない。

## 規制資本FCFEの確認式（計算器は未実装）

21〜22頁は、金融機関の再投資が通常の設備だけでなく規制資本へ向かう点を説明し、22頁は次を明記する（引用F06）。

```text
FCFE_financial,t = NetIncome_t − ReinvestmentInRegulatoryCapital_t
```

この中間量の入力は、期間を揃えた純利益予測配列と規制資本再投資予測配列。出典、連結・単体、普通株主等の利益帰属、資本の定義、通貨・単位・対象期、明示した外部仮定を揃える。増加資本をどの規制指標や資本政策から算定するかは外側で根拠付きに作り、原典の例示資本比率を適用しない。

中間量の結果が負でも、0へ切り上げない。必要資本が利益を上回る可能性の表現として残し、資金調達の実現性・株主負担は別途点検する。原典は規制資本比率と追加活動の収益性の重要性を示すが、現行日本の制度に対応した必要資本計算器は提供していない。

**p21〜22のFCFE節では、規制資本FCFEを用いた終価 `FCFE_(n+1)/(k−g)` を直接確認できなかった。** p15にあるのはDPSの終価である。今回の仕様ではFCFE終価・FCFEからの総株主価値・株価換算を未確認/未実装とし、DDMの式の記号を勝手に入れ替えない。明示翌期FCFEがあっても、この制限を解除したことにはならない。

将来のFCFE評価器を検討する際に、明示翌期のNI・規制資本再投資・FCFE、株主資本コスト、安定成長・資本政策、普通株式数等が研究項目になることは整理できる。ただし、これらを入れれば終価・希薄化まで正しく計算できるとの原典確認は今回得ていない。

## cash・debt・sharesを通常FCFFのように扱わない

14頁は株主価値を直接求める方針を示し、21頁は株主CFを負債支払・再投資後のCFと説明する（引用F01・F07）。DDMはさらに1株当たりの分配を割り引くため、結果は既にJPY/株である。

したがって今回のDDM入力には `cash_jpy`、`debt_jpy`、`shares_outstanding` を持ち込まない。通常FCFFの結果に対するようにcashを足し、debtを引き、さらに株数で割ると、価値の範囲や単位を取り違える。このフィールド除外は、原典のequity基準に対応するprojectの契約である。

原典の確認箇所から「金融機関の全cashは常に無価値」「いかなる非営業資産の調整も禁止」とまでは結論しない。余剰資産、別種の持分、特別な資本構造を調整するなら、別の根拠と範囲の橋渡しが必要であり、今回の単純なDDMへ暗黙に足さない。

## 増資・希薄化・買戻し・生存リスク

10〜11頁は、成長には資本が必要なこと、配当を過大に支払って新株発行で埋める問題を説明する（引用F08）。18頁は買戻しが株主への現金還元にもなり、配当だけを見ると歪み得ることを説明する（引用F10）。しかし、この論文の確認箇所では、将来増資・複数種類株・権利発行・買戻しを一括してDPSと既存株主価値へ配分する完全な希薄化計算規則は確認できていない。

今回のDDMは**入力DPSに将来の株式数・分割・希薄化の扱いが外側で一貫して織り込まれていること**を必要とし、自動で株数を予測しない。現在株数で将来総配当を割る、純利益をEPSへ変換する、新株発行収入を企業価値へ追加する等の機能もない。将来DPSの帰属を説明できなければ入力準備を未解決にする。買戻しをDPSへ勝手に加えることもしない。

13頁は、規制があるから全銀行のリスクが等しいと考える危険を説明する（引用F09）。このDDMを計算できることは、資産健全性、規制資本、資金繰り、破綻・処理・株主価値毀損の問題を解決したことではない。銀行の生存/失敗確率や破綻時回収価値を自動推定する規則は当該節で未確認であり、計算器に生存確率1や失敗時価値0を既定設定しない。重要な存続リスクが未解決なら、継続前提のDDM値を無条件の投資判断へ利用しない。

## 実装前に確認する不変条件

- 予測期と安定期のコストを別入力にし、片方の欠損を補完しない。
- 終価の分子は明示したn+1期DPS、割引期間はn。最後のDPSを使い回さない。
- 配列内の0は明示配当、空配列やnullは欠損/契約違反として区別する。
- 完成した結果の単位はJPY/株で、FCFFの企業全体値やFCFEの中間量と混在させない。
- 数式や入力検証が通ったことを、規制・希薄化・生存・投資条件のレビュー完了と報告しない。
- 銀行という業種だけでこのモデルを自動推奨せず、金融PERの禁止ルールも作らない。

## 原典照合表

以下は同じNYU原典の短い逐語引用。保存抽出本文の指定頁と空白正規化後の一致を確認した。数式は上記の対応箇所を参照する。

| ID | PDF/印字頁 | 確認した原文 |
|---|---:|---|
| F01 | [14](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=14) | “discounting cashflows to equity at the cost of equity” |
| F02 | [15](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=15) | “Expected dividend per share in period t” |
| F03 | [15](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=15) | “dividends per share next year.” |
| F04 | [16](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=16) | “assumptions have to be internally consistent” |
| F05 | [19](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=19) | “Payout ratio in stable growth” |
| F06 | [22](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=22) | “Net Income – Reinvestment in Regulatory Capital” |
| F07 | [21](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=21) | “after debt payments have been made and reinvestment needs met.” |
| F08 | [11](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=11) | “far too high and then try to compensate by issuing new shares.” |
| F09 | [13](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=13) | “all banks are equally risky” |
| F10 | [18](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=18) | “stock buybacks as a way of returning cash to stockholders.” |
| F11 | [10](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=10) | “some banks pay out less in dividends than they can” |
| F12 | [16](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=16) | “start with the current dividends of the bank as a base” |
| F13 | [11](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf#page=11) | “we will arrive at the result of a zero value for equity.” |

保存原本SHA-256: `2e1b2d45a8d04ab14b8ed48825b64e7765dd896d59e1db34cce32ded23d07472`。原本・抽出本文は既存sources.jsonから読み、変更していない。本仕様で追加したフィールド名・型・定義域・未対応範囲はproject設計であり、著者が同じAPIや自動運用を提案したものではない。
