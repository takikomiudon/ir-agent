# 日本電設工業（1950）：初期公開資料確認

**公式root・IR資料集・決算情報一覧を保存した。日本語Q1 PDFのliteralは見つかったが、5 GET上限に達したため本文は未試行。** 動的な空一覧やPDFの取得エラーとは区別する。

## 選択と取得

343社の個人IR受付明示候補で1926の次が1950。実1,819社台帳との一致、既存会社snapshot、実DB公開source0をSQLite URI `mode=ro` / `query_only` で照合した。会社研究dirはなく、旧1950記録は窓口原文の外部著者候補検索（route0）で、財務取得停止ではなかった。既存selector／inventoryを再利用し、1926等の経路は再開していない。

選択SQL・両CSV SHA／行数／列／選択行・会社snapshotは `selection.json`。投資順位ではなくcoverage順で、過去の窓口確認を現在の送信適格性・回答保証にせず、フォームにもアクセスしていない。

| GET | 役割 | HTTP | 取得終了UTC |
|---|---|---|---|
| 1 | [issuer_robots](https://www.densetsuko.co.jp/robots.txt) | 200 | 2026-10-16T03:01:22.075483+00:00 |
| 2 | [issuer_root](https://www.densetsuko.co.jp/) | 200 | 2026-10-16T03:01:40.621486+00:00 |
| 3 | [results_index](https://www.densetsuko.co.jp/company/ir/irlibrary/) | 200 | 2026-10-16T03:02:04.471739+00:00 |
| 4 | [quarter_results_index](https://www.densetsuko.co.jp/company/ir/irlibrary/financial-information) | 301 | 2026-10-16T03:02:34.257921+00:00 |
| 5 | [canonical_results_index](https://www.densetsuko.co.jp/company/ir/irlibrary/financial-information/) | 200 | 2026-10-16T03:02:55.343388+00:00 |

robotsはwildcard `/wp/wp-admin/` を禁止し、一部admin-ajaxをAllow。今回の対象はparserで許可された。12 exact-host保留と固定UA、通常proxy/TLSを維持。JS・外部host・検索・フォーム・Cloud診断・retryは0。

root anchor36「IR資料集」→資料集anchor107「決算情報」とliteralを辿った。4件目は同hostの末尾slash付きURLをLocationで明示する301で、0byteの完全entity／SHAを保存した。許可されたsame-host1hopとして転送先を5件目に計上し、元301とcanonical200を別snapshotで保持した。自動redirectではなく、slashやendpointを推測していない。

## 見つかった財務原典と未試行の区別

canonical決算一覧は静的HTMLで、2027年3月期の第1四半期決算短信〔日本基準〕（連結）の日本語PDFをanchor112として明示している。正確なhref／URL・label・年／四半期の本文引用・元source IDとpointerは `link-provenance.json` に保存した。

[一覧に明示された日本語PDF](https://www.densetsuko.co.jp/pdf/company/ir/irlibrary/financial-information/2027/20260731__sihanki.pdf) は**未試行**。robotsとsame-host転送を含め5 GET上限に達したためで、PDF403／503、禁止、存在しないという結果ではない。PDFラベルの566KBはサイトの案内で、本文の実受信サイズではない。このtaskはここで終了し、自動の追加取得は予定していない。

## 公開回答と不足

会社は日本のインフラを支える総合設備企業と説明し、鉄道電気工事・一般電気工事・情報通信工事・環境エネルギー工事等を案内している。事業の一般的な範囲や資料の所在は公開回答として使えるが、セグメント売上・利益率・顧客依存を確認したことにはならない。

rootには9月11日の自己株券買付状況報告書という告知もあるが、その本文は取得しておらず、自己株式数・現在EPS分母を推測していない。決算一覧の日本基準／連結／Q1というタイトルも金融本文の意味確認とは分け、正式期間・実績／会社予想・単位・営業／親会社利益・一時要因・株数・取得／連結範囲は未確認を維持する。

Anthropicの公開情報先行と、Damodaranのモデル適合／主体・利益・CF基準の確認に従い、通常事業もneeds_data、他ルートやモデル選択はnull。IR質問・独自予測・倍率・税・確率・閾値・正常化・正規化は作っていない。本文を読んでいない事項を「会社が未回答」と呼ばず、現在の資料原典への到達可否も推測しない。

## 保存範囲

raw/SHA/サイズ／開始・headers受信・終了・保存時刻／完全性は `capture.json` と各snapshot。rawはresponse entityバイトでwire転送の保存ではない。HTML原バイトとvisible extractionを分離し、公表日は各ページとも未確認で `published_at:null`／unknown精度。PDF filenameの日付風文字列を公表日として採用していない。

既存capturerとshared source builderを再利用し、builder用snapshotには元complete capture全objectを保持した。`source-bundle.json` は成功HTML3 source、companies/theses空。robotsと301は取得証拠として保持し、事業開示sourceにはしない。意味確認は選んだ事業説明・静的カテゴリ・現在期のPDF案内に限定し、全サイト・過去資料・PDFの読了ではない。PDF全文抽出・意味画像確認は0。

5引用を原source SHA／UnicodeとUTF8 byte位置へ対応付けた。metadataのfinancial_content=falseはproducerの内容判断で、native分類完了ではない。共有generic byte verifierは未実行で、builder／個別SHA・引用位置照合をmatchedと扱わない。`validation.json` はproducer確認で、金融意味の独立検証・モデル採用は別。新sourceはfile-onlyで待機し、実DB／旧file／新case／金融入力／IR・注文の変更は0。
