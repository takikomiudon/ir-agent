# 1975 保存済み短信の2ページ追補（2026-10-16）

株式会社朝日工業社の2027年3月期第1四半期短信について、まず物理3ページの目次を所在確認だけに使用し、指定の物理 **9・10ページ（印字7・8）**と実見出しが一致することを確認した。この2ページの本文再抽出と画像の意味確認を完了した。物理10には連結受注高と個別受注高の両方があるため、別表として保持する。

原PDFは12ページ。初回の意味・画像読解 [1, 2, 4, 7] と当時の未読ページ一覧は変更せず、今回の追補と分けて保存した。全PDF読解完了ではなく、2ページで停止して親の画像・意味レビューを待つ file-only 成果物である。

- 既存source: `case-public:1be0616e6cd3190c24777d4fc73d7e98da23fef874d4049aa38b667dbefdbdea`
- 公表日: 2026-08-04（日のみ、時刻不明）。原取得: 2026-10-16T04:18:59.234370+00:00。
- raw PDF SHA-256: `197dbf719ededc450d856e3eb9dda745a2fe92c1ac0325847aa150cfb4487a85`
- native UTF-8 SHA-256: `5b590ae0edd7df00cc1b165437bc4e81d23fa117addbbbd948ff827668b95c83`

## 確認できた公開回答

- セグメント注記は前年2025年4〜6月と当年2026年4〜6月、百万円単位。利益・損失合計は連結営業利益と一致すると明示する。前年は設備工事1,912・機器製造販売△25・合計1,887、当年は2,242・△37・合計2,205百万円。経常・税引前・親会社利益やCFと混ぜない。内部売上・調整額の「－」を数値0へ補完しない。
- 当Q1の連結CF計算書は未作成。減価償却費は前年170・当年172百万円で、のれんを除く無形固定資産償却を含む。CF未作成はCFOゼロではなく、D&Aや現金残高増減もCFO・維持投資・FCFFではない。
- 受注補足は同じ前年/当年の四半期累計flow。連結受注合計は31,261→36,232百万円、個別受注合計は31,107→35,156百万円。構成比・公表増減額・率は表記のまま保存し、合計や増減を再計算しない。連結と個別の差を子会社寄与と断定しない。
- 株主資本の著しい変動・継続企業の前提の注記はそれぞれ該当事項なし。当該2項目の範囲だけで扱う。

## この2ページで残ること

受注残高stock・期末日・契約金額変更や取消の集計定義・調整内訳は確認できない。受注高flowから残高や受注残identityを作らず、契約変更ゼロともしない。資料全体に記載が無いという主張にはしない。

この2ページには税計算方法、数値税率、現金納税額、正常税率は示されない。初回の四半期特有会計処理「無」は履歴のまま保持し、actual tax・tax cash・正常率を代用しない。将来CF・維持投資・利益の持続性・案件構成の寄与も未確定である。

## ファイルと検証

[pins.json](pins.json) が初回aware日時、既存source、raw/native/fullcontent、元初期folder全32ファイルと指示文書のbytes/SHAを固定する。[toc-location-check.json](toc-location-check.json) は目次の無補正Unicode引用・offsetと見出しの一致を保存する。[extraction.json](extraction.json) は2ページだけの再抽出・renderの引数とoriginを記録し、[image-review.json](image-review.json) がその後の実読完了を記録する。抽出時点の `manual_image_read:false` は履歴として残した。

[source-quotes.json](source-quotes.json) には2全ページと6論点の完全一致引用を保存し、native全体/各ページのUnicode code pointとUTF-8 byte offset、引用SHA、page/image pinを付す。[review.json](review.json) が公開回答と残余・比較境界、[validation.json](validation.json) が原本不変・完全一致・scopeの局所検証、[manifest.json](manifest.json) が全新成果物（自身除く）のbytes/SHAを記録する。generic外部byte verifierや全suiteの実行を意味しない。

新GET・DB・source登録・shared code・case/job・金融採用・予測・normalizer・IR草案・旧ファイル変更は0。追加ページへ進まない。
