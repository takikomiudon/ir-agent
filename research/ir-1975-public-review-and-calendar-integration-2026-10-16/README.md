# 1975の公開比較・実台帳レビュー・予定の接続

JPX公表結果と個人IR受付記録の交差23社の接続例として、既存1975 caseを進めた。投資順位や売買判断の採用ではない。

- [公開資料の追加読解](../ir-case-studies-2026-10-15/1975/backlog-and-full-year-input-followup-2026-10-16/README.md)で施設別繰越高と通期会社計画を確認した。
- [8月6日説明会資料33頁](../ir-case-studies-2026-10-15/1975/public-qa-presentation-followup-2026-10-16/README.md)では連結繰越高117,864百万円を確認。施設別表110,795とは範囲を同一視せず、差額・利益・回収を補わない。
- [calendar/PDFの新2sourceを実保存・分類](../ir-case-studies-2026-10-15/1975/public-source-calendar-and-presentation-connection-2026-10-16/actual-verification.json)し、[定性比較](../ir-case-studies-2026-10-15/1975/public-source-calendar-and-presentation-connection-2026-10-16/qualitative-review/actual-verification.json)を完了。旧条件IDを保ちnative v2/config1・既読6へ進めた。管理日2027-01-16を維持し再queue0。
- [実DBに対する予定レポート](../ir-case-studies-2026-10-15/1975/catalyst-schedule-connection-2026-10-16/actual-report/parent-acceptance.json)は4予定を原典へ結合した。時刻・timezone不明のためdue:null、実施未確認で、売却時期ではない。
- [NCAV会計入力](../ir-case-studies-2026-10-15/1975/ncav-accounting-input-review-2026-10-16/parent-acceptance.json)と[株数換算](../ir-case-studies-2026-10-15/1975/ncav-per-share-input-bridge-2026-10-16/parent-acceptance.json)はfile-onlyの数値条件再現。現在価格との合否、金融モデル・policy・質問・売買への採用はしていない。

[09:05UTCの読取専用状態確認](readonly-verification.json)では212資料/分類211、全119job完了、native26case/49版/151既読。金融thesis・明示保有・実policy・正式質問・返信・判断履歴は0。旧27tableの全行とschemaを保った追加処理は実batchの検証に記録した。索引v37の210/25/47/144は過去のsnapshotとして保持する。

before-*は今回の共有文書更新前の全bytes。新source候補の事前firstsave:null、旧native v1、古い状態報告、完了済みmutatorは書き換えず、再実行しない。共有コードは固定44pinとの不変照合を行う。次の作業は[研究ベースライン](../../docs/research-baseline.md)と[継続状態](../../docs/ongoing-work.md)に記す。
