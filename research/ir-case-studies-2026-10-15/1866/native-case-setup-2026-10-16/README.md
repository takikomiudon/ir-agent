# 1866：数値仮説前の継続監視case登録候補

既存Anthropic earnings-previewの指標・会社予想・戦略変更点検とthesis-trackerの四半期レビューを、公開資料の同一条件比較へ適応した。[case-context.json](case-context.json)が元条件、[review-manifest.json](review-manifest.json)が限定既読3sourceのID/原source全object・snapshot SHA/取得時刻と実初保存の照合、[register-request.json](register-request.json)がroot用登録入力である。売買方針・金融thesis・質問は作成していない。

1866はQ1実績と通期会社予想の期間・利益区分を分け、分割調整済みEPS/株式数を二重調整せず比較する。建設/ホテルの公表済み増益、会社予想据置、分割基準は再質問しない。詳細要因/CF等の保存未読箇所を未回答IRと認定しない。

reviewed_atは **2026-10-16T01:13:09.555769+00:00**、6sourceの実初保存01:07:53.577025 UTCより後の今回handoff再照合時刻である。過去初読/全冊読了/新しいWeb更新確認を意味しない。全文テキスト保存と限定頁の意味確認を分ける。

[management-basis.json](management-basis.json)の **2027-01-16 Asia/Tokyo** はTokyo2026-10-16から3calendar months後の内部研究管理日。著者の「少なくとも四半期」をprojectで具体化した日であり、会社予定・売却期限ではない。新保存資料はそれ以前に比較できる。

[validation.json](validation.json)に既存APIでのコピー検証を保存した。2case/2版を登録し既読+6、queue0件（両case no_new_trigger）。旧全rows保持、変更はqualitative_case_versions+2だけ、金融records不変。コピーは一時DBで終了後削除し、実case登録0。実DBはmode=ro/query_onlyのみ、main SHAは前後 `2f564bee9fce54684e7f4a6214d433d6248f2b86182e273838d29ddfaddacb6a` で一致、Store初期化/GET/元成果・共有編集/金融入力/送信0。rootが後で実登録する入力であり、コピーの保存時刻を実case保存時刻へ転用しない。
