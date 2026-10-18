# 7325 保険販売事業とモデル点検範囲

会社公式「保険販売事業」HTMLの保存原本から、指定された3blockだけを意味確認した。[原source1件](source-only-bundle.json)、[逐語引用3件](quotes.json)、[論点記録](case-record.json)、[検証記録](validation.json)を保存した。論点IDは `7325-business-and-model-scope`。robotsは取得可否の証跡であり、会社事業sourceには含めない。

会社は、保険ショップ直営店で独自の保険分析・検索システムを使った保険選択支援を行い、FC店へ比較推奨・送客・教育・運営指導等を提供すると説明している。末尾の4事業紹介は保険クリニック、販売事業者向けソリューション、FA、グループ会社のシステム/AI-OCRを含む。FC店舗数等の記述は原文のまま残し、売上・利益や成長予測へ使っていない。

この会社説明だけでは、グループ全体の引受責任がないこと、手数料認識、規制資本の適用主体、負債の営業上の役割、通常事業モデルへの適合を確定できない。採用済み[Damodaran研究routing](../../../valuation-model-routing-2026-10-15/routing.json)に従い、会社根拠と方法参照を分け、業種名「保険業」から銀行型の規制資本FCFE適用や一括除外へ進めない。これは既存方針の研究適応であり、Damodaran自身が7325を判断したという主張ではない。モデル選択は未解決。

会社原本はHTTP200、本文完了 **2026-10-15T20:06:17.141819+00:00**。`retrieved_at` はこの時刻、公表日/時刻は不明のため `published_at: null` とし、1999年等の事業説明年を公表日へ転用しない。historical first saveも不明のまま保持する。HTML response entity raw SHAと保存UTF8本文SHAを分け、既存抽出器によるraw→本文の完全再現と全引用の文字/byte offsetを確認した。意味確認は3blockに限り、全文の機械抽出を全体の意味レビューとは扱わない。

主担当が既に行った取得はfresh robotsと事業HTMLの2GET。今回の成果物作成では追加GET・実DBアクセス/書込み・既存capture/raw/text変更・モデル採用・数値予測・倍率・投資action・IR質問・外部送信・発注は0。主担当の最終受入後のDB保存は別作業。具体的な金融/segment定義がモデル採用等に必要となった場合に、別の有限タスクとして会社財務原本を確認する計画だけを残し、新しい取得は行っていない。

主担当の[受入](parent-acceptance.json)後、原source1件を[実保存・分類](actual-completion.json)し、case `7325-business-model-scope-monitor` へ既読1件と2027-01-16 Tokyoの研究管理日を登録した。全14case・18版・69既読、実DB123資料/分類122/完了job55、今回queue0はこの時点の結果。保存前のpreflightでproducer compact JSON SHAとnative snapshot SHAの違いを検出し、原source不変のまま[対応記録](hash-domain-bindings.json)と[case v2](case-record-v2.json)を採用した。旧v1を保持し、誤ったdigestでのDB登録や二重取得はない。[独立点検](independent-recheck.md)は80項目・指摘0で、二つのhash domain・3blockの意味と旧row保持を確認した。
