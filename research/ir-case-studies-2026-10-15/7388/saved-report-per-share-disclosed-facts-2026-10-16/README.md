# 7388：保存済み統合報告書の表示2値の構造化

既存normalizerで、物理42頁（印刷41頁）の最新「2025.11」列にあるEPS **88.79円**、BPS **508.60円**だけを`reported_fact` / `JPY-per-share`へ構造化した。

表の原見出し・年度列・単位・分割調整注記・丸め注記を連続原文のまま保持する。p2の既受入対象期間「2024年12月〜2025年11月」は別参照であり、日付端点やBPSの正確な時点日はnull。表題の2026を対象年度にしない。

会計基準、連結・単体、basic/diluted、普通株利益・持分帰属、EPS平均株数・BPS期末株数は未確認のためnull。分割注記の普通株表記からこれらを補完せず、総純資産・株数からの逆算や二重分割調整もしない。Graham入力・7社コホートへの適合、参考値・株価・金融採用は認定しない。

`normalization-input.json`と`normalized-bundle.json`には既存原典44頁のsourceオブジェクトをそのまま保持する。原典の再取得・再登録・分類変更、派生sourceのDB保存は行っていない。新しい派生の実DB初回保存日時はnull。

再現（DB・ネットワーク・CLI呼出なし）：

```bash
.venv/bin/python -B research/ir-case-studies-2026-10-15/7388/saved-report-per-share-disclosed-facts-2026-10-16/reproduce.py
```

`audit.json`は原文・値・単位・来歴と未知項目の保持を点検する。モデル入力監査APIやvaluation計算は呼び出していない。`manifest.json`に固定コア・既受入資料・新成果物のSHAを記録した。
