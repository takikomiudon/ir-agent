# 2327 日鉄ソリューションズ：初回公開財務入口

固定343個人IR明示名簿の2315次、**2327 日鉄ソリューションズ**をcoverageコード順で選定。投資順位/業種選別ではない。`selection.json` に343データ20行目（header込み21）、1819対応行・元CSV SHA・RO DB会社snapshotを固定。開始時の実DB全source0/publicsource0/nativecase0、既存財務研究/未受入producer/issuer金融route停止なし。過去contact root503は後続root/FAQ/form200が保存済みであり、閉じたcontact/作者no_match経路を再開しない。

旧root保存snapshotの `$.links[59]` に明示された `https://www.nssol.nipponsteel.com/ir/finance.html` を入口とした。**最大4 GET・実行2 GETで停止**。robotsは完全404（既存missingrobots branch、HTMLを許可規則と解釈しない）。同host決算短信一覧はHTTP200完全56,141bytes。通常proxy/TLS・固定UA・redirect/retry0。holds-v8 exacthost非該当を照合し原SHAを固定した。

保存した静的HTMLのanchorは218、**PDF hrefは0**。原HTMLには空のE-IR library containerと `setParts('library')` のscript呼出しがある。`raw-marker-evidence.json` はこの原markupだけをraw SHA/UTF8位置で固定し、JSを実行したりfeedへアクセスしたりしない。残り2 GETを消化せず、他一覧・別host・検索・URL推測へ広げない。

今回のsourceは必要な**入口HTML1件のみ・財務本文0**。公開日/対象期/会計基準/実績・会社予想/利益段階/基本希薄化EPS/経常項目有無/株数split/配当期別/連結範囲/CFは全て未取得で、0や該当なしへ変換しない。`metadata.financial_content:false` は資料ラベルしかないという内容判断で、native分類実行ではない。PDF/fulltext/意味画像は未着手（0頁）。HTML原raw/visible textは保存した。

`source-quotes.json` は見出し/旧社名注意書きの限定1引用、native object SHA・Unicode/UTF8位置・rawSHAを保持。原markup証拠はsource.content引用と別に保存。共有source builderを再利用し、汎用byte verifierはnot run/unknownのまま。動的表示という取得限界を、会社資料の不存在・投資対象除外・調査完了へ拡張しない。

新会社folderのみ使用し、DB/Store/共有code/旧files/金融採用/予測/IR草案・送信は0。この入口で一度freezeしroot受入を待つ。
