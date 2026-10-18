# 岩井NO335残り6社：会社決算資料への保存済み経路

**5社に会社の資料入口が残り、6754にはPDF hrefもある。8725は既知robots403で停止した経路を再開候補にしない。** 新GET・JS/API・DB・code・既存file変更は0。今回6社の財務本文を取得/確認したという意味ではない。

| 会社 | 過去窓口台帳 | 保存された経路 | 次に有限確認できる範囲（未実行） |
|---|---|---|---|
| 290A | confirmed / 個人受付not_stated | 短信/説明資料一覧への保存resolved URL。href原値は未保存 | 指定一覧1URL。動的/文書未特定なら停止 |
| 6080 | confirmed / 個人受付not_stated | 決算説明資料・決算短信一覧のliteral href | 指定一覧1URL。動的/文書未特定なら停止 |
| 6754 | provisional / 個人受付not_stated | 短信IFRS/説明/ノート付/Q&Aの4PDFと資料一覧のliteral href | 1本のQ&A PDFのみ、本文で対象期を確認 |
| 7741 | confirmed / 個人受付not_stated | IR資料室literal href。決算一覧本文は未確認 | 指定一覧1URL。動的/文書未特定なら停止 |
| 8252 | confirmed / 個人受付not_stated | 決算説明/短信一覧literal href。異なる期の見出しが同じ一覧へ | 指定一覧1URL。動的/文書未特定なら停止 |
| 8725 | unconfirmed / 個人受付not_stated | 本文なし。ホーム前のrobots403、中央7host非掲載でも再試行しない | 既知negativeを維持、候補なし |

全6社は窓口台帳内。290A/6080/7741/8252は過去confirmed、6754はprovisional（form link）、8725はunconfirmed。現在の受付や個人適格性へ格上げしない。

選択したlegacy snapshotは原HTML/rawへの参照を持たないため、厳密な保存anchor位置はfile SHA＋JSONpathで示す。6080/6754/7741/8252にはhref原値があり、保存baseからのresolveを照合した。290Aはurl/labelのみであり、原hrefやHTML offsetを復元しない。レスポンスSHAの自己申告をraw bytesの独立照合と呼ばない。

選択11経路のexact URLは、指定した原台帳evidence/attempt＋8725既知recoveryの有限集合では本文未取得。全repo/Webに存在しないという証明ではない。各経路hostは中央7hostに非該当だが、robots許可の認証ではない。特に8725の保存403は別に尊重する。

6754のQ&A入口labelは「2027年3月期第1四半期」。PDF名のfy2026/260731から対象期を推測せず、本文で後日確認する。8252のFY2027/3Q1とFY2026/3通期labelは同じ一覧に向いており、各本文を取得したとはしない。

[routes.json](routes.json)に会社ごとの過去窓口・11anchorの元snapshot SHA/JSONpath/href/url・取得済み照合・host境界・1件ずつの有限次読取を保存。[validation.json](validation.json)に参照と入力不変の確認を保存。author条件抽出は別担当で、ここでは著者予想/期/目標評価を補わない。この3fileを固定し以後編集しない。
