# 研究inquiryの現在作業一覧

`.venv/bin/python scripts/report_research_inquiries.py --db EXISTING.sqlite3` は研究inquiryだけの現在作業一覧をJSONで返す。全inquiry／全返信をID順に保持し、返信ごとに既存 `ResearchInquiries.current_view(..., reply_id=...)` を明示して呼ぶ。先頭20件への省略や最新返信だけへの集約は行わない。ID順は投資順位・連絡優先順位ではない。

`inquiries[].state` は保存された送受信状態。並列 `categories` は `draft`、`awaiting_reply`、`unreviewed`、`evidence_held`、`comparison_note`、`unknown`。一つのinquiryに古い未レビュー返信と利用可能な別返信があれば両カテゴリが残る。`replies[]` は各返信ID・最新レビュー版・既存status／reason_codes・branch IDと、既存current_viewが許す場合だけ固定比較注記を示す。返信なしは `no_reply_view` へ理由を保持する。無回答終了・辞退・取消の保存状態も残し、無回答を仮説の否定にしない。単独の `no_reply/no_response/reply_unreviewed` を情報訂正の保留に数えない。

質問・返信原文・引用・rationale・public-review全文は出力しない。比較注記は固定分岐由来で、未解決分岐を含み得る。別返信間の矛盾を自動統合せず、比較注記を金融判断・case更新・送信readyにしない。月次積立額、銘柄配分や投資適合性は入力・計算の対象外。

SQLiteは既存パスを `mode=ro`、`query_only=ON`、単一BEGINで開き、rollback後にclosingで閉じる。Store constructor／migration／書込みAPIは使わず、既存SELECTメソッドだけのadapterを渡す。実行時計を1回固定し全返信へ共有する。Pythonの `now` は内部テスト用のtrusted clock引数で、CLIに過去as-of指定はない。

研究3表の欠落・列非対応は `status:unknown`、該当件数はnull。完全一覧が作れない場合に空配列を既知0件として解釈しない。依存表のschema不足は `dependencies` にunknownを出し、個別current viewもunknownにする。読解ファイル／case／公開性等の理由は既存current_viewを再利用する。想定外の読取エラーは本文を含み得る例外文を出さず `current_view_unavailable`。`known` はこの一覧が取得できた意味だけであり、公開性・経済的意味の全認証ではない。

新14focused testsはsynthetic一時DBでPASS。全返信保持、後発の研究レビュー訂正と旧ir_reply原典の公開性訂正、case更新、23件全保持、本文非表示、欠落／非対応schema、真の0件、ro/query_only/BEGIN/閉鎖／DB bytes不変、CLI成功／不存在DB非作成／as-of非対応を確認した。初期下書き検証はsrc配置待機中のためsubprocessがmodule未配置で1件失敗したが、配置後の最終検証では解消（draft-focused-tests.logを履歴として保持）。実DBアクセス・新GET・外部送信は0。全suiteと実DB一覧はrootが別途行う。

準備原則は [独立proposal](../ir-next-logic-gap-review-2026-10-16/proposal.md) の採用済みDD／公開既答確認のproject適応で、著者の売買条件ではない。既存core/shared docs・schema・不変request/branchを変更していない。固定入力と生成物SHAはimplementation.json、最終実行ログはfocused-tests.log。
