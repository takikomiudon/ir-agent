# 8151 東陽テクニカ：Astris外部レポートの限定確認

会社公式IRページが明示したAstris案内から、**2025年6月3日付・2025年9月期2Q決算アップデート（11頁）**を取得した。保存ページの静的掲載5件内では最新だが、2026年10月15日現在の最新予測とは確認していない。会社予想の転載だけでなく、著者自身の数値予測が見つかった。金融モデル・投資判断・IR草案への採用は0。

公式起点は既存 `research/ir-contacts-universe-2026-10-11/evidence/8151/20261011T235519303745Z/02.json`（SHA256 `359318f5e32c6446d876d259684c211f832c6e2d0980200907288f838d1e0009`）の`$.links[67]`。href/resolved URLとも `https://corporateresearch.astrisadvisory.com/ja/toyo`。公式ラベルの「アストリアス」と本文著者の「アストリス」の表記を各原文のまま残す。

## 確認できたこと

- **予測主体**：PDF p5「アストリス・アドバイザリーの業績予想」は、25年9月期**会社予想**と著者25/26/27年9月期（予）を別列にする。例えば25年9月期売上は会社33.00に対し著者33.21、営業利益は2.40に対し2.49（原単位１０億円）。共通脚注「会社データに基づき…作成」だけで会社予想へ読み替えない。
- **外部予測候補**：p1 `9/25E,9/26E,9/27E` EPS `80.88,103.69,147.83`円、1株当たり配当 `69.00,72.00,80.00`円。p1/p5の列を画像でも確認した。Eラベル・年度・作者・元単位を保持する候補記録で、正規化/出典数値監査/意味確認/モデル採用は未実施。
- **著者・利害関係**：p11の作成主体はアストリス・アドバイザリー・ジャパン株式会社。個人著者は確認できなかった。PDF管理上のAuthor=`Tavkel`をアナリスト氏名と認定しない。p1とp11は対象会社の委託・支払いを明記する。支払金額/契約条件/予測精度/独立性は未確認。
- **評価**：p1の「2026年9月期予想PER13.7倍」「PBR1.2倍」は当時の取引倍率。構造的成長による倍率拡大余地という見解はあるが、公正PER・目標価格・明示目標算式・目標リターン期間は確認範囲で見つからない。掲載株価1,420円を現在価格にせず、EPS×倍率の目標価格を逆算しない。
- **仮説と反対材料**：防衛・AD/ADAS・リカーリングや高収益事業の構成比改善という前提と、投資/採用/販管費による相殺を分離する。p4は政策に伴うAD/ADAS納入遅延と翌期ずれ、受注から計上まで12カ月超の案件を説明する。受注残を当期売上としない。これらは古い著者の前提/リスクであり、機械的な買い・売り・反証閾値は未設定。

次に必要なのは後続著者版/改訂と同期間の会社公開実績・納入説明、EPSの株数/希薄化・配当の権利/支払時点等。外部著者の公正倍率や条件解釈を会社IRが保証するとは扱わない。FCFも名称・比率だけでDamodaran FCFF/FCFEへ対応付けない。

## 取得・保存範囲

最大4GETを使い切って終了：provider robots200 → 会社HTML200 → 明示PDFホストrobots200 → HTML中のliteral PDF1本200。両robotsはsample/preview等の限定禁止のみで、この対象への固定UAの許可を確認。認証/登録なし、JS0、自動redirect0、retry0、推測URL0、代替経路0。共有 `/tmp/ir-public-get-global-rate.lock` / `.last` の0.5rps上限を使用。

PDFは `application/pdf`、`%PDF-` magic、実835,303bytesと宣言Content-Length835303を別々に点検。最初から16MiB上限のbounded streamで取得した。rawはrequestsの保存response entity bytesで、wire captureではない。`source.retrieved_at`は本文受信完了時刻、開始/ヘッダ受信時刻とは別。日付だけの公表ラベルを午夜timestampにせずpublished_at=null。HTTP Last-Modified/PDF作成時刻を公表時刻に転用しない。

`source-bundle.json`はcanonical `jp:8151`の一覧HTMLとPDFの2public_disclosure source、companies/thesesは空。PDFはHTML sourceをoriginal_source_idとして辿る。metadata providerは既存の保存bytes契約名であり、会社決算資料であるとの意味は持たない。本文はHTML可視テキストと`pdftotext -layout`の抽出。静的`application/json`掲載一覧は別原文として保持し、JSを実行していない。

- `capture.json`, `01.json`–`04.json`, `raw/`：有限GETと元response。
- `02.embedded-reports.json`, `02.links.json`, `02.txt`, `04.txt`：静的JSON/リンク/抽出本文。
- `quotes.json`：本文内の逐語引用7件、PDF物理頁・Unicode文字offset。
- `provenance.json`, `review.json`, `validation.json`, `byte-verifier.json`：経路・主体/期間・狭い出典照合。
- `build_artifacts.py`：保存資料だけから再現、GET/DBなし。`fetch_one.py`は取得記録用で、追加実行しない（budget4消費済み）。

オフライン検証の一致は、保存bytes・引用・schemaが対応することを示す。財務数値/著者見解の正しさや現在の投資適格性を保証しない。実DB/既存source/会社status/金融モデル/方針/質問/返信/注文は変更していない。
