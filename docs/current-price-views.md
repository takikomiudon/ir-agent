# 現在の判断表示と過去の価格計算

保存したreviewの評価日時と、いま表示している時刻を区別する。過去時点での計算が正しくても、株価が方針の有効期限を過ぎれば、現在のactionは価格の再点検を必要とする。既存の `policy_snapshot.parameters.max_quote_age_seconds` をそのまま使い、新しい投資閾値は作らない。

[decision.py](../src/ir_agent/decision.py) の `check_quote_timing(quote,max_quote_age_seconds,*,as_of)` を純粋計算と現在表示で共有する。観測からの年齢は整数microsecondsで比較し、有効期限ちょうどは許可、1µs超過はstale。現在より後の観測/取得はunavailable、保存quote/policyを解決できなければunknown。day精度の扱いや原典bindingを検証する既存処理は保持する。

## 動的表示

`current_decision_view(store,review,*,now=None)` と `current_evaluation_view(store,evaluation,*,now=None)` のnowはengineの信頼できるruntime時計で、省略時は実行時点。CLI/request JSONから表示時計を過去へ指定するfieldは設けない。テストでは外部入力と別のruntime依存性として架空時計を注入する。

- `current_quote_check` はchecked_at、fresh/stale/unavailable/unknown、理由、age_microseconds、既存max_ageを返す。freshは価格の時間条件だけの確認で、現在の仮説・保有・全根拠・金融入力を再検証した意味ではない。
- `current_review_requirements` は情報訂正・仮説版・価格再点検を並べる。優先表示はrequires_information_review、requires_thesis_review、requires_price_reviewの順。
- 現在の価格条件を満たさない場合は現在result/actionをunresolvedにする。元の計算はhistorical_resultと保存済みreviewで保持し、ID、原文、実保存時刻、仮説版を上書きしない。未解決の歴史結果をこの表示だけで買いへ昇格させない。

返信適用と価格reviewの初回/再送、decision-review show、reply show、inboxは現在表示を通す。inboxのrequires_price_reviewは新しい価格の確認対象であり、IRの再送を意味しない。確認済みの新しいquoteで `decision-review add` を行えば、返信評価を再適用せず新reviewを残せる。

再送は不変の元requestと保存履歴を保持するが、現在の表示は時間経過で変わる。元JSONをそのまま取得するStoreの読取りと、現在利用の可否を示す表示を区別する。表示の変更を新しい仮説や同じ返信の再適用として数えない。

[全1069テストと独立再確認](../research/ir-current-price-integration-2026-10-15/README.md)で、20時の古いquote、全入口・再送、DB不変、新quoteによる新review、有効期限境界を確認した。架空検証であり実投資の成績を示すものではない。


## 現在DBの仮説版も照合する

`current_thesis_check` は保存reviewのreviewed_versionと現在DBのcurrent_versionを表示する。不一致・解決不能は現在actionを保留し、inboxをrequires_thesis_reviewへ回す。株価がfreshでも旧仮説への判断を現在候補へ流さない。旧IR分岐を新版へ自動適用せず、新規reviewの既存版guardを維持する。

これはraw最新版との機械的な版照合であり、金融妥当性・PIT履歴の完全復元・将来版の採用可否を保証しない。[全1077テストと独立再確認](../research/ir-thesis-version-integration-2026-10-15/README.md)に、v2→v3の全入口・再送とDB不変を保存した。
