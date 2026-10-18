# 数値thesis前の定性IR確認を保存する

`ResearchInquiries(store)` は研究用の問い・外部で送信済みの記録・受信原文・公開性と比較分岐のレビューを保存する。数値thesis、金融入力、評価額、売買、外部送信は扱わない。既存の金融質問・返信表へ行を入れず、元caseやjobも自動更新しない。

Anthropic DDの既知情報と懸念の区分、thesis trackerの継続点検、日本IR協議会指針の公開既答確認を参照する。[質問準備](ir-question-preparation.md)に原典と適用範囲がある。A/B・混合・曖昧回答を比較注記へ結ぶ部分は本プロジェクトの適応で、著者の売買規則ではない。

## 保存とAPI

モジュールの `SCHEMA` を所有するStoreの接続へ導入する。新しい表は `research_inquiries`、`research_inquiry_replies`、`research_inquiry_reviews` の3つだけ。各表の `first_saved_at` は呼び出し側が与える信頼済みruntime時計で記録し、申告の作成・受信・レビュー日時と分ける。既存 `record_availability` のquestion/reply型名を流用しない。

```python
from ir_agent.research_inquiries import ResearchInquiries
api = ResearchInquiries(store)
saved = api.add_inquiry(request)
api.mark_sent(saved['id'], externally_sent_at)  # 実送信を行わない
reply = api.add_reply(received_request)
review = api.add_review(review_request)
view = api.current_view(saved['id'])
```

時刻を使う各APIの `now` keywordはテスト等で信頼済みruntimeを渡すためのもので、JSON申告欄ではない。省略時は実時計。新規書込は新3表の初保存・送信記録・閉鎖記録より古いruntimeを拒否する。

`add_inquiry` の必須requestは次の形。文字列欄は空にせず、追加キーは拒否する。

```json
{
  "id": "research-definition-1",
  "case_id": "existing-case-id",
  "issue_id": "existing-issue-id",
  "expected_case_version": 1,
  "expected_config_revision": 1,
  "created_at": "2026-10-16T13:00:00+00:00",
  "topic": "public-rate-definition",
  "question": "公表された料率の比較対象と期間は何ですか。",
  "already_answered": "商品別に率が異なるという公表説明を確認した。",
  "remaining_uncertainty": "同条件の料率差か、構成差を含む平均かは未確認。",
  "branches": [
    {"id": "A", "condition": "公表根拠で同条件の変更と特定", "comparison_note": "特定された対象系列だけに注記する。"},
    {"id": "mixed", "condition": "複数要因が公表説明で区別される", "comparison_note": "要因を併記し、寄与額を推計しない。"},
    {"id": "unresolved", "condition": "曖昧又は回答なし", "comparison_note": "比較対象未解決を維持する。"}
  ],
  "public_information_review": {
    "reviewed_at": "2026-10-16T12:59:00+00:00",
    "reviewer": "researcher",
    "rationale": "公表済みの対象範囲を確認し、この定義が残った。",
    "sources": [{"source_id": "existing-public-source", "source_snapshot_sha256": "実際のnative JSON SHA256", "scope": "対象頁・表・期", "basis_quote": "保存本文からの逐語引用"}]
  }
}
```

上記ID・時刻・SHAは説明用で、そのまま投入する例ではない。caseの会社・論点・head/config・実保存・原文ファイルを照合し、server側でcase全snapshot/native SHAと公表根拠closureを固定する。caseの既読原典も、問い合わせに直接引用した公表根拠とは別に、既存定性レビューのnative SHA・分類・公開性・来歴チェックで点検する。初回は作成境界と現在、現在表示では現在の利用可否を調べ、legacy資料のknown-by例外も既存経路を使う。financial_content=trueを求める新gateではない。

