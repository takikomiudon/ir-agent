# 日本株の決算発表後ドリフト：有限な原典確認

日本株PEADの原著候補1件を特定したが、**売買ルールの採用に必要な本文は未取得**。Naohiko Matsumura, “Post-earnings announcement drift: An analysis of market expectations using the Foster model”, *Journal of Behavioral Economics and Finance* 3 (2010), pp.1–17, DOI [10.11167/jbef.3.1](https://doi.org/10.11167/jbef.3.1)。書誌上の公表年2010とJ-STAGE掲載日2010-09-10を区別し、精密公表日時は不明。作者の日本語表記は今回未確認。

保存資料の限定検索では、同戦略を採用できる既存原典は特定できなかった。公式起点→HTMLに明記されたGET検索フォーム（入力語「決算発表後」）→実表示の論文記事へ4 GETで到達。書誌と掲載誌のabstractを直接確認した。検索結果を論文本文の代わりにはしていない。

robots200の `Disallow: /*_pdf` が記事のPDF実URLに適用され、固定UAでも不許可だったためPDFは未要求。記事HTMLはoverview/abstractで、静的な本文HTMLリンクを見つけていない。最大6 GETの残り2回は使わず終了。別host・転載・URL推測・JS・API・認証・購入・既存閉鎖経路を利用していない。

要旨が述べるのは日本市場のPEADとunderreactionに関する著者の解釈まで。signal算式、標本期、entry時点、比較benchmark、測定保有窓、exit推奨、費用・流動性等は未確認のまま。CAPM/3-factorへの言及を執行benchmarkにせず、測定窓を売却規則へ変換しない。数カ月〜1年への適合、因果、現在の収益性、メールIRの超過収益を認定していない。新しい投資閾値・数値方針・金融採用は0。

[capture.json](capture.json) は4要求のraw/HTTP完了/保存時刻とheader、[guard.json](guard.json) は実URLとrobots、[quotes.json](quotes.json) は短引用の原文・文字/UTF8位置、[review.json](review.json) は未確認欄と読取範囲を保持する。全textは原HTMLの可視文字抽出で、論文PDF全文ではない。DB/Store・既存source・コード・共有文書・質問・送信の変更はない。
