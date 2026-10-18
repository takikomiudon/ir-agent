# 135A 中間B/S入力候補

2026-10-15の後日読取として保存した。既存の正式中間短信（日本基準・非連結、表紙2026-10-14）の保存PDFを使い、新GET/DB/既存変更は行っていない。これは評価入力候補の一歩であり、valuation完成や採用記録ではない。

2026年8月31日の現金及び預金はB/S物理p6（印字4）で138百万円。CF注記p9（印字7）は同日末の現金及び預金138百万円と現金及び現金同等物138百万円の関係を明示する。既存normalizerで2つの表示事実を各138,000,000JPYに変換した。同じ残高の対応なので2つを加算しない。B/Sの比較列427は2026年2月28日、CF注記の比較列89は2025年8月31日で、比較期を混同しない。金額の百万円未満切捨て注記を保持し、換算で未丸め精度が増したとはしない。

p2の期末発行済普通株式数10,256,000株は自己株式を含む。期末自己株数の「－」は0とせず、同じ数字の期中平均株数も別行/期間概念である。株→sharesは現行normalizer未対応のためraw候補だけに留め、JPY等へ偽装しない。p6短期借入金の「－」もraw候補/nullのまま、前期400や返済CFから0を補完しない。全金融負債範囲と自己株控除後net sharesは未確認。

Damodaranの既存9入力仕様への候補対応は `model-input-map-candidates.json` に保存し、全9採用値とモデルpathはnull。帳簿上現金と評価加算用余剰現金、期末の株数と評価分母を同一視しない。CFO223をFCFFへ転換せず、将来値/価格/確率/閾値/IR条件/売買も作っていない。

[normalization-input.json](normalization-input.json) と [normalized-bundle.json](normalized-bundle.json) は既存pure API契約の2cash facts。[raw-candidates.json](raw-candidates.json) に株数/自己株dash/短期借入dash、[source-quotes.json](source-quotes.json) に5引用の原文・頁/半開offset・画像SHAを保存した。レビュー実時刻 `2026-10-15T15:17:39.874347+00:00` と派生取得実時刻 `2026-10-15T15:17:39.876172+00:00` は元snapshotの取得時刻から分離し、原sourceID・本文・取得時刻・published_at nullを不変にした。原legacy snapshotにHTTP完了の別fieldやDB first-save receiptはなく、それらの時刻を補わない。

既存API全bundle replay/reproducer、独立Decimal換算、原raw/text/snapshot/manifestのSHAと再抽出一致を確認。financial_inputs_verified:false、meaning_review_required:trueのまま。CLI/Store起動・SQLite接続・実DB・新GET・コード/テスト・index/monitor変更・IR作成/送信・金融採用は0。旧9facts/model-input-mappingと30CF行等の保存入力を保持した。今回確認した保存範囲の外でcash/debt全定義が不開示と断定しない。

この成果を固定し、以降の訂正は別版/補足とする。詳細は [validation.json](validation.json)。
