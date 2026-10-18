# 2315：6資料の初期分類投入準備

本成果は**準備のみ**。親受入済みinitial原文3件（公式root、財務一覧、連結Q3短信）、営業外通知を示すニュース一覧1件、別phaseで取得した通知PDF本文1件、原短信12数値の派生1件をsource-only bundleへまとめた。正規化bundleの原短信は重複しない。保存短信の注記/セグメント追加読解も新sourceにしていない。会社・thesisは空配列、金融入力採用・IR登録/送信は0。

| source | kind / financial_content | 分類根拠と境界 |
| --- | --- | --- |
| 公式root | business_description / false | システム開発の知見を使うセキュリティサービスの会社説明。金融という表現だけで銀行評価ルート等を認定しない |
| 財務IRライブラリー | index_only / false | 年度別短信/有報リンク。リンク先本文・最新性の証明とは別 |
| 2026年10月期連結Q3短信 | financial_statement / true | 日本基準、9カ月累計。会社定義調整後EBITDAとOP/経常/親会社利益、百万円表紙と千円P/Lを分離 |
| 営業外通知へのニュース一覧 | index_only / false | このphaseは実hrefを確認し対象302で終了、金融本文0。その歴史を後続PDFの取得で書き換えない |
| 個別営業外損益の通知PDF | other / true | 1頁の金融本文。業績予想修正通知としない。通知対象の5月1日〜7月31日と短信9カ月/通期を分離 |
| 原短信12表示の構造化 | other / true | 同じ原開示の派生で新開示・独立予測ではない。中間DPS0と未定期末/年間を分離 |

原sourceのID・全JSON object・content・HTTP完了時刻・published_at:null・metadataを受入済み入力のまま保持する。`classification-evidence.json`は6逐語引用をexact source.contentのUnicode文字offsetとUTF8 byte offsetへ結び、native SHAを `sha256(models.json_text(source).encode('utf-8'))` で記録する。compact JSON SHAと混同しない。`source-map.json`にraw SHA/bytes・snapshot SHA・保存抽出とcontent一致を保持。派生は純粋reproducerで12factsを再現し原短信snapshot一致を確認した。新numeric fact生成は0。

意味は初期短信18頁中の1/2/4/5、後続の同source注記10/13/18とセグメント16/17、通知1頁の既存親受入を再利用した。今回全PDFを新しく精読した記録ではない。notes/segmentは凍結parent receiptだけを参照し、sourceを増やしていない。

会社調整後EBITDAはその会社定義を持ち、CFO/独立正常利益とはしない。営業外補助金/持分法損失、段階取得益/減損など特別損益、税・NCIを区分し、同じような表示額を相殺/OP足戻ししない。短信9カ月は2025年11月1日〜2026年7月31日、個別通知は2026年5月1日〜7月31日のQ3会計期間、通期予想は別期間。通知/短信の丸め表示一致から期間内訳の同一を認定しない。善光の取り込みPL3カ月と全社9カ月、セグメント再編前後の範囲を混ぜない。前期/当期・連結会社持分・自己株/潜在株式の不明を補完せず、EPSから分母を逆算しない。

通知は同日短信への反映、経常/親会社利益の従前予想割れ、当時通期予想据置と影響検討を併記する。影響0・将来損失消失・現在予想保証とはしない。表示中間DPS0.00だけが実数で、期末/年間未定dashを0にしない。配当支払や正常利益への採用も認定しない。

## 固定入力とroot実行手順

`input-pins.json`は4組の受入済みproducer manifest列挙files/明示outputsとmanifest/parent acceptance、および同source notes/segmentの凍結親receiptだけ。未freezeノート・別担当index/native case/監視・current docs等を広くpinしない。`prepared-code-pins.json`のsrc44 Python filesは最新1558tests受入時のfixed-code pinsと完全一致。prepared=currentだが実行時にも再照合する。

受入済み [2163の手順](../ir-2163-initial-with-facts-intake-2026-10-16/README.md) のrunner/API/journal/copy→actual/全旧row保持を再利用した。`adapted-runner.diff`はcompany、6source数、baseline hash/件数・case件数、作業ID/backup名、期待完了件数だけを変更している。runnerはimport/実行せずAST parseのみ。

rootは入力とrunnerを読んで新規 `parent-input-acceptance.json` を保存する。後の `parent-acceptance.json` と別名のまま保持する。以下は将来rootだけが実行するコマンド。CODE_SHAを受入済み44file manifestの実SHAへ置換する。コードが変わった場合は旧preparedを上書きせず、新しい受入manifestを指定する。

```bash
.venv/bin/python research/ir-2315-initial-with-facts-intake-2026-10-16/run_once.py shadow --execution-code-pins research/ir-2315-initial-with-facts-intake-2026-10-16/prepared-code-pins.json --execution-code-pins-sha256 CODE_SHA
```

成功shadowの全table旧row/schema/case不変と増分を受入し、同じrunner/data/execution-code SHAでrootだけがstageをactualへ変え1回実行する。actualはparent入力受入と成功shadowを必須とし、実DB変更前にGit対象外data/backupsへ完全backupを作る。準備ではbackup/copyを作っていない。

APIは実時計の `Harness.ingest(source-only)` → `Intake.queue(company_id=jp:2315,new_only=True)` → request ID付きobserved claim → `Harness.complete(expected_attempt=1)` の1jobだけ。新journalへ各段階begin/succeededをfsync、packet/source全snapshot・worker/generation/leaseを点検する。pipeline全体は単一transactionではない。失敗/不明段階はjournal/backupを確認し、成功済み又は不確実なmutatorを自動再送しない。原HTTP完了/準備時刻を将来実ingest firstsaveに置換しない。

## 読取baselineと将来期待差分

実DB main SHAは `f61e892f68d4518e659899e00d0238b163b660d94f5399b8c37ae63f1b03ffca`。`mode=ro/query_only/contextlib.closing`で195sources/194classifications/108全完了jobs、105attempts/210events/105request receipts、23case heads/44versions/134reviewed sources、2315既存会社/source0、新6ID未登録を確認した。Store初期化/DB書込みは0、読取前後main SHA不変。

将来の期待増分はsources+6 / record_availability+6 / source_classifications+6 / jobs+1 / job_attempts+1 / job_attempt_events+2 / job_request_receipts+1だけ。201sources/200classifications/109全完了jobs、106attempts/212events/106receiptsとなる。schema、全table旧row、既存company、case23/44/134は不変を要求する。runnerは全tableをmultiset比較し、旧rowの変更/削除や他table増分を拒否する。今回これらの将来成功を主張しない。

新GET・DB書込み・Store初期化・backup/copy・runner/shadow/actual実行・production/shared file変更・金融採用・IR/注文は0。準備14filesだけを固定し、rootレビュー待ちで停止する。
