# ピーエス・コンストラクション（1871）：初期公開資料確認

**公式rootと決算短信の静的一覧を保存した。財務本文は未取得のまま、3 GETで終了した。** 一覧に直接のPDFリンクがなく、動的配信先・別hostへ進まず、残り2 GETも使っていない。

## 選択

1,819社の窓口台帳と343社の個人受付明示候補、前回の会社研究inventoryを再利用した。1870より後を証券コードの辞書順に照合し、1871は既存会社研究ディレクトリなし、実DBの公開source0件だった。SQL・URI `mode=ro` / `query_only`・会社snapshot・両CSV SHA／行数／列・選択行は `selection.json`。投資順位ではなく未カバー順である。

旧1871記録には、窓口調査の保存原文を外部著者レポート候補として検索した一覧があるが、該当route0で、当社の財務取得失敗・保留ではなかった。1375等の停止経路は再開していない。過去の個人受付明示は今の送信適格性・返信保証ではなく、フォーム再確認・入力・送信もしていない。

## 取得と限定停止

| GET | 役割 | HTTP | 取得終了UTC |
|---|---|---|---|
| 1 | [issuer_robots](https://www.psc.co.jp/robots.txt) | 404 | 2026-10-16T01:38:07.173108+00:00 |
| 2 | [issuer_root](https://www.psc.co.jp/) | 200 | 2026-10-16T01:38:22.697970+00:00 |
| 3 | [results_index](https://www.psc.co.jp/about/ir/library/financial_report.html) | 200 | 2026-10-16T01:38:41.810174+00:00 |

robotsは完全な404本文であり、issuerのエラーHTMLをrobots規則とは解釈していない。既存のcomplete404 missing-robots分岐でroot／一覧へ進んだ。12 exact-host保留を照合し、固定UA `Codex-IR-Research/0.1`、通常proxy/TLSを維持。retry・redirect追従・JS・フォーム・Cloud調査は0。

root anchor60のliteral `/about/ir/library/financial_report.html` から一覧を取得した。静的一覧は `<div id="tc_list"></div>` が空で、PDF anchorとraw `.pdf` はともに0。配信scriptの参照は見えたが取得・実行していない。索引本文を取得できたことと財務本文に到達したことを区別し、会社資料の不存在・アクセス障害・投資不適格とは結論しない。この有限調査はここで終了する。

## 確認した公開内容と未取得

rootはPCaPC工法の2つのPC技術、工場での部材生産による品質／省力化、あらかじめ圧縮力を加える技術、工期・耐震耐久・環境・ライフサイクルコスト等のメリットを説明する。会社が公表する技術・サービスの説明であり、効果の独立測定・売上構成・将来利益にはしていない。一般的な「PC技術とは何か」をIRで繰り返し尋ねる前に、この公開回答を利用できる。

2026年8月6日付で「2027年3月期 第１四半期決算短信〔日本基準〕（連結）」を追加したとのroot告知がある。ただし金融本文は未取得で、正式期首期末・会計基準・連結範囲・単位・実績値・会社予想・一時要因・株式基準の意味確認はすべて未完了。タイトルの語句だけで金融入力の定義を確認済みにしない。古い決算説明会「主な質疑応答」の掲載告知も見えるが、その回答本文や現四半期Q&Aを読んだことにはならない。

原文の4引用と一覧rawの空container1引用を `source-quotes.json` にsource ID・SHA・文字offset付きで保持した。意味確認範囲はこの技術説明・選んだ告知と静的一覧で、rootの過去年表全体やリンク先資料の読了ではない。PDF取得は0のため全文PDF抽出・画像確認も0。HTMLの原rawと可視本文は分けて保存した。

まず正式な決算原典、実績／会社予想、連結や株数の変更、損益と営業CF、公開説明・Q&Aを点検する必要がある。未取得を「会社が未回答」とは扱わず、具体的IR草案や回答分岐は作っていない。Anthropicの公開情報先行、Damodaranのモデル適合点検に沿い、通常事業もneeds_data、他ルートや投資適格性は未決定。数カ月〜1年の検証材料や公表日・管理日・売却期限を推測していない。

## 保存と検証

`capture-once.py` は既存1870の有限取得器を会社IDだけ適応し再利用した。raw SHA・サイズ・開始／headers受信／終了／保存時刻・完全性を `capture.json` と個別snapshotに保持。response entityバイトでありwire captureではない。sourceの取得時刻はHTTP終了で、DB初回保存の証明ではない。金融資料の公表時刻は不明で `published_at:null`、rootのニュース日をページ全体の公表日にしていない。

`source-bundle.json` は2 source、`companies=[]` / `theses=[]`。robotsは事業開示に数えない。既存provider `finite_initial_public_review` を再利用し、共有byte verifierの対応外であるunknownを明示した。`validation.json` はproducerによるsource契約・共有stable ID・raw/本文/引用位置の照合であり、独立検証・金融入力の採用・Web runtimeの確認ではない。独自予測・倍率・税率・確率・閾値・評価額・IR質問・DB変更・旧file変更・送信／注文は0。
