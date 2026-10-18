# 1904 分割配当・円銭原表示の入力準備

状態は **入力票のみ・生成待ち**。受入済みの旧raw候補3件と原通知p2画像・全7引用、保存済みnative case v3を再読した。normalizer/APIは実行しておらず、数値fact・bundle・派生sourceは作成していない。固定したparser設計のみを参照し、編集中の実装コードは読取・依存していない。独立実装レビューと全件検証をrootが受け入れ、別途生成を指示するまで実行しない。

|原表示そのままのraw_value|列・意味|原注記の基準日|
|---|---|---|
|99 円 00 銭|今回修正・中間、分割前株式数基準|2026-09-30|
|24 円 75 銭|今回修正・期末、分割後株式数基準|2027-03-31|
|198 円 00 銭|今回修正・年間の会社表示【本株式分割前換算】参考|未設定|

3件を別concept/definition/scope/columnとし、任意指定`raw_value_format: jpy_yen_sen`、原単位`円`、指定単位`JPY-per-share`を置いた。raw_valueは数と円銭の連続部分だけで、注1/注2や括弧はbasis_quoteと位置に残す。quoteと各表示に文字・UTF-8 byteの半開区間、元p2画像SHAを付ける。通常の年間欄は`－（注 3）`、注3中の表記は`―`であり、0にも3件目の通常年間値にも変えない。中間と期末は合算しない。

FYは原ラベル2027年3月期だけを保持し、開始日/終了日・会計基準・連結範囲はnull。中間/期末の基準日はFY境界へ転用せず、年間参考へ期末基準日をコピーしない。9月10日の会社予想・会社参考表示であり、支払済み・分割実施済み・10月現在の最新予想・DDM配当列の確認ではない。金融入力/モデル/数値thesis/質問への採用はない。

`normalization-input.json`は将来実行用の宣言入力、`quotes.json`は逐語原文と位置、`source-reference.json`は元source全objectと原取得/原本/transport/現case/設計・旧成果物のpin、`input-validation.json`は本段階のローカル照合だけを記録する。原source全object/metadata/ID/取得時刻は同一、今回の準備時刻を原取得や実DB firstsaveとしない。case v3は過去の保存観測であり、次jobの権限ではない。未解決の現在EPS分母や取得寄与/正常CFを解消していない。

1904 sixfactの元bundle・入力・manifest・reproduce・そのmanifest内の旧codeSHAを固定した。旧raw候補で記録した当時APIの限界も過去記録のまま保持した。新GET/DB接続/コード・旧成果物変更/数値合成は0。検証はファイルhash、source object一致、逐語substring、表示位置、列・注記・null境界に限り、新parserによる受理や再現成功は主張しない。
