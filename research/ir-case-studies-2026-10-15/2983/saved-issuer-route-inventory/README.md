# 2983 アールプランナー：会社原資料への保存経路

**5種類の実経路を固定した。4PDF＋株式基本情報の入口で、本文取得・金融採用は0。** 目的は外部レポートのEPS・会社予想転載と、同期間の会社原表・会計範囲・株式基準を比較する前準備である。

| 種類／旧02.jsonの位置 | 保存labelの対象・日付 | 保存済みresolved URL |
|---|---|---|
| 2Q短信／`$.links[18]` | 2027年1月期第2四半期（中間期）決算短信〔日本基準〕(連結)、2026.09.10.15.09.00 | https://ir.arrplanner.co.jp/ja/ir/news/auto_20260909533539/pdfFile.pdf |
| 2Q説明／`$.links[17]` | 2027年1月期第2四半期決算説明資料、同日付表示 | https://ir.arrplanner.co.jp/ja/ir/news/auto_20260909533552/pdfFile.pdf |
| 中間差異・通期予想修正／`$.links[16]` | 2027年１月期第２四半期（中間期）連結業績予想と実績値との差異及び通期連結業績予想の修正、同日付表示 | https://ir.arrplanner.co.jp/ja/ir/news/auto_20260909533562/pdfFile.pdf |
| 半期報告書／`$.links[14]` | 第24期(2026/02/01-2027/01/31)、2026.09.10.17.09.00 | https://ir.arrplanner.co.jp/ja/ir/news/auto_20260910170900_S100Z1KP/pdfFile.pdf |
| 株式基本情報／`$.links[48]` | 対象期・基準日表示なし | https://ir.arrplanner.co.jp/ja/ir/stock/basic.html |

選択元は`research/ir-contacts-universe-2026-10-11/evidence/2983/20261011T062708648312Z/02.json`、SHA `5f3b01eb002fb7775cdd0315927847faa019738d055a31c47ae159fffbce33fa`。同dirの01／03／04／05と併せ**5snapshotで終了**した。4件がHTTP200の会社本文・links、05はweb.fisco.jpの旧robots停止recordで本文ではない。旧停止先は再開しない。同codeの他の保存fileは今回未読である。

02の申告取得は2026-10-11T06:27:23.839755+00:00、本文GET完了は06:27:29.007314+00:00。初回公表とは区別する。linklabel中の2026.09.10.15.09.00等はそのまま表示値として保持し、timezoneや精密公表時刻を補わない。「最新」認定も行わない。

選択5件には`href`キーがなく**保存済みresolved URLのみ**である。原HTMLのliteral href・位置や生HTMLを確認したとはしない。[routes.json](routes.json)へsnapshot SHA／text SHA／JSONpath／逐語labelとUnicode・UTF8位置を保持した。可視本文にlabelの`pdf`tokenがない箇所は、別の実在する可視text引用として位置を照合し、label全文の完全一致と偽装しない。01の同一URLなどの重複は別経路に数えない。

短信labelは日本基準・連結と明示するが、本文中の基準/範囲、正確な対象期、会社EPSの原表や分割注記は未読。説明資料labelにない会計範囲を同じだと補わない。半期報告書labelにある年度レンジを上半期の開始終了へ置き換えない。会社EPSの外部転載が原会社値か著者換算かは未確認のまま。

株式分割の直接告知URLはこの5snapshot内では未特定。FAQには1月末決算と1単元100株が説明されるが、単元株数を分割比率・分割日・EPS分母/調整状態にしない。株式基本情報入口や報告書に必要注記があるかも本文未読である。未特定を未公表・不存在へ広げない。

[中央7host保留](../../../ir-source-access-holds-2026-10-15/holds-v3.json)に選択先`ir.arrplanner.co.jp`はexact一致しなかったが、現robots・到達可能性・別hostへのredirect先は未確認。host変更・JS/API・URL構築や既知hold再開は0。親membershipの`individual_access: not_stated`を保持し、個人拒否や送信適格を認定しない。

次は別の有限作業でアクセス条件と実本文を確認し、対象期・単位・会計範囲・実績/会社予想・株式基準を照合する段階。著者レポートの別訂正は本記録へ取り込まない。新GET・DB・旧file/code/index/mon変更、IR、数値モデル・金融採用は0。追加物は本README／routes／validationのみ。pathはrepo-root基準。
