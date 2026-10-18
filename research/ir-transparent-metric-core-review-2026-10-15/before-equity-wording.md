# crible独自ROIC・ROC・EY：最小算術境界の静的確認

固定commit `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`の指定3blobを3GETで取得し、decoded bytesとGit blob SHAを再計算照合した。**このrepoが計算する3指標の本体、平均期、株式選択、per-symbol出力の±∞除去は特定できた。日本株原典binding、PIT、依存runtimeの実行、金融採用は未実施。** 前段proofは不変。

参照は[upstream-extras.py](upstream-extras.py)＝E、[upstream-canonical.py](upstream-canonical.py)＝C、[upstream-snapshot.py](upstream-snapshot.py)＝S。1起算行位置で示す。3file以外のrepo本文・外部依存は追加取得しない。

## 閉じた独自算術（有限・整合済みの入力という限定）

| 指標 | 確認できた実装 | 期間・符号・境界 |
|---|---|---|
| `roic` | 税率＝税金費用÷税前利益を0〜0.5へclip。NOPAT＝EBIT×(1−税率)。資本＝純資産＋有利子負債−現金等の期首期末平均。NOPAT÷平均資本。[E:59–69] | 税前利益は**>0**が条件なので0も赤字もNaN。平均資本>0、かつ**平均資本≥0.1×平均総資産**。境界ちょうど10%は残る。前年不足はNaN。税額負値はclipで税率0、税率50%超も0.5に抑える。EBIT自体の正条件はなく、条件を満たす0/負EBITは0/負の結果を保つ。総資産正の独立gateはない。 |
| `greenblatt_roc` | EBIT÷（当期working_capital＋当期net_ppe）。[E:88–93] | 税前・平均資本ではない。分母>0のみ。EBIT0/負はその符号を保持。ROICの税率clipや小分母10%guardはこのROCへ適用されない。 |
| `greenblatt_earnings_yield` | 時価総額＝価格×選択株数、EV＝時価総額＋負債−現金等。EBIT÷EV。[E:99–113] | EV>0のみ。価格なしはNaN。[E:132–141] EBIT0/負はその符号を保持。少数株主持分・優先株・別の非事業資産を式に追加しない。EV/EBIT一般ratioとの同値は未読依存へ拡張しない。 |

税率clip・小分母10%は**maintainerの実装仮定**で、Greenblatt本人の規則でも、本projectが採用した条件でもない。税前利益と営業EBITへ同じ実効税率を適用してよいか、税効果・一時税・連結主体の対応は会社原典で別途確認が要る。

C:94–127の平均は、直前行の期末が当期末の300–430日前にあるときの(当期＋前年)÷2。単純な全期間平均や任意の過去年との比較ではない。全ラベルが日付解析不能なら位置shiftへ戻るため、実会社入力は正しい期末年月日と昇順が必要。年だけのラベルは12月31日に解釈するので、日本の3月期を年度名だけで入力しない。これらの窓・暦仮定もmaintainer仕様として記録し、独自の投資期限へ転用しない。

### 必要なcanonical行と由来

C:14–64,149–202はprovider列をcanonicalへ対応し、不明列はNaN。以下は既存normalizerから**必要になる候補行・期**の一覧で、対応済みや抽出済みという認定ではない。5988有報の行探索・抽出は別担当へ委ね、新規抽出0。

| 目的 | 必要行 | 期・source対応 |
|---|---|---|
| ROICの分子 | EBIT、税引前利益、税金費用 | 同じ対象年・連結/単体・会計範囲。営業利益を自動でEBITと同一視しない。 |
| ROICの分母・guard | 純資産、有利子負債、現金等、総資産 | 当期末と直前の適格年度末の2組。平均資本だけでなく平均総資産も必要。税率・割合と通貨建て金額を混同しない。 |
| ROC | working_capital、net_ppe、当期EBIT | 当期末BSと対応する年次利益。運転資本はprovider行が全期欠損のときだけ流動資産−流動負債で導出する。[C:184–185] providerの既存行があればその定義との適合を要確認。 |
| EYのEV | 株価、株数、当期末負債・現金等、当期EBIT | 価格の観測日・通貨/単位と期末株式/分割基準を合わせる。負債は総額が全期欠損なら長期＋短期を足し、片側欠損は0にしない。[C:191–196] |

EBITはproviderのEBIT列が全期欠損の場合だけ税前利益＋支払利息で導出する。[C:189–190] この算術が日本原典の営業利益や事業利益と同じ意味になるとは限らない。Cのfallbackは**列全体が欠損か**で判断するため、一部の期だけ欠損する場合を行ごとに補完する実装ではない。

