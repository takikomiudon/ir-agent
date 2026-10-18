# 保存研究の価格判断レビュー接続

返信を必須としない `research-decision-review add/show` と `Harness.review_research_decision` を追加した。採用済みの公開baselineと返信後評価の分離保存を実現し、旧daily提案やir-planの仮定分岐を判定済baselineとして扱わない。[利用契約](../../docs/research-decision-reviews.md)、[設計](../ir-public-decision-review-design-2026-10-15/README.md)、[実装・検証manifest](implementation.json)を参照する。

新 `research_decisions.py` が独立tableとimmutable request/record/current viewを扱う。Storeのschema初期化、HarnessとCLIに最小接続を加えた。固定policy版、最新thesis、明示position、quote、全原典・依存返信の来歴/公開性を解決し、既存evaluate_decisionで計算する。価格source/field bindingだけをdecision.pyの小helper2つへ共有抽出し、旧pureの早期return順序と金融判断条件は維持した。before完全bytesは [before-files.json](before-files.json) と `before/` に保存した。

requestのassessmentは根拠付き人/agent評価であり、engineが事業や金融入力の正しさを認定しない。basisはsaved_research、public_onlyは保存済み型/metadata/来歴検査を通るIR祖先なし閉包という機械的区分で、元サイト公開/真正性の独立認証ではない。rawreplyの受信時初期分類と正式適用IR sourceの分類を分け、既存の初期unclear→public適用経路を保持する。

新focused **29件**と旧関連回帰 **78件**（decision24、quote21、thesis8、reply lifecycle17、policy CLI8）が成功した。全fixtureはsyntheticでmemory/temp DBのみ。最新rawとstrict選択不一致、無関係な旧legacy partial、quote第二親/cycle/別会社/synthetic、誤bindingと不足、IR元bindingと後日訂正、再送/CAS、1µs期限、明示position、current同版receipt不整合、atomic rollback、CLI add/showを確認した。開発中の修正もmanifestに明記し、最終ログを保存した。

旧reply schema/JSON、RecordAvailability entity、金融モデル/数値閾値を変更していない。実運用DBアクセス/書込み・network・外部送信/注文・実企業の金融入力採用は0。producerはfull suiteもroot所有demoも実行していない。rootのdemo結果と独立reviewは別ファイルであり、ここで独立受入済みと主張しない。全suiteと最終受入は主担当待ち。

## 主担当の受入

[独立63項目](independent-review.md)でP2の2件を修正・再確認し、未解決指摘0。[全1,480件・36.669秒成功](parent-full-suite.json)、実DB124資料SHA不変を確認した。[架空demo](parent-demo.json)は返信前hold_review/public_onlyから質問分岐点検を経て返信後exit_reviewへ進むが、前後の価格も違うためIR効果の推定ではない。送信・注文・実企業への金融採用0。[受入記録](parent-acceptance.json)に最終code/SHAと限界を固定する。元producer時点・修正前の記録は当時の状態として保持。
