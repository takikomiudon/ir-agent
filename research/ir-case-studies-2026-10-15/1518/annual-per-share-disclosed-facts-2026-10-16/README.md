# 1518 年次連結EPS/BPS：直接公表2facts

固定normalizer core d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51 の既存directfunctionで、原p1連結実績**EPS148.30円・BPS原1,453.23円→1453.23**だけをreported_fact/JPY-per-share/v1decimalとして保存した。EPSannualduration2025-04-01～2026-03-31、BPSinstant2026-03-31。同一quoteの対象日付・連結scope・円 銭・該当列を保持し、原20頁source全objectは不変。

p20ordinaryEPS平均45289824株とBPS末38295660株、BBT末983000株と平均985154株の控除を別basisで保持。2025-10-01効力1対5split・比較値調整が会社公表で既に反映された値を使い、二重分割換算やBBT二重控除をしない。純資産55800/NCI147/普通株帰属55652等の丸め表示から再計算もしない。

当時guide185.40、後日7月修正229.67/8月Q1据置と、個別EPS44.61/BPS1041.70は混入0。年次利益の譲渡・売却・税費用を正常利益へ補正せず、石炭/非継続分類も新造しない。現在split/sharebasis・利益持続性・金融method適合は未認証。

normalized-bundleは原本そのまま＋派生2factsの2source、会社/thesis更新空。frozen real nowで標準reproducerがbytes完全再現、引用/数値UnicodeUTF8位置・旧29pins/入力7pinsを照合した。native models.json_text SHA、normalizercompactoriginalsnapshotSHA、raw/contentSHAを区別する。CLI/valuationcodeは呼ばずpinしない。model-input-audit-requestはstrict既存入力の準備だけで、内部計算を避け実行していない。金融・独立meaning・expectedvalue採用false、meaningreviewrequiredtrueのまま。

再現: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-case-studies-2026-10-15/1518/annual-per-share-disclosed-facts-2026-10-16/reproduce.py`。既存1518case・元条件ID・既読/DB来歴を変更せず、新nativecase登録要求も作らない。GET/DB/Store・共有旧company/source/case/docs/index・計算/金融採用/価格/IR送信0でfreeze。
