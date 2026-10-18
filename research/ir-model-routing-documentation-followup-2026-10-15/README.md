# モデル振り分け文書の実装状況追補

[docs/model-routing-inputs.md](../../docs/model-routing-inputs.md)の旧実装状況を、現valuationと3仕様へ照合して訂正した。DDMを未実装とする記述を除き、既存の `dividend_discount`・明示終価DCF・明示株主価値調整の純計算を区別した。実装名の一覧へ既存の `dcf_explicit_terminal_equity_bridge` を補った。

規制資本再投資FCFE/その終価・株価換算、株主超過収益、履歴取得から全体整合までの正常化、若い成長企業の収益化/資金/希薄化/存続調整を実装済みとはしていない。純計算の成功と、会社予測・分配/資本・持分・適用根拠の確認は別のまま。

編集前に[source-before.md](source-before.md)へ全バイトを保存し、編集後の[source-after.md](source-after.md)は現在文書とbyte一致。[review.json](review.json)に前後SHA・3箇所の記述置換と1追補・完全diff・根拠pathsを保存した。この限定変更を取り消すと旧全byteへ一致し、残りの文書は完全保持される。

24factsのtemplate、確認事実/タスク/研究labelの節と数値基準は不変。根拠の3仕様・valuation・templateのSHA不変を確認し、10有限照合を記録した。code/tests/DB/GET/他docs/既存研究fileの変更0、実行テストも0。snapshot/reviewは固定し、後の補足は別記録にする。
