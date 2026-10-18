# 1904：分割前後の配当3表示は現APIで一式の数値factにできない

**有限結論は現APIで忠実な3数値factの構造化不可。normalized-bundle・派生source・金融採用は0。** p2原図、2頁全文、7引用、親受入と定性比較の観測を確認した。3表示は `raw-display-candidates.json` に原表示・概念・基準・場所を保って記録したが、normalizer bundle/API入力/モデル入力ではない。

| 今回修正の会社表示 | 意味 | 既存normalizerの境界 |
|---|---|---|
| 中間99円00銭 | 2026-09-30基準、分割前株数、予想 | 整数token99と00銭なら同額を表せる余地はあるが、今回は部分的な数値抽出をしていない |
| 期末24円75銭 | 2027-03-31基準、分割後株数、予想 | 原文は`24 円 75 銭`。単一数値token`24.75`がなく、円銭複合表示/銭→JPYの既存mappingもない |
| 【分割前換算】年間198円00銭 | 会社が直接示す比較参考表示 | 整数token198と00銭は表現可能な余地があるが、通常の現在年間DPSや投資家計算値ではない。今回は数値抽出しない |

既存normalizerは原quoteに存在する単一のstrict numeric tokenと、固定のunit multiplierを検査する。`24.75`を連結して原tokenと呼ぶと実際にValueErrorで拒否される（normalizer-boundary.log）。`24`だけでは75銭を失い、scopeに原表示を書いても数値24が正しくなるわけではない。1518の00銭整数例を非ゼロ銭へ一般化しない。値が公表されているのにmissing/nullのfactへ置き換える方法も使わない。

raw候補のcanonical_numeric_value=nullは「正規化未実施」の印で、会社の値の欠損を意味しない。`unsupported-token-probe.json` は拒否検証専用の意図的な不適合入力で、実抽出/ingest入力ではない。原sourceを完全copyし、`reproduce_boundary.py` をDB/GETなしで1回実行して、token不在という予定どおりの拒否を確認した。新しいAPI・parser・unit mappingは追加していない。

会社は今回の年間欄を`－（注 3）`とし、単純合計ができないと説明する。dashを0や欠落値の推計へ変換せず、中間と期末を足さず、分割前参考198をDDM配当列や現在annualDPSへ採用しない。予想の記載は支払い完了の証拠ではない。分割日程の経過を独立の実施確認にもしない。

FYは2027年3月期という表示を保持するが、同sourceに正確な年度開始/終了日が印字されていないためstart_date/end_dateはnull。注1/2の配当基準日は年度境界とは別fieldで保持する。GAAP/連結ラベルもnullとし、Q1短信から補わない。新しい比率計算、99の分割調整、配当足算、EPS/株数/利回り/評価は0。

原sourceは `case-public:d5515999569e0a44d30c01701d683bb136b302cc8166a9374e625fe753b23d83` の全objectをそのまま使用。公表日2026-09-10・exact時刻不明のpublished_at:null、取得時刻、metadata、本文を変更していない。raw/text/transport・原snapshotのSHA、p2 quote/3表示の文字/UTF8位置と画像SHAをsource-reference/quote/candidates/validationへ記録。原定性caseのunresolvedと未解決の現在分母/寄与/正常利益等を更新していない。

元通知・既存6factのfile SHA不変。新GET・DB接続・実index/旧file/production/共有変更・金融採用は0。結果はfile-onlyの限界記録としてfreezeし、追加研究は始めずここで終了する。