各値には会社/証券同定、対象範囲、期首/期末/対象期間、実績/予想、通貨と百万円等の倍率、原source・頁/行・SHA、定義対応と算術来歴が必要。公表時刻/精度、実初回保存/known-by、訂正・後着を別に保持し、最新snapshotを過去の利用可能値にしない。これらは未bindingで、コード存在では充足しない。

## 株数・価格の基準

C:136–146は期末株数を基本とし、加重平均株数との比が0.5〜2（両端含む）の範囲外なら加重平均へfallbackする。比がNaNなら一度期末値を許容し、最後に欠損を加重平均で埋める。加重平均が欠損でも期末値が存在する場合は期末を使い得る。株数の正・有限をこのhelperだけが全面検証するとは言えない。C:74–81の過大/過小scale除外も系列medianとの相対guardで、実際の正しい株式分母を証明しない。

EPS用の株数と価格掛算の株数は別。[E:100–106; C:34–37] 自己株式控除、期中増資、クラス株、株式分割、reported/financial currencyの選択は原典へ結び付ける必要がある。S:148–181の通常価格選択は最新期の1行だけに価格を置き、S:92–104は古すぎる期、FX・分割の処理を呼ぶ。ただし外からprice Seriesを直接渡す経路は同じ最新行生成を通らず、FX/split helper内部も未読なので、全入力経路のPIT安全性を認定しない。

## 非有限出力の到達境界

S:106–110はcanonical/各計算block/overlay/provenanceの後、**per-symbolの返却直前**に正負のnp.infをnp.nanへ置換する。S:277–296でE.compute_extrasがその経路へ確実に接続されている。前段で未確認だった出力∞除去の場所はここで特定できた。

ただし入力のfinite検証ではなく出力の置換である。非有限の分母で有限0になったり、clipで有限値になった結果まですべて欠損化するものではない。最小算術仕様の適用は、元入力の有限性・単位・期間が確認済みである範囲へ限定する。missing_inputsはCの欠損項目を列挙するだけで、非正分母・前年不足・clip・∞置換の全理由を説明する診断ではない。[S:330–350]

S:686–703はその後にFX・rank・追加指標をattachする。ここで最終frameを再度一律∞置換するコードはなく、未読helperが生成する列や公開済みキャッシュ・runtime全体まで非有限安全性を広げない。EのROIC/ROC/EY局所の欠損挙動を、repo全指標が欠損を一切補完しないという結論にも広げない（主対象外の配当処理に明示代替がある）。丸ごと導入の適否は今回未判定。

## 順位と将来ROCの境界

- S:29はranks.attach_ranksをimportし、S:698で全銘柄のcross sectionへ適用する。その実装は未読。INDICATORSのpercentile平均とGreenblattのordinal順位和が同じ順になるという説明は**こちらの認定にしない**。peer group、因子ごとの欠損集合、同順位・欠損処理を確認していない。Brazilのdense＋first方式や同じkernelへ混合せず、順位/選定/退出規則の追加取得・採用0。
- 本projectの[stable-reinvestment仕様](../../docs/cyclical-reinvestment-spec.md):5,50–56,74が要するROC_newは、将来安定期の新規投資に対応する税後利回り。歴史税前のgreenblatt_rocとは分子・分母・時点・投資範囲が違い、歴史税後roicでも新規投資利回りを示す追加根拠が要る。どちらもROC_newへコピーしない。本体が読めたことは将来g・税率・再投資率の採用ではない。

## 今回閉じた範囲と停止

期間の正しい有限canonical入力が揃えば、上の3つの式とguardを再記述できる単位まで閉じた。ただしnumpy/pandasのversion・runtimeを実行検証せず、一般ratio/全snapshot/順位の再現器を作っていない。新規の算術数値例も実行・生成していない。依存はpandas/numpy、FX/split、audited merge/reconcile、各rank等が未読のまま。必要以上の追跡・新しい候補一覧は作らず、3GETで止める。

[guard.json](guard.json)、01–03 capture、raw/、[acquisition-results.json](acquisition-results.json)、[validation.json](validation.json)に選択元・hold/robots再利用・HTTP entity完了時計・SHA/Git blob再計算を保存した。コードcopyもsourceデータとして扱い、import/実行していない。新GET3、robots再GET/retry/redirect/他path/外部依存・データGET0。生成英語引用は新規0、既存と累計21words。MIT元本文・前段proof・共有file・DB・他担当fileは変更していない。日本株sourceへのbinding、financial policy、著者本人方式、投資有効性の認定は0。
