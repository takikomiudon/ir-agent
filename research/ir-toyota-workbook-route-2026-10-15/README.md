# Toyota例の元workbook：同PDF内では経路未特定

保存済みDamodaran *Ups and Downs: Valuing Cyclical and Commodity Companies*（2009年9月）の **commodity.pdf 1件・40頁だけ**をオフライン確認した。著者表示3,943円と既存表示入力計算3,944.09円の差を詰める元workbookの実リンクを、このPDF内では特定できなかった。候補URLは0、ここで終了する。

原PDFは[保存sources](../valuation-model-routing-2026-10-15/sources.json)の `/sources/2/raw_pdf_base64`、SHA `16c80720551749bcb08cfc06de0f94ce46a3162fe0e9a7cf9b3abf097c433d40`、670,511bytes。元取得は2026-10-15T01:26:14.401821UTC。新しい取得ではない。

`pdfinfo -f 1 -l 40 -url` のURL object列挙はheaderのみで0件。`pdftotext -layout` の再抽出は既存本文SHA `bc0de814b9bac9a6923a09919084071f4342e1fbfe5f9665c678d32ce096ea5b` と完全一致し、URL・xls系拡張子・spreadsheet/workbook/Excel等の本文検索も0件だった。補助的な原バイトの `/Annots /URI /GoToR /Launch /EmbeddedFiles /ObjStm` tokenも各0。[route.json](route.json)にcommand・tool版・stdout・検索範囲・source参照を保存した。URLが見つからなかったため、引用/annotation位置はnull。

先行の[Toyota readiness](../ir-toyota-author-valuation-readiness-2026-10-15/readiness.md)は表示入力9群と不整合を確認し、後の[equity bridge仕様](../../docs/explicit-equity-bridge-spec.md)も表示入力結果と著者値の差を保持している。[価値と価格の範囲点検](../ir-value-price-policy-scope-review-2026-10-15/README.md)は価格比較と操作可能な購入規則を区別した。今回それらの算術又は買い規則探索は繰り返していない。

このPDF内の経路未特定を、著者サイト全体や他版にworkbookがないという主張へ広げない。xls名・directoryを推測せず、精度差の理由も丸めと断定しない。現在のToyota価格・予測・買い条件へ転用しない。新GET/外部検索/DB/code/旧資料変更/金融採用は0。[validation.json](validation.json)に12項目の有限照合と旧5参照の不変を残した。
