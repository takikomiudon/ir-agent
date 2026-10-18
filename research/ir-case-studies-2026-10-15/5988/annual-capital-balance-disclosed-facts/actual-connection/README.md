# 5988 資本残高8fact：source-only接続準備

shadow検証成功。実DB書込み・新GET・金融採用・暦補完・nativecase登録は0。親rootが実台帳の唯一のwriterであり、本scriptにactual実行モードはない。実DBはmode=ro/query_onlyでbackup/照合にだけ接続した。main SHAは前後とも `b554610546a874eb3d57c0e3689a77a68aa67912551e2bbdea87715a7bb513cf`。

`input-pins.json` に受入済み8fact bundle、元sourceを含むinput、意味レビュー/親受入を含む全既存top-level成果物をpinした。原source objectはそのまま照合するだけで、`derived-only-bundle.json` に入れるのは `disclosed-facts:cba31cbae3e2b2d78353862ceb382b11f3d92efc2195eb944dc0871209e49bd5` の1sourceだけ。companies/thesesは空。`classification-request.json` はother/financial_content=true、正規化contentの逐語引用と「8公表歴史残高の構造化」という理由を保持する。分類はcanonical equity/debtやROIC入力の金融適合を認証しない。

`shadow_preflight.py` は旧14factのactual-connectionで成功したAPI順を参照し、別のSQLite backupに対して1回だけ実行した。ingest→5988 intake(new_only)→request-ID付きobserved claim→分類completeを実時計で行い、会社/source/job/packet/leaseを照合する。各stageのbegin/succeededをfsync付きjournalへ記録し、同dirに既存run receiptがあれば再送しない。失敗時はerrorを保存して停止する。全体は単一transactionではないので、失敗や不確定な応答の後に成功済mutatorを無条件再送しない。

コピー上ではsources/availability/classifications/jobs/attempts/request receiptsが各+1、attempt eventsが+2。全tableの旧行集合を比較し、旧86completed jobs・16current cases/31case versions・既読98件と金融関連recordsはすべて不変。借入金等2factのas_of/end nullとopening/closing boundary_role、元/派生sourceの全objectも変わっていない。コピーでのfirst-save `2026-10-16T00:40:09.805420+00:00` は実台帳first-saveではない。派生source retrieved_atの00:25:58もbundle生成時刻である。

親による実接続では、このshadow scriptを実DBへ向け直さない。以下のAPI順を親管理の新規stage journalと既存actual write手順の中で使う。事前に意味レビューと本接続proofを受け入れ、上記expected main SHA/全table状態、派生ID不在、pending/leased=0、検証済みbackup、新しいrequest IDを確認する。実行時点が進んで状態が変わっていた場合はこの基準で盲目的に進めない。

```python
# root専用の実行手順参照。この準備taskでは実行していない。
from datetime import datetime, timezone
from ir_agent.harness import Harness
from ir_agent.intake import Intake

# storeは親がbackup/事前guard後に管理する実台帳Store。
# source_only / classification_requestはこのdirのJSONを改変せず読む。
clock = lambda: datetime.now(timezone.utc)
h = Harness(store)
added = h.ingest(source_only, now=clock())
assert added == {"companies": 0, "sources_added": 1, "theses_added": 0}
at = clock()
queued = Intake(store).queue(at.isoformat(), company_id="jp:5988",
                            new_only=True, now=at)
# selectedは1job、会社jp:5988、source_count=1、deferred/skipped=0を照合。
job_id = queued["selected"][0]["job_id"]
# store.job(job_id).packetがkind=intake/stage=source_classification、
# companies/source snapshotとSHAが今回1sourceだけであることを照合。
worker = "codex-5988-annual-capital-balance-intake"
envelope = h.claim(worker, now=clock(), measurement_synthetic=False,
    caller_namespace=worker, request_id="5988-balance-actual-20261016-1")
# original_response/current_leaseのjob/company/worker/generation/packetSHA、
# replayed=false/valid_now=trueを照合してから同generationでcompleteする。
generation = envelope["original_response"]["generation"]
done = h.complete(job_id, worker, classification_request,
                  expected_attempt=generation, now=clock())
```

actualでもsource1/availability1/classification1/job1/attempt1/requestreceipt1/events2以外の差分がないこと、全旧行・既存case・全金融records・借入2factのnull暦を照合し、実時計の保存receiptと最終main SHAを親が別途記録する。native定性jobの登録/読解はこの接続とは別taskであり、ここではqueueしていない。API呼出し例は外部連絡や注文を行わない。

旧成果物は変更せず、新成果物は本dirと `/tmp/ir-5988-balance-shadow-*` のコピーDBだけ。変更前状態からの全行比較はshadow-completion、実呼出しはshadow-stage/log、input pinsとfreeze SHAはmanifest/validationを参照する。production code変更・新規tests/full suite実行はない。
