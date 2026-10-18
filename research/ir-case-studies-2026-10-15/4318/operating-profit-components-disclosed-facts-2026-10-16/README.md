# 4318：年次営業利益構成4行のprepare-only

既読の2026年3月期連結短信p11（印字9）から、当期2025-04-01〜2026-03-31の売上高33,924,750／売上原価11,337,224／販売費及び一般管理費18,003,834／営業利益4,583,690を各原token・千円で構造化した。日本基準連結。既存normalizerの明示倍率1000だけでJPYへ換算し、報告実績4factとして保存。会社作者と抽出担当を分離する。p15のD&Aや旧EPS/BPSはfactsに追加していない。

表示上の売上−原価−販管費は4,583,692千円で、報告OPより2千円大きい。4つの直接表示値を維持し、OPを修正せず、差の原因を丸め/切捨てと認定しない。単位換算成功とPL恒等式の表示完全一致は別である。

原sourceはread-only SQL（mode=ro/query_only/closing）で現保存objectと旧requestの全field同値を確認。native JSON SHAとcontent SHA・normalizer compact SHAを区別してprep.jsonに保持。原public表示日は2026-04-30、精密published_atはnull、元retrieved_atは10:20:34.020327UTCのまま。派生の今のAPI作成/取得時刻は、実台帳への初保存ではない。DB/Store書込・ingest/job/index更新なし。原/派生2sourceのbundleであり、新しい原典が増えたわけではない。

特別売却益をOPへ再加減せず、税後正常EPSの不足を解決扱いしない。日本OPはCarlisle Operating Earnings/OIADPと未同定。D&A内包範囲・TTM・四半期・最新性・fair value・EV/順位・価格・金融採用・IR準備は認証しない。既読p11の受入を再利用し、新たな頁/画像確認や取得は0。

normalization-input.json→normalized-bundle.jsonを純APIで実行し、全4値Decimal換算・同時刻replay・reproduceを確認。prep.jsonに原文位置・同一source・差額・旧pins不変と限定検証を保存。rootの独立review後に別taskでDB接続するため、ここでfreezeして待つ。
