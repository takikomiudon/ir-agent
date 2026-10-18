# 6323 保存済み会社IR経路の有限棚卸し

新GETなしで6323の既存試行を先にpath検索し、連絡先調査の旧503/circuit-breakerと、その後の成功snapshot3件を確認しました。6323の既存有限case-route試行は今回の検索範囲では見つかりませんでした。新たに調べた成功bodyはhome/FAQ/contactの3件だけです。

公式IR入口、IRライブラリ、決算説明資料/短信のliteral hrefがありました。保存した該当anchorは21件、exact resolved URLは5種です。

- 説明資料: https://www.rorze.com/wp_rorze/wp-content/uploads/2026/10/meeting_2027_Q2.pdf
- 短信: https://www.rorze.com/wp_rorze/wp-content/uploads/2026/10/20271008_2027_Q2.pdf

両anchorのlabelは2027年2月期第2四半期、保存home textの掲載日表示は2026.10.08です。短信ファイル名の20271008を修正せず、label/掲載日/URLを別々に保持しました。PDFを取得・解釈しておらず、資料表紙の日付や最新性は確認していません。

元HTMLは保存参照も該当SHA名fileも見つからず、原HTML href offsetはnullです。代わりに元snapshotのpath/SHA、links配列のJSONpathと保存JSONのhref文字列tokenの位置を記録しました。宣言されたresponse entity SHAを実原文で再検証したとは扱いません。/ir/libraryと末尾slash付き/ir/library/も統一していません。

対象host www.rorze.comは中央7holdに該当しませんが、取得許可や現在のrobots確認とは別です。禁止hostへの別経路探索はしていません。旧negativeを再取得せず保持しました。

CSV上の6323掲載は確認済みです（CSV全3686行、confirmed 1558行）。実DB所属/状態は未確認で、親報告から補っていません。過去contact confirmedも現在の個人適格性には変換していません。

この新dirのroutes/review/validation/READMEだけを保存して有限停止しました。DB/GET/再取得/URL推測/API・code/旧資料/監視/索引編集/著者再研究/新PDF読取/外部送信は0です。
