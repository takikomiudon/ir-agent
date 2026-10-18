v2について、2983-DF-R01-multi-origin-scopeの限定解消を確認しました。旧v1と旧指摘は変更していません。

派生factから短信の日本基準・予想照合・切捨て参照を外し、accounting_basisはnull、期間根拠は正式修正通知だけになっています。短信情報はsupplemental-review-only.jsonへ退避され、元v1 inputのSHAと結び付いています。派生content/metadataの実source参照は修正通知に限定されています。

2値・単位・通期期間・元修正通知source・引用・株式分割注記は維持され、既存APIの全出力の再現、native reproduction、Decimal換算、引用位置の照合に合格しました。新派生IDはdisclosed-facts:4e8f7dcb7903ca58074646fd7ff2e6d784ac23b881165cbbd513b393ae0fd644です。追加の実不一致は0件です。

元p1の既確認結果を再利用し、追加ページ意味読取、画像閲覧、PDF描画、GET、DB/Store、コード、旧ファイル、index/monitorの変更は0件です。v2元5files、v1元6files、旧独立記録2filesのSHAを保全しました。会社/著者EPS分母、最新性、金融モデル採用やDB108/補助資料の実DB状況は認定していません。

固定時刻(UTC): 2026-10-15T17:29:06.658984+00:00
