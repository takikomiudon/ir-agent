# 1518ニュース一覧：限定独立確認

**保存済みニュース一覧の来歴・抽出・引用を99項目で独立照合し、99項目成功・不一致0。** 新GET、DBアクセス、コード・既存ファイル変更、IR・モデル採用は0。詳細と照合時のSHAは [independent-recheck.json](independent-recheck.json) に保存した。

- 保存captureは `/news/` への1GET、HTTP200、292,131bytes。raw SHA、UTF-8復号、既存`Page` parserによる本文・title・headings・202links・forms等の再抽出が一致した。保存本文は3,692文字。
- 完全source schemaを検証し、既存`stable_source_id`で `case-public:cd2408d3d8faf81e8a4459c8b2d6244775f3f89323f887fbd50eb3d9306b8995` を再現。会社IDは`jp:1518`、companies/theses空、非金融ニュース一覧、financial_inputs_verified=false。取得時刻は本文受信完了の **2026-10-15T10:46:27.083197UTC**、published_atはnullのまま。
- 原raw・抽出本文・captureとsource metadataのpath/SHA/bytecountを照合。3引用は元保存バイトを改行変換せず復号し、SHA・文字位置・source IDが一致した。
- 再利用robotsは同一host・同日07:53:16.132860UTCのHTTP200保存原バイト。`/news/`の許可と管理画面の禁止を既存parserで確認した。旧producerとFetcherのSHA・UA設定、新captureの宣言UAが一致する。過去リクエストのwire headerを独立保存した証明ではなく、現在のrobots状態も今回再取得していない。
- 旧8入力の保存SHAが一致し、確認開始時に存在した今回caseの9ファイルもすべて不変。新providerに対するgeneric verifierのunknownは維持し、今回の直接照合をprovider対応済みとは表現しない。

山洋の実anchorは `$.GETs[0].links[129]` の **2026.07.22「株式会社山洋の株式取得（子会社化）に関するお知らせ」** 1件で、以前保存した予定告知URLと一致した。raw/本文の山洋は各1箇所、保存レビューにある「取得完了」「完了」「8月21」等の限定検索は各0で再現した。コウナンは別対象で、山洋の完了根拠に転用していない。

この結果は**今回表示された一覧で完了文言・新しい完了告知本文を確認できなかった**という範囲に限る。取引未完了、全社で非公表、全ニュース履歴に存在しないという判定ではない。ページ送り・他カテゴリ・未取得記事本文の確認もない。7/22タイトルや旧8/21予定から、法的取得日、みなし取得日、連結開始／範囲、業績寄与や対価を補っていない。元財務資料とFISCO旧条件への変更・予測計算は行わず、完了や比較条件の判断はnullを保持する。
