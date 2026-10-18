# SBI S株：保存robotsのSitemapからの有限取得

保存済みwww robotsに明記された `https://go.sbisec.co.jp/www_sitemap.xml` を1GET。完全200・420282Bのurlsetで、子Sitemapは追っていません。1940 loc中の実掲載index456、国内fractionサービス候補を選択し、保存www robotsとcurrent helperでexact queryを照合して1GETしました。計2/2GETで終了です。

掲載先は静的本文を完全200・276766Bで保存し、見出し「S株 (単元未満株)」を確認するlocatorを保持しました。URLの推測、他fraction頁、関連リンク、JS/API、自動redirect、retry、認証・注文・POSTは0です。Sitemap XMLの`&amp;`と実URLの`&`を分け、CRLF保存bytesと文字列のescapeを混同していません。

GET2はgzipをrequestsが復号したentityで、圧縮wireではありません。HTTP charset `Windows-31J` を初期Pythonが未知codecとした記録を原captureに保持し、ローカルcp932 aliasでstrict復号して別text/抽出JSONを保存しました。再GET・置換文字による補完なし。raw/decoded-textのSHA、HTTP開始・完了時計、robots元SHA/観測時計、元XML URLのUnicode/UTF8位置は各JSONにあります。

取得prepare-onlyで、1株・対象・手数料・spread・執行時刻・積立方式の意味判断と利用者への適合は親担当へ引き渡します。旧phase/既存原典・DB・Store・共有code/docs・金融採用・送信は変更0。before10pinsのうち旧証拠/holds/helper等9件不変、技能のみ並行更新を検知しbefore/after SHAを保持。収集手順と研究IR一覧の追補を再読し親担当へ通知しました。全pins不変とは扱わず、取得をここでfreezeします。
