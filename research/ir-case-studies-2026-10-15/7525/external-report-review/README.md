# 7525 リックス：Q&N掲載ページは確認、PDFは取得器上限で保留

公式IRの保存リンクをSHA/実hrefと照合し、robots、QUICK&NOMURA掲載ページ、同頁に明示されたPDFの**3 GET（上限4）**で終了しました。全応答は200ですが、PDFは既存Fetcherの3MiB上限でValueErrorとなり、完全な原バイト・本文は保存できていません。HTTP拒否や503・robots禁止とは区別します。再取得・別経路・JS実行・自動redirectは行っていません。

掲載ページは、対象会社・QUICK・野村インベスター・リレーションズの3社間契約に基づき**QUICKが作成**し、執筆者は対象会社からスポンサー料を受領するため独立した立場ではないと明記しています。機関投資家を主に想定すること、巻末重要事項を読む必要があることも確認しました。これは作者/経済関係の一次説明で、個々の数値を誰が予測したかや独立検証の証明ではありません。委託関係だけで著者自身の推計不存在とも判定しません。

レポート本文の著者個人名・日付・独自EPS/利益予測・会社計画の再掲・目標価格・明示評価式・対象期間・事業仮説/反証条件・巻末重要事項は**unknown**です。不在とせず、掲載ページから未読本文の数値を補いません。この範囲ではIR後再評価の数値モデルを再現できるとは確認できません。

robotsは当該掲載ページ/PDFパスを許可し、共有lockで0.5rpsを守っています。既知の禁止hostへの要求0。explicit343社台帳内照合は旧窓口根拠であり、現在の送信適格性や投資候補採用ではありません。

`source-bundle.json` は成功した説明HTML1件のみ（非金融、companies/theses空、canonical jp:7525、financial_inputs_verified=false）。`source.retrieved_at` は**HTTP本文完了09:18:45.436364UTC**で、元dispatch/開始時刻はmetadataに別保持。PDF要求完了は失敗試行の完了時刻であり、未取得本文のsource時刻にしていません。公表時刻/日付はnullです。

raw/text/captureSHA・原公式リンク/新PDFhref・4逐語引用・既存2ファイル不変を保存。パスは`research/ir-case-studies-2026-10-15`基準、新providerのgeneric verifier未対応はunknown扱いです。DB/旧file/code変更・予測/モデル採用・IR草案/送信は0、残り1GETは使わず完了します。
