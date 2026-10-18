VRAIN Solutionの正規IRフォーム `https://vrain.co.jp/ir/inquiry/` を、2026-10-16T14:01:10.750573+00:00の完全受信まで静的GETで確認した。旧保存IRトップのliteral `/links/74`、AGENTS/技能/holds-v8、同hostの旧robotsを照合し、今回fresh robots200→フォーム200の2GETで終了。入力・submit・POST・JS・旧performance503・他リンクの取得は0。

会社名は表示必須で、現HTMLのplaceholderにも「個人の方は『個人』と入力してください」という案内がある。氏名・ふりがな・会社名・メール・電話・本文は表示必須、郵便番号・住所は表示任意。重要な区別として、電話番号欄には他の5必須欄にある `aria-required=true` やrequiredクラスがない。HTMLの `required` 属性は全欄になく、formには `novalidate` がある。これを理由に電話を任意とせず、画面の必須表示と属性・実際の検証動作を分ける。ブラウザ/JS/サーバの受付検証は行っていない。

メールはtype=emailだが、`example@vrain.com` は入力例でありIR宛先ではない。問い合わせ内容によって電話や手紙で返信する場合があると記載される。ヘッダ/フッタの一般電話や受付時間も、IRの電話対応・メール返信・期限の保証へ移さない。

プライバシーポリシーへの同意表示とcheckboxがあり、問い合わせに送った個人情報を問い合わせ対応以外に使用しない旨が当頁にある。リンク先privacy本文や未同意時の拒否動作は未確認。回答の転載/二次利用・全件回答保証/回答期限・沈黙期間については、当頁に明示された条件を確認できなかった。許諾や条件不存在とはせず、別ポリシーや個別回答の公開性を別に確認する範囲として残す。

[review.json](review.json) に条件と未確認、[form-elements.json](form-elements.json) にフォーム/非hidden10controlの属性・必須表示・元HTML位置、[quotes.json](quotes.json) に8非空逐語引用とrawHTML/visibletext別のUnicode/UTF8 offsetを固定した。完全rawはフォーム74,761bytes、robots167bytesで、転送圧縮のwire captureではない。新しいsourceや質問は登録せず、旧draft/preflight・DB/Store・元資料は不変。

これは当日の静的な受付案内の確認である。送信準備完了、送信権限、サーバ受付/メール到達/実返信、返信の公開性を認定しない。残りGET枠は使わずfreezeしroot独立レビュー待ちとする。
