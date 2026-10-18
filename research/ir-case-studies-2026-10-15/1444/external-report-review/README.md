# 1444 ニッソウ：保存経路を確認、既知host保留でGET0終了

旧候補の会社公式ページ `evidence/1444/01.json` のSHAと `$.links[104]` を照合しました。表題「FISCO：企業調査レポート」の実URLは <https://web.fisco.jp/platform/companies/0144400/report> で、**提供者の一覧への経路**です。直接PDFではなく、旧JSONはoriginal hrefを保持していないため保存resolved URLをそのまま用います。

最初に既知5hostのholds索引を照合した結果、`web.fisco.jp` は同日保存のrobots403で規則不明として取得保留中でした。既存robots capture/rawSHA・完了時刻・403原文引用を再照合し、**新GET0件**で終了しました。robots403は対象一覧やレポート本文403でも、全パスDisallow確認でもありません。UA/host変更・別提供経路・再要求・接続診断は行っていません。

旧候補記録は本文未読で、1444の既読本文を持つ専用caseも今回の確認範囲ではありません。作者個人・報酬・時点・独自EPS/利益と会社予想転載の別・目標価格・採用倍率/評価式・反証/期限は本文未取得のunknownです。項目不存在や、数値評価モデルを再現可能/不可能と確定した扱いにはしません。

`review.json`に公式経路・holds・原robots引用のpath/offset/SHAを保存、旧5ファイル不変を`validation.json`へ記録。新sourceはなく、fullschemaのsource-bundleは空配列です。未取得PDFのretrieved_at/公表時刻は作りません。旧窓口のindividual_accessはnot_statedで、explicitや現在送信適格性へ昇格していません。DB/code/旧資料変更・新予測/価格/閾値・モデル・IR草案/送信は0、この限定確認で完了します。
