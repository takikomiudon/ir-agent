# ライト工業（1926）：初期公開資料確認

**公式事業説明と静的IR案内を保存し、決算短信一覧の動的containerで終了した。財務本文は0件。** robots込み最大5 GETのうち4件を実施し、全件200・完全entity。残り1 GETを使わず、配信script／feed・別host・別資料へ進んでいない。

## 未カバー順の選択

343社の個人IR受付明示候補で1904の次が1926。実1,819社窓口台帳との一致、会社snapshot、公開source0をSQLite URI `mode=ro` / `query_only` で確認した。既存会社研究ディレクトリはなく、過去の1926記録は窓口原文の外部著者候補検索（route0）で、財務取得停止ではなかった。前回selector／inventoryを再利用し、既存1871・1904などの経路は再開していない。

`selection.json` にCSV SHA／列／行数／選択行、SQLと会社snapshot、元selectorと指示fileのpinを保持した。投資順位ではなくcoverage順である。過去の個人受付明示を現在の送信適格性・実返信保証にせず、窓口フォームへアクセス・入力・送信していない。

## 取得経路と停止理由

| GET | URL | HTTP | 取得終了UTC |
|---|---|---|---|
| 1 | https://www.raito.co.jp/robots.txt | 200 | 2026-10-16T02:50:11.690850+00:00 |
| 2 | https://www.raito.co.jp/ | 200 | 2026-10-16T02:50:29.617830+00:00 |
| 3 | https://www.raito.co.jp/ir/irshiryou/ | 200 | 2026-10-16T02:50:49.727031+00:00 |
| 4 | https://www.raito.co.jp/ir/irshiryou/tanshin/ | 200 | 2026-10-16T02:51:16.623076+00:00 |

robotsはwildcardで `/wp/wp-admin/` を禁止し、一部admin-ajaxをAllow。今回のroot／IR資料室／短信一覧はparserで許可された。12 exact-host保留、固定UA、通常proxy/TLSを維持し、redirect・retry・JS・検索・外部host・Cloud診断は0。

root anchor31の「IRライブラリー」から資料室へ進んだ。資料室は決算短信・説明資料・有報等の静的なカテゴリ案内で、anchor61「決算短信」が同hostの一覧を明示していたため、そのliteralだけを次に取得した。一覧rawは `<div class="eir" data-area-name="area_tanshin_007"></div>` が空で、PDF anchorとraw `.pdf`文字列がともに0。動的scriptは取得・実行していない。

ここまでの全GETは正常200で、停止理由は財務PDFのliteralが静的応答にないこと。会社資料の不存在・アクセス障害・投資不適格を示すものではない。同義の追加phaseや残枠消化は行わず、この会社の初期研究を終了した。

## 公開回答と未取得の境界

rootは特殊土木の事業、独自の技術開発と自社保有建機、土木・建築・海外・研究開発という案内を公表している。専門性や施工対応力は会社の説明で、競争優位・設備効率・将来採算を独立検証したことにはならない。一般的な事業・技術概要や資料のカテゴリ所在は公開回答があるので、同じ質問をIRへ送る前に利用できる。

財務原典は取得していないため、正式な最新決算名／公表日、Q1／年度の開始終了、実績／会社計画、日本基準等、個別／連結、単位、営業利益／親会社純利益／一時要因、株数・取得／連結範囲変更はすべて未確認。索引の「最新資料」という語句を最新業績の検証にしない。決算説明や公開Q&Aも本文未取得であり、未取得を「会社が未回答」とは扱わず、具体的IR草案や回答分岐は0。

Anthropicの公開情報先行と、Damodaranのモデル適合・主体／利益／CF基準の確認手順に沿い、通常事業もneeds_data、金融・循環正常化・赤字成長ルートの該当やモデル選択はnull。業界・技術紹介だけで除外／採用を決めず、独自予測・倍率・税・確率・閾値・評価額・正常化・正規化を補完していない。

## 保存と確認範囲

raw/SHA/サイズと開始・headers受信・終了・保存時刻／完全性を `capture.json` と個別snapshotへ保存した。rawはresponse entityで、wire転送の保存ではない。HTML原バイトとvisible extractionを分け、sourceの取得時刻はHTTP終了、公表日は未確認で `published_at:null`／unknown精度。copyrightやsoftware日付で公表日を補っていない。

既存capturerとshared source builderを再利用し、builder入力用snapshotには元complete captureの全objectを埋め込んだ。key変換・visible text・rawの対応を保存し、原objectを上書きしていない。`source-bundle.json` はrootと2索引の3 sourceのみ、companies/thesesは空。robotsは事業開示sourceに数えない。意味確認は選んだ事業説明・静的カテゴリ案内・空containerに限定し、全サイト／リンク先資料の読了ではない。PDF取得・全文PDF抽出・画像確認は0。

`source-quotes.json` は本文3引用とraw1引用を、source／raw SHA、Unicode文字とUTF8 byte位置へ対応付けた。metadataのfinancial_content=falseはproducerの内容判断で、実DBのintake分類完了ではない。共有generic byte verifierは未実行で、builder／個別SHA・引用位置の照合をmatchedとは扱わない。`validation.json` はproducer検証で、独立確認・金融入力採用は別である。

新case・正式IR・実DB・旧file・会社状態・送信／注文の変更は0。取り込みと分類はroot担当であり、このbundle作成を実登録や金融内容の検証と呼ばない。
