# 1723 日本電技：保存済み会社資料の入口

**実経路は2種類。1Q短信・説明資料・Q&Aの直接URLは、指定された旧3snapshot内では未特定。** 新GET・DB・金融本文読解は0。

| 保存label | 保存済みresolved URL | この段階で分かること |
|---|---|---|
| IR資料室 | https://www.nihondengi.co.jp/ir/data/ | 公式資料室への入口。同じ27.3期1Qの個別資料・対象期・日付・本文は未確認 |
| IRニュース | https://www.nihondengi.co.jp/ir/news/ | 公式IRニュースへの入口。同じ1Qの具体的な告知・原本は未確認 |

優先根拠は`research/ir-contacts-universe-2026-10-11/evidence/1723/02.json`の`$.links[35]`と`$.links[39]`。同じ経路は01／02の複数のナビゲーションにも存在し、重複を別種類に数えない。03は外部フォームの保存ページで、会社財務資料の原本にしない。[routes.json](routes.json)に3captureのbyteSHA・textSHA・申告取得時刻、選択リンクのJSONpath・逐語label・Unicode／UTF8位置を保持した。これらの旧captureにはGET完了時刻と`href`キーがないため、それぞれnullのままとし、resolved URLをliteral hrefや原HTML上の位置とは呼ばない。原HTMLrawの欠損は回復していない。

02の別labelには「7月 第1四半期決算発表」等の一般年間カレンダーがあるが、年・FY・具体日は示されていない。著者が述べるJuly24や27.3期1Qに割り当てず、今回の候補を埋めるため追加しなかった。`経営計画`・`業績ハイライト`も、同期間の原資料が特定されたことにはしない。最大5種類の上限に対し、直接必要な2入口で閉じる。

[中央7host保留](../../../ir-source-access-holds-2026-10-15/holds-v3.json)とexact hostnameで照合し、選択先の`www.nihondengi.co.jp`は一致しなかった。現在のrobots・到達可能性を確認したことではない。既知失敗の再試行・別host・JS/API・URL構築は0。

親の[parent-target-membership.json](../parent-target-membership.json)を帰属確認の保存receiptとして参照した。台帳の`individual_access: not_stated`は個人受付の明示なしで、拒否や現在の送信適格を意味しない。receipt当時のDB件数を現状へ延長しない。Envalithの著者仮説は本成果でケース化せず、会社の数値・定義・期が未確認のまま比較や金融採用に進めない。

次に進む場合は、選択入口のアクセス条件を別の有限作業で確認し、そこに実表示された同期間の原資料リンクをたどる。今回の未特定を未公表とせず、別担当の取得状況や現在Web全体の不存在も断定しない。追加物はroutes／本README／validationのみ。pathはrepo-root基準、引用位置は指定保存JSON文字列の半開区間。
