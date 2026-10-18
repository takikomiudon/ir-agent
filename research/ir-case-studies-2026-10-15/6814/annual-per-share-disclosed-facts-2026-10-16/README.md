# 6814 直接公表EPS/BPS：2facts file-only

normalizer core d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51 の既存directfunctionだけで、原p1の連結annualEPS529.53円・BPS原2,826.61円→2826.61をreported_fact/JPY-per-share/v1decimalとして正規化した。EPSduration2025-03-01～2026-02-28、BPSinstant2026-02-28。raw円 銭/年次日付/連結scope/該当列を同一引用に固定する。

原p21ordinaryEPS平均31604751株、BPS期末31608824株、普通株期末純資産89345百万円/NCI控除426/総純資産89772は別表示・精度で保持し、丸め総額の引算/割算はしない。p13株主資本76310/OCI13035/NCI426を外部provider持分へ無条件に置換しない。個別414.55/1780.67、当時guide411.28/中間253.09は対象外。会計方針基準改正「有」の詳細p19未読、10/9guide修正・後発Q2literal未取得、current splitbasis未認証をscopeへ残した。

原source全22頁objectは不変、派生1本だけ追加。CLI・valuationcodeを呼ばずpinせず、保存frozen nowで純関数再現bytes完全一致を確認。model-input-audit-request.jsonは入力準備のみで実行せず、金融/独立meaning/expectedvalue採用false・meaningreviewrequiredtrueを維持する。

再現: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-case-studies-2026-10-15/6814/annual-per-share-disclosed-facts-2026-10-16/reproduce.py`。旧32pins・入力8pins、quote/token位置・原source不変を点検。GET/DB/Store・共有旧file/docs/index変更・新頁意味読解・計算/採用/IR送信0でfreeze。
