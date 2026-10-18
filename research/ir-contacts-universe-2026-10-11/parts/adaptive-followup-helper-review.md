# followup helper の限定オフラインレビュー

レビュー日時: 2026-10-11T09:48:10.612659+00:00。対象は root が304 unit testsの成功を保存した実装で、既存テストを再実行していない。外部GET、code/tests/企業records/原snapshotの変更は0。追加の再現は実データを読み取ったメモリoverlayとmock HTTPだけで行い、実ファイルへはこのメモのみ保存した。

対象実装SHA256:

- `scripts/collect_ir_followups.py`: `827972b33c0ab2699a9b66fce1f0df385cf3c1cb8ea377b0b2f851d0f5143c14`
- 呼出先 `scripts/research_ir_universe.py`: `73ae0e36506210aaa7db7dff5aee43ddecadc5a67406120cb20ce7210e60c45e`
- 親phaseの順番は実装の冒頭「Run after the initial collector has stopped.」と root の単一収集担当運用を前提に点検した。helperのファイルlockはstate単位（975〜979行）であり、異なるstateを持つmain/refresh/regular間の排他まで実装しているとは扱わない。親側で main終了→parser-refresh→regular followups を守る必要がある。

**重大1件: identity discoveryの共通503停止後、resumeで未完了URLを完了扱いにする。**

3901の固定2候補を使い、1本目 `https://www.marklines.com/en/corporate_profile/` をmock 200、2本目 `https://www.marklines.com/portal_top_ja.html` をmock共通Invalid argument 503とした。JPX事前確認200、robots404もmockであり、外部接続はない。

| 時点 | 実装上の結果 |
|---|---|
| 初回候補 | 正式監査sourceとrecord SHAを満たす2 URL、purpose=`issuer_identity_discovery` |
| 1本目成功・2本目共通503の後 | return2、status=`environment_stopped`、GET4、done1、todo1（portal_top_ja） |
| 自身のrecord追記後 | 元SHA `2e9a4b283b08c6ecf842abc97f989aed7cde9a7f822bb706933571b0ac869386` → mock時刻込みSHA `d5589945cef181f53112602d6bdced147a861bfe019061a1ba48cd10b9c77359`。manual_review退避、manual_review_required=true |
| CLIと同様のfresh build_plan | selected0。active review条件（381行）と元record SHA（409行）を満たさなくなる |
| そのplanで同じstateをresume | JPX preflight mock GETだけ実行。未完了portalを`already_saved_or_no_longer_eligible`としてdoneへ追加（874〜877行）、return0、status=`completed`、todo0 |

append_observationはidentity取得が失敗しても人手レビュー待ちにする（781〜789行）。それ自体は慎重な処理だが、候補構築が更新前のレビューとrecord SHAに依存するため、自身の追記で候補が消える。collectの`identity_record_shas`（870/933行）は同じプロセス内だけで、stateには保存されない。停止時のtodoは残っていても、再開時にはそれを消して成功完了に変えてしまう。単一identity URLの初回共通503や、3901の2本目未着手時に中断した場合にも同様の取りこぼしが生じ得る。

最小の修正方向は、当runが自身で書いたrecord SHAと元のsource/監査proofをstateに保存して検証し、固定selected内の未完了identity候補のみを再開すること。外部writerによる変更、別会社、未承認URL、元source/監査SHAの変更は今まで通り停止する。候補の証明が失われた場合は明示的なpending停止とし、黙ってdoneへ移さない。この finding と再現条件は root と helper writer に送付済み。コードは変更していない。

その他の重点確認では、追加の重大な不整合は実証しなかった。

- 2300/3440/3695は3コード限定、引用・現会社/旧会社名・実リンク・元review・proposalを結ぶidentity-only処理（298〜373行）。3853/3901は固定社名/seed/親snapshot/英語社名/3実リンク/監査SHAが必要（376〜436行）。確認した現データの候補は計6 URLだけ。identity proofはIR受付確認をfalseとし、これを新しい一般URL探査や窓口確認に拡張していない。
- regularはunconfirmed/provisionalだけを対象に、保存済み実リンクから候補を作る。別会社codeのsnapshotを除き、実IRの親/引用結合を使い、POST action・既取得・保存robots/401/403/429を除く（177〜194、268〜287、439〜594行）。未リンクhostへのredirectとprivate/session/action URLはGET前に拒否する（82〜108、711〜724行）。IRラベルだけで分類をconfirmedへ変更する処理やPOST呼出しはない。
- parser-refreshは保存監査の2752/2784だけ、正確な既200 URL・親link・redirect列・全source SHA・未claim record SHA・parser SHAを確認。固定state、0.25 RPS、最大12 GET、会社1回claimをGET前に永続化する（619〜699、799〜839、894〜907行）。claim済みは中断後も再送しないという明示設計であり、未取得成功をIRなしと解釈していない。
- BoundedFetcherは継承元のdispatchを一箇所で制限するため、preflight/robots/redirectも全GET予算に含まれる（711〜724、821〜847、859〜867行）。parser-refreshはdispatch前のreserved_get_countも固定stateに永続化する。rate/robots/proxy/TLSの既存制約を引き継ぐ。一般modeのSIGKILL等で保存前に失われるカウンタまで保証するものとは確認していない。
- helperは共通503を1件観測した時点で全体停止（726〜730行）、通常の未着手taskはdoneに加えない（934〜940行）。ただし前述のidentity resume取りこぼしがあるため、この点を全候補で満たすとは報告できない。
- 新captureは新snapshotへ保存し、旧recordをarchiveして追記する。旧分類、public_ir_emails、identity_status、元引用、条件は引き継ぎ、成功やidentity取得は人手レビュー待ちにする（765〜794、916〜934行）。3901の同一process内2本目は自身更新SHAを追跡し、別writer変更は停止するが、resumeへは未継承なのが今回のfinding。

