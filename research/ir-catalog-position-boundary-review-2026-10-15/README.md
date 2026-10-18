# Catalog既定heldと判断用保有観測の境界

**P1・1件を2つの合成DBで再現した。** 窓口catalogには保有申告がないが、`held`省略が`false`へ補われ、明示ユーザーの`held:false`と同じ`kind:observed`の保有記録になる。同じ既存合成モデル/方針/価格では両者が`buy_review`、`held:None`だけの対照は`position_not_verified / unresolved`。質問契約にも`synthetic_position`なしでfalse/observedが固定される。

これはcatalog import単独が買いを出すという主張ではない。import自体はwatch会社を作り、財務資料・thesis・jobを作らない。一方、後続判断に必要な他の入力が揃うと、申告の欠損が保有確認の保留を解除する。単に「observed」という名前の問題でも、明示申告をbrokerの実保有証明と呼ぶべきという要求でもない。

[contacts.py:149](../../src/ir_agent/contacts.py#L149)はheldなしのcompanyを返し、[models.py:137](../../src/ir_agent/models.py#L137)が既定falseを追加する。[Store:178](../../src/ir_agent/store.py#L178)は無条件にposition観測を作り、[position_for:72](../../src/ir_agent/decision_lifecycle.py#L72)が判断contextへ渡す。省略と明示falseの`validate_company`結果も同一だった。

fresh default抑止だけでは足りない。同じ使い捨てDBの観測だけを空へ戻す隔離段階では、[status-only更新](../../src/ir_agent/harness.py#L117)も[旧DB起動](../../src/ir_agent/store.py#L99)も既存company値からfalse/observedを作り直した。実/旧DBを削除した実験ではない。また、現在の同値boolだけの重複抑止は、旧origin不明falseを明示falseとして改めて確認した時にも新しい来歴を残せない。

会社JSONのdefaultfalseは既存の明示仕様で、値を表示する互換性は維持できる。legacy bootstrapテストも「起動時にDB metadataの状態を観測し、以前へ遡らせない」という意図を持つ。これを実保有/明示申告の確認と分ける必要がある。

最小案は、catalog/provider既定や省略、status-only、bootstrapから確認済みの判断用保有観測を作らず、信頼する明示申告を来歴と観測時刻付きの新記録にすること。`company.held`、旧source/仮説/観測/判断JSONは上書きしない。旧観測にはoriginがなく、明示申告か既定値かを復元できないため、不明な旧rowを確認済みへ移行せず、新しい申告を別観測として残す。同じfalseでもこの確認を落とさない。正当な申告がなければ判断用途はunknownとする。

[review.json](review.json)に根拠line、既存テスト意図、旧originの限界、実装していない最小案を保存した。[probe.py](probe.py)と[probe-result.json](probe-result.json)は再実行可能な有限証跡。新GET・実DB・本体/旧ファイル変更・fullsuiteは0。修正実装は行っていない。
