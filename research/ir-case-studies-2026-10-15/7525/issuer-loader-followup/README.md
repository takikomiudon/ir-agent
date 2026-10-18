# 7525：静的ローダー経路を確認、データhostのrobotsで停止

保存済み決算説明会資料ページの実src `/xj/XjStorageLoaderlibrary03.js` を、同日保存の公式robots・同UA・正確なpath許可を照合して取得した。**新2GET（JS1＋接続先robots1）で終了し、データ／PDFは0GET**。JS実行・再試行・リダイレクト追従・別経路・ネットワーク診断は0。

JSはHTTP200・16,234bytes、受信完了2026-10-15T11:08:10.871177UTC、raw SHA `379bf48b66201accd1cc790600a226643c8e812bf882e5a97e239c2afb4af87b`。コードに次が明記されていた。

- domain `//www.xj-storage.jp`、完全company文字列`75250`、doctype`13,98,113`。
- `/public-list/GetList2.aspx?company=`にcompany、`len=10000`、doctype、`output=json&callback=?`を連結する。末尾constructorは引数なしで、当該既定値を使う。
- PDF/HTML実リンクは未取得レスポンスの`item.files[].url`から得る。コード中に最新資料の実PDFhrefはない。冒頭コメント「決算短信」と文書種別コードから、最新説明資料の期や内容を補わない。

`callback=?`には実行時識別子がないため、初回JS確認時点では完成HTTP要求と見なさなかった。その後、親の明示承認により[既存135A手順](../../135A/library-followup/request-derivation.json)と同じ`ir_agent_review`を呼出側のtransport値として使う方針を記録した。これは原典の金融値／会社IDを推測するものではなく、jQueryが生成する実行時名の再現でもない。他のqueryを削除・変更せず、もし許可された応答を得た場合だけ固定wrapperを厳密に剥がして既存`parse_json`で読む方式だった。今回は下記禁止によりデータ取得もwrapper解析も実行していない。

接続先は中央索引にあった`contents.xj-storage.jp`とは別のexact host **`www.xj-storage.jp`**。新しい正確なrobots URLを1回確認すると、HTTP200・26bytesで次を返した。

```text
User-Agent: *
Disallow: /
```

原raw SHAは`7ea4052aea20413007bfc2686ba0ad7276882075c2606c86a9e6b08742b3a4ca`、受信完了2026-10-15T11:09:53.720443UTC。UA`Codex-IR-Research/0.1`に対し対象データpathも禁止されるため、**データ0GETで即停止**した。予算残1を他path/hostへ使わない。同一内容のrobotsを持つ他hostと取得originを混同せず、この保存時点の正確hostの制約として保持する。投資除外や恒久禁止にはしない。

[preflight.json](preflight.json)に元source種別・原HTMLのsrc/文字位置・同日robots再利用・中央保留照合、[capture.json](capture.json)に2回の受信完了・headers・bytes、[quotes.json](quotes.json)に7引用とSHA/offset、[routes.json](routes.json)に静的連結式・callback採用理由・新host停止を保存した。[source-bundle.json](source-bundle.json)は**許可された会社hostの静的JSのみ**の任意研究用bundle（会社/thesis空・非金融）で、robotsはtransport根拠として別保存。元一覧sourceを親として全来歴を残したが、DBへ登録していない。

[validation.json](validation.json)は33チェック成功・不一致0、旧31ファイル不変。新providerのgeneric verifierはunknownを維持する。環境policy観測もunknownであり、適用済みとはせず、継承proxy/CAとTLS検証を保持した実応答だけを記録した。

動的データ経路は特定できたが、最新資料・対象期・現在のオリジナル品比率・定義・QUICK29.3%や会社40/55%目標との比較はnullのまま。資料や比率が会社で非公表という意味ではない。IR草案・モデル・金融値・DB・code・旧成果物への変更は0。
