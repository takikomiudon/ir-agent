# 構造化金融資料25sourceの保存・分類preflight（v2）

索引v23の`artifact_resolution`に従って親entryと各factのartifact/source overrideを解決・重複排除し、**新規候補25source・実payload91fact・16社**を固定した。対象外8331/9702の2sourceと、既存5988財政状態3factの1sourceは除いた。実台帳への適用・金融入力採用はまだ行っていない。

## 最終成果物

- [candidate-manifest-v2.json](candidate-manifest-v2.json)：親26entry/101factから28組のartifact/source参照を解決。各会社・原source snapshot完全一致、派生有無、除外理由、再現証拠のpinを保存。
- [derived-only-import-bundle-v2.json](derived-only-import-bundle-v2.json)：新規派生25sourceだけ。companies/thesesは空、原典sourceを再投入しない。
- [classification-requests-v2.json](classification-requests-v2.json)：25sourceの分類request。全件`kind:other / financial_content:true / expected_version:0`。
- [classification-quote-proof-v2.json](classification-quote-proof-v2.json)：保存source.contentのJSONをoffset付きで読み、同じfact内のconcept/unit/valueを含む最短の連続member範囲を逐語取得。minified形式を仮定せず、文字範囲・選んだfact・値・quote SHAを保存。引用長は1,159〜3,156文字で、3field間の他memberもそのまま保持し、断片を連結していない。
- [temp-intake-preflight-v2.json](temp-intake-preflight-v2.json)、[stage-intake-v2.jsonl](stage-intake-v2.jsonl)、[temporary-job-completions-v2.json](temporary-job-completions-v2.json)：新しい一時DBでの最終成功記録。

元factのreported_fact/issuer_guidance/external_estimate等の区分・著者・期・単位・符号を保持し、分類rationaleへ実concept/kindを記録した。資料分類otherは構造化派生資料を指し、元の短信・説明資料・外部レポートそのものの種類へすり替えない。source/factsの`financial_inputs_verified:false / meaning_review_required:true`、分類の`inputs_verified:false`を維持する。

既存23候補分の再現記録に加え、別2束（5480売上1fact・135A CF4fact）も各root-recheckのbundle SHAと`reproduced`を現在のbundle bytes/完全一致原snapshotへ結び直して再利用した。**新しいnormalization・原典再解析・reproduce実行は0**。引用fragment生成は分類対象の保存済みJSONを読む処理であり、財務意味を再認定するものではない。

## 一時DBで確認した結果

実DBは`mode=ro`・`query_only`・一貫read transactionで開き、SQLite backup APIで一時コピーを作成。Store/Harnessはこのコピーにだけ使用した。開始時に全kindのpending/leased=0、未分類の公開source=0を確認した。

1. sourcesだけのingestで25追加、125→150。再ingestは追加0、全table論理行が初回後と完全同値。
2. 未分類公開sourceは候補25件だけ。会社別`Intake.queue(new_only=True)`で16jobを作り、各packetのsource集合が会社別候補集合と厳密一致。
3. namespace/request ID付き`Harness.claim(measurement_synthetic=False)`を使い、返却job set・source IDs・有効lease・世代を確認。返った世代をexpected_attemptへ渡し、各APIの通常transactionでcomplete。外側transactionは置かない。
4. 新16jobは全completed、25sourceが各1版で分類済み。公開sourceの未分類0、pending/leased0。分類149、jobs73、attempt70/events140/request receipt70、source150は**一時DBの件数**。
5. 既存27tableの全旧行を保持。変更はsources/record_availability/source_classificationsへ各25新行、jobs/attempt/requestへ各16新行、attempt eventsへ32新行の追加だけ。他20tableは全行完全一致。会社・原source・旧派生・native case・policy・仮説等は不変。

measurement_synthetic=Falseは今回指定されたAPI引数であり、この一時実験を実台帳の処理測定や実IR成績へ加算しない。新receipt/分類/lease時刻は一時DB内の実行時計で、実台帳の初回保存証跡ではない。一時コピーは終了後削除した。

## v1訂正と最初の一時実行の履歴

v1のmanifest/bundle/temp-preflight/README完全bytesを[before-override-resolution](before-override-resolution/)へ保存し、[archive receipt](v1-archive-receipt.json)でpinした。v1は親entryだけを列挙して23sourceを候補にしていた。親entry内の索引fact数91をpayload実数と誤記したが、実payloadは86factだった。5480売上・135A CFはper-fact overrideの別2sourceであり、rootのscope拡張後にv2へ追加した。索引101factや元producer artifactは変更していない。旧v1 JSONは履歴として保持し、実適用候補はv2だけとする。

v2の初回一時実行は25件保存・16job完了まで成功したが、summary生成前の一回用runnerでPath式を誤記したため停止した。[エラー](attempt1-postcompletion-error.json)とattempt1のstage/completionsを保持する。API・実DB・本体コードの失敗ではない。一時DBはcontext終了時に削除され、状態を再読できなかったため、式だけを直して新backupで**1回だけ**再実行し、上の最終成功記録を得た。

## 実台帳との境界

実DB本体SHAは前後とも`b0086b397a8a949e0616f5923cb183358d87b30f3b8a05bfe6fc0373af443e88`、WALは前後とも0bytesのSHAで不変。実台帳はsource125・分類124・job57のまま。rootは適用前にv2のbundle/quote/会社・原source・派生有無を独立照合し、実適用時のtrusted時刻を使う。元retrieved_atや一時receiptへ遡らせない。

新GET・実台帳書込み・native case変更・金融/政策採用・src/tests/元index/producer artifact変更は0。実台帳への分類job作成・claim/completeも本preflightでは実行していない。
