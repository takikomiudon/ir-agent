# 公表Q&A抽出v2：会議日と公開日を分離

IIJの原h2は「2026年8月7日：2027年3月期 第1四半期 決算説明会（オンライン開催）」という**会議日表示**です。公開日の独立した裏付けはなく、snapshotのpublication_timeもnullです。旧metadataのpublication_date=2026-08-07は値を残しますが、旧派生ラベルを公開日の証明として使いません。実際の公開日・公開時刻はunknown/nullです。

`input-cases-v2.json`ではpublic-qa-03/04の範囲説明2箇所だけを「公表表示」から「会議日表示」へ訂正しました。6組の質問・回答、18quote spans、sourceIDs、数字、source版、元の取得/完了clock、要旨注記・FY26定義は完全に維持しています。

| case | 原典 | 質問内容 |
|---|---|---|
| public-qa-01 | IIJ財務FAQ Q4 | IFRS16リース適用の影響 |
| public-qa-02 | IIJ財務FAQ Q9 | 2027年3月期の見通し |
| public-qa-03 | IIJ決算Q&A要旨・掲載順4 | コンピュータ部品価格高騰の業績影響 |
| public-qa-04 | IIJ決算Q&A要旨・掲載順6 | PTC GPU案件の運用フェーズ収益性 |
| public-qa-05 | リックス公開FAQ・掲載順2 | 決算発表時期 |
| public-qa-06 | リックス公開FAQ・掲載順5 | 売買単位 |

IIJは会社が公表したQA要旨であり、実発言の逐語録・我々が送ったIRへの返信・当時の事前予測・投資成績ではありません。FAQも実投資家の発言を実証する資料とは扱いません。パイオラックス0組は有限保存資料の範囲で未特定という結論のままです。

訂正版の実作成時刻は **2026-10-15T12:30:15.253646+00:00**、初回抽出時刻は **2026-10-15T12:25:57.798284+00:00** とrevision provenanceで分けました。旧4ファイルと元sourceは変更していません。`source-manifest-v2.json`へ原h2のSHA/位置と未検証の公開日を記録、`validation-v2.json`で2labelのみのcase差分と全18span/旧4SHA/旧source不変を点検しました。正解鍵・評価・preview更新はなく、GET/DB/code/送信0です。
