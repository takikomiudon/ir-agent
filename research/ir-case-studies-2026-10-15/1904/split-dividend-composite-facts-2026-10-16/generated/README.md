# 1904 分割配当・円銭原表示の生成結果

状態は **file-only生成済み、root独立照合・接続判断待ち**。受入済みコード `d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51` を使い、原通知1sourceと新派生1source、3表示factのbundleを生成した。正規化版は2。先行入力5filesと親入力受入は固定した。

|原表示|値（JPY-per-share）|会社が示す性格|
|---|---|---|
|99 円 00 銭|99.00|今回修正・中間、分割前株式数基準、2026-09-30基準日|
|24 円 75 銭|24.75|今回修正・期末、分割後株式数基準、2027-03-31基準日|
|198 円 00 銭|198.00|会社表示の【本株式分割前換算】年間比較参考、基準日未設定|

年間の通常欄は原文ダッシュのままで数値factを作らない。3件は別concept・definition・scope・columnで、中間/期末の合算、分割調整、支払又は分割実施確認、10月現在の最新予想認定、DDM配当列や評価入力への採用を行っていない。FY開始/終了日・会計基準・連結ラベルはnull、基準日をFY境界や年間参考へ転記していない。円銭合成のDecimal算術・原表示一致と、金融上の意味/採用の確認は別で、financial_inputs_verified:false・meaning_review_required:trueを保持する。

`generation-request.json`と先行入力の差分は、全3件の準備時processstate `scope.normalization_performed:false` の除去と、実生成直前のreview（author/recorded_at/rationale）更新だけ。原source全object/metadata/ID/内容は不変。機械差分6pathをgeneration.logに保存した。原取得2026-10-16T02:03:26.069103+00:00、原公表日2026-09-10・公表時刻nullを保持。新派生retrieved_at **2026-10-16T02:54:48.862530+00:00** は派生処理時刻であり、実DB firstsaveではない。DBへの接続/receipt操作はなく、原来歴を推定・遡及せず、新派生のactual firstsave/known-byは未登録。

実行: `.venv/bin/python .../generated/generate_once.py` のprimary生成1回。続いて `.venv/bin/python .../generated/reproduce.py > .../generated/reproduction.log` を1回実行した。同じnowで全文bundle/IDが一致し、既存reproducerでも原文hash matched・原snapshot matched_supplied_snapshotとなった。各成分token/半開位置、Decimal再合成、宣言field全保持、原文の文字/UTF-8位置、null/金融非採用、旧pin不変を検査した。再現検証では明示normalize replay1回に加えてreproducer内部の再構成を行うため、全検証呼出しをprimary生成1回と混同しない。全件suiteはこの資料生成では再実行していない（コード受入側で1534件成功済み）。

`generate_once.py` は既存出力があれば拒否し、失敗時の無条件再送をしない。`reproduce.py` は保存時刻での有限offline再現用。`generation.log`と`reproduction.log`は実行結果、`validation.json`と`manifest.json`は検証・SHAの固定記録。新GET/DB接続/旧成果物・production code変更/新予測/質問/価格判断は0。このbundleの実登録はrootの後段判断に委ねる。
