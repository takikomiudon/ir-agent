# 2983 純利益の英語単位キーだけの訂正

旧固定 `review.json` の2キーは原単位「10億円」に対し `10billion_JPY` と誤記していた。原単位の1表示単位は **1,000,000,000 JPY＝1 billion JPY** であり、英語ラベルだけが10倍違う。印字値・元資料・引用・作者帰属は正しい。

| 旧キー（誤ラベル） | 有効な解釈キー | 値（不変） |
|---|---|---|
|company_plan_as_reported_NI_10billion_JPY|company_plan_as_reported_NI_billion_JPY|3.25|
|author_new_NI_10billion_JPY|author_new_NI_billion_JPY|3.28|

両キーは `$.forecast_capability.visible_company_vs_author_example` 内。旧ファイルのキーは消去せず、この訂正を重ねて単位を読む。独立指摘 `2983-R01-NI-unit-key`（independent-recheck.json SHA256 856647d85b733bfa0198f7e6512a20b14a416e425f940f8d524fed2c5e34c1b0）への限定対応である。

既存p4会社計画表見出しとp8著者純利益行の固定引用を再利用した。元PDFの再精読や財務全体の再監査はしていない。2983保存テキスト中の誤英語キー完全一致を機械確認すると、旧reviewと独立findingの参照だけに現れた。別の固定caseへの訂正は不要。

旧ファイル全件のSHA、原source ID、3.25/3.28とEPS308.31/339.81/369.46を保持した。新しい取得・正規化・source ID生成・DB/Store・モデル採用・IR草案/送信は0。実訂正記録時刻はJSONのrecorded_atに別記し、旧研究作成時刻を変更していない。
