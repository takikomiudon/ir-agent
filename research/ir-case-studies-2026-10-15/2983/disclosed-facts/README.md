# 2983 Astris著者EPS3件の構造化

記録: 2026-10-15T16:55:53.610585+00:00。固定された外部レポートのp1だけを値/列の観点で確認し、1/27E **308.31円**・1/28E **339.81円**・1/29E **369.46円** を `external_estimate` / `JPY-per-share` として既存APIで構造化した。原FYラベルを保持し、正確な開始終了日・連結範囲・会計基準・basic/diluted・split/net/weighted/share分母は未認証のままnull。

報告主体はアストリス・アドバイザリー・ジャパン株式会社。個人著者はproducer確認5頁で未同定。会社から委託・支払を受けたレポートという帰属を保持し、独立経済関係や内容の独立検証を認定しない。review.authorは抽出担当で、予測作者とは別。会社転載EPSは原公表/著者換算が未解決のため抽出せず、p4の配当split注記をEPS全体に拡張しない。参考PER・peer指標も今回のfactや公正倍率に採用しない。

依頼時点でprimaryのaudit_consumer独立点検は進行中と伝達されていた。今回参照したのは固定producerのreview/quotesと画像p1で、その独立点検の完了/合格を消費・先取りしていない。p4/7/8/11の文脈はproducer記録を再利用し、5頁や全PDFの意味監査を再実施していない。

原PDFsource `case-public:cc1056ccbd3204206ab15aceab33c1b05c85f4dace3f235e12f454bd7169b328` と元entrysource `case-public:b09d26eefd2fcd9929a26acea3e455d41644892d76d1579f0194e54f17fba65b` の親来歴、原object/取得時刻/pubnullを保持した。派生 `disclosed-facts:a3cb5324cb1b7b03aaa770994f45af9f986432d2849604dda37d706e65431da7` は原PDFだけを直接parentに持ち、PDF原snapshotのoriginal_source_idsが入口へつながる。review `2026-10-15T16:55:53.610585+00:00` と実派生retrieval `2026-10-15T16:55:53.611886+00:00` は別。元first-save unknownを埋めない。

引用は同じ連続table spanに年度列/円/EPS値を含み、global/頁内offsetと画像SHAを保存。API全bundle replay/reproducer・独立Decimal単位算術が一致した。金額NIを株数で割る計算や著者EPSの再推計は行わない。入力・出力・引用・検証は [normalization-input.json](normalization-input.json)、[normalized-bundle.json](normalized-bundle.json)、[source-quotes.json](source-quotes.json)、[validation.json](validation.json)。

financial_inputs_verified:false、meaning_review_required:true、モデル未採用。GET・DB/Store・CLI・コード/テスト・旧source/facts/index/監視変更・IR草案/送信・価格/倍率/確率/閾値/売買採用は0。新5filesを固定し、今後の訂正は別版/補足とする。
