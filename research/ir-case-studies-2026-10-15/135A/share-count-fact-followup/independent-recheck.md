# 135A発行済株式数1factの独立点検

限定点検は不備なし。準備済み4ファイルは固定SHAどおり保持され、実行後のbundle/validation/READMEとは別に残る。原表p2の画像・raw再描画の独立確認は先行結果を再利用し、今回PDF全体や画像を再監査していない。

新1factは2026-08-31期末の普通株式発行済総数（自己株式を含む）の10,256,000株→10256000shares。旧p2の同じ逐語span・当期列・行/conceptを確認した。単位乗数1のDecimal計算、API全bundle replay、request不変、reproduce、元source object/ID、JSONの2serialization方式SHAと派生IDは一致した。

自己株dashは不確定のまま。期中平均/EPS分母、自己株控除後net、希薄化後、現在評価時点の株数に置換していない。全9入力の値とmodel pathはnull、金融意味false/未採用を保持する。金額の百万円切捨て注記を株数に適用せず、現金factの再抽出・加算もしていない。

準備review時刻15:30:24.133560と、実行/派生取得15:32:38.797225（UTC）は別。準備mapのderived pathがnullなのは未実行時点の履歴であり、実行結果は後の別artifactに保存される。これをmodel採用pathへ昇格しない。1380件passは親の受入根拠として記録されたもので、この1fact独立点検で全suiteを再実行したとはしない。

[independent-recheck.json](independent-recheck.json) に準備4ファイル/producer7ファイル・旧入力SHA、原引用、API再現と意味限界を記録した。GET・DB・Store・CLI・コード・旧ファイル・索引/監視変更は0。表示1件の再現性確認であり、unit機能の一般性能や全財務入力の採用認証ではない。固定後の訂正は別補足とする。
