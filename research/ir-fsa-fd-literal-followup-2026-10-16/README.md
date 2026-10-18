# 金融庁FD公式入口：JIRA保存リンクからの有限確認

JIRA2018保存資料の脚注に明記されたHTTP URLを起点に、金融庁の公式発表HTMLを確認できた。HTMLは「平成30年2月6日」と表示し、FDガイドラインの別紙2、パブリックコメント回答の別紙1を直接リンクし、平成30年4月1日付の制定・適用を記す。これは2026年に取得した2018年発表の表示であり、2018年当時に取得保存した記録や現行法の全面確認ではない。

初期タスクの4GETはHTTP robots301→同host literal HTTPS robots404→JIRA literal HTTP本文301→同host literal HTTPS本文200。自動redirectはせず、各実要求を数えた。完全robots404は既存missing-robots処理を再利用し、エラーHTMLを規則/明示許可とは扱わない。rootが「HTTPエラー停止」は完全robots404を除くと明確化した来歴をguardへ保持した。旧閉鎖検索の再試行ではなく、新たに保存された明示URLによる初回取得である。

公式HTMLが読めた範囲は発表・導線・当時の適用日まで。対象者、公表済み説明の補足、未公表重要情報、公表方法は、別紙本文をまだ読んでいないため未確認。リンク77/78の実href/label/位置はsources.jsonに保存したが、この初期4GETではPDF本文GET0。

既存public_clarification/unclear/potential_nonpublicはプロジェクト内の利用/保留分類で、公式の法的区分と同一ではない。今回のHTMLからメール回答の合法性/公開性や自動利用可を判定せず、分類器・新gate・一般警告・個社質問の変更は0。後年改定・現在の適用関係も未確認。

公式HTMLは35,849bytes、raw SHA fa31214fb4098ce4a83921c0afd0c022269af13c58ee33db05845403797738a3。entity iteration完了とHTTP呼出し終了は別記し、HTTP終了01:49:35.330721UTC、歴史的first_saved_atはnull。HTTP Date/Last-Modifiedを2018発表時刻へ転用しない。rawはresponse entity bytes（符号化展開後の可能性）でwire captureではない。

固定UA ir-agent-public-research/0.1、通常proxy/CA/TLS、40秒/10MiB、共有2秒lock、各URL1回、4GETで有限終了。raw/text/capture/guard/route、4短引用、readscopeと旧入力SHAを保存した。DB・コード・共有docs・旧研究・質問・外部送信変更0。raw/textはこのdirectory基準、旧研究へのpathはrepository root基準。
