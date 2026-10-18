# 2983 会社修正予想2項目の構造化

2026年9月10日付の正式修正通知p1「今回修正予想（B）」から、通期EPS **304.27 JPY/share** と親会社株主に帰属する当期純利益 **3,250百万円 → 3,250,000,000 JPY** の2factだけを既存`normalize_disclosed_facts`で構造化した。両方`issuer_guidance`。対象期は修正通知に明記された2026年2月1日〜2027年1月31日、連結。会社の予想であり実績や著者自身の予測ではない。Astrisの308.31円等の既存factsは不変。

EPSは原表の「円 銭」欄のdecimal token `304.27`。既存の円→JPY-per-share係数1を使い、空白を含む元複合ヘッダは引用/scopeへ保持した。純利益は百万円→JPY係数1,000,000のみ。表示単位の換算を会社内部予測の1円精度としない。

同p1の注記は2026年2月1日の普通株式1株→2株、前連結会計年度の期首に分割したと仮定した1株当たり当期純利益と明示する。これは会社の当該注記の適用であり、期末株数・中間平均・NIから将来EPS分母を逆算しない。AstrisのEPS基準へも移さない。会社が予測の原作者、review.authorは抽出担当者。

短信p1に「日本基準・連結」と同じ期間/EPS/純利益があることを補強照合した。**日本基準は短信の別source ID/逐語引用による補強参照で、normalizerの自動origin closureには含まれない。** 既存単一原典APIの出力を改造せず、派生の直接originは正式修正PDFだけ。scopeの意味assertionや補強参照まで自動検証済みとはしない。

`normalized-bundle.json`はAPI素出力（正式修正PDF＋派生）。`source-bundle.json`は元の正式修正PDF objectと短信objectを完全不変で含むfullschema3source bundle（元2＋派生、companies/theses空）。API素出力全体のreplay、known normalizer reproduction、引用の頁/全文Unicode・UTF8位置、原画像SHA、独立Decimal換算が一致した。元の取得時刻/pubnull/歴史的first-save unknownを保持し、reviewと実派生取得の時計は分けた。

新しく意味確認したのは修正通知p1と短信p1の対象箇所だけ。依頼時点で会社資料の独立監査は並行中で、本作業は最終結果を消費せず合格を先取りしない。不一致は見つからなかったが、財務全体・現在最新・会計意味・分母・予測の実現性や評価モデル採用を認定しない。`financial_inputs_verified:false`、`meaning_review_required:true`、model/latestness falseを維持。

新GET、DB/Store/SQLite、既存資料・著者facts・コード・索引・監視・docs変更、IR草案/登録/送信、価格・倍率・確率・将来値・投資判断の追加は0。新6ファイルを固定し、今後の訂正は別版/追補とする。

