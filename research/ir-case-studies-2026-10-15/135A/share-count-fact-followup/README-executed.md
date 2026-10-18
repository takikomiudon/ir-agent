# 135A 株数表示1件の実行記録

実行now/派生取得: 2026-10-15T15:32:38.797225+00:00。親の株数unit受入連絡後、固定した [normalization-input.json](normalization-input.json) を既存APIで実行し、[normalized-bundle.json](normalized-bundle.json) を別成果として保存した。準備review時刻 `2026-10-15T15:30:24.133560+00:00` と今回の実行時計を分け、準備4filesは変更していない。

出力は2026-08-31期末の普通株式発行済総数（自己株を含む）**10256000 shares** の1表示だけ。raw10,256,000株/乗数1を保持する。自己株dashは未確定で、自己株控除後net・期中平均・希薄化後・現在評価株数へ代用していない。全9採用値/pathはnullのまま。新しい金融入力やIR条件の採用ではない。cash2factsも再抽出/結合していない。

原sourceID `case-public:4b9aaae627aa90731140aa648b9c8bf60be1767accaab06041ac23dc5f6955fb`、原snapshot/本文/取得時刻/pubnullは不変。派生ID `disclosed-facts:c7be36460e1fc23dd43cc82acdcb407ea129dc6f27049e9e956f880cae340026`。元p2quoteのglobal/頁内offset一致、API全bundle replay/reproducer、独立Decimal算術を確認した。原PDF・画像の再抽出/再読は前段の固定独立確認を再利用し、この段階では行っていない。

API実行中はStore constructorとsqlite3.connectを失敗guardし、両呼出0。GET・DB/Store起動・CLI・コード/原source/旧facts/index/monitor/準備file変更・モデル/価格/予測/閾値/IR条件/売買採用は0。準備段階で未実行だった記録は履歴として保持し、今回実行の結果はこの新記録で区別する。[execution-validation.json](execution-validation.json) に検証とSHAを保存した。新成果を固定し、後続訂正は別版にする。
