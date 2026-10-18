# 141A：会社の決算関連資料入口のみ確認し終了

**正式FY2026/6財務本文・公開事業Q&Aは取得していない。** 保存済みIR FAQが明示する決算関連資料入口を1件だけ確認した。robotsは404の通常HTML、入口は200で、合計2GET。静的169リンクにPDF hrefはなく、本文のFY2026/6ラベルも未確認。pagePropsは空で、client chunk参照だけがあるため、JS/API/別経路へ進まず残1GETを使わず終了した。

保存IRトップには「2026年08月12日 2026年6月期 第4四半期 決算説明会」の同入口リンクがあるが、正式本文の内容・会計期間・開催実施を認定しない。既存FAQは資料の掲載先を案内する範囲で、西友統合・価格施策・店舗改革への回答は確認できなかった。この限定経路で未取得なのであり、会社が非公表であることや資料が存在しないことの証明ではない。

今回のsourceは非金融のindex-only。会社実績・会社計画・著者独自予測の数値はすべて未取得で、2026/3著者レポートを現在最新・システム事前予測へ置き換えず、的中率・株価・倍率・EPS・IR質問・モデル入力を作らない。

`capture.json`/`01.json`/`02.json`とraw/textを保存。HTTP本文完了はrobots13:51:13.999387UTC、入口13:51:18.683333UTC、2026-10-15。published_at:null。Last-Modifiedを公表日時へ転用しない。原rawはRequests応答entity bytesで、gzip等のデコード後でありwire bytesの証明ではない。固定UAはCodex-IR-Research/0.1、TLS/proxy/CAを保持し、全7exacthost holdを事前照合した。404はrobots規則の明示許可ではない。

`source-bundle.json`は未importのwatch会社metadataと入口source1件だけ。held:falseもmetadataであり保有申告ではない。DB・既存source・index・code・監視・送信は変更しない。原文短引用/位置はquotes.json、出所と限界はreview.json、有限byte/parser/schema照合はvalidation.jsonへ保存し、この成果を固定する。
