# 1963：Q1実績・当時会社予想の9表示を構造化

原短信の物理1/2/7を自分で画像確認し、Q1実績4件と2026-08-07時点会社予想5件を既存normalizerへ入力した。root受入済み原本の再表現であり、新会社開示や独立予測ではない。成果はfile-only、DB未投入。

| 種別・原表 | 直接表示 | 正規化単位 |
|---|---|---|
| Q1実績（2026-04-01〜06-30） | 売上159,299 / 営業12,355 / 親NI11,617百万円 | JPY実額へ各×1,000,000 |
| 同Q1通常EPS | 48.03円 | JPY-per-share。潜在株式調整後47.96とは別 |
| 当時FY会社予想（2026-04-01〜2027-03-31） | 売上670,000 / 営業40,000 / 親NI46,000百万円 | JPY実額へ各×1,000,000 |
| 同FY会社予想EPS | 190.25円 | JPY-per-share |
| 年間DPS会社予想・合計欄 | 52.00円 | JPY-per-share。期末欄/前年欄の同額tokenを選んでいない |

DPSは2027年3月期(予想)という年次labelのみ。start/end/配当基準日・GAAP・連結範囲はこの表だけで確認できずnullを保持し、利益表の期間・範囲を移植しない。利益予想/配当予想の修正無は当時の表示で、前回公表日やOctober最新予想を認定しない。配当支払開始予定日のdashも支払0や将来支払保証にしない。

物理2の新規連結1社JGC Emirates L.L.C-FZ・四半期固有処理有、期末発行済/自己株/期中平均の区別、物理7の為替差益3,882百万円が営業外という区分をscopeで保持した。親NI11,617と四半期NI11,624/税9,703/NCI7は別段階で、総額の丸め補正・正常利益/税/将来CFを作らない。新1社の機構/開始/寄与や当該処理詳細は未読のまま、organic成長や現在分母を補わない。

必須basis_quoteは全9factに保持。補足のsource_context_references27箇所は既存引用のpath/SHA/id/page/spanへ対応し、長文原文を9回複製していない。本文説明は同日決算概要へ案内され、公開説明/Q&A本文はまだ未取得であり会社未回答とは呼ばない。参照一致は内容の金融認証ではない。自身の画像再確認は1/2/7、物理4は既存root受入済みの案内引用参照だけ。原14頁の全冊読了にはしない。

[normalization-input.json](normalization-input.json)に原source全object/原文tokenと引用、[quotes.json](quotes.json)に9tokenのUnicode/UTF8位置・画像SHAを保存。[normalized-bundle.json](normalized-bundle.json)は無変更原source＋派生sourceの2件。表示は既存numeric decimal形式でraw_value_format未指定、normalization_version1のまま。原公表day/時刻null/取得終了を保ち、派生取得は今回の処理時刻とした。金融入力検証/採用はfalse。

生成はgenerate_once.pyを1回。reproduce.pyで同入力/同nowのbundle全JSONとID完全一致、既存reproducerはreproduced/matched_supplied_snapshot。9値を独立Decimal/明示倍率で照合し、原42fileのSHA不変を確認。DB/network関数は再現時に禁止patchを置いた。GET/DB接続/商品code/モデル/API新設・旧file編集・新IR/売買/金融採用は0。rootの独立意味レビューと実投入判断を待つ。
