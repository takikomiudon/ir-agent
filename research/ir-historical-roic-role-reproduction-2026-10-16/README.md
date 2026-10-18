# FY2026：仮定を明示したrole別ROIC研究算術

rootの[選択票](../ir-historical-roic-binding-design-2026-10-16/conditional-research-selection.json)に従い、**FY2026だけを1回、stdlib Decimalで計算した**。結果は`conditional_on_research_mapping:true`。8開示factの意味review受入は表示行の確認であり、provider equity/debt・連結利益範囲の同値性や金融入力採用を認証しない。

| 計算結果 | JPY（比率以外） |
|---|---|
| 期首参照資本 E前期末＋Dopening−C前期末 | 60,825,000,000 |
| 期末参照資本 E当期末＋Dclosing−C当期末 | 66,656,000,000 |
| 両roleの平均資本 | 63,740,500,000 |
| 平均総資産 | 103,439,500,000 |
| maintainer10%guardの比較額 | 10,343,950,000 |
| 正資本＋10%guard | pass |
| 既存clip後NOPAT（再計算しない） | 508,500,000 |
| 条件付きFY2026 role ROIC（ratio） | 約0.00797765941591295957829 |

表示額からの正確な比の表現は**1017000000 / 127481000000**。stdoutに分子/分母、Decimal precision80・ROUND_HALF_EVENの近似とinexact flagを保存した。元表示は百万円単位なので、この比を未丸めの実際の経済利回りとしない。割合は百分率ではなくratio。丸めをguard判定へ持ち込まない。

## 保持したmappingとnull

Eは普通株式に係る期末純資産の仮canonical対応、Dはleaseを含む借入金等合計の仮対応、C/Aは現金同等物/資産合計の仮対応。E/C/Aの前期末を期首参照にすることと、p104 Dのopening/closingをp65のFY文脈へ関連付けることは**選択票の研究者仮定**である。providerのequity、利益範囲、TotalDebtとの同値性はfalseのまま。

Dの元factのexact dateはすべてnullを維持し、暦日を挿入していない。C.averageの300–430日日付窓/runtimeを再現したとは呼ばない。strict FY2026 ROICはnull。2024opening一式がないFY2025 ROICもnull。future ROC_new、EY、valuation、rankは理由付きnullで、歴史値を将来の税後新規投資利回り・IR後倍率/予測・financepolicyへ転用しない。税clip0〜50%と10%guardはmaintainer conventionで、Greenblatt本人の規則や会社の正常税率ではない。

## 入力固定と再現物

[input-pins.json](input-pins.json)に旧14fact bundle `4c7723e…`、既存NOPAT stdout `a528deaf…`、8fact bundle `642534fa…`、意味review `8266ec33…`、root受入、選択票、設計、固定crible C/E本体とMIT本文を**全SHA**で直接pinした。本体はcommit00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7のGit blob SHAも再計算照合。MITをissuer/providerデータの利用許可へ拡張しない。

[reproduce.py](reproduce.py)はupstreamをimportせず独立のrole算術を記述する。元source objectが14/8 bundleで完全一致すること、各8fact ID・scope・unit・役割・null日付・原表示換算・原文quoteを照合し、8件の二段JSONpointerとsource SHAを出力した。既存NOPATの3入力fact ID・原表示単位・2段pointerは、旧scalarのbindingを変更せず参照している。NOPATや税率を今回別方式で作り直していない。

実行stdoutは[reproduction.stdout.json](reproduction.stdout.json)、stderrは[reproduction.log](reproduction.log)、入力/出力/script SHAと限界は[validation.json](validation.json)。計算実行1回・再実行0。rootの別Fraction照合は本担当で実行・採用していない。scriptの実行時刻は研究記録であり、公開時刻や実DB初回保存ではない。

実金融入力採用false。GET、DB、prod API/CLI、元fact/他proof/共有file変更、upstream runtime実行、外部依存導入/importは0。この限定された研究算術を終了する。
