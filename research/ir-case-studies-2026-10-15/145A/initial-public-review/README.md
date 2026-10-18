# 145A L is B — 公式一次資料の初期確認

2026-10-15 08:36–08:37 UTCに4GETで終了しました。公式の決算短信・決算説明資料の索引は取得できましたが、JavaScriptを実行しない保存HTMLでは資料一覧が空で、正式PDFのリンク・対象期を特定できませんでした。財務本文の取得は0件です。これは投資対象からの除外理由や、会社が財務情報を公開していないという判断ではありません。

[保存済み経路](../../../ir-next-case-routing-2026-10-15/routes.json)の `145A-02-40`（決算短信）を起点としました。GETは次の4件だけです。

| GET | URL | 応答・扱い |
|---|---|---|
| 1 | `https://l-is-b.com/robots.txt` | 302。明示Locationだけを次の別GETへ |
| 2 | `https://l-is-b.com/ja/robots.txt` | 404。robots不在として扱い、本文は財務資料に含めない |
| 3 | `https://l-is-b.com/ja/ir/results/` | 200。短信索引、資料一覧のHTML要素は空 |
| 4 | `https://l-is-b.com/ja/ir/presentations/` | 200。説明資料索引、同じく一覧は空 |

上限はrobots込み5GET、同一実行内の送信間隔は2秒以上、再試行・自動リダイレクト・JavaScript実行は0です。GET2はGET1が実際に返した同一ホストのLocationへの明示的な別要求で、URL推測ではありません。保存HTMLは `www.xj-storage.jp` の外部loaderを指定しますが、そのscript/APIの取得・推測・実行には進んでいません。5件目を使うためだけの別候補巡回もしませんでした。

`contents.xj-storage.jp` は[同日の既存robots証跡](../../1332/longterm-trade-payables-review/02.json)が `User-Agent: *` / `Disallow: /` を返しています。原バイトSHAとguard結果を再確認し、新しいrobots/PDF要求は0件です。今回の静的HTMLではこのホストのPDF URL自体を発見していません。この禁止を別ホスト `www.xj-storage.jp` にまで拡張したり、PDFサーバが503を返したと扱ったりしていません。

確認できた事業情報は、索引HTMLのmeta説明にあるビジネスチャット「direct」、カメラ・クラウド共有「タグショット/タグアルバム」、企業向け動画共有「ナレッジ動画」と現場の業務改善・DX支援、および本文フッターの製品名です。料金・継続課金・収益認識・セグメント別売上の説明は確認できていません。SaaS企業という分類やARR・解約率等の値/定義/対象期を推定しません。

最新正式資料の対象期、会計基準、連結範囲、実績と会社予想、CF計算書の有無は未確認です。「キャッシュ・フローの状況」というナビゲーションはCF表の存在確認に使いません。赤字や業種による除外、EPS倍率モデルへの強制、将来予測・IR質問・モデル採用・DB操作はいずれも行っていません。

[review.json](review.json)に確認済み/未確認と10件の逐語引用を、[link-provenance.json](link-provenance.json)に旧実リンク・新索引リンク・robots参照を保存しました。HTML引用にPDF頁番号は付けず、保存raw HTMLまたは抽出本文の文字位置を示しています。[source-bundle.json](source-bundle.json)は実際に200で取得した有用な索引本文2件だけを `index_only` / `financial_content: false` として保持し、robots・404・財務本文を装った資料は含めません。これはDB登録や財務カバレッジの追加ではありません。

[validation.json](validation.json)で4応答のrawバイト、2本文のSHA、capture SHA、stable source ID、全引用、指定した旧24ファイルの不変を確認しています。既知providerの検証形式を仮装せず、generic verifierはunknownのままです。ハッシュ/引用一致は金融上の意味や採用の検証ではありません。全件テストは実施していません。

このディレクトリ内のcapture/raw/text相対パスはこのディレクトリ基準です。`original_*_file`、旧route/snapshot、baselineのパスはリポジトリルート基準で、各JSONにも基準を記しています。rawはHTTP content decoding後の保存応答entityバイトであり、通信パケットのwire bytesではありません。クラウド設定の適用状態unknownを接続保証にせず、ここでは各要求の実応答だけを報告します。
