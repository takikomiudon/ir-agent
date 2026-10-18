# 8151 — QUICK表示パラメータの構造化候補

2026年9月25日QUICK企業価値研究所レポート（佐久間聰・園田三保）から3表示値だけを保存しました。原source ID `case-public:2469a802adda7396e6c4d0d235d11db39011a5d6077f37c6cd305007561640a4`、本文取得完了2026-10-15T10:11:43.240269Z、公表時刻nullを完全に保持しています。

| 表示 | 正規化 | 帰属・期間 |
| --- | --- | --- |
| EPS124.53円 | 124.53 JPY-per-share | 連26/9期予想。会社純利益予想2,600百万円を基礎にQUICKが算出 |
| CAPM7.0％ | 0.070 ratio | 26年8月の株主資本コスト推計 |
| CAPM直近12カ月平均6.3％ | 0.063 ratio | 原文の相対窓。開始/終了日を補完しない |

EPSを会社公表EPSやQUICK独自純利益予想として扱いません。`external_estimate`は第三者の1株値計算・資本コスト推計という表示の保存であり、モデル入力の採用ではありません。`review.author`は抽出担当者、predictor/calculatorはscopeに原文通り分離しました。表紙の連続引用はEPS(円)列、26/9期行、NI2,600と算出注記を含みます。CAPM引用は方法・26年8月・直近12カ月・推計にすぎないという注意を含みます。

WACC5.6%程度は値自体の対象時点が未確定なので除外しました。25/9期という利息入力の期やCAPM26年8月をWACCの時点に移植しません。リスクフリー/プレミアム/βの数値を補完せず、市場PER/PBRや等式をfair multipleへ変換しません。

[request.json](request.json)→既存normalize-factsのCLI parser/純粋dispatcherとlibrary replay→[bundle.json](bundle.json)を再現しました（実Store/DBなし）。原PDFのpdftotext-layout再抽出、表紙/p55画像、頁内/全体引用offset、Decimal/Fractionの値、原source snapshot・derived ID・原典からのreproduceを照合しています。[validation.json](validation.json)に実レビュー/派生時刻と未採用条件を保存しました。

既存Astris6項目は別source/vintageとして完全に残し、更新・平均・置換していません。新GET・DB・コード・旧file変更・将来予測/評価/IR質問の採用は0です。finance意味/適用割引率/予測精度/過去時点の利用可能性は未検証です。
