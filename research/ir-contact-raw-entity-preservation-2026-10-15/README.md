# 新規IR調査の完全response entityを保存する

`Fetcher.raw_get`が完全受信後に計算済みだった元bytes/SHAを、明示した保存先へ保持する最小変更を実装した。以前の9702等のcaptureは書き換えず、再取得していない。今後の新規取得で、可視text抽出により失われるscript・iframe周辺・コメント等を含む元HTMLをオフラインで再解析できるようにする。

## 契約と変更範囲

`scripts/research_ir_universe.py`の`Fetcher`末尾optionalに`raw_directory=None`を追加した。未指定の旧APIはファイル保存・raw関連metadataの追加を行わず、従来挙動を保つ。通常CLIは`output/raw`へ接続した。`scripts/collect_ir_followups.py`は`BoundedFetcher`末尾optionalを伝播し、`collect`が自分で生成する時だけ`output/raw`を渡す。callerから渡されたfetcherの保存先は変更しない。

原bytesは`requests.iter_content`を最後まで読み終えた**response entity**である。requestsがContent-Encodingを復号した場合もあり、wire上の圧縮転送bytes・gzipファイルの原bytesを認証するものではない。既存3MiB制限を維持し、完全受信後・文字encoding解釈やHTML抽出より前に保存する。encoding不正で後のdecodeに失敗しても、受領済みentityは保存できる。partial受信や上限超過は完成品として保存しない。

ファイル名はSHA-256で、同じdirectory内の一意な一時ファイルへwrite/flush/fsyncしてからhard linkで完成名をatomicに作成する。完成名へpartial fileを露出せず、既存同名fileは置換しない。同bytesなら既存fileを再利用し、同名で異bytes・symlink等の場合は保存失敗とする。途中失敗は一時ファイルを除去し、除去失敗があればcleanup診断を別に残す。非SHAの一時ファイルを完成した原典として扱わない。

| 新metadata | 意味 |
|---|---|
| `raw_storage_status` | `saved` / `reused` / `failed` / `not_saved_incomplete_entity`。最後は未試行・中断等を含み、完全entity保存の成功ではない。 |
| `raw_file`, `raw_sha256` | 保存/同bytes再利用の成功時だけ。保存先へ渡したpathを使用し、相対pathはcollectorの作業directoryが基準。`raw_file_path_basis`にも明記する。 |
| `raw_body_completed_at` | 完全entityのiteration終了をローカル時計で観測した時刻。wire完了・公表時刻・実DB初回保存日時ではない。 |
| `raw_entity_semantics` | 上記entity/復号/wireの区別を記録する。 |
| `raw_storage_error` | 保存失敗時の例外型。例外message・秘密値を出力しない。 |

保存失敗は`error`や`failure_signature`へ混ぜない。HTTP/抽出結果を保持し、保存できなかったことを上記metadataで明示する。network障害として再試行や403解消を開始しない。保存成功を必須とする将来consumerはこのstatusを点検する必要がある。既存の`retrieved_at`・開始/応答/完了時刻、rate/backoff・robots・UA・redirect・circuit breaker・窓口分類の条件は変更していない。

## 検証と凍結

新規`tests/test_ir_raw_entity_preservation.py`はsynthetic responseだけを使う。元HTML/script保持、cp932、decode失敗前の保存、旧API未指定、directory保存失敗、書込み後fsync失敗、破損済target不変、partial受信、3MiB境界/超過、空entity、同bytes再利用、並行atomic公開、空の架空CLI/collect入力でのwiringとcaller設定保持を確認した。実サイト取得・現行の収集業務は起動していない。

- 既存contact focused：79件成功、[実出力](focused-contact-tests.log)。
- 既存followup focused：76件成功、[実出力](focused-followup-tests.log)。
- 新規raw preservation focused：11件成功、[実出力](focused-raw-tests.log)。

変更前script完全bytesは`before/`、[before-files.json](before-files.json)へ保存した。既存testsは変更せず新testだけ追加した。変更差分と現在SHAは[implementation.patch](implementation.patch)と[implementation-receipt.json](implementation-receipt.json)に固定する。full suiteと独立レビューはroot担当で、ここでは完了を主張しない。新GET・実DB操作・旧capture変更は0、金融指標・parser・汎用artifact基盤は追加していない。

root受入：独立21項目・対応必須指摘0、[全1,512件・37.048秒成功](parent-acceptance.json)。実DBのSHAは前後一致し、新規収集GET・実DB書込みは0。
