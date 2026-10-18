# 5988のnative定性case：登録前の固定入力

`case-register-input.json` は新case `5988-cost-tax-basis-monitor`／論点 `5988-cost-tax-cashflow-basis` の登録候補。expected-versionは0を想定するが、実登録・版衝突確認・現在の公開性/分類/来歴のAPI検証・queueはrootの後続作業。今回はStoreを起動していない。

元公式9sourceの実DB snapshotをSQLite mode=ro＋query_onlyで読み、旧保存bundleの8件と追加3Q1件が完全一致すること、native models.json_text SHAとDB保存data SHAが一致することを確認した。9件の既読は過去の限定レビューの引継ぎであり、PDF5件全文の再認定やHTML4件の全財務意味の認定ではない。現在の引継ぎ確認時刻をreviewed_atとし、古い公表・取得・初保存時刻へ遡らせていない。元ID/SHA・保存snapshot参照・読解範囲はreview-manifestへ保持した。保存済み派生1sourceとその他のderived pending群は対象外。

内部研究管理日は、2026-10-16のTokyo現地研究日から3暦月後の2027-01-16（Asia/Tokyo）。Anthropicの少なくとも四半期という研究手順への明示的適応であり、会社予定・反証期限・売却日ではない。新保存sourceは先にレビューを起票し得る。

追跡するのは減損/CFOの二重加算防止、過去の税負担と将来税/NOLの区別、会社固有の範囲/期間/定義の不足。既存closedを再調査せず、実際の新しい原文が得られた場合だけ変更箇所へ対応する。通常DCF適格、正常化利益、将来税、予測、数値方針、IR準備完了は認定しない。

新GET・実DB書込み・共有index/code/docs編集は0。tax-basis-reviewの全証跡SHAは不変。実行用CLI/Storeや一時DB登録の検証も今回は行っていない。rootがコピー事前検証と単一writerで受け入れるまで、file-only候補である。
