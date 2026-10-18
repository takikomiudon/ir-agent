# 個人受付未記載1,476社の保存済み著者レポート経路

**5社・5実URLを研究候補として固定した。対象本文の取得・読解は0。** これは著者自身の予測や評価式へ進めるかを調べる入口であり、金融入力・投資順位・IR送信適格の判定ではない。

| コード・会社 | 保存公式ページの著者ラベル | 保存済みresolved URLと範囲 |
|---|---|---|
| 1723 日本電技 | エンヴァリスによる当社調査レポート | https://envalith.com/ja/companies/1723 — 会社別entry、原本未読 |
| 1980 ダイダン | QUICK & NOMURA コーポレート・リサーチ | https://www.nomura-ir.co.jp/ja/qnresearch/report_1980.html — 会社別entry、原本未読 |
| 2134 北浜キャピタルパートナーズ | ジェイ・フェニックス・リサーチ株式会社 | `2134-remaining-catalog-author-route-32` — 2026年8月24日公開告知PDFの長い実URLを[routes.json](routes.json)へ保存。レポート本体やその公表日とは未確認 |
| 2983 アールプランナー | アストリス | https://corporateresearch.astrisadvisory.com/ja/arrplanner — labelと会社別research entryのみ確認。本文の役割・予測・式は未知 |
| 3023 ラサ商事 | フィスコ社・企業調査レポート・2026年7月15日発表 | https://www.rasaco.co.jp/pdf/ir/library07/20260715.pdf — 保存公式labelが示す個別PDF、原本未読 |

台帳1,819社から[旧other-author探索](../ir-author-report-routing-other-authors-2026-10-15/routes.json)の個人受付explicit343社を除いた**1,476社すべてを列挙**した。全社の`individual_access`は`not_stated`。個人受付の明示がないという台帳上の状態であり、個人拒否が確認された会社ではない。研究候補に含めても、現在の個人受付・静粛期間・送信適格は未確認のまま。

Oct11／Oct13の指定evidenceだけをコード・path順に走査した。既存case／岩井コスモ既検討のうち残母集団内12社（1332、1375、1379、141A、1444、290A、3774、6080、6323、6754、7741、8252）は意図的skipし、未調査とは呼ばない。残る保存JSON9,063件を読み、1,417社で公式host・HTTP200本文を検索、47社は該当する保存本文がなくunknown。15,000 JSONの上限未到達で、上限による未走査は0。旧343社の検索再開は0。会社別の列挙数・読取数・対象本文数・skip／未確認はJSONに保持する。

旧探索と同じ別著者・一般reportキーワード、および旧ラベル由来のQUICK／野村IR／Astrisの手掛かりを再利用した。部分一致のプロセッサー、株価情報リンク、一般アナリスト一覧、自社サービス・自社方針の「企業価値」を外部企業レポートにしない。1905のようにFISCO名があっても個別原本が特定されないissuerアナリスト資料一覧は今回の5経路に含めなかった。5社・8URLは上限であり、今回は個別性の確認できた5社・5URLで閉じる。後続の機械一致を全件意味精査した、他にレポートが存在しない、という主張はしない。

[中央holds-v3](../ir-source-access-holds-2026-10-15/holds-v3.json)の7 exact hostとSharedResearch経路は取得候補から除外した。wildcard禁止、robots403で規則未知、AI個別禁止に基づく運用保留は異なる理由のまま保持し、host変更や既知負ルートの再試行をしない。会社の投資除外とは別である。選択5URLが既知holdにないことは、現時点の取得許可や到達可能性を確認したことではない。

選択5件はすべて旧snapshotに`href`キーがなく、**保存済みresolved URLのみ**。literal href、原HTML上の位置、当時の生HTMLを確認したとは呼ばない。snapshot byteSHA、保存textSHA、`$.links[index]`、逐語label・保存文字列中のUnicode／UTF8位置を保持する。labelが本文にない2983はlabel自体の引用に限定する。旧`retrieved_at`は申告取得時刻として保持し、GET完了欄がない1723／1980／2134を完了時刻へ付け替えない。

全9,063旧snapshotのhash一覧を作る作業は行わず、選別入力と選択5snapshotの再現性だけを[validation.json](validation.json)で確認した。author本人、独自業績予測、会社予想の転載、評価式・target・報酬・対象期・最新性は全候補で未確認。新GET、DB、旧file／code／index／monitor変更、質問草案、金融採用、送信、注文は0。次の原本確認を別の有限作業として行う場合も、この保存経路と現在のアクセス条件の確認が必要になる。

追加物は本README／routes／validationの3ファイルだけ。新しい根拠pathはrepo-root基準。CSVの元source_record絶対pathだけは申告値を別fieldへ保持し、repo相対pathを併記した。
