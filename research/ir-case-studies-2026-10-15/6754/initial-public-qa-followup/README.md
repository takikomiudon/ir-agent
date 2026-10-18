# 6754：会社Q&A1頁を取得・未採用で保存

**会社が説明する2027年3月期Q1のQ&A5問を確認した。** 保存済み公式IR snapshotのliteral hrefから、exact hostのrobots1GET（404 XML）と指定PDF1GET（200）のみ。redirect/retry/他PDF/JS/API/別経路は0。PDFは277,328bytes・1頁で、全文と画像を確認した。

- 通信計測の売上は社内想定どおり。受注はDC関連需要好調に加え顧客生産計画を見越す前倒しもあり、想定超過。
- 光トランシーバー計測の1.6TE向け受注もあるが、800GE向けの比率がまだ多い。数値比率はない。
- モバイル需要は当面低調・横ばい。Pre-6G前の需要回復は会社の期待/可能性で、実施実績や確定日ではない。
- 受注超過でも売上が計画どおりのため、通期業績予想は据置。予想数値自体はこのPDFから抽出していない。
- PQA北米は食肉加工向けX線検査機と、長年の市場開拓/顧客基盤拡大を好調要因と説明。

本文タイトルがFY2027/3・第1四半期を明示する一方、開催日・公表日は明記していない。source.published_atはnull。URLのfy2026/260731、HTTP Last-Modified、PDF作成日時を日付の代替にしない。本文完了は2026-10-15 **14:08:13.147763UTC**でsource.retrieved_atと一致するが、DB first_saved receiptではない。DB未import。

`capture.json`と個別snapshot・raw/text・p1画像・`quotes.json`へ短い逐語引用/頁/offset/SHAを保持。`source-bundle.json`は新会社watch/heldfalse metadataと公開Q&A source1件のみで、active/保有申告ではない。robots404は規則不存在時の挙動として記録し、明示的なサイト/AI許可を認定しない。UA固定、TLS/proxy/CA維持、全7exacthost hold非該当を事前確認した。

著者条件との比較は別担当作業で未実施。会社説明・会社見通し・著者独自予測は混ぜず、株価/倍率/将来EPS/IR質問/監視/モデルを作らない。financial_inputs_verified/model_adoptedはfalse。`review.json`へ実際の要点と限界、`validation.json`へ有限byte/schema/引用照合を保存し成果を固定した。実DB・code・旧files・index・外部送信変更は0。
