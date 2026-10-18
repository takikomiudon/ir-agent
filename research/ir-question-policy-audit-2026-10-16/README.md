# IR質問方針と現実装の監査

4原則は既存手順とコードに概ね接続済み。**公開情報レビューの参照固定と、contractなし旧互換記録の扱いに2つの境界が残る。** 新しい投資ルールや再実装は必要ない。まずrootレビューを待つ。

| 原則 | 現状と具体的な根拠 | 残る範囲 |
| --- | --- | --- |
| 既答を再質問から除く | `evaluate_ir_plan`は`public_answer_status != not_found`を要再確認とし、contract付き`validate_send`が拒否する。通常の`evidence_ids`と会社/時点/thesisへの参照もある。既存testは公開確認未記録のholdを確認。 | どのQ&Aの範囲をいつ誰が読み、なぜ未解決かをscope/time/hash/quoteで専用固定してはいない。not_foundは担当者の意味レビュー申告。 |
| 仮説/反証・評価へつながらない問いを送らない | `evaluate_ir_plan`が事前分岐、thesis、許可pathを比較。`DecisionLifecycle.freeze/validate_send/validate_branch`が不変保存と再点検。no_decision_change/needs_reviewはcontract付き既送信記録を拒否。 | contractは任意の旧互換仕様。ir-planのaction差は限定的な比較で、金銭EVSIや外部送信許可ではない。 |
| 無回答/曖昧を悪化/売りへ直結させない | unresolved分岐は必須・valuation指定不可。closeは質問状態のみ変更。`evaluate_reply`は曖昧/非publicを非適用、既存testsもモデル不変を確認。VOIは明示尤度で扱う。 | 引用存在だけで意味は確定せず、分岐/公開性の対応はレビュー責任。無回答を必ず無情報とする原著ルールも作らない。 |
| 方針未採用のまま売買へ進めない | policy未設定はunresolved、未保有で確率なしの期待値は作らない。旧互換replyもactionはmissing_decision_contract/unresolved。定性jobは別契約で研究継続。 | 全入力欠損を受理する契約ではなく、不正/不完全な数値API入力はvalidationerrorの場合がある。既保有の明示反証等は確率なしで点検可能という既存区別を保つ。 |

`audit.json`に関数と既存テスト名・行・SHA、10の短い原著引用と位置を保存した。Anthropic DDの既知事項/優先質問・thesisの反証、Damodaranの事業説明→評価入力と新情報後の見直し、BaioらのEVSI、JIRAのFAQ公開という根拠を区別している。回答分岐/公開性3分類/入力path/保留/送信記録gateはprojectの適応であり、著者が日本株メールIRの一律売買規則を示したものではない。

不足は最大2件。G1は既存evidence参照が無いという意味ではなく、公開Q&Aレビューに特化したscope/time/hash/quoteの結合が無いこと。新しい実質問の事前準備前に小さい参照固定を検討する価値があるが、意味上の「答えが無い」を自動認証しない。G2は外部既送信の記録と旧互換仕様であり、旧経路を今回一律禁止しない。現研究のnotreadyを外して数値・送信へ進む必要はない。

合成のpure API確認ではnot_foundのみplanが区別可能、found/未記録は要再確認、必要policy未設定はunresolvedを再確認した。既存unit testは対象本文を読んだもので全実行はしていない。GET・DB・code/旧ファイル変更・新金融条件採用・質問送信は0。
