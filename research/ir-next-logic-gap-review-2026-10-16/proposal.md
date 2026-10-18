# 次の実装：研究inquiry専用の現在作業一覧

**独立read-only scriptを1本実装する。** 仮名 `scripts/report_research_inquiry_inbox.py --db PATH`。保存済みの質問→返信→固定分岐レビューをそのまま再利用し、毎回どの返信をレビューすべきかを一覧にする。親がこの候補を採用済み。今回は提案までで、実装担当は別agent。

現行の登録・送信済記録・返信・分岐選択・公開性訂正・現在再点検は既実装なので再実装しない。足りないのは、その対象を漏らさず拾う経路。

- `src/ir_agent/research_inquiries.py:94–99` のlistはID順の状態一覧だけ。`answered`から未レビュー／公開性保留／利用可能な比較注記を識別できない。
- `src/ir_agent/harness.py:638–669` の金融inboxは旧questions/repliesのみ。研究inquiryを除くのは意図した境界であり、ここへ混ぜない。
- `research_inquiries.py:364–407` のcurrent_viewは返信指定を省略すると最後に保存した返信だけを選ぶ。後の返信が処理済みでも、先の未レビュー返信を作業一覧から消してはいけない。
- 固定入力 `research/ir-three-draft-review-packet-2026-10-16/packet.json#/items` の3件は当時draft／返信0。7388は料率の同条件変更対構成差、135Aは社数単位と期間内変更、7525は両計画の売上範囲の共通性という既存分岐を持つ。いまは3draftを拾い、実受信後は同じ一覧から未レビューを拾える。現在の実DBを本レビューで再読したとの主張ではない。

## 最小の振る舞い

1. 現在のruntime時計を1回固定し、全研究質問を母集団にする。過去as_of機能は追加しない。表示はID等の安定順で、投資優先度やIR価値を計算しない。
2. draft、返信待ち、終了済みの状態を保持し、各質問の**全返信**へ `current_view(inquiry_id, reply_id=保存返信ID, now=同じ時計)` を呼ぶ。未レビュー、根拠保留、比較注記ありを分け、既存reason_codes／review版／branch IDを表示する。返信本文の一括転載は不要。
3. 返信なしの通常draft／返信待ちを、`no_reply`という理由だけで情報訂正案件としない。質問stateとviewの理由は別軸。無回答終了・辞退・取消も保持し、架空返信・負の投資信号へ変えない。必要ならカテゴリ別limitと総件数／省略件数を出し、先頭20件のlistを全母集団として再利用しない。
4. 分岐条件の意味判定は人／担当agentに残す。公開根拠を確認した固定comparison_noteは既存current_viewから取り、caller作成の注記、金融action、send_ready、元case更新を足さない。別のreplyが保留でも、個別replyの現判定を潰さない。一覧は競合回答の自動統合でもない。

## Store初期化なしで既存判定を呼ぶ

`Store.__init__`（`src/ir_agent/store.py:74–99`）はWAL設定・schema導入を行うため呼ばない。既存script `scripts/report_research_monitoring.py:17–27` と同じくSQLiteを `mode=ro`／`PRAGMA query_only=ON`／単一BEGINで開き、Row factoryを設定してfinallyで閉じる。

小さいread-only adapterに必要なのは `connection`、実時計を正規化する `_clock`、`source(id)`、条件付きの旧金融 `reply(id)`／`question(id)`。後者2つは公表根拠の全祖先にir_replyがある場合に `DecisionLifecycle.review_public_information`（`decision_lifecycle.py:92–108`）が呼ぶ。read methodsは既存StoreのSELECTと同じJSON形を保持する（source:266–270、reply:451–455、question:442–449は状態欄も付加）。不要なcompany/thesis/policy/書込methodは追加しない。

`ResearchInquiries`／`QualitativeResearch`／`DecisionLifecycle`のconstructorは接続保持のみ。current_view→`_case`（inquiries:110–133）ではcase版・file・既読sourceを、`_public`（135–149）では公開根拠closureを読む。`QualitativeResearch._source_check`（179–201）は既存ScheduleReader／availability／分類をSELECTで再利用する。`RecordAvailability.at`（availability.py:204以降）は読むだけで、保存receiptを新規発行しない。

**source_assessmentsを空dictで代用しない。** `information_review.py:154–168` はadapter.sourceで全sourceを読み、ir_reply祖先の訂正を `assessments`（104–115）のreply_information_reviews表から選ぶ。これはadapterの新methodではなく、既存current_viewの呼出経路そのもの。`decision_lifecycle.py:109–117` は当時／境界／現在の訂正を再照合する。表欠落を訂正0件と見なすと保留を迂回する。

実装は必要表／列の存在を先に確認し、欠落・非対応schemaはunknownと理由を出す。研究3表が揃って0行なら既知0件。case／sources／record_availability／分類／公開性訂正／必要な旧返信表の欠落は依存不足で、0件や利用可にはしない。既存readerの欠落診断を保持し、SQLiteエラーを一括で空配列へ変えない。

## 著者手順との関係と完了条件

採用済みAnthropic DDの既知事項／懸念、資料差のfollow-up（`third_party/anthropic/skills/dd-meeting-prep/SKILL.md:16–17,70–76,89–100`）と、JIRA指針物理14頁のFAQ等の公開・一定の回答方針を研究の継続確認へ適応する。後者は企業向け2018年指針であり投資家への強制ルールではない。参照関係は `docs/ir-question-preparation.md:5–17,25–37`。未レビューを落とさず固定比較へ戻す一覧設計はproject適応で、著者の買売条件ではない。

既存 `tests/test_research_inquiries.py:105–115,195–235` とCLIテストは個別返信・保留・旧表不変を確認する。追加検証は、複数質問／複数返信で古い未レビューが後返信に隠れないこと、訂正・case/file変化が個別reasonへ伝わること、未返信3状態と終了を混ぜないこと、欠落unknown≠既知0、read-only実行前後のDB不変に絞る。新しい売買閾値や疑似送信は不要。現3draftに対する実RO一覧と一時DBの複数返信例が通れば、この1taskは完了。

本調査はGET／DBアクセス／Store初期化／コード・共有文書変更0。新原典探索・純算術API・質問や返信の創作は行っていない。
