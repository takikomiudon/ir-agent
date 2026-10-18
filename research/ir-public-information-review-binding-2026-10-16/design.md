# 公開情報レビューの任意参照固定（実装前設計）

`question.public_information_review` のみopt-in。厳密な非空object `{reviewed_at, reviewer, rationale, sources}`、sourcesは非空listで各itemは `{source_id, source_snapshot_sha256, scope, basis_quote}` のみ。scopeは非空string、SHAは小文字hex64桁、sourceID重複/余剰typo/欠損は拒否。reviewed_atは自己申告で `<= question.created_at <= plan.as_of`。quote存在とscope記録は、未回答という意味・実読・全公開資料の最新性を機械認証しない。

小moduleのshape validatorをmodels.validate_questionからopt-in時だけ呼ぶ。pureplanは渡された原source objectをnative `models.json_text` UTF8のSHAへ結び、同社/public_disclosure又は明示public_clarificationのIRreply、全DAGの原典/利用可能時点/公開性を点検する。market_data/他社は拒否。financial thesis evidence以外のQ&A根拠も可能で、評価への採用とはしない。原source/quote/scopeを変更しない。

pureの不正shape/hash/quote/会社/market/循環はValueError。source時点不足・欠けたancestor・公開性holdは既存needs_reviewを使う。結果には根拠ID/closure/hash/理由と意味確認未完了を示すcheckを、fieldがある場合だけ追加する。新status/投資閾値はない。

Lifecycle.planだけで追加reviewsource closureを解決してpureplanへ渡す。既存sources_forの他用途は広げない。persist checkはStore.source_availabilityの原典DAG receiptをreviewed_atの両時計で確認し、trustedfirstsave/legacyknownby/unknownを保持。reviewed_at/as_of/trustedruntime現在の情報訂正も読み、current metadata/IRreply originのholdも適用する。後付け保存を過去の実読へしない。

contract付きは既存preflightにnotready理由を含める。contractなしでもnewfieldがある場合は保存前に同じcheckを行い、下書きへ `public_information_review_check` をサーバー計算の固定観測として付ける。不正参照は早期拒否、時点/公開性不足は下書きの理由に残しmark_sentの新field分岐で再点検して止める。callerに派生checkを新規指定させない。旧互換未導入は全出力/動作を維持。

question原文とcheckの初回観測は不変。同一requestのretryは保存値を返し、差分は拒否。mark_sentは新しい送信記録をする直前にtrustedruntimeで再点検し、既送信の同一再送は既存履歴のまま。既存外側transactionへ接続し、新table/CLIを作らない。

変更予定はnewmodule + models/decision/lifecycle/harnessの分岐のみ、新test1file。専用testは同source別scope、shape/hash/quote/会社/時点/DAG/market拒否、receipt後付け/legacyknownby/current訂正、draftnotready/sendhold、retry/不変/transactionrollback、未導入JSON・結果互換を検証する。実DB/GET/外部送信/金融採用は0。fullsuiteはroot最終実行。
