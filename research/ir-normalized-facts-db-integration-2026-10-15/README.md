# 5988の構造化財務資料を研究台帳へ接続

2026-10-15 21:47 UTCに、パイオラックスの[会計上の財政状態3値](../ir-case-studies-2026-10-15/5988/balance-book-value-facts/README.md)を含む**派生source 1件だけ**を実DBへ保存・分類した。元の公式短信、会社状態、金融仮説、policy、保有申告は変更していない。原表の総資産・純資産・参考自己資本を別概念として保持し、BPS・PBR・本源価値・将来予測へ転用しない。

今回の目的は、原典に対応する構造化資料を既存の資料取得・分類の台帳で参照できるようにすること。`financial_inputs_verified:false`、意味のレビューが必要という宣言を維持した。分類は派生資料として`other`、財務内容あり。原典の短信自体の分類とは区別する。

## 確認と適用範囲

[読取専用の照合](read-only-preflight.json)では、旧索引24束と今回の新1束のうち23束について、既存会社・原sourceとsnapshotが一致した。8331/9702の2束は実DBの対象会社・原sourceがなく、対象を追加していない。[23束の原文・単位換算再現](read-only-reproduction.json)もすべて`reproduced`。これは財務的な意味・モデル適合や入力採用の認証ではない。

実適用は新しい5988の1束に限定した。他22束は照合しただけで、旧索引の24束すべては引き続きfile-only。[一時DBの検証](5988-bs-shadow-preflight.json)で、1source追加、再取り込み0件、1sourceだけのintake・分類完了、会社/原典の不変を確認した。

[実適用記録](5988-bs-actual-completion.json)と[完了job](5988-bs-actual-intake-job.json)を保存した。実DBは125source（公開124・市場1）、分類124、完了job57（intake54・定性3）。attempt54/event108/request receipt54。原sourceの旧取得日時と派生資料の処理日時を保持し、派生資料の実初回保存は**2026-10-15T21:47:39.565188+00:00**。この初回保存を以前の調査時点へ遡らせない。

旧全テーブルの既存行を保持し、無関係のテーブルは完全一致。native監視15case/19版/70既読は不変で、5988を暗黙に新caseへ追加していない。実金融入力/予測・policy・正式質問・返信・送信・注文の採用は0のまま。[索引v22](../ir-case-studies-2026-10-15/disclosed-fact-index-v22.json)は旧97factを保持して100factへ更新し、今回1束の実保存だけを明示した。

## 適用時の訂正と再実行

最初の一時DBで、minified JSONに空白があると仮定した引用作成に失敗した。[失敗記録](5988-bs-shadow-preflight-attempt1.json)を残し、保存本文そのものに一致する部分文字列で修正した。

実適用の初回は、API自身が開始するtransactionへ外側から重ねて失敗した。[エラー](5988-bs-actual-error.json)と[直後の照合](5988-bs-after-attempt1-state.json)のとおり、既存全行は完全不変で、追加は現行Storeが初期化する空の`research_decision_reviews` tableだけだった。元データを復元・改変せず、一時DBで成功した各APIの通常の呼び出し順へ戻して完了した。[第2回の段階記録](5988-bs-actual-stage-v2.jsonl)を保持する。

各APIの更新は原子的だが、この全工程が単一transactionという意味ではない。保存済みreceiptとjob状態を読んで現状を判断する。履歴の一回用適用スクリプトを自動で再実行しない。新GET・本番コード変更は0で、データ接続のために全件コードテストを再実行していない。