これはGET前の限定レビューである。rootが保存した304-test成功は対象SHAの既存検証として参照したもので、新しいresume反例の成功を意味しない。修正後はidentityの503→fresh plan→resumeと他writer/source変更拒否を追加回帰で確認する必要がある。

---

## 修正後の限定再確認

再確認日時: 2026-10-11T09:56:26.798296+00:00。新helper SHA256: `a4d2e773672d31c654cc61bb0bedb3689e1b24d1155f743932957f0d858f0f96`。上記の旧SHAで確認した重大findingは、以下の範囲で解消した。旧指摘と再現条件は履歴として残す。

同じ実3901の保存record/sourceを読み、write_jsonはメモリへ保存、requests.getはmock、source/part/record/archiveの変更例もメモリoverlayだけで作った。外部GET0、disk上のcode/tests/records/source変更0、既存テスト再実行0。helper writerの専用30-test成功は受領済みだが、本再確認で実行したのは次の6ケースだけであり、全suiteを再実行したことにはしない。

3901のcorporate_profile=mock200→portal_top_ja=mock共通503で、停止状態は以前と同じreturn2／environment_stopped／done1／todo1／累計mock GET4。自身更新でfresh build_planがselected0となる条件も以前と同じ。新コードはstateにsource_record_sha256、expected_record_sha256、最初のoriginal_record_archiveを保存していた。元record SHAは`2e9a4b283b08c6ecf842abc97f989aed7cde9a7f822bb706933571b0ac869386`、今回のmock時刻を含む停止時own SHAは`8b87a448fa78ae863bb13ff9b854f003c2e55e7e10a59389bb6b991676849592`。元archive SHAと現record最終own SHAの一致を検算した。

| 再開ケース（変更は全てメモリのみ） | 終了code／status | done／todo | 累計mock GET | 再開時mock dispatch |
|---|---|---:|---:|---|
| 正常復帰 | 0／completed | 2／0 | 7 | JPX、robots、portal_top_jaの3回だけ |
| 元sourceを変更 | 2／identity_source_changed_stopped | 1／1 | 4 | 0 |
| 提案元partを変更 | 2／identity_source_changed_stopped | 1／1 | 4 | 0 |
| 外writerが現recordを変更 | 2／identity_source_changed_stopped | 1／1 | 4 | 0 |
| 最初のarchiveを変更 | 2／identity_source_changed_stopped | 1／1 | 4 | 0 |
| 旧state相当でlineageを欠損させる | 2／identity_resume_proof_missing_stopped | 1／1 | 4 | 0 |

正常復帰では未完了portal_top_jaだけを1回取得し、成功済みcorporate_profileの追加取得は0だった。旧分類unconfirmed、identity_status、原evidenceは一致し、人手レビュー待ちは維持した。検証できない5ケースはpreflightより前で止まり、元doneを増やさずpendingを保持し、企業recordも再開時に書き換えなかった。

旧実装との差分を重点部分で確認した。

- 旧コードのプロセス内identity_record_shasを、stateのidentity_record_lineageへ置換した（新875〜879、1015〜1029行）。元SHA・最新own SHA・最初の不変archiveを永続追跡する。最初のarchiveが元SHAと合うこと、自身append直後のrecordが返却own SHAと合うことを要求する。
- verified_identity_resume_task（新740〜791行）で、現recordとown SHA、元archiveの会社別attempts配下・SHA、source/partの許可パス・SHAを検証する。その後、元reviewed recordから元の有限company_candidatesだけを再構築し、proof_record_sha256のoverrideは検証済み元SHAに限って用いる。候補は保存task全体と完全一致しなければ復帰しない。IR候補や一般URLを新たに探索する処理ではない。
- pending identityの復帰検証をpreflight前へ移した（新920〜939行）。証明が失われたidentity taskは旧874〜877行の一般skip/done処理へ流さず、return2とpending保持にした（新955〜958行）。GET直前にもcurrent/source/part SHAを再確認する（新969〜977行）。

この再確認は旧findingの停止・再開とproof改変検知だけを対象にした。parser-refreshその他のscopeは再調査しておらず、新たな一般探査・ネット取得・実装修正も行っていない。
