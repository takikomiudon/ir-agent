# 7325 保存済み会社原本の経路棚卸し

既存の7325証跡JSONを**5件だけ**読み、会社の保険クリニック事業と会社概要へのliteral linkを2件選んだ。[経路・引用・有限取得計画](route-inventory.json)と[照合記録](validation.json)に、元ファイルSHA、link配列位置、literal href、解決済みURLを保存した。新GETや実DBアクセスは行っていない。

保存済み公式TOP本文には、保険ショップ『保険クリニック』の運営と保険選び支援、保険販売事業者向けソリューション、グループ会社でのシステム/AI-OCR事業が明記されている。同hostの株式情報本文に証券コード7325がある。これらの逐語引用はJSON `/text` 値に対する文字・UTF8 byte offset付きで保存した。昔のsnapshotの `official_identity_basis: third_party_unverified` は改変せず、今回の同host会社名/証券コード照合を別記録にした。

この保存本文だけでは、代理店の登録・手数料契約と収益構成、グループ全体の引受責任の有無、規制資本の適用主体を確定していない。「保険業」という業種タグから引受会社や規制資本FCFEモデルを自動決定せず、モデル選択は未解決のまま保持する。投資順位付けも行っていない。

保存時系列には初回TOP/robots503、その後のcircuit-breaker、後日のTOP/robots200が共存する。旧失敗を消したり失敗TOPを再開したりしていない。候補host `www.irrc.co.jp` は中央v3の7 exact-host holdに該当せず、保存済みrobots200は `/wp-admin/` 禁止を含み固定UAで両候補pathを許すが、2026-10-11時点の記録であり現在の許可ではない。新規原本候補の本文は未取得。

主担当が取得する場合の計画は、fresh robots1件と `https://www.irrc.co.jp/business/insurancesales.html` 1件の計2GET、全体上限3GET・会社原本1件・意味確認最大3頁相当（HTMLは同一文書の明示的な最大3事業説明block）。余り1GETは再試行や探索の許可ではない。会社概要候補は今回の自動fallbackにしない。robots/transport/TLS/redirect/拒否時は停止し、本文で定義を確認できない場合も未解決でこの有限経路を閉じる。UA変更・JS/API推測・別host回避は行わない。

原snapshot変更、実DB書込み、金融入力採用、共用docs編集、外部送信・発注は0。
