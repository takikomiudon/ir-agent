# ファイル計算CLIのDB副作用を解消

ファイルだけで完結する既存操作は、Store/Harnessを生成する前に分岐するよう変更した。正常な入力でも無関係なDB保存先のpath競合で失敗し、空DBを作成していた問題を解消した。常時12コマンドと、FILE付きの `observations summarize`、明示した `contacts import --dry-run` が対象。

既存の計算・JSON検証・出力・例外・時計は維持する。`decision FILE` と `ir-plan FILE` は従来からsnapshot計算であり、保存系の `decision-review`、返信、質問、PIT等のDB検証はそのまま使う。

[変更と対象7テスト](implementation.json)、[固定差分の独立レビュー](independent-review.md)、[全1,339テスト成功・37.023秒](parent-full-suite.json)、[親の完了確認](parent-acceptance.json)を保存した。独立レビューはblocking指摘0で、3つの差分probeを実施した。全suiteは固定コードで1回だけ実行し、レビュー後の同一コードとのbyte一致を確認した。実研究DBのmainファイルSHAは不変、実DBを開いていない。

[修正前の2再現と調査](README.md)は当時の記録として保持する。その末尾の「未修正」はその調査時点を表す。財務入力・実売買方針の採用や外部送信を行った変更ではない。
