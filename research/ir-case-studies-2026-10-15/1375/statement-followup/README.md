# 1375：最終の有限追跡、公開feed503で保留

**財務本文は未取得のまま、この会社の追加取得を保留した。** 最後に許可された最大3 GETのうち2件を実施し、2件目の503で終了。残る1 GET・別feed・host置換・再試行・診断・新しいphaseは使っていない。

| capture | URL | HTTP | 初回取得UTC |
|---|---|---|---|
| 01 | [common_conf.js](https://ssl4.eir-parts.net/Custom/public/v5parts/1375/jp/20250305/app/conf/common_conf.js) | 200 | 2026-10-15 05:10:57.302648 |
| 02 | [primary announcement feed](https://v4.eir-parts.net/V4Public/eir/1375/ja/announcement/announcement_0.js) | 503 | 05:11:11.673669 |

保存済みの日本語config/coreは再取得せず再利用。coreが明記する共通configと、保存configの確定したapp baseから01へ進んだ。01の原文は次のprimary feedを明記する（`sources.json` のsource content文字offset付き引用）。

> _e.json= "http://v4.eir-parts.net/V4Public/eir/1375/ja/announcement/announcement_0.js";

親から許可された取得器のtransport選択として、このURLの**schemeだけHTTP→HTTPS**へ変更した。同一host/path/queryを保ち、ssl4などへのhost置換はしていない。元サイトの `_e.toSslPath` 実装/動作を再現・検証したとは主張しない。元URL・実リクエストURL・理由は02 snapshot/manifest/`request-derivation.json` に保存。JS/JSONPは実行していない。

02は91byteのHTTP503本文としてraw/text/SHA/transportを保持し、発行体の開示sourceへ含めない。成功01も配信設定であって財務本文ではない。`source-bundle.json` は既存 `jp:1375` の成功config1件、`companies=[]` / `theses=[]`。全件 `financial_inputs_verified:false` / `financial_values_automatically_adopted:false`。公開金融資料の日時は未確認で `published_at:null`。

最新の正式決算名/公表日/期首期末/比較期/会計基準/連結範囲/単位/実績と会社予想の値はnullを維持した。公開決算Q&A・正確な次回予定も未取得。初期一般FAQの事業/コード/決算月を保持するが、財務情報の不足を補うものではない。取得不能は資料の不存在、会社の投資不適合、IRを送る価値の証明にはしない。

`review.json` のstatusを `company_additional_financial_retrieval_on_hold_final_feed_HTTP503` とした。予測・倍率・税率・確率・閾値・モデル値は作成せず、質問登録・IR送信・実DB操作もなし。初期caseと先行followupは変更していない。

`validation.json` は成功source契約/stable ID/raw/snapshot、2件のraw/text SHA、逐語引用位置、既存46ファイル不変をオフライン確認した結果。原文一致は金融入力やモデル適合の検証ではない。このtaskはここで完了し、新phaseを増やさない。
