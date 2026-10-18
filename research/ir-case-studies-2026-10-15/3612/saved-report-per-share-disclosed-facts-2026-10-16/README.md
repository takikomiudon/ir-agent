# 3612：表示年次1株利益の1fact

保存統合報告書の2026/2列「**1株当たり当期利益**」171.36円を、既存concept `reported_annual_earnings_per_share` / `reported_fact` / JPY-per-shareとして構造化した。basic/diluted・ordinary帰属・厳密連結scope・EPS平均分母はnull/未確認を保持。年度ラベルの精度を保ち、報告書対象期間をEPSの正確な開始/終了日へ自動転用していない。

IFRS18を2027/2から早期適用し2026/2へ変更反映という注記、EPS全期間は2026-03-01の1→2分割を遡及反映という注記、p66株数は分割前という区別をscopeへ固定。BPSは作らず、7社の年次Graham入力適合コホートへ追加認定しない。新normalizerはなく固定コアd434b41c…を使用。

[normalization-input.json](normalization-input.json) は期間列・単位・値が同じ逐語範囲に入る連続原文を保持（見出しと行の人工連結ではない）。[normalized-bundle.json](normalized-bundle.json) は原source全object不変＋新派生1sourceで、独立原典追加ではない。[audit.json](audit.json) と [reproduce.py](reproduce.py) でAPI wholebundle replay/reproducer/Decimal/引用位置・旧pinsを検証。

原典は親報告の既actual、新派生はfile-onlyで初回DB保存未確認。GET/DB/Store/CLI/再原典登録/金融計算採用/予測/price/IR/nativecase/共有索引/code/旧files変更0。成果を固定して停止。
