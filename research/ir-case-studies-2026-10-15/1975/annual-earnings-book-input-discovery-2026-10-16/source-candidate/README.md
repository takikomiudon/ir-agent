# 通期短信 source-only 候補1件

既存 `scripts/build_case_source_bundle.py` の契約だけで、朝日工業社2026年3月期連結決算短信を1sourceへ変換した。`source-only-bundle.json` はcompanies/theses空、source1件。共有builder・DB・Store・旧folder内容は変更していない。

公表日は実表紙と公式libraryの **2026-05-14（日精度）**。`published_at:null`、取得は元PDF本文完了 `2026-10-16T09:25:36.353470+00:00`、実DBfirstsaveはnull。HTTPDate/LastModifiedや読み直し時刻を公表時刻/保存時刻へ転用していない。

PDF原本300,823bytes、16頁全文textを同一バイトで保存。意味確認は物理1/2/7/15のみ、13引用のUnicode/UTF8位置と頁を照合した。通期実績EPS358.13円・BPS1,965.51円、普通株式に係る親会社利益9,240百万円・純資産50,858百万円、年間平均25,802,361株、期末発行済27,200,000株・自己株1,324,317株の根拠を保持。金額切捨て・注記千株表示・直接表示値を混同せず、日本基準の株主資本44,745百万円を無条件に英語StockholdersEquityへmappingしない。

`requires_research:true` と金融入力verified/adopted=falseを維持。intake分類・normalize・Graham計算・仮説更新・IR反映は0。候補source IDとnative snapshot SHAは `validation.json`。rootの画像/引用確認と実保存・intakeを待つ。
