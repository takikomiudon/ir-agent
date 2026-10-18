# 5988の監視登録と構造化4資料の起票

受入済みknown-by修正後、一時DBで元の9原本bootstrap入力を再検証し、実台帳へcase5988-cost-tax-basis-monitorを登録した。旧8原本は検証済みpresence以後の読解として引き継ぎ、正確な初回保存が判明したとは扱わない。元の9件入力・レビューmanifest・旧v1失敗/v2保留の証跡を改変していない。

[コピー検証](shadow-preflight.json)と[実適用](actual-completion.json)は、case1件・既読9件の登録、4つの構造化sourceだけをpendingに持つjob1件の起票を確認した。元全tableの全旧行を保持し、追加はqualitative_case_versions1行とpending job1行だけ。資料・分類・receipt・金融thesis・policy・質問・保有状態は不変。

登録時点でnative監視は16case/20版/79既読。EPS/DPS、年度末BPS、6月末book measures、税注記の4sourceは自動既読化せず、新しいjobで著者条件との比較を行う。管理日2027-01-16 Asia/Tokyoは内部研究日で、会社予定や売却期限ではない。

本書のpending状態は登録時点の記録。後続の比較完了は[10社の固定packetと処理記録](../../../../ir-structured-facts-qualitative-review-2026-10-15/claims.json)及び実台帳を読む。新GET/実送信/金融入力採用は0。
