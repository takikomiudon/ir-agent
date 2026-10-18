# 1866：公開確認後の残余準備票

**正式IR問・数値分岐は0。今IRを使う判断価値は未立証。** Anthropic DDの既知/懸念/比較/follow-upと、JIRA指針の公開先行・既答除外というproject適応を使う。原著者の売買ruleではなく、既存の採用予測・モデル・閾値不足も変えない。

| 論点 | 公開で閉じた範囲・再質問から除く部分 | 残る比較前提／変わり得る比較／owner |
|---|---|---|
| Q1実績・会社予想・分割 | 既知6fact、Q1と通期、Aug6観測/May12予想参照、既知の分割基準。汎用的な値・変更有無を再質問しない | 将来資料との同期間/同範囲比較は公開読解担当。予想の採用は投資家/著者方針担当で、会社への確認で自動採用しない |
| 受注・完成・繰越 | p11は**提出会社単独の建設部門**。契約変更増減を受注/完成に含む。表の有無・既載合計・この定義を再質問しない | 新規/取消/変更、地理/連結範囲、工期/採算/回収は未確認。判明すれば比較対象の対応が変わるが、EPS/利益率の数値変更は未許可。公開読解担当→残る会社定義のみissuer、金融仮定は投資家側 |
| セグメント利益 | 建設/ホテル利益は既読p4で公表済み。単独工事高と連結全社/segmentを混ぜない | 同一範囲・調整と原価/案件mixの比較は未確認。**保存p9は未読で、非開示ではない**。公開担当の別有限task候補だが今回は開かない |
| Q1 CF | p10の「当Q1連結CF計算書は作成していない」は確認済み。同短信のCF表の有無を再質問/再取得しない | **未作成は0ではない**。減価償却費・受注・繰越をCFへ置換しない。未成工事受入金/認識/回収との関係は公開読解担当、正常/将来CF・税の採用は別の著者方針担当 |

この票は新IR草案ではない。不明というだけで質問価値を認定せず、今後も既答を除外した上で、残る会社事実がどの採用入力/比較へ接続するかを別に立証する。受注≠売上、繰越≠利益保証、単独≠国内限定、前年Q1≠前quarter、実績≠会社計画を保持する。

## 次の正当なjobへの手動引継ぎ

[worker-handoff.json](worker-handoff.json)に受入済み追補のread_at・file/SHA・原source/native SHA、解消/残余、担当を固定した。旧case v2は過去観測で、将来のcase/CAS/lease権限ではない。rootが実際の新着または既存管理日の正当なjobで、当時の固定packetと票/追補を明示して渡す。今回source/config/管理日を変えてjobを作らない。

次担当は追補を既存原典の既知文脈として読み、**summaryとcase_observation.rationaleの両方**へ追補の時刻/path/SHA/原sourceと解消/残余を残す。source_reviewsだけでは次のprior_reviewへ要旨が渡らない。source_reviews/evidenceは実pendingだけ。管理日jobでpendingが空なら両方空で、旧追補だけからsupports/counterevidenceへ上げない。次回outcome/管理日は事前決定しない。

現コードは票や追補を自動探索/受領/typed evidence検証しない。rootと独立担当が実読・意味・既知と新観測の区分を完了前に確認する。結果SHAの保証と追補受領の保証は別である。[受入済み1870設計](../../../ir-1870-additional-reading-native-handoff-design-2026-10-16/README.md)とroles.mdの追加読解節を参照した。

入力20fileのSHAと5quoteの原全文offset、原sourceと保存case v2のnative SHA一致をfile-onlyで照合し、元file変更0。新PDF頁/GET/DB/normalizer/金融値・採用/新question・分岐/共有file/現native書込みは0。

worker-handoff SHA: `5fc2c55ffc75512d49823336ef37f3d83e2e611c0b33f6961c98be65e3a3d5e8`。親受入待ちでfreezeする。
