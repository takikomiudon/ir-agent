# 1518：山洋の完了は今回のニュース一覧でも未確認

保存公式ページの `$.links[46]`「ニュースリリース」から、公式 `/news/` を **新1GET（上限3、HTTP200）** で確認しました。同日の保存robotsを原rawSHA・同UA設定・実path許可で再照合し、robots再GETは0です。本文完了は2026-10-15T10:46:27.083197UTC、292,131bytes。共有2秒lock、通常proxy/TLS、retry/自動redirect/JS/APIは0です。

今回表示された一覧にある山洋リンクは、以前発見した **2026.07.22「株式会社山洋の株式取得（子会社化）に関するお知らせ」** 1件だけでした。保存raw内の山洋も1箇所で、取得完了・完了・8月21日実施を示す文言は見つかりません。新たな完了告知の実hrefがないため、その本文への追加GETはせず終了しました。7/22告知のタイトルや旧8/21予定を、実行済みの根拠へ変換していません。コウナンの取得告知は別対象です。

**取得完了・実際の完了日・対価・連結開始と範囲はnullのまま**です。これは取引未完了や会社全体で非公表という判定ではありません。一覧先頭の表示日は8/7ですが、10/15時点の全開示の最新性を保証するものでもありません。未使用2GETで別カテゴリ・ページ・記事名・API・別hostを探し広げていません。

`source-bundle.json`はcanonical `jp:1518`、companies/theses空、取得したニュース一覧1sourceだけです。金融本文ではなく、financial_inputs_verified=false。retrieved_atは新HTTP本文完了、公表日時はnull、日付付きニュースの表示は別に保持しました。metadataパスは `research/ir-case-studies-2026-10-15` 基準、新providerのgeneric byte verifier対応はunknownです。raw/text再抽出、3引用offset、元リンクと新actualhref、旧8入力SHA不変を確認済み。DB/code/旧file・予測/EPS bridge・モデル・IR草案/送信変更は0です。
