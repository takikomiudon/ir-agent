# 大成温調1904：native定性case登録候補

Q1実績・当時の会社予想と、その後の株式/連結範囲の告知を比較する登録入力を準備した。case `1904-earnings-and-event-basis-monitor`／issue `1904-quarter-guidance-share-and-perimeter-basis`。Anthropic earnings-previewのmetrics/guidance/strategy変更、thesis-trackerの更新・四半期点検、DDの既知情報先行/資料差分確認を研究段階へ適応した。金融thesis・数値反証・売買条件・質問を作っていない。

[case-context.json](case-context.json)の3論点は、①Q1累計/通期、営業/親会社利益、要約百万円/詳細PL千円、②当時の信託控除を含む株式基準と後日の分割/配当修正告知、③Q1内の範囲変更なしと後日の子会社化/戦略告知。原典に既答のQ1数値、予想据置、中間予想省略理由、当時の株数定義等を再質問しない。後日通知本文は未取得のため、分割比率・効力日・修正DPS・取得後の範囲/寄与は未確認のまま。告知見出しの日付を実施/効力日にしない。

[review-manifest.json](review-manifest.json)は原2sourceの全objectと実DB保存snapshot一致、native/compact別SHA、実firstsave **2026-10-16T01:59:22.254207 UTC**、既存9引用/offsetを保持する。[登録入力](register-request.json)のreviewed_at **2026-10-16T02:03:13.638722+00:00** はそれ以後の今回handoff再照合時刻。原PDF全文12頁の保存と、意味/画像確認1・2・4・7頁を区別し、過去初読や全冊読了を主張しない。原sourceの取得/公表/初保存時計は変更しない。

[management-basis.json](management-basis.json)の **2027-01-16 Asia/Tokyo** はTokyo2026-10-16から3calendar months後の内部研究管理日であり、会社イベント・分割/取得効力日・売却/反証期限ではない。

[validation.json](validation.json)は既存register/queue APIの使い捨てコピー検証。追加case1・版1・既読2、queue0（no_new_trigger）、旧全行保持、他26table不変・金融記録不変。コピーは削除済み。実DBはmode=ro/query_onlyだけで、main SHA前後 `882e1a467e1c590c0d4187188915fbc6b663cf732abf57032fe8e23e07767c6e` 一致。**実case登録は未実行**。rootが後で登録するためのfile-only入力であり、コピー時刻を実台帳保存時刻に転用しない。GET/元成果・共有編集/金融入力/送信は0。