公開既答レビューは[既存の参照契約](ir-question-preparation.md)を再利用する。後着資料を過去のレビューに混ぜず、同社の原典DAG・引用・保存来歴・現在の公開性訂正を確認する。実caseはDAGのどの階層でもsynthetic=trueの原典を使えない。synthetic caseがflagなし資料を使えることは既存monitor規約と同じ。既読や全資料の最新性、未回答の意味、個人IR受付条件の認証ではない。

分岐は2件以上、重複なしで `unresolved` が必須。各分岐は `id, condition, comparison_note` だけを持つ。action・valuation・金融parameterは受け取らない。`add_inquiry` は会社/topicの未完了研究質問と既存金融質問の重複を拒否する。逆方向の金融質問登録にも同じ存在確認が必要である。

`add_inquiry` は不変recordを返す。`show_inquiry(id)` は `{record,state,replies}`。stateは `draft/awaiting_reply/answered/expired/declined/cancelled` と送信・閉鎖時刻。`list_inquiries(limit=20)` はid順にid/会社/topic/state/初保存を示す一覧で、優先度や時点認証を追加しない。

## 送信記録・受信・公開性レビュー

`mark_sent(id, sent_at)` は原質問の実保存後・未来でない外部送信済時刻だけを記録する。caseが変わったり原典が保留になれば新たな送信済登録を拒否する。作成時・申告送信時・実記録時の公開性を分ける。`close_inquiry(id, reason)` は `no_response/declined/cancelled`。無回答や辞退は送信済が必要で、無回答から内容を推定しない。元の閉鎖履歴を残しつつ、後日の実返信は受信保存できる。

`add_reply` は `{id,inquiry_id,received_at,raw_text}`。受信原文を不変保存し、公開性の初期値は常に `unclear`。明示する場合もunclearだけを受け付ける。受信は送信より前・未来を拒否する。送信後にcaseが古くなっても、実際の受信原文は保存できる。

`add_review` は `{reply_id,expected_version,branch_id,basis_quote,rationale,recorded_at,information_status}`。公開性は `public_clarification/unclear/potential_nonpublic`。publicの場合だけ追加の `public_information_review` が必須で、非publicではこの欄を受け付けない。返信の逐語引用と公開原典の根拠は別であり、公開性・選択分岐の意味はcallerの判断として保存する。

reviewはappend-onlyのCAS版。原返信・事前分岐・caseのbindingを照合し、比較注記はcallerの新文ではなく固定分岐からserverが取り出す。public化はcase/files・公表原典の整合が必要。caseや古い根拠が変わった後でもunclear/potential_nonpublicへの安全側の訂正は保存でき、過去のpublicレビューを上書きしない。訂正で元caseや金融入力が変わることはない。初回レビューは返信の実保存後、後続レビューは前版の記録・実保存後とし、時刻逆行を拒否する。

`add_inquiry/add_reply/add_review` と送信/閉鎖の同内容retryは元の不変recordを返す。ID同じ別本文・分岐・送信時刻・閉鎖理由への差替えは拒否する。retryは現在利用できるという認証ではなく、現在表示を別に読む。

## 現在表示と限界

`show_reply(id)` は原recordと全review履歴。`current_view(inquiry_id, reply_id=None)` は最新受信保存（又は指定返信）の最新reviewを点検する。現在のcase head/config/原文ファイル、同社source snapshot・DAG・公開性と実保存を再照合し、`held` と理由又は `comparison_note` を返す。古いcaseへの自動rebaseは行わない。後日の非公開性訂正や後着保存があれば比較注記を現在の利用可能結果として返さず、過去recordは保持する。回答なし・未レビューも未解決のまま。

新3表内の返信を旧 `ir_reply` sourceへ変換せず、既存公開原典だけを共通public-review checkerへ渡す。返信をqualitative jobへ流す機能はこのsliceにはない。元caseへの手動比較接続や実際のIR送信には別の操作と根拠確認が必要。正式金融questionのgateや既存inbox/evaluationは変更しない。

単体検証は `python -m unittest discover -s tests -p test_research_inquiries.py -v`。synthetic一時DBとファイルだけを使う。
