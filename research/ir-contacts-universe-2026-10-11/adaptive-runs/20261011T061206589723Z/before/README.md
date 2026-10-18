# 東証国内普通株のIR窓口・全社調査一覧

確認日：2026年10月11日（日本時間）。保有期間の前提は数カ月〜1年。

対象は **3,686社**。全社の銘柄とサイトURLを用意し、取得結果・未確認理由を各社に保存した。ただし、**全社のIR窓口確認は完了していない**。接続失敗や通信停止で3,154社が未確認。接続失敗をIR窓口不存在・企業側の受付拒否と判定していない。

IRメール・質問入力欄までの確認済みは **220社**、案内リンクや会社との対応など追加確認が必要な会社は **71社**。Codexが個別レビューした返信調査向け窓口候補は **283社**（確認済み217社、追加確認66社）。受付制限・個別回答なしは別枠。個人受付が未記載の会社を、個人の無条件利用可能と解釈しない。

## ファイル

- [companies.csv](companies.csv)：全社一覧。UTF-8 BOM付き。確認水準、窓口URL、メール、受付条件、未確認理由を含む。
- [companies.json](companies.json)：全社の詳細。引用、取得時刻、保存証拠、Codexの個別レビュー履歴を含む。
- [contact-candidates.csv](contact-candidates.csv)：Codexが個別レビューした返信調査向け窓口候補。
- [restricted.csv](restricted.csv)：個人等に受付制限のある窓口・個別回答なし。
- [retry-network-errors.csv](retry-network-errors.csv)：通信障害で未確認。復旧後の再開対象。
- [other-unconfirmed.csv](other-unconfirmed.csv)：IR用途未実証、robots・アクセス制限、取得・解析の失敗など。窓口不存在の一覧ではない。
- [additional-followups.csv](additional-followups.csv)：通信復旧用の再開対象以外で、入力欄・メール・用途等の追加確認が必要な会社。案内リンクのみの会社も含む。
- [watchlist-bundle.json](watchlist-bundle.json)：個別レビュー済み窓口候補を既存ハーネスのwatchへ取り込む入力。金融仮説・売買指示は含まない。
- [coverage.json](coverage.json)、[validation.json](validation.json)：対象・取得・窓口確認の別集計とデータ検証。
- [evidence](evidence/)・[parts](parts/)：公開取得証拠と分担レビュー結果。[evidence-index.json](evidence-index.json) は保存ファイルのSHA-256を記録し、取得時の本文ハッシュと区別する。

## 母集団と上場照合

[JPX月末一覧](https://www.jpx.co.jp/markets/statistics-equities/misc/01.html)の2026年9月末データを基準にした。[元Excel](../ir-contacts-2026-10-11/evidence/jpx-data-2026-09.xlsx)・[変換CSV](../ir-contacts-2026-10-11/evidence/jpx-listing-universe.csv)・[取得記録](../ir-contacts-2026-10-11/evidence/jpx-listing-manifest.json)を保存済み。内国株式3,702行のうち、5桁コードの優先株・社債型種類株式7行を除くと普通株は3,695社。前回の調査レポートではこの7行を普通株の母集団へ含めていたため、今回は[除外記録](excluded-share-classes.json)に分けた。

10月1日〜11日の[新規上場](https://www.jpx.co.jp/listing/stocks/new/index.html)3社と[上場廃止](https://www.jpx.co.jp/listing/stocks/delisted/index.html)12社を公式表で照合し、3,695＋3−12＝3,686社へ補正した。承認日・公表日と効力日を区別し、10月12日以降の予定は適用しない。[変更記録](listing-deltas.json)には根拠・効力日・取得時刻を残している。新規640A・641A・642Aの公式URL・市場・業種も別途照合した。

対象は東証プライム・スタンダード・グロースの国内普通株。ETF・ETN・REIT・インフラファンド・外国株・種類株・TOKYO PRO Market、および名証・福証・札証だけの上場会社はこの母集団に含めない。これは窓口調査の範囲で、投資一般の優劣や除外判定ではない。銀行・保険など専用評価が必要な業種も窓口一覧には含めた。

現在価格・売買代金・値動き・個別財務・適時開示・決算日程の検証は未実施。現在の買付可否や金融投資対象の確定を保証しない。

## サイト発見と窓口確認

サイトURLの発見は[出典と版](seed-sources.md)に記録した。第三者の2024年10月一覧と2026年3月プライム一覧は発見の入口として使い、不足分はJPX公式の2024〜2026年新規上場表から補完した。古いURLは最新の受付根拠に使わず、取得した公式本文で会社名・コード・用途を点検する。JPXの承認時URLにも更新されない旨の注意がある。

メールは企業がIR用に指定した公開宛先だけを採用。記入例、privacy・製品・採用・広報のメールや株主優待専用メールをIR業績質問の宛先に推定しない。フォームはIR専用見出し、IRカテゴリ、公式IRの明示リンクとリンク先の実メール・質問欄を確認する。全ページのIRナビ、個人情報方針の投資家という語、電話のIR案内に隣接する製品フォームだけでは確認済みにしない。

外部フォームは公式親ページのリンク／埋め込みからたどる。JavaScript画面、空本文、HTTP200のみ、検索欄、メール認証だけでは質問入力欄の確認にならない。個人可の明示は投資家種別・個人の記入説明・公開placeholder等から確認し、それ以外は未確認とする。規約や沈黙期間は取得できた公開範囲の記録で、別ページの全規約を網羅した確認ではない。

公開ページのメール表示用エンコードを保存hrefから復元した場合は、原文引用と派生値を分け、元href・復元手法・IR用途の公式リンクを保持する。復元したアドレスが保存された可視本文に存在するとは扱わない。

公開GETのみ。メール・フォーム送信、認証メール、会員登録、回答実績の確認は行っていない。回答の到達・所要時間・返信保証も未検証。前回37社の保存証拠は再利用し、取得日時と確認水準を昇格させずに引き継いだ。

## 通信障害と再開

[今回の再試行集計](runs/20261011T044639285379Z/summary.json)：前回通信失敗の3,408社を選択し、実際の企業本文GETは255社、本文取得成功は244社。3,145社は回路停止によりGET前に終了し、8社はrobots等のアクセス方針を守って本文GETを行わなかった。更新された企業行の数を、アクセス済みの社数と混同しない。

初回の全社取得と今回の再試行を合わせ、本文GETを一度でも試みた会社は3,645社。失敗も含む試行数で、本文取得成功や窓口確認の社数ではない。再利用した37社の以前の取得は別枠。legacy集計名の `*_current_run` / `*_this_run` は各社の最新記録を集計しており、今回だけの実GET社数は再試行集計の255社で確認する。

再試行前のメール・入力欄確認136社／案内等48社から、現在の220社／71社へ更新した。前回の一覧・検証・証拠ハッシュは[再試行前の保存](runs/20261011T044639285379Z/before/)に残した。新しい取得証拠は取得時刻別の別ファイルで保持している。

接続回復後に再開できたが、途中で同じEnvoy503が再発し、JPXとラクスの再確認でも同じ応答だった。取得できた記録をレビューして反映し、残りは復旧後の対象として保存した。並列数の変更とエラーの再発は記録するが、並列数が原因とは断定しない。

保存した各社の最新取得記録では478社に成功した公開本文がある（別途、以前の37社の証拠を再利用）。初回の全社取得では、途中から異なる企業・JPX・前に取得できたラクスまで共通のHTTP503が返り、本文が `Invalid argument|remote address:envoy://cloudflare_https_tunnel/` 等になった。[診断記録](network-diagnostics.json)と[接続確認](network-healthchecks/)に保存した。同一エラーが共通経路の問題を示しているが、サービス内部の根本原因は特定できていない。ネット設定を迂回せず、TLS検証も維持した。

成功取得が銘柄コードの前半に偏るため、今の結果から全市場のIR受付率や業界別の受付率を推定できない。全社行の作成率と公式本文の取得率、窓口確認率は別の指標として残す。

通信復旧後はリポジトリルートから一度だけ以下を実行する。先にJPXへの接続と本文を確認し、失敗中は再試行を開始しない。同じ通信失敗が複数ホストに出た場合も取得を止める。robots・403・429は迂回せず、1ホストずつ間隔を空け、1社のページ数を制限する。確認済み記録は保持し、接続失敗の会社だけ再調査する。回路停止後の未着手会社は再調査済みと扱わず、旧記録を保持する。旧試行・証拠は別ファイルに保ち、定期取得は登録しない。

```bash
.venv/bin/python scripts/research_ir_universe.py \
  --universe research/ir-contacts-2026-10-11/evidence/jpx-listing-universe.csv \
  --seeds research/ir-contacts-universe-2026-10-11/seeds-current.json \
  --output research/ir-contacts-universe-2026-10-11 \
  --previous research/ir-contacts-2026-10-11 \
  --listing-deltas research/ir-contacts-universe-2026-10-11/listing-deltas.json \
  --resume-network-errors --workers 4 --max-pages 7
```

新しく取得した結果は再びIR用途・個人条件を点検し、検証器で照合してから候補一覧へ反映する。再取得を終えたことと、全社の窓口確認完了は同一視しない。

この再開コマンドの対象以外にも、312社で追加確認が必要。取得済み本文から専用フォームへのリンクを見つけたがリンク先を取得できなかった会社などを含み、[別の作業一覧](additional-followups.csv)へ保存した。アクセス制限は尊重し、未取得を『メール・フォームなし』とは判定しない。

再取得・個別レビュー後は、上のコマンドの `--resume-network-errors` を `--compile-only` に置き換えて再集計し、次の順に検証とレポート生成を実行する。レポート生成は `records/` と集計JSONが一致しない場合に停止する。

```bash
.venv/bin/python scripts/validate_ir_universe.py research/ir-contacts-universe-2026-10-11 \
  --universe research/ir-contacts-universe-2026-10-11/universe.csv \
  --previous-root research/ir-contacts-2026-10-11 \
  --output research/ir-contacts-universe-2026-10-11/validation.json --require-complete
.venv/bin/python scripts/report_ir_universe.py research/ir-contacts-universe-2026-10-11
```

## 保存データの検証

[構造・引用の検証](validation.json)：エラー0件、警告13件（検証 2026-10-11T05:05:17.899965+00:00）。これは窓口の実送信・回答や投資適格性の検証ではない。

警告対象は会社名等が必須なのに個人の記入方法が明示されていない窓口：143A、1716、1994、211A、2186、2303、2376、2489、254A、3673、4493、6226、6947。IR用途の確認は保持し、個人利用の可否・入力方法は未確認としている。

[一覧・保存ハッシュ・一時DBでの取り込み検証](integration-validation.json)も保存した。watchのみの取り込みで仮説・調査job・質問は作成されず、同じ資料の再取り込みで重複が生じないことを確認した。

## 確認した窓口

| コード | 会社 | 窓口 | 調査判定 | 確認水準 | 個人条件 | 返信運用 |
|---|---|---|---|---|---|---|
| 1301 | 極洋 | [公式窓口](https://www.kyokuyo.co.jp/inquiry/contact/index.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 130A | Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉｃｏ | [公式窓口](https://www.veritasinsilico.com/form/jp/agree_02.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 135A | ＶＲＡＩＮ　Ｓｏｌｕｔｉｏｎ | [公式窓口](https://vrain.co.jp/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1375 | ユキグニファクトリー | [公式窓口](https://www.yukiguni-factory.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1377 | サカタのタネ | [公式窓口](https://corporate.sakataseed.co.jp/inquiry/form.php?type=ir) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 137A | Ｃｏｃｏｌｉｖｅ | [公式窓口](https://campage.jp/cocolive-ir/form) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1383 | ベルグアース | [公式窓口](https://bergearth.co.jp/contact/?contact_option=2) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1384 | ホクリヨウ | [公式窓口](https://www.hokuryo.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 138A | 光フードサービス | [公式窓口](https://hikari-food-service.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1401 | エムビーエス | [公式窓口](https://www.homemakeup.co.jp/contact-list/contact.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1407 | ウエストホールディングス | [公式窓口](https://www.west-gr.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1414 | ショーボンドホールディングス | [公式窓口](https://www.sho-bondhd.jp/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 1417 | ミライト・ワン | [公式窓口](https://www.mirait-one.com/contact/inquiry.php?type=01) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 141A | トライアルホールディングス | [公式窓口](https://trial-holdings.inc/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1420 | サンヨーホームズ | [公式窓口](https://www.sanyohomes.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 142A | ジンジブ | [公式窓口](https://jinjib.co.jp/ir/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 1433 | ベステラ | [公式窓口](https://www.besterra.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1435 | ｒｏｂｏｔ　ｈｏｍｅ | [公式窓口](https://corp.robothome.jp/contact/form/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1436 | グリーンエナジー＆カンパニー | [公式窓口](https://green-energy.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1438 | 岐阜造園 | [公式窓口](https://www.gifu-zohen.co.jp/ir/contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 143A | イシン | [公式窓口](https://ishin1853.co.jp/ir/contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1444 | ニッソウ | [公式窓口](https://reform-nisso.co.jp/company/ir/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 1450 | ＴＡＮＡＫＥＮ | [公式窓口](https://cloud.swcms.net/tanakenPublic/ja/inquiry.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 145A | Ｌ　ｉｓ　Ｂ | [公式窓口](https://l-is-b.com/ja/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 146A | コロンビア・ワークス | [公式窓口](https://columbiaworks.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 148A | ハッチ・ワーク | [公式窓口](https://hatchwork.co.jp/contact) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1491 | 中外鉱業 | [公式窓口](https://www.chugaikogyo.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 149A | シンカ | [公式窓口](https://www.thinca.co.jp/ir/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 150A | ＪＳＨ | [公式窓口](https://www.jsh-japan.jp/ir/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1514 | 住石ホールディングス | [公式窓口](https://www.sumiseki.co.jp/sub/contact.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1515 | 日鉄鉱業 | [公式窓口](https://www.nittetsukou.co.jp/contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1518 | 三井松島ホールディングス | [公式窓口](https://www.mitsui-matsushima.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 153A | カウリス | [公式窓口](https://caulis.jp/ir/form-ir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 155A | 情報戦略テクノロジー | [公式窓口](https://www.is-tech.co.jp/ir_top/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 156A | マテリアルグループ | [公式窓口](https://go.materialprmenu.jp/l/1122733/2026-02-18/bvg23j) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 157A | グリーンモンスター | [公式窓口](https://greenmonster.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1662 | 石油資源開発 | [公式窓口](https://fs220.xbit.jp/w794/form2/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 166A | タスキホールディングス | [公式窓口](https://tasuki-holdings.co.jp/en/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 167A | リョーサン菱洋ホールディングス | [公式窓口](https://form.rr-hds.co.jp/m?f=7) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 168A | イタミアート | [公式窓口](https://www.itamiarts.co.jp/investor-relations/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 1716 | 第一カッター興業 | [公式窓口](https://www.daiichi-cutter.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1721 | コムシスホールディングス | [公式窓口](https://www.comsys-hd.co.jp/secure/contact/ir/input) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1723 | 日本電技 | [公式窓口](https://reg18.smp.ne.jp/regist/is?SMPFORM=mhki-qarfk-be9e4eaef3b0a40d9eb9b336706cdd81) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1724 | シンクレイヤ | [公式窓口](https://www.synclayer.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 173A | ハンモック | [公式窓口](https://www.hammock.jp/ir/inquiry.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 175A | Ｗｉｌｌ　Ｓｍａｒｔ | [公式窓口](https://willsmart.co.jp/contact/ir-contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1762 | 高松コンストラクショングループ | [公式窓口](https://www.takamatsu-cg.co.jp/inquiry/index.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1766 | 東建コーポレーション | [公式窓口](https://www.token.co.jp/inquiry/input.asp?id=002) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1770 | 藤田エンジニアリング | [公式窓口](https://www.fujita-eng.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 177A | コージンバイオ | [公式窓口](https://kohjin-bio.jp/contact/contactir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1780 | ヤマウラ | [公式窓口](https://yamaura.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1783 | ｆａｎｔａｓｉｓｔａ | [公式窓口](https://fantasista-tokyo.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1787 | ナカボーテック | [公式窓口](https://www.nakabohtec.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1788 | 三東工業社 | [公式窓口](https://www.santo.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1799 | 第一建設工業 | [公式窓口](https://www.daiichi-kensetsu.co.jp/contact/form/?kind=30) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1801 | 大成建設 | [公式窓口](https://f.msgs.jp/webapp/form/10878_kcq_15/index.do) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1802 | 大林組 | [公式窓口](https://contact.obayashi.co.jp/n/form/ahmb/HbD9QLspvTewxmJNz-Scw) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1803 | 清水建設 | [公式窓口](https://f.msgs.jp/webapp/form/20233_fydb_58/index.do?code=inquiry) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1812 | 鹿島建設 | [公式窓口](https://kajima-corp-inquiry.spiral-site.com/ir_contact_form/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1813 | 不動テトラ | [公式窓口](https://www.fudotetra.co.jp/contact/form/?kind=ir) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1820 | 西松建設 | [公式窓口](https://www.nishimatsu.co.jp/contact/input?type=2) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1822 | 大豊建設 | [公式窓口](https://www.daiho.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1827 | ナカノフドー建設 | [公式窓口](https://www.wave-nakano.co.jp/contact/form/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1828 | 田辺工業 | [公式窓口](https://www.tanabe-ind.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1833 | 奥村組 | [公式窓口](https://www.okumuragumi.co.jp/inquiries/ir/index.php) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1835 | 東鉄工業 | [公式窓口](https://www.totetsu.co.jp/inquiry) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1840 | 土屋ホールディングス | [公式窓口](https://www.tsuchiya.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1847 | イチケン | [公式窓口](https://www.ichiken.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1848 | 富士ピー・エス | [公式窓口](https://contact.fujips.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 184A | 学びエイド | [公式窓口](https://www.manabi-aid.jp/service/contactIr) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1861 | 熊谷組 | [公式窓口](https://www.kumagaigumi.co.jp/contact/ir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1866 | 北野建設 | [公式窓口](https://www.kitano.co.jp/contact/?inquiry=recruit) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1867 | 植木組 | [公式窓口](https://www.uekigumi.co.jp/form/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1870 | 矢作建設工業 | [公式窓口](https://www.yahagi.co.jp/contact/ir_contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1871 | ピーエス・コンストラクション | [公式窓口](https://www.psc.co.jp/form/input?message_type=4) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1879 | 新日本建設 | [公式窓口](https://www.shinnihon-c.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1882 | 東亜道路工業 | [公式窓口](https://www.toadoro.co.jp/inquiry/index.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1885 | 東亜建設工業 | [公式窓口](https://inquiry.toa-const.co.jp/form/pub/toa/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1888 | 若築建設 | [公式窓口](https://www.wakachiku.co.jp/contact/?m=reform) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1897 | 金下建設 | [公式窓口](https://www.kaneshita.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 189A | Ｄ＆Ｍカンパニー | [公式窓口](https://www.dmcompany.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1904 | 大成温調 | [公式窓口](https://www.taisei-oncho.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1905 | テノックス | [公式窓口](https://www.tenox.co.jp/en/contact/contact_ir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 190A | Ｃｈｏｒｄｉａ　Ｔｈｅｒａｐｅｕｔｉｃｓ | [公式窓口](https://www.chordiatherapeutics.com/ja/contact/contact2.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1911 | 住友林業 | [公式窓口](https://inquire.sfc.jp/sfc/m/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1925 | 大和ハウス工業 | [公式窓口](https://www.daiwahouse.co.jp/qa/inquiry_form.asp?page=from_header) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1926 | ライト工業 | [公式窓口](https://www.raito.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1928 | 積水ハウス | [公式窓口](https://www.sekisuihouse.co.jp/mail/form.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1929 | 日特建設 | [公式窓口](https://www.nittoc.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 192A | インテグループ | [公式窓口](https://ma.integroup.jp/l/830143/2024-04-30/38zf9b) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1938 | 日本リーテック | [公式窓口](https://docs.google.com/forms/d/e/1FAIpQLSdLFPghc6NeHyvVytAnYDxj2Q0XjpMql_R6YDb980wzdgRG7g/viewform?embedded=true) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1939 | 四電工 | [公式窓口](https://www.yondenko.co.jp/inquiry/form.php?type=ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1946 | トーエネック | [公式窓口](https://www.toenec.co.jp/contact/ir/index.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1950 | 日本電設工業 | [公式窓口](https://www.densetsuko.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1952 | 新日本空調 | [公式窓口](https://www.snk.co.jp/info/form.html?frmid=11) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1960 | サンテック | [公式窓口](https://reg31.smp.ne.jp/regist/is?SMPFORM=oboi-lfpaog-d3727284489b172114627fe9b1c1ca7f&type=3) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1963 | 日揮ホールディングス | [公式窓口](https://www.jgc.com/jp/inquiries/general/input/?kind=2) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1964 | 中外炉工業 | [公式窓口](https://www.chugai.co.jp/contact_form) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1968 | 太平電業 | [公式窓口](https://www.taihei-dengyo.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 196A | ＭＦＳ | [公式窓口](https://ir.mortgagefss.jp/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1975 | 朝日工業社 | [公式窓口](https://www.asahikogyosha.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 1976 | 明星工業 | [公式窓口](https://www.meisei-kogyo.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 197A | タウンズ | [公式窓口](https://www.tauns.co.jp/investors/contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 1980 | ダイダン | [公式窓口](https://www.form.daidan.co.jp/n/form/c/v1/ojpb/forms/Gd6FS2t-Lak6HS5SSnEGX) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1981 | 協和日成 | [公式窓口](https://www.kyowa-nissei.co.jp/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 198A | ＰｏｓｔＰｒｉｍｅ | [公式窓口](https://help.postprime.com/hc/ja/requests/new?ticket_form_id=9766923764879) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 1994 | 高橋カーテンウォール工業 | [公式窓口](https://t-cw.co.jp/form/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2001 | ニップン | [公式窓口](https://www.nippn.co.jp/customer/inquiry/index.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2002 | 日清製粉グループ本社 | [公式窓口](https://www.nisshin.com/inquiry/ir/?utm_source=nisshin_com&utm_medium=link_products&utm_campaign=23_cus-p-cat_ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2003 | 日東富士製粉 | [公式窓口](https://www.nittofuji.co.jp/form/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2004 | 昭和産業 | [公式窓口](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 205A | ロゴスホールディングス | [公式窓口](https://logos-holdings.jp/english/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2060 | フィード・ワン | [公式窓口](https://www.feed-one.co.jp/form/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 208A | 構造計画研究所ホールディングス | [公式窓口](https://www.kke-hd.co.jp/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2108 | 日本甜菜製糖 | [公式窓口](https://www.nitten.co.jp/ir/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2109 | ＤＭ三井製糖 | [公式窓口](https://www.msdm-hd.com/jp/contact/input) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2117 | ウェルネオシュガー | [公式窓口](https://www.wellneo-sugar.co.jp/contact/contact/?type=%E6%A9%9F%E8%83%BD%E6%80%A7%E7%B4%A0%E6%9D%90%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 211A | カドス・コーポレーション | [公式窓口](https://cados.jp/ir/inquiry_ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2120 | ＬＩＦＵＬＬ | [公式窓口](https://f.msgs.jp/webapp/wish/org/showEnquete.do?enqueteid=15&clientid=13425&databaseid=jwt) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2121 | ＭＩＸＩ | [公式窓口](https://mixi.co.jp/inquiry/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2122 | インタースペース | [公式窓口](https://www.interspace.ne.jp/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2127 | 日本Ｍ＆Ａセンターホールディングス | [公式窓口](https://www.nihon-ma.co.jp/action/contact/?ctype=ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 212A | フィットイージー | [公式窓口](https://fiteasy.co.jp/contact/ir-inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2130 | メンバーズ | [公式窓口](https://marke.members.co.jp/contact.public.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2134 | 北浜キャピタルパートナーズ | [公式窓口](https://kitahamabank.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2136 | ヒップ | [公式窓口](https://www.hip-pro.co.jp/form/form.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2138 | クルーズ | [公式窓口](https://crooz.co.jp/contact-form/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2146 | ＵＴグループ | [公式窓口](https://form.ut-g.co.jp/webapp/form/20691_vpeb_106/index.do) | 追加確認 | 案内・リンクのみ | 個人受付の明示あり | 窓口候補 |
| 2148 | アイティメディア | [公式窓口](https://corp.itmedia.co.jp/ir/other/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2153 | Ｅ・Ｊホールディングス | [公式窓口](https://www.ej-hds.co.jp/etc/contact/contact.cgi?p=ir) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2158 | ＦＲＯＮＴＥＯ | [公式窓口](https://www.fronteo.com/ja/contact/assignment?task_point=%E3%80%90%E6%B1%BA%E7%AE%97%E3%83%BBIR%E3%80%91%E6%B1%BA%E7%AE%97%E5%86%85%E5%AE%B9%E3%80%81%E6%B1%BA%E7%AE%97%E8%B3%87%E6%96%99%E3%80%81%E3%81%9D%E3%81%AE%E4%BB%96IR%E5%85%A8%E8%88%AC%E3%81%AB%E9%96%A2%E3%81%99%E3%82%8B%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B&hsLang=ja) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2160 | ジーエヌアイグループ | [公式窓口](https://www.gnipharma.com/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 個別回答なし |
| 2163 | アルトナー | [公式窓口](https://www.artner.co.jp/ir/other/contact-form/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2168 | パソナグループ | [公式窓口](https://www.pasonagroup.co.jp/contact/ir.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2169 | ＣＤＳ | [公式窓口](https://www.cds-japan.jp/ja/ir_contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2170 | リンクアンドモチベーション | [公式窓口](https://www.lmi.ne.jp/ir/inquiry/entry.php) | 確認済み | 質問入力欄確認 | 個人等に制限あり | 受付対象に制限 |
| 2173 | 博展 | [公式窓口](https://www.hakuten.co.jp/contact/business) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2175 | エス・エム・エス | [公式窓口](https://www.bm-sms.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2181 | パーソルホールディングス | [公式窓口](https://contact.persol-group.co.jp/@investor-contact) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2183 | リニカル | [公式窓口](https://www.linical.com/ja/investors-contact) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2185 | シイエム・シイ | [公式窓口](https://www.cmc.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2186 | ソーバル | [公式窓口](https://www.sobal.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 218A | Ｌｉｂｅｒａｗａｒｅ | [公式窓口](https://liberaware.co.jp/contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2193 | クックパッド | [公式窓口](https://info.cookpad.com/contact/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2195 | アミタホールディングス | [公式窓口](https://www.amita-hd.co.jp/contact/index.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 219A | Ｈｅａｒｔｓｅｅｄ | [公式窓口](https://heartseed.jp/ir/Inquiries/index.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2204 | 中村屋 | [公式窓口](https://www.nakamuraya.co.jp/inquiry/qa.cgi?job=3) | 追加確認 | 案内・リンクのみ | 個人等に制限あり | 受付対象に制限 |
| 220A | Ｆａｂｅｒ　Ｃｏｍｐａｎｙ | [公式窓口](https://www.fabercompany.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2216 | カンロ | [公式窓口](https://support.kanro.jp/hc/ja/requests/new?ticket_form_id=360008237675) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2222 | 寿スピリッツ | [公式窓口](https://www.kotobukispirits.co.jp/form/ja/agree_02/inquiry_02.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2229 | カルビー | [公式窓口](https://faq.calbee.co.jp/form/ir.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2264 | 森永乳業 | [公式窓口](https://www.morinagamilk.co.jp/ir/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2281 | プリマハム | [公式窓口](https://www.primaham.co.jp/ir/stock/inquiry/form.php) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 未確認 |
| 2282 | 日本ハム | [公式窓口](https://sy.nipponham.co.jp/webapp/form/22143_rtgb_45/index.do) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 228A | オプロ | [公式窓口](https://corp.opro.net/contact/ir.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2291 | 福留ハム | [公式窓口](https://www.fukutome.com/contact/company/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2296 | 伊藤ハム米久ホールディングス | [公式窓口](https://www.itoham-yonekyu-holdings.com/ir/inpuiry.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2303 | ドーン | [公式窓口](https://www.dawn-corp.co.jp/contact/inquiry02form/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2311 | エプコ | [公式窓口](https://www.epco.co.jp/contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2315 | ＣＡＩＣＡ　ＤＩＧＩＴＡＬ | [公式窓口](https://www.caica.jp/ir-inquiry/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2317 | システナ | [公式窓口](https://www.systena.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2325 | ＮＪＳ | [公式窓口](https://www.njs.co.jp/form/ja/agree_03/inquiry_03.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2327 | 日鉄ソリューションズ | [公式窓口](https://www.nssol.nipponsteel.com/cgi-bin/form/inquiry.pl) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2329 | 東北新社 | [公式窓口](https://www.tfc.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2334 | イオレ | [公式窓口](https://www.eole.co.jp/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2337 | いちご | [公式窓口](https://www.ichigo.gr.jp/contact/?category=recruit) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2351 | ＡＳＪ | [公式窓口](https://www.asj.ad.jp/ascgi-bin/ir_inquiry.cgi) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2353 | 日本駐車場開発 | [公式窓口](https://n-p-d.co.jp/contact/form_ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2370 | メディネット | [公式窓口](https://www.medinet-inc.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2375 | ギグワークス | [公式窓口](https://www.gig.co.jp/contact/ir) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2376 | サイネックス | [公式窓口](https://www.scinex.co.jp/ask/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2378 | ルネサンス | [公式窓口](https://www.s-renaissance.co.jp/contact/form/?s=1) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2379 | ディップ | [公式窓口](https://www.dip-net.co.jp/contact/company) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2385 | 総医研ホールディングス | [公式窓口](https://soiken.com/ir/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2391 | プラネット | [公式窓口](https://www.planet-service.jp/customer/contactHPInsInput.do;jsessionid=0B0BEA54C22369973343ED29DA4B3904.jvm1) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 未確認 |
| 2408 | ＫＧ情報 | [公式窓口](https://www.kg-net.co.jp/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2410 | キャリアデザインセンター | [公式窓口](https://cdc.type.jp/contact/ir_index.php) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2411 | ゲンダイエージェンシー | [公式窓口](https://www.gendai-a.co.jp/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 241A | ＲＯＸＸ | [公式窓口](https://roxx.co.jp/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2429 | ワールドホールディングス | [公式窓口](https://world-hd.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2436 | 共同ピーアール | [公式窓口](https://www.kyodo-pr.co.jp/investor/contact) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2438 | アスカネット | [公式窓口](https://www.asukanet.co.jp/contents/ir/contact.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 244A | グロースエクスパートナーズ | [公式窓口](https://www.gxp-group.co.jp/contact/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2459 | アウンコンサルティング | [公式窓口](https://www.auncon.co.jp/ir/contact-ir/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 245A | ＩＮＧＳ | [公式窓口](https://ingsinc.co.jp/ir_contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2461 | ファンコミュニケーションズ | [公式窓口](https://www.fancs.com/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2462 | ライク | [公式窓口](https://www.like-gr.co.jp/inquiry/index.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2469 | ヒビノ | [公式窓口](https://www.hibino.co.jp/support/input-ir.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 246A | アスア | [公式窓口](https://www.asua.ne.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2471 | エスプール | [公式窓口](https://www.spool.co.jp/contact_ir/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2477 | 手間いらず | [公式窓口](https://www.temairazu.co.jp/contact/inquiry?subject=ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 247A | Ａｉロボティクス | [公式窓口](https://ai-robotics.co.jp/ir/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2480 | システム・ロケーション | [公式窓口](https://slc.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2483 | 翻訳センター | [公式窓口](https://www.honyakuctr.com/inquiry/general/?place=ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2488 | ＪＴＰ | [公式窓口](https://www.jtp.co.jp/contactus/ir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2489 | アドウェイズ | [公式窓口](https://ir.adways.net/inquiry.cgi) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 248A | キッズスター | [公式窓口](https://www.kidsstar.co.jp/contact/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2493 | イーサポートリンク | [公式窓口](https://www.e-supportlink.com/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2497 | ユナイテッド | [公式窓口](https://united.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2498 | オリエンタルコンサルタンツホールディングス | [公式窓口](https://www.oriconhd.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2502 | アサヒグループホールディングス | [公式窓口](https://forms.asahigroup-holdings.com/web-service/asahig-hd/ir/contact_ir/form.wsp.html?CMD=onForm) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2503 | キリンホールディングス | [公式窓口](https://faq.kirin.co.jp/form/kh_03.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2531 | 宝ホールディングス | [公式窓口](https://ir.takara.co.jp/form/ja/Contact.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2533 | オエノンホールディングス | [公式窓口](https://www.oenon.jp/customer/inquiry/input/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 254A | ＡＩフュージョンキャピタルグループ | [公式窓口](https://aifcg.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2573 | 北海道コカ・コーラボトリング | [公式窓口](https://www.hokkaido.ccbc.co.jp/form/ir-contact/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2585 | ライフドリンク　カンパニー | [公式窓口](https://form.movabletype.net/FFFE927C-1D05-11EC-A1F9-282636F7A6C0?embed=true) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2586 | フルッタフルッタ | [公式窓口](https://www.frutafruta.com/ir_info/ircontact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2587 | サントリービバレッジ＆フード | [公式窓口](https://ssl1.suntory.co.jp/apl/btcr/cp/CSUNF1307031/form) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2588 | プレミアムウォーターホールディングス | [公式窓口](https://premiumwater-hd.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2593 | 伊藤園 | [公式窓口](https://www.itoen.co.jp/form/inquiry-ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2594 | キーコーヒー | [公式窓口](https://www.keycoffee.co.jp/company/ir/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2612 | かどや製油 | [公式窓口](https://www.kadoya.com/contact/page01.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 261A | 日水コン | [公式窓口](https://reg34.smp.ne.jp/regist/is?SMPFORM=qgki-mclfsb-7dba4524d69aec7e84d1aab3348cfb97) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 265A | Ｈｍｃｏｍｍ | [公式窓口](https://hmcom.co.jp/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2667 | イメージ　ワン | [公式窓口](https://www.imageone.co.jp/inquiry/general/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2674 | ハードオフコーポレーション | [公式窓口](https://www.hardoff.co.jp/ir/) | 追加確認 | IRメール確認 | 個人条件の明示未確認 | 未確認 |
| 2678 | アスクル | [公式窓口](https://www.askul.co.jp/iqr/corpInquiryInputView/?inqKbn=2) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2689 | オルバディーブイエックスヘルスケア | [公式窓口](https://www.olbadvx.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 268A | リガク・ホールディングス | [公式窓口](https://rigaku-holdings.com/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2700 | 木徳神糧 | [公式窓口](https://cloud.swcms.net/kitoku-shinryoPublic/ja/contact/contact3/inquiry3.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2708 | 久世 | [公式窓口](https://www.kuze.co.jp/contact/form2.html) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2730 | エディオン | [公式窓口](https://www.edion.co.jp/contact/corporate) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2733 | あらた | [公式窓口](https://www.arata-gr.jp/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2737 | トーメンデバイス | [公式窓口](https://www.tomendevices.co.jp/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2750 | 石光商事 | [公式窓口](https://www.ishimitsu.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2762 | ＳＡＮＫＯ　ＭＡＲＫＥＴＩＮＧ　ＦＯＯＤＳ | [公式窓口](https://www.sankofoods.com/contact/index.php?type=2) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2764 | ひらまつ | [公式窓口](https://www.hiramatsu.co.jp/ir/inquiry.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2768 | 双日 | [公式窓口](https://www.sojitz.com/jp/contact/ir/input.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 276A | ククレブ・アドバイザーズ | [公式窓口](https://ccreb.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2778 | パレモ・ホールディングス | [公式窓口](https://palemo.co.jp/contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2780 | コメ兵ホールディングス | [公式窓口](https://komehyohds.com/ir/ircontact/index.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2789 | カルラ | [公式窓口](http://www.re-marumatu.co.jp/tousikajyouhou/IRotiawse.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 278A | Ｔｅｒｒａ　Ｄｒｏｎｅ | [公式窓口](https://terra-drone.net/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2790 | ナフコ | [公式窓口](https://www.nafco.tv/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2796 | ファーマライズホールディングス | [公式窓口](https://www.pharmarise.com/ir/contact.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2798 | ワイズテーブルコーポレーション | [公式窓口](https://www.ystable.co.jp/corporate/contactform_ir.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2804 | ブルドックソース | [公式窓口](https://contact.bulldog.jp/ir-contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 280A | ＴＭＨ | [公式窓口](https://www.tmh-inc.co.jp/ir/contact/index.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2810 | ハウス食品グループ本社 | [公式窓口](https://housefoods-group.com/inquiry/index.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2811 | カゴメ | [公式窓口](https://www.kagome.co.jp/company/ir/contact/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2814 | 佐藤食品工業 | [公式窓口](https://www.sato-foods.co.jp/other/contact.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2816 | ダイショー | [公式窓口](https://www.daisho-customer.jp/inquiry/media-shareholders) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2818 | ピエトロ | [公式窓口](https://www.pietro.co.jp/company/ir/faq.php) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 285A | キオクシアホールディングス | [公式窓口](https://www.kioxia-holdings.com/ja-jp/contact/agree-ir.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 286A | ユカリア | [公式窓口](https://eucalia.jp/inquiry_ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2871 | ニチレイ | [公式窓口](https://www.nichirei.co.jp/form/form_IR) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2874 | 横浜冷凍 | [公式窓口](https://reg31.smp.ne.jp/regist/is?SMPFORM=qhpj-mbkcnh-de1342356e218f82460798c1af598eb9) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2875 | 東洋水産 | [公式窓口](https://www.maruchan.co.jp/customer/inquiry.php) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2882 | イートアンドホールディングス | [公式窓口](https://f.msgs.jp/webapp/form/12105_pxr_6/index.do) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2883 | 大冷 | [公式窓口](https://www.dai-rei.co.jp/ir_info/ir_inquiry.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 2884 | ヨシムラ・フード・ホールディングス | [公式窓口](https://www.y-food-h.com/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 288A | ラクサス・テクノロジーズ | [公式窓口](https://corp.laxus.co/inquiry/individual?from=ir) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 2892 | 日本食品化工 | [公式窓口](https://www.nisshoku.co.jp/ir/ir-contact.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 2894 | 石井食品 | [公式窓口](https://www.ishiifood.co.jp/contact/form/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2901 | ウェルディッシュ | [公式窓口](https://wel-dish.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2903 | シノブフーズ | [公式窓口](https://www.shinobufoods.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 2904 | 一正蒲鉾 | [公式窓口](https://www.ichimasa.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 3092 | ＺＯＺＯ | [公式窓口](https://corp.zozo.com/contact/ir/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 3134 | Ｈａｍｅｅ | [公式窓口](https://hamee.co.jp/ir/contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 3197 | すかいらーくホールディングス | [公式窓口](https://corp.skylark.co.jp/ir/ir_inquiry/) | 確認済み | IRメール確認 | 個人等に制限あり | 受付対象に制限 |
| 3673 | ブロードリーフ | [公式窓口](https://www.broadleaf.co.jp/form/input/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 3923 | ラクス | [公式窓口](https://www.rakus.co.jp/ir/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 4058 | トヨクモ | [公式窓口](https://www.toyokumo.co.jp/ir/contact) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 個別回答なし |
| 4371 | コアコンセプト・テクノロジー | [公式窓口](https://www.cct-inc.co.jp/ir/inquiry/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 4413 | ボードルア | [公式窓口](https://www.baudroie.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 4417 | グローバルセキュリティエキスパート | [公式窓口](https://www.gsx.co.jp/ir/inquiry) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 4475 | ＨＥＮＮＧＥ | [公式窓口](https://hennge.com/jp/ir/inquiry/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 4481 | ベース | [公式窓口](https://www.basenet.co.jp/ir/contact.html) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 4493 | サイバーセキュリティクラウド | [公式窓口](https://www.cscloud.co.jp/contact/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 4971 | メック | [公式窓口](https://www.mec-co.com/contact/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 5132 | ｐｌｕｓｚｅｒｏ | [公式窓口](https://plus-zero.co.jp/ir/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 590A | ギフティグループ | [公式窓口](https://giftee-group.com/contact/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 6226 | 守谷輸送機工業 | [公式窓口](https://moriya-elevator.co.jp/inquiry/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 6240 | ヤマシンフィルタ | [公式窓口](https://www.yamashin-filter.co.jp/ja/form/form_redirect7.html) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 6254 | 野村マイクロ・サイエンス | [公式窓口](https://www.nomura-nms.co.jp/contact/05_02.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 6266 | タツモ | [公式窓口](https://tazmo.co.jp/contact/form02/) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 6278 | ユニオンツール | [公式窓口](http://ynirnem.uniontool.co.jp/info/Inqform.nsf/fmLoad?OpenForm&cd=ir) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 6339 | 新東工業 | [公式窓口](https://www.sinto.co.jp/inquiry/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 6387 | サムコ | [公式窓口](https://www.samco.co.jp/contact/investor/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 6532 | ベイカレント | [公式窓口](https://www.baycurrent.co.jp/contactus/) | 確認済み | IRメール確認 | 個人条件の明示未確認 | 窓口候補 |
| 6914 | オプテックスグループ | [公式窓口](https://www.optexgroup.co.jp/inquiry/form.php) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 6947 | 図研 | [公式窓口](https://www.zuken.co.jp/contact/?type=IR) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 7071 | アンビスホールディングス | [公式窓口](https://ir.amvis.com/ja/ir/contact1.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 7685 | ＢｕｙＳｅｌｌ　Ｔｅｃｈｎｏｌｏｇｉｅｓ | [公式窓口](https://buysell-technologies.com/contact/form-ir/) | 追加確認 | 案内・リンクのみ | 個人条件の明示未確認 | 窓口候補 |
| 7734 | 理研計器 | [公式窓口](https://www.rikenkeiki.co.jp/contact/ir) | 確認済み | 質問入力欄確認 | 個人受付の明示あり | 窓口候補 |
| 8078 | 阪和興業 | [公式窓口](https://www.hanwa.co.jp/contact/form1/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 9279 | ギフトホールディングス | [公式窓口](https://www.gift-group.co.jp/contact/ir) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 9416 | ビジョン | [公式窓口](https://www.vision-net.co.jp/ir/guide/contact.html) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 9558 | ジャパニアス | [公式窓口](https://jna.co.jp/ir_contact) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |
| 9692 | シーイーシー | [公式窓口](https://www.cec-ltd.co.jp/inquiry/ir/) | 確認済み | 質問入力欄確認 | 個人条件の明示未確認 | 窓口候補 |

## 受付条件・根拠

### 1301 極洋

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR案内ページのメールフォームリンクを確認。実フォーム取得は空のため入力項目・個人条件は未確認。

根拠：

- [公式ページ](https://www.kyokuyo.co.jp/ir/contact/index.html)／[保存証拠](evidence/1301/02.json)（取得 2026-10-11T03:58:42.295917+00:00）：問い合わせ IRに関するお問い合わせ、ご要望は下記までお願いいたします。 住所 〒107-0052 東京都港区赤坂三丁目3番5号 株式会社 極洋 管理本部 経営管理部 法務ＩＲ課 メールフォームによるお問い合わせ こちら よりお問い合わせください。 （受付時間） 平日9:00～17:00 (土曜・日曜・祝日、及び年末年始・盆休暇、その他当社休業日を除く) お客様の個人情報、お寄せいただいたご意見・ご質問内容は厳重に取り扱いま

### 130A Ｖｅｒｉｔａｓ　Ｉｎ　Ｓｉｌｉｃｏ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式お問い合わせ一覧からIR専用ページが案内されている。入力欄は保存取得では確認できない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://www.veritasinsilico.com/form/jp/agree_02.html)／[保存証拠](evidence/130A/06.json)（取得 2026-10-11T03:58:52.835568+00:00）：IRに関するお問い合わせ \| 株式会社 Veritas In Silico \| form
- [公式ページ](https://www.veritasinsilico.com/jp/contact.html)／[保存証拠](evidence/130A/04.json)（取得 2026-10-11T03:58:48.999011+00:00）：IRに関するお問い合わせ

### 135A ＶＲＡＩＮ　Ｓｏｌｕｔｉｏｎ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。会社名は必須だが、入力欄のplaceholderに個人の方は「個人」と入力する案内がある。
- 氏名・ふりがな・メールアドレス・電話番号等が必須表示。電話・手紙で回答する場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://vrain.co.jp/ir/inquiry/)／[保存証拠](evidence/135A/06.json)（取得 2026-10-11T03:58:51.081065+00:00）：IRについてのお問い合わせ 下記のお問い合わせフォームに必要事項を入力のうえ下の「上記の内容で送信する」をクリックして下さい。
- [公式ページ](https://vrain.co.jp/ir/inquiry/)／[保存証拠](evidence/135A/06.json)（取得 2026-10-11T03:58:51.081065+00:00）：会社名 必須
- [公式ページ](https://vrain.co.jp/ir/inquiry/)／[保存証拠](evidence/135A/06.json)（取得 2026-10-11T03:58:51.081065+00:00）：お問い合せの内容によりましては、電話やお手紙でお返事する場合もございますので、お電話番号・ご住所は、よくご確認してくださいますようお願いします。
- [公式ページ](https://vrain.co.jp/ir/inquiry/)／[保存証拠](evidence/135A/06.json)（取得 2026-10-11T03:58:51.081065+00:00）：個人の方は「個人」と入力してください

### 1375 ユキグニファクトリー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答の転載・二次利用をご遠慮との記載。
- 返信方法が電話・手紙になる場合がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.yukiguni-factory.co.jp/contact/)／[保存証拠](evidence/1375/03.json)（取得 2026-10-11T03:58:44.019170+00:00）：報の適正な取り扱いに関する基本方針 」 をご覧いただいた上でご利用ください。 お問い合わせの種類 商品に関するお問い合わせ 株主優待に関するお問い合わせ 採用に関するお問い合わせ IR関連に関するお問い合わせ メディア関係者の方 その他のお問い合わせ お名前 住所 電話番号 メールアドレス お問い合わせ内容 お問い合わせフォームをご利用の際は、必ず 「 個人情報の適正な取扱いに関する基
- [公式ページ](https://www.yukiguni-factory.co.jp/contact/)／[保存証拠](evidence/1375/03.json)（取得 2026-10-11T03:58:44.019170+00:00）：た、お問い合わせ内容によっては、Eメールではなく、お電話やお手紙でご返答させていただく場合がございますので、ご了承ください。 当社からのお返事は、お客様個人宛にお送りするものです。一部または全部を転載、二次利用することはご遠慮ください。 氏名 会社名 国名 住所 電話番号 メールアドレス お問い合わせ内容 お問い合わせフォームをご利用の際は、必ず 「 個人情報の適正な取り扱いに関する基本方針 」 をご覧いただいた
- [公式ページ](https://www.yukiguni-factory.co.jp/contact/)／[保存証拠](evidence/1375/03.json)（取得 2026-10-11T03:58:44.019170+00:00）：いやメール設定環境の影響が考えられます。ご確認の上、再度送信してください。 いただいたメールに対して、お返事を差し上げられない場合がございます。 また、お問い合わせ内容によっては、Eメールではなく、お電話やお手紙でご返答させていただく場合がございますので、ご了承ください。 当社からのお返事は、お客様個人宛にお送りするものです。一部または全部を転載、二次利用することはご遠慮ください。 氏名 会社名 国名 住所 電話番

### 1377 サカタのタネ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://corporate.sakataseed.co.jp/contact/)／[保存証拠](evidence/1377/02.json)（取得 2026-10-11T03:58:44.464289+00:00）：決算など投資家情報に関するお問い合わせ 業績や決算発表など。 投資家情報に関するご質問 お問い合わせフォーム 045-945-8800 本社代表

### 137A Ｃｏｃｏｌｉｖｅ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お電話でのお問い合わせは承っておりませんのでご了承ください。
- お問い合わせの内容によっては返信に時間がかかる場合や、 回答を差し控えさせていただく場合もございます。
- また、土・日、祝日、年末年始休業期間等は、 翌営業日以降の対応とさせていただきます。

注意・未確認：公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://cocolive.co.jp/ir/faq/)／[保存証拠](evidence/137A/02.json)（取得 2026-10-11T03:58:43.314587+00:00）：IRお問い合わせ
- [公式ページ](https://campage.jp/cocolive-ir/form)／[保存証拠](evidence/137A/03.json)（取得 2026-10-11T03:58:46.288266+00:00）：IR（投資家情報）に関する お問い合わせ
- [公式ページ](https://campage.jp/cocolive-ir/form)／[保存証拠](evidence/137A/03.json)（取得 2026-10-11T03:58:46.288266+00:00）：お電話でのお問い合わせは承っておりませんのでご了承ください。
- [公式ページ](https://campage.jp/cocolive-ir/form)／[保存証拠](evidence/137A/03.json)（取得 2026-10-11T03:58:46.288266+00:00）：お問い合わせの内容によっては返信に時間がかかる場合や、 回答を差し控えさせていただく場合もございます。
- [公式ページ](https://campage.jp/cocolive-ir/form)／[保存証拠](evidence/137A/03.json)（取得 2026-10-11T03:58:46.288266+00:00）：また、土・日、祝日、年末年始休業期間等は、 翌営業日以降の対応とさせていただきます。

### 1383 ベルグアース

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 返信が3営業日を超えても届かない場合はアドレス・受信設定を確認して再問合せ等を案内。返信期限の保証ではない。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://bergearth.co.jp/contact/?contact_option=2)／[保存証拠](evidence/1383/02.json)（取得 2026-10-11T03:58:45.045400+00:00）：のお間違い、ドメイン拒否などの可能性がございます。 大変お手数ですが、再度、お問い合わせ頂くか、お電話にてお問い合わせください。 お問い合わせ種別 必須 製品に関するお問い合わせ 株主・投資家に関するお問い合わせ 採用情報に関するお問い合わせ その他のお問い合わせ お名前 必須 メールアドレス 必須 電話番号 必須 都道府県 必須 —以下から選択してください— 北海道 青森県 岩手県 宮城
- [公式ページ](https://bergearth.co.jp/contact/?contact_option=2)／[保存証拠](evidence/1383/02.json)（取得 2026-10-11T03:58:45.045400+00:00）：等 適時開示情報 報告書 株主総会関連 その他IR資料 その他 IRカレンダー 電子公告 よくあるご質問 お問い合わせ頂いた内容に関して、担当者からメールでご返信させて頂きます。 返信が3営業日を超えても届かない場合は、メールアドレスのお間違い、ドメイン拒否などの可能性がございます。 大変お手数ですが、再度、お問い合わせ頂くか、お電話にてお問い合わせください。 お問い合わせ種別 必須 製品に関

### 1384 ホクリヨウ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答の転載・二次利用に関する注意事項がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.hokuryo.co.jp/contact/)／[保存証拠](evidence/1384/03.json)（取得 2026-10-11T03:58:44.124107+00:00）：タンを押してください。 お問い合わせが完了しました。 お名前 必須 名字だけでも可 メールアドレス 必須 確認用 お問い合わせの内容 必須 当社製品に関して サービス内容に関して IRに関して メッセージ 必須 ファイル添付 × ファイルのサイズの上限は合計で10Mです。 当社製品に関してを選択した場合は、以下も入力してください。 商品名 必須 ※1 賞味期限 必須 ※
- [公式ページ](https://www.hokuryo.co.jp/contact/)／[保存証拠](evidence/1384/03.json)（取得 2026-10-11T03:58:44.124107+00:00）：休暇・年末年始）にいただいたお問い合わせは、翌営業日以降に返信しますことをご了承ください。 弊社からの回答は、お客様個人宛てにお送りするものです。 当社の許可なく、一部または全部を転載、二次利用することはご遠慮ください。 お問い合わせ内容によっては、ご回答までにお時間を要する場合がございます。予めご了承ください。 【個人情報の取り扱いについて】 お客様の個人情報

### 138A 光フードサービス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 共通フォームのご用件に「IRに関するお問い合わせ」がある。社名欄は法人の場合と表示。
- 内容により回答が遅れる・回答できない場合がある。1週間を過ぎても返信がない場合の再問い合わせ案内があるが、返信期限の保証ではない。
- サービス等の営業・提案は受け付けず、担当者との面談も受けない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://hikari-food-service.jp/contact/)／[保存証拠](evidence/138A/03.json)（取得 2026-10-11T03:58:43.812462+00:00）：ご用件 IRに関するお問い合わせ 店舗に関するお問い合わせ 採用に関するお問い合わせ FCに関するお問い合わせ その他ご相談
- [公式ページ](https://hikari-food-service.jp/contact/)／[保存証拠](evidence/138A/03.json)（取得 2026-10-11T03:58:43.812462+00:00）：社名（法人の場合）
- [公式ページ](https://hikari-food-service.jp/contact/)／[保存証拠](evidence/138A/03.json)（取得 2026-10-11T03:58:43.812462+00:00）：お問い合わせ内容によっては、お時間を頂戴する場合やお返事を差し上げられない場合がございます。
- [公式ページ](https://hikari-food-service.jp/contact/)／[保存証拠](evidence/138A/03.json)（取得 2026-10-11T03:58:43.812462+00:00）：一週間を過ぎてもお返事が届かない場合は再度お問い合わせください。

### 1401 エムビーエス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.homemakeup.co.jp/contact-list/contact.html)／[保存証拠](evidence/1401/04.json)（取得 2026-10-11T03:58:46.607306+00:00）：IR、お知らせ、全体に関するお問い合わせ｜株式会社エムビーエス 主要ページへ移動 メニューへ移動 ページ下へ移動 サイト内検索 検索する IR情報 IR情報 適時開示 決算短信 IR資料 お知らせ 会社概要 会社概要 社

### 1407 ウエストホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 受付区分は「IR取材」。一般のIR質問の扱いは追加確認が必要。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 保存本文に Vue の未展開テンプレートも含まれる。表示後の入力条件と「IR取材」での一般質問の受付は未検証。

根拠：

- [公式ページ](https://www.west-gr.co.jp/contact/)／[保存証拠](evidence/1407/03.json)（取得 2026-10-11T03:58:44.033263+00:00）：ST GROUP Contact お問い合わせ 必須項目のご入力 入力内容のご確認 送信完了 お問い合わせ種別 産業用・営農型太陽光 メガソーラー エスコ 工事 製品・材料 採用 IR取材 その他 {{ お問い合わせ種別 }} お名前 {{ 姓 }} {{ 名 }} お名前（ふりがな） {{ せい }} {{ めい }} 会社名・組織名 {{ 会社名・組織名 }} 
- [公式ページ](https://www.west-gr.co.jp/contact/)／[保存証拠](evidence/1407/03.json)（取得 2026-10-11T03:58:44.033263+00:00）：ST GROUP Contact お問い合わせ 必須項目のご入力 入力内容のご確認 送信完了 お問い合わせ種別 産業用・営農型太陽光 メガソーラー エスコ 工事 製品・材料 採用 IR取材 その他 {{ お問い合わせ種別 }} お名前 {{ 姓 }} {{ 名 }} お名前（ふりがな） {{ せい }} {{ めい }} 会社名・組織名 {{ 会社名・組織名 }} 

### 1414 ショーボンドホールディングス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`info@sho-bondhd.jp`。

取得範囲の受付条件：

- メールにはホームページ内容の質問である旨・名前・電話番号またはメールアドレスを明記。
- 質問により回答準備に相応の期間が必要、または回答できない場合がある。
- 各決算日の翌日から決算発表日まで沈黙期間で、決算に関する回答を控える。

注意・未確認：個人投資家の明示受付条件、字数制限、メール到達・返信は未確認。

根拠：

- [公式ページ](https://www.sho-bondhd.jp/inquiry/)／[保存証拠](evidence/1414/03.json)（取得 2026-10-11T03:58:44.085073+00:00）：本ホームページの内容（IR情報等）に関するお問い合わせは、以下のご連絡先宛てにお願いいたします。なお、採用に関するお問い合わせは、 採用情報のページ をご覧ください。 ご連絡先 ショーボンドホールディングス株式会社 総務部 〒103-0015 東京都中央区日本橋箱崎町7番8号 TEL：03-6892-7101（代表） Eメール： info@sho-bondhd.jp
- [公式ページ](https://www.sho-bondhd.jp/inquiry/)／[保存証拠](evidence/1414/03.json)（取得 2026-10-11T03:58:44.085073+00:00）：※お問い合わせの際には、本ホームページの内容に関するご質問である旨と、お名前とご連絡先（電話番号またはe-mailアドレス）を、お知らせください。 ※ご質問へは、当社内で適切な担当者を選定のうえ回答いたします。ご質問内容により、回答準備に必要な相応の期間を頂戴する場合や、回答自体をいたしかねる場合がございますことを、予めご承知おきください。
- [公式ページ](https://www.sho-bondhd.jp/ir/policy/)／[保存証拠](evidence/1414/07.json)（取得 2026-10-11T03:58:49.555349+00:00）：各決算日の翌日から決算発表日までの期間を沈黙期間とし、この期間については決算に関するお問い合わせへの回答を控えさせていただきます。

### 1417 ミライト・ワン

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.mirait-one.com/contact/inquiry.php?type=01)／[保存証拠](evidence/1417/03.json)（取得 2026-10-11T03:58:45.907212+00:00）：IRに関するお問い合わせ \| 株式会社ミライト・ワン 日本語 english 採用情報 日本語 english HOME 企業情報 ニュース サービス・ソリューション 事例紹介 ESG IR情報 採用情報
- [公式ページ](https://www.mirait-one.com/contact/inquiry.php?type=01)／[保存証拠](evidence/1417/03.json)（取得 2026-10-11T03:58:45.907212+00:00）：方針」 をご覧ください。 下記フォームに必要事項を記入の上、「送信内容の確認画面に進む」ボタンをクリックしてください。 は必須項目となります。 お問い合わせ件名 お問い合わせ内容 法人・個人 法人 個人 お名前 お名前（カタカナ） 会社名 部署名 メールアドレス メールアドレス（確認用） 郵便番号 都道府県 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県

### 141A トライアルホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 株主・投資家向けIR専用フォーム。問い合わせ前にFAQ確認を案内。
- IR以外は回答しない。会社名欄はあるが、今回保存証拠に個人の記入方法や会社名必須の明示は見当たらない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://trial-holdings.inc/contact/ir/)／[保存証拠](evidence/141A/04.json)（取得 2026-10-11T03:58:51.780268+00:00）：IR（株主・投資家向け情報）に関するお問い合わせ専用フォームです。
- [公式ページ](https://trial-holdings.inc/contact/ir/)／[保存証拠](evidence/141A/04.json)（取得 2026-10-11T03:58:51.780268+00:00）：IRに関すること以外のお問合せをいただきましても、お返事を差し上げることはできませんのであらかじめご了承ください。
- [公式ページ](https://trial-holdings.inc/contact/ir/)／[保存証拠](evidence/141A/04.json)（取得 2026-10-11T03:58:51.780268+00:00）：会社名 ご氏名 姓 名 Eメールアドレス 電話番号 お問い合せ件名 お問い合せの詳細をご記入ください

### 1420 サンヨーホームズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 必須項目は赤色指定。テキスト抽出では色による指定を完全には復元できない。
- 許可のない回答内容の転用・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.sanyohomes.co.jp/ir/contact/)／[保存証拠](evidence/1420/04.json)（取得 2026-10-11T03:58:55.124854+00:00）：IR情報 お問い合わせ \| サンヨーホームズ株式会社 お問い合わせ サイトマップ IR情報 企業情報 採用情報 サンヨーホームズTOP IR情報 お問い合わせ 土曜･日曜･祝休日、年末年始･夏季休暇期間
- [公式ページ](https://www.sanyohomes.co.jp/ir/contact/)／[保存証拠](evidence/1420/04.json)（取得 2026-10-11T03:58:55.124854+00:00）：て入力いただきますようお願いします。 入力いただいたお客様の個人情報の取り扱いについては、 プライバシーポリシー をご参照ください。 情報の入力 ▼お客様の基本情報を入力ください 赤色の項目は必須項目です お名前 （姓） （名） ふりがな （姓） （名） 性別 男性 女性 年齢 歳 ▼ご連絡先を入力ください。 郵便番号 ‐ 番号を入力しボタンを押してください。 番号を入力しボタンを
- [公式ページ](https://www.sanyohomes.co.jp/ir/contact/)／[保存証拠](evidence/1420/04.json)（取得 2026-10-11T03:58:55.124854+00:00）：こちら お問い合せの内容は、できるだけ具体的にお願いいたします。内容によっては、回答まで時間を要したり、当社から折り返し質問をさせていただく場合がございます。予めご了承ください。 当社の許可なく回答内容の一部または全部を転用、二次利用することはご遠慮ください。 お問い合わせの種類 選択して下さい 決算関連について 株式関連について その他のご質問 サイトポリシー プライバシーポリシー 個人情報保護方針

### 142A ジンジブ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@jinjib.co.jp`。

取得範囲の受付条件：

- IR問い合わせ先として経営企画部の ir@jinjib.co.jp を公開。
- 内容により返信まで時間がかかる場合がある。個人投資家の利用条件は明示されていない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://jinjib.co.jp/ir/contact/)／[保存証拠](evidence/142A/06.json)（取得 2026-10-11T03:58:58.414020+00:00）：IRに関するお問い合わせ先 経営企画部 担当：新田 メール ir@jinjib.co.jp
- [公式ページ](https://jinjib.co.jp/ir/contact/)／[保存証拠](evidence/142A/06.json)（取得 2026-10-11T03:58:58.414020+00:00）：お問い合わせの内容などにより、お返事に日時を頂戴する場合もございます

### 1433 ベステラ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.besterra.co.jp/contact/)／[保存証拠](evidence/1433/03.json)（取得 2026-10-11T03:58:52.615144+00:00）：not fill) お問い合わせ内容 お問い合わせの種類を選択してください。 プラント解体 3D計測・データサービス 人材派遣・紹介サービス 採用について 採用応募 メディア取材 IRについて その他 応募職種 応募職種を選択してください。 施工管理職 工事事務職 ３Ｄ設計職 企画職 総合職(新卒採用) お名前 ※必須 ふりがな ※必須 貴社名 部署名 メールアドレス 

### 1435 ｒｏｂｏｔ　ｈｏｍｅ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 翌営業日以降の回答、内容による無回答・時間を要する場合を案内。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://corp.robothome.jp/contact/form/ir)／[保存証拠](evidence/1435/07.json)（取得 2026-10-11T03:59:00.691402+00:00）： 内容によりお答えできない場合や、お時間を要する場合がございます。 予めご了承いただきますようお願いします。 *は必須事項です。 法人名 お名前 * ふりがな メールアドレス * お問い合わせ内容 * 個人情報のお取扱いについて 株式会社robot home 個人情報保護管理者 コンプライアンス統括本部長 ご入力いただく個人情報は、サービス提供における以下の目的に利用いたします
- [公式ページ](https://corp.robothome.jp/contact/form/ir)／[保存証拠](evidence/1435/07.json)（取得 2026-10-11T03:59:00.691402+00:00）：。 なお、回答にお時間をいただく場合がございますので、あらかじめご了承ください。 入力内容に誤りがあります。 ご確認のうえ、再度ご入力ください。 ご入力いただいたメールアドレス宛に翌営業日以降に回答いたします。 内容によりお答えできない場合や、お時間を要する場合がございます。 予めご了承いただきますようお願いします。 *は必須事項です。 法人名 お名前 * ふりがな メールアドレス *
- [公式ページ](https://corp.robothome.jp/contact)／[保存証拠](evidence/1435/03.json)（取得 2026-10-11T03:58:54.230166+00:00）：窓口をお選びください。 株式会社robot home 01 購入・売却のご相談に関するお問い合わせ 02 入居者さまのお問い合わせ窓口 03 解約・退去に関するお問い合わせ 04 IRに関するお問い合わせ 05 人事に関するお問い合わせ 06 広報に関するお問い合わせ 07 仲介業者さまの空室確認に関するお問い合わせ 08 その他のお問い合わせ 株式会社rh investment 

### 1436 グリーンエナジー＆カンパニー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名は任意。個人投資家の受付を明記した表現までは確認していない。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://green-energy.co.jp/contact/)／[保存証拠](evidence/1436/03.json)（取得 2026-10-11T03:58:54.413239+00:00）：ずご入力ください。 メールアドレスは正しくご入力ください。（当社より返信メールが届きません。） 半角カナ入力は文字化けの原因となりますのでご注意ください。 お問い合わせ内容 必須 IR・株主・投資家の方 取材・メディアの方 採用について ビジネスパートナー・業務提携 系統用蓄電所 太陽光発電所 ネットゼロ・エネルギー・ハウス、トレーラーハウス スマート農業・農業GX 太陽光・蓄電
- [公式ページ](https://green-energy.co.jp/contact/)／[保存証拠](evidence/1436/03.json)（取得 2026-10-11T03:58:54.413239+00:00）：トゼロ・エネルギー・ハウス、トレーラーハウス スマート農業・農業GX 太陽光・蓄電所のメンテナンス 土地売却・土地活用 その他お問い合わせ お名前 必須 お名前（フリガナ） 必須 会社名 任意 住所 任意 〒 住所自動入力 都道府県名 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県

### 1438 岐阜造園

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.gifu-zohen.co.jp/ir/contact)／[保存証拠](evidence/1438/04.json)（取得 2026-10-11T03:59:00.737377+00:00）： よくあるご質問 免責事項 採用情報 お問い合わせ お問い合わせ IRについて 協力会社募集について ｜ EN IR 情報 IR INFORMATION TOP > IR情報 > IRお問い合わせ メニュー IR MENU IR情報TOP IRニュース 経営情報 個人投資家の皆様へ 財務ハイライト IRライブラリー 株式について IRカレンダー IRお問い合わせ よくあるご

### 143A イシン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。貴社名、氏名、電話番号、メール、問い合わせ内容が必須表示。
- 貴社名必須だが、所属のない個人の記入方法は今回の保存証拠では未確認。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 所属を求める欄が必須表示だが、所属のない個人の記入方法・利用可否は未確認。

根拠：

- [公式ページ](https://ishin1853.co.jp/ir/contact)／[保存証拠](evidence/143A/04.json)（取得 2026-10-11T03:58:56.094131+00:00）：IRに関するお問い合わせは、下記の欄に内容をご記入の上、お気軽にお問い合わせください。
- [公式ページ](https://ishin1853.co.jp/ir/contact)／[保存証拠](evidence/143A/04.json)（取得 2026-10-11T03:58:56.094131+00:00）：貴社名 必須 必須
- [公式ページ](https://ishin1853.co.jp/ir/contact)／[保存証拠](evidence/143A/04.json)（取得 2026-10-11T03:58:56.094131+00:00）：お電話番号 必須 必須 メールアドレス 必須 必須 お問い合わせ内容 必須 必須

### 1444 ニッソウ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`irkoho@reform-nisso.co.jp`。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://reform-nisso.co.jp/company/ir/)／[保存証拠](evidence/1444/02.json)（取得 2026-10-11T03:58:57.603342+00:00）：だけます。 株主総会 株主総会の召集通知書、報告書、決議通知書などを掲載しております。 業績ハイライト 株式情報 株主・投資家の皆様へ ディスクロージャーポリシー よくあるご質問 IRお問い合わせ 電子公告 免責事項 サービスサイトはこちら PAGE TOP お問い合わせ サイトポリシー 個人情報保護方針 サイトマップ Copyright (C) Nisso Corpora

### 1450 ＴＡＮＡＫＥＮ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用案内ページから外部フォームを確認。保存時に robots_access_denied_stopped で実フォームは未取得。アクセス制御を回避していない。

根拠：

- [公式ページ](https://www.tanaken-1982.co.jp/ja/contact/contact3.html)／[保存証拠](evidence/1450/03.json)（取得 2026-10-11T03:59:00.644204+00:00）：IRお問い合わせ \| お問い合わせ \| TANAKEN株式会社 企業情報 社長挨拶 企業理念 会社概要 役員一覧 沿革 組織図 品質方針・環境方針・労働安全衛生方針 アクセス 業務内容 解体事業 

### 145A Ｌ　ｉｓ　Ｂ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。属性に「個人投資家」「機関投資家」「証券会社」「その他法人」がある。
- FAQを事前確認。非公開情報、金融商品取引法第166条の重要事項、株式市場の値動き、誹謗中傷には回答しない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://l-is-b.com/ja/ir/inquiry/)／[保存証拠](evidence/145A/05.json)（取得 2026-10-11T03:59:03.761026+00:00）：L is BのIRについてのお問い合わせは、下記のフォームからお寄せください。
- [公式ページ](https://l-is-b.com/ja/ir/inquiry/)／[保存証拠](evidence/145A/05.json)（取得 2026-10-11T03:59:03.761026+00:00）：個人・法人 個人投資家 機関投資家 証券会社 その他法人 会社名 お名前 ふりがな メールアドレス 電話番号 お問い合わせ内容
- [公式ページ](https://l-is-b.com/ja/ir/inquiry/)／[保存証拠](evidence/145A/05.json)（取得 2026-10-11T03:59:03.761026+00:00）：非公開情報（業績動向など）に関するお問い合わせ 金融商品取引法第166条の「重要事項」に該当する可能性のあるお問い合わせ 株式市場の値動きに関するお問い合わせ 誹謗中傷に該当するメッセージやお問い合わせ

### 146A コロンビア・ワークス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 共通フォームにIR取材・投資家の問い合わせ選択肢がある。会社名・学校名・所属は任意。
- 氏名・メールアドレス・電話番号・住所・問い合わせ内容が必須表示。内容により回答まで時間がかかる場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://columbiaworks.jp/contact/)／[保存証拠](evidence/146A/03.json)（取得 2026-10-11T03:58:59.357472+00:00）：お問い合わせ項目 必須 事業に関するご連絡・お問い合わせ IR取材・投資家の方からのお問い合わせ 求人に対するご応募
- [公式ページ](https://columbiaworks.jp/contact/)／[保存証拠](evidence/146A/03.json)（取得 2026-10-11T03:58:59.357472+00:00）：会社名・学校名・所属 任意
- [公式ページ](https://columbiaworks.jp/contact/)／[保存証拠](evidence/146A/03.json)（取得 2026-10-11T03:58:59.357472+00:00）：メールアドレス 必須 電話番号 必須 住所 必須 お問い合わせ内容 必須
- [公式ページ](https://columbiaworks.jp/contact/)／[保存証拠](evidence/146A/03.json)（取得 2026-10-11T03:58:59.357472+00:00）：Q. 証券コードは何番ですか？ A. 146Aです。

### 148A ハッチ・ワーク

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IRページには「IRについてのお問い合わせ」から https://hatchwork.co.jp/contact へのリンクがある。
- 外部一般フォームは文字化けしており、IR用の入力欄・受付条件と公式IRリンク先との到達関係を保存証拠だけで十分確認できない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。 / 保存した外部一般フォーム03/05.jsonに文字化けあり。日本語のIR用途・受付制限を復元・推測していない。

根拠：

- [公式ページ](https://hatchwork.co.jp/ir)／[保存証拠](evidence/148A/02.json)（取得 2026-10-11T03:59:00.552517+00:00）：IRについてのお問い合わせ

### 1491 中外鉱業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.chugaikogyo.co.jp/contact/)／[保存証拠](evidence/1491/03.json)（取得 2026-10-11T03:59:01.416991+00:00）：P 3 送信完了 STEP 1 お問い合わせ内容入力 STEP 2 入力内容の確認 STEP3 送信完了 お問い合わせ内容入力 入力内容の確認 送信完了 お問い合わせの件名 必須 株主・投資家情報に関するお問い合わせ その他 お名前 必須 フリガナ 必須 企業・大学・研究所名 所属部署名 郵便番号 ご住所 電話番号 メールアドレス 必須 お問い合わせ内容 必須 入力内容の確認 会社情報 会社情

### 149A シンカ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@thinca.co.jp`。

取得範囲の受付条件：

- IR問い合わせメールとして ir@thinca.co.jp を公開。返信に時間がかかる場合がある。
- 個人の受付条件・返信期限は今回の保存窓口ページでは明示されていない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.thinca.co.jp/ir/contact/)／[保存証拠](evidence/149A/04.json)（取得 2026-10-11T03:59:03.456853+00:00）：IRに関するお問い合わせ先 メール ir@thinca.co.jp
- [公式ページ](https://www.thinca.co.jp/ir/contact/)／[保存証拠](evidence/149A/04.json)（取得 2026-10-11T03:59:03.456853+00:00）：お問い合わせの内容などにより、お返事に日時を頂戴する場合もございます

### 150A ＪＳＨ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IR問い合わせページにフォーム利用の説明があるが、保存GETでは質問入力欄を確認できない。
- 問い合わせ内容により電話・手紙で回答する場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://www.jsh-japan.jp/ir/inquiry/)／[保存証拠](evidence/150A/04.json)（取得 2026-10-11T03:59:02.639889+00:00）：IRについてのお問い合わせ
- [公式ページ](https://www.jsh-japan.jp/ir/inquiry/)／[保存証拠](evidence/150A/04.json)（取得 2026-10-11T03:59:02.639889+00:00）：下記のお問い合わせフォームに必要事項を入力のうえ下の「確認」 をクリックして下さい。
- [公式ページ](https://www.jsh-japan.jp/ir/inquiry/)／[保存証拠](evidence/150A/04.json)（取得 2026-10-11T03:59:02.639889+00:00）：お問い合せの内容によりましては、電話やお手紙でお返事する場合もございます

### 1514 住石ホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 各四半期末翌日から決算発表まで沈黙期間。決算・業績質問への回答を控える。
- 非公開情報、直近業績動向、株価の値動き、重要事実に該当し得る事項等への回答は控える。
- ご意見・ご感想には個別回答しない。質問内容により回答遅延・回答できない場合がある。
- 回答の一部または全部の転載・二次利用は控える。
- 氏名・ふりがな・メール・電話・住所・問い合わせ内容の必須表示と個人情報への同意を確認。

注意・未確認：個人投資家としての明示受付条件・字数制限・送信後の到達や返信は未確認。

根拠：

- [公式ページ](https://www.sumiseki.co.jp/ir/disclosure.html)／[保存証拠](evidence/1514/07.json)（取得 2026-10-11T03:59:09.842708+00:00）：（IRに関するお問い合わせの際のお願い） 当社は、公平かつ正確な情報提供を徹底し、回答の一貫性および業務の効率化を図るため、IRに関するお問い合わせ対応を電話から当社ホームページのお問い合わせフォームに一本化いたします。
- [公式ページ](https://www.sumiseki.co.jp/sub/contact.html)／[保存証拠](evidence/1514/03.json)（取得 2026-10-11T03:59:04.423300+00:00）：IRに関するお問い合わせは 事前にこちらをご確認ください
- [公式ページ](https://www.sumiseki.co.jp/sub/contact.html)／[保存証拠](evidence/1514/03.json)（取得 2026-10-11T03:59:04.423300+00:00）：所属先 （会社名・学校名） お名前 ＊ ふりがな ＊ メールアドレス ＊ メールアドレス(確認) ＊ 電話番号 ＊ ご住所 ＊ 郵便番号 ＊ 都道府県 ＊ 市区町村 ＊ 町域／番地 ＊ 建物名／部屋番号 お問い合わせ内容 ＊ 個人情報の取り扱いについて に同意する 内容のご確認
- [公式ページ](https://www.sumiseki.co.jp/ir/disclosure.html)／[保存証拠](evidence/1514/07.json)（取得 2026-10-11T03:59:09.842708+00:00）：各四半期の決算期末日の翌日から当該決算発表までの期間を沈黙期間とし、この沈黙期間中は、電話やメールフォームを含むあらゆる問い合わせに対して、決算や業績に関する質問への回答は控える等、社内ルールを設けて対応しています。
- [公式ページ](https://www.sumiseki.co.jp/ir/disclosure.html)／[保存証拠](evidence/1514/07.json)（取得 2026-10-11T03:59:09.842708+00:00）：お問い合わせの内容によっては、回答までにお時間をいただく場合や、お返事を差し上げられない場合がございます。また、以下の内容に関するお問い合わせには回答を差し控えておりますので、あらかじめご了承ください。 非公開情報（直近の業績動向など） 株価の値動きに関するご質問 金融商品取引法上の重要事実に該当する可能性のある事項（株主還元、株価対策など） ご意見・ご感想（社内で共有いたしますが、個別のご回答はいたしかねます） なお、当社からのご回答内容の一部または全部の転載・二次利用はご遠慮いただきますようお願い申し上げます。

### 1515 日鉄鉱業

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 18 歳未満は保護者同意が必要。
- 内容や状況により回答遅延・無回答。土日祝は翌営業日以降。
- 回答を許可なく問い合わせ目的以外に使用しない。フォーム案内・個人情報方針への同意。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.nittetsukou.co.jp/ir/faq/)／[保存証拠](evidence/1515/03.json)（取得 2026-10-11T03:59:03.534091+00:00）：日鉄鉱業(株) 経営企画部 広報・IR課 〒100-0004 東京都千代田区大手町一丁目5番1号（大手町ファーストスクエアウエストタワー21階） TEL : 03-3284-0518 受付時間：9時00分～12時00分・13時00分～17時15分（土曜・日曜・祝日を除く） メールでの お問い合わせ
- [公式ページ](https://www.nittetsukou.co.jp/contact/)／[保存証拠](evidence/1515/04.json)（取得 2026-10-11T03:59:05.145052+00:00）：メールによるお問い合わせへの回答には、お時間がかかる場合（土曜日、日・祝日は翌営業日以降のご対応となります）、もしくは回答できない場合がございますので、予めご了承ください。 お問い合わせいただきました内容についての当社からの回答は、お客さま個人に宛てたものです。当社からの回答の一部またはすべてを、当社の許可なくお問い合わせの目的以外でご使用になることはご遠慮ください。 お問い合わせフォームは、セキュリティとしてSSL（データ暗号化技術）を使用しております。 日鉄鉱業(株)における個人情報の取り扱いについては「 プライバシーポリシー 」をご参照ください。 上記で示した事項は、法令その他の事情により変更する場合があります。 上記に同意してフォームに進む

### 1518 三井松島ホールディングス

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 未公開の業績動向・見込み、重要事実に該当し得る株価対策、株価動向等の質問は回答対象外。
- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.mitsui-matsushima.co.jp/contact/)／[保存証拠](evidence/1518/04.json)（取得 2026-10-11T03:59:05.079653+00:00）：から回答した内容について、その一部又は全部を転載、二次利用することはご遠慮ください。 下記の項目にご記入下さい。 Japan お問い合わせ種別 必須 —以下から選択してください— 投資家向け広報（IR）のお問い合わせ 取材のお問い合わせ 株主優待のお問い合わせ その他のお問い合わせ お問い合わせ内容 必須 法人・個人 必須 —以下から選択してください— 法人 個人事業主 個人 会社名（法人様・
- [公式ページ](https://www.mitsui-matsushima.co.jp/contact/)／[保存証拠](evidence/1518/04.json)（取得 2026-10-11T03:59:05.079653+00:00）：問い合わせ種別 必須 —以下から選択してください— 投資家向け広報（IR）のお問い合わせ 取材のお問い合わせ 株主優待のお問い合わせ その他のお問い合わせ お問い合わせ内容 必須 法人・個人 必須 —以下から選択してください— 法人 個人事業主 個人 会社名（法人様・個人事業主様のみ） 任意 お名前 必須 E-mail 必須 ※上記メールアドレスにお間違えがないか、今一度ご確認ください。 住所 任意 〒 ハイフン無しで詰めてい
- [公式ページ](https://www.mitsui-matsushima.co.jp/contact/)／[保存証拠](evidence/1518/04.json)（取得 2026-10-11T03:59:05.079653+00:00）：く場合がございます。また下記に該当するお問い合わせについては、回答を差し控えさせていただきますので、あらかじめご了承ください。 [1]直近の業績動向や業績見込など、適時開示において公開されていない情報に関するお問い合わせ [2]株価対策などの金融商品取引法第166条「重要事実」に該当する可能性のあるお問い合わせ [3]株価動向など株式市場の値動に関するお問い合わせ ●当社から回答した内容について、
- [公式ページ](https://www.mitsui-matsushima.co.jp/contact/)／[保存証拠](evidence/1518/04.json)（取得 2026-10-11T03:59:05.079653+00:00）：どの金融商品取引法第166条「重要事実」に該当する可能性のあるお問い合わせ [3]株価動向など株式市場の値動に関するお問い合わせ ●当社から回答した内容について、その一部又は全部を転載、二次利用することはご遠慮ください。 下記の項目にご記入下さい。 Japan お問い合わせ種別 必須 —以下から選択してください— 投資家向け広報（IR）のお問い合わせ 取材のお問い合わせ 株主優待のお問い合わせ 

### 153A カウリス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用問い合わせページにフォーム案内はあるが、保存取得では入力欄を確認できない。
- 返信が遅れる・回答を控える場合がある。回答の一部・全部を許可なく問い合わせ目的外で使用しない案内。
- 顧客サービスや具体的対応の詳細はセキュリティ体制・機密情報を含むため回答しない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://caulis.jp/ir/form-ir/)／[保存証拠](evidence/153A/02.json)（取得 2026-10-11T03:59:03.353013+00:00）：IRお問い合わせ
- [公式ページ](https://caulis.jp/ir/form-ir/)／[保存証拠](evidence/153A/02.json)（取得 2026-10-11T03:59:03.353013+00:00）：お問い合わせフォーム
- [公式ページ](https://caulis.jp/ir/form-ir/)／[保存証拠](evidence/153A/02.json)（取得 2026-10-11T03:59:03.353013+00:00）：お問い合わせの内容によっては、ご返信に時間がかかる場合、回答を差し控えさせていただく場合がございます
- [公式ページ](https://caulis.jp/ir/form-ir/)／[保存証拠](evidence/153A/02.json)（取得 2026-10-11T03:59:03.353013+00:00）：当社からの回答の一部またはすべてを、当社の許可なくお問い合わせの目的以外でご使用になることはご遠慮ください。
- [公式ページ](https://caulis.jp/ir/form-ir/)／[保存証拠](evidence/153A/02.json)（取得 2026-10-11T03:59:03.353013+00:00）：お客様へのサービス提供内容や具体的な対応の詳細につきましては、当該お客様や関係先様のセキュリティ体制・機密情報に関わる事項を含むため、弊社としてはお答えいたしかねます

### 155A 情報戦略テクノロジー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用ページにメール/確認用メールと問い合わせ本文のフォームがある。企業名・部署名欄があるが、保存表示だけでは個人の記入方法・必須条件が十分分からない。
- 内容により回答が遅れる・回答できない場合がある。許可なく回答を転用・二次利用しない案内。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.is-tech.co.jp/ir_top/contact/)／[保存証拠](evidence/155A/05.json)（取得 2026-10-11T03:59:07.832181+00:00）：IRお問い合わせ - 株式会社 情報戦略テクノロジー
- [公式ページ](https://www.is-tech.co.jp/ir_top/contact/)／[保存証拠](evidence/155A/05.json)（取得 2026-10-11T03:59:07.832181+00:00）：お名前 ふりがな 企業名 部署名 メールアドレス メールアドレス（確認） お問い合わせ内容
- [公式ページ](https://www.is-tech.co.jp/ir_top/contact/)／[保存証拠](evidence/155A/05.json)（取得 2026-10-11T03:59:07.832181+00:00）：当社からの回答の一部または全部を、当社の許可なく転用及び二次利用することはご遠慮ください。

### 156A マテリアルグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://materialgroup.jp/ir/)／[保存証拠](evidence/156A/02.json)（取得 2026-10-11T03:59:04.398198+00:00）：IRお問い合わせ
- [公式ページ](https://materialgroup.jp/ir/ir-contact/)／[保存証拠](evidence/156A/04.json)（取得 2026-10-11T03:59:06.235352+00:00）：IRお問い合わせ
- [公式ページ](https://go.materialprmenu.jp/l/1122733/2026-02-18/bvg23j)／[保存証拠](evidence/156A/06.json)（取得 2026-10-11T03:59:09.655208+00:00）：姓 名 会社・団体名 部署 メールアドレス 電話番号 お問い合わせ内容 Comments

### 157A グリーンモンスター

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 共通フォームにIR選択肢がある。会社名/組織名・部署名欄に必須表示は見当たらない。
- 未公開業績、金融商品取引法第166条の重要事実、株価の変動・出来高・株式市場の値動き、誹謗中傷には回答を控える。
- アプリ利用方法の問い合わせはこのフォームでは受け付けず各アプリから行う。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://greenmonster.co.jp/contact/)／[保存証拠](evidence/157A/03.json)（取得 2026-10-11T03:59:06.766084+00:00）：お問い合わせ種別 必須 選択してください サービスについて 採用について IRについて その他 お問い合わせ内容
- [公式ページ](https://greenmonster.co.jp/contact/)／[保存証拠](evidence/157A/03.json)（取得 2026-10-11T03:59:06.766084+00:00）：直近の業績動向や業績見込みなど、適時開示において公開されていない情報に関するお問い合わせ
- [公式ページ](https://greenmonster.co.jp/contact/)／[保存証拠](evidence/157A/03.json)（取得 2026-10-11T03:59:06.766084+00:00）：株価動向などの株式市場の値動きに関するお問い合わせ

### 1662 石油資源開発

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 所属を必須表示。個人投資家の所属欄の記入方法は未確認。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://fs220.xbit.jp/w794/form2/)／[保存証拠](evidence/1662/05.json)（取得 2026-10-11T03:59:14.165842+00:00）： and " * " are required items. お問い合わせ項目/Category * 報道取材のご依頼・その他のお問い合わせ/To Media Relations IR面談のご依頼・その他IR関連のお問い合わせ/To Investor Relations IR資料などに関するお問い合わせ/Inquiry about our IR Disclosures ご所属/Organization 
- [公式ページ](https://fs220.xbit.jp/w794/form2/)／[保存証拠](evidence/1662/05.json)（取得 2026-10-11T03:59:14.165842+00:00）：依頼・その他IR関連のお問い合わせ/To Investor Relations IR資料などに関するお問い合わせ/Inquiry about our IR Disclosures ご所属/Organization * お名前/Name * メールアドレス/E-mail * お電話番号/Phone Number 例/ex.) 03-1234-5678 お問い合わせ内容/Inquiry * 入力内
- [公式ページ](https://www.japex.co.jp/en/contact/)／[保存証拠](evidence/1662/04.json)（取得 2026-10-11T03:59:10.813518+00:00）：quiries about JAPEX General Inquiries about JAPEX Contact to Media and Investor Relations Media Relations: Interview requests and other inq

### 166A タスキホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@tasuki-holdings.co.jp`。

取得範囲の受付条件：

- 公式英文問い合わせフォームにInvestor Relationsの選択肢があり、IRメール ir@tasuki-holdings.co.jp も案内。
- 英文フォームはYour company、氏名、メール、電話、問い合わせ内容等が必須表示。所属のない個人の記入方法は未確認。返信に時間がかかる場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 所属を求める欄が必須表示だが、所属のない個人の記入方法・利用可否は未確認。

根拠：

- [公式ページ](https://tasuki-holdings.co.jp/en/inquiry/)／[保存証拠](evidence/166A/03.json)（取得 2026-10-11T03:59:08.712281+00:00）：For IR inquiries, you may also contact us at ir@tasuki-holdings.co.jp.
- [公式ページ](https://tasuki-holdings.co.jp/en/inquiry/)／[保存証拠](evidence/166A/03.json)（取得 2026-10-11T03:59:08.712281+00:00）：Type of inquiry * Inquiries about Investor Relations Inquiries about Business Subject * Your company * Name * First name Last name Email address * Please enter again for confirmation. Phone number * Details of Inquiry *
- [公式ページ](https://tasuki-holdings.co.jp/en/inquiry/)／[保存証拠](evidence/166A/03.json)（取得 2026-10-11T03:59:08.712281+00:00）：Please kindly understand that it may take some time for us to reply.

### 167A リョーサン菱洋ホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：https://form.rr-hds.co.jp/m?f=1: robots_disallowed / https://form.rr-hds.co.jp/m?f=7: robots_disallowed / https://form.rr-hds.co.jp/m?f=8: robots_disallowed / 公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://www.rr-hds.co.jp/contact/)／[保存証拠](evidence/167A/03.json)（取得 2026-10-11T03:59:08.353648+00:00）：お問い合わせ お問い合わせフォーム IR お問い合わせフォーム 採用 お問い合わせフォーム

### 168A イタミアート

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`itami.ir@itamiarts.co.jp`。

取得範囲の受付条件：

- 管理部のIR問い合わせメール itami.ir@itamiarts.co.jp を公開。返信に時間がかかる場合がある。
- 個人の受付条件・返信期限は今回の保存窓口ページでは明示されていない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.itamiarts.co.jp/investor-relations/contact/)／[保存証拠](evidence/168A/04.json)（取得 2026-10-11T03:59:10.032113+00:00）：IRに関するお問い合わせ先 管理部 一ノ瀬 メール itami.ir@itamiarts.co.jp
- [公式ページ](https://www.itamiarts.co.jp/investor-relations/contact/)／[保存証拠](evidence/168A/04.json)（取得 2026-10-11T03:59:10.032113+00:00）：お問い合わせの内容などにより、お返事に日時を頂戴する場合もございます

### 1716 第一カッター興業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 貴社名・貴社所在地を必須表示。個人の入力方法やIR選択時の条件分岐は未確認。法人限定とまでは断定しない。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.daiichi-cutter.co.jp/contact/)／[保存証拠](evidence/1716/03.json)（取得 2026-10-11T03:59:10.807257+00:00）：てもご対応致しかねます。 当社営業担当もしくは、最寄りの事業所及びグループ会社までご用命ください。 事務所及びグループ会社一覧はこちら お問い合わせの種類 必須 選択してください IR全般に関するお問い合わせ 施工（工事）に関するご相談 採用に関するお問い合わせ その他 工事件名 工事場所 必須 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 
- [公式ページ](https://www.daiichi-cutter.co.jp/contact/)／[保存証拠](evidence/1716/03.json)（取得 2026-10-11T03:59:10.807257+00:00）：府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 現場市町村 貴社名 必須 貴社所在地 必須 ご担当者名 必須 フリガナ メールアドレス 必須 電話番号 必須 FAX番号 ご希望の連絡方法 メール お電話 FAX その他 お問い合わせ内容 必須 アンケー

### 1721 コムシスホールディングス

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

公開IRメール：`info@comsys.co.jp`。

取得範囲の受付条件：

- IR専用フォームが送信できない場合の代替として info@comsys.co.jp を明示。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.comsys-hd.co.jp/secure/contact/ir/input)／[保存証拠](evidence/1721/03.json)（取得 2026-10-11T03:59:12.641292+00:00）：IR情報 お問い合わせ 入力 \| コムシスホールディングス株式会社 IR情報 お問い合わせ 1 内容のご入力 2 入力内容のご確認 3 送信完了 必須 項目は必ずご記入ください。 お問い合わせ内容 お問
- [公式ページ](https://www.comsys-hd.co.jp/secure/contact/ir/input)／[保存証拠](evidence/1721/03.json)（取得 2026-10-11T03:59:12.641292+00:00）： 内容のご入力 2 入力内容のご確認 3 送信完了 必須 項目は必ずご記入ください。 お問い合わせ内容 お問い合わせ内容 必須 1,000文字以内で入力してください。 お客様情報 お客様区分 必須 個人 法人 会社名 例 : コムシスホールディングス株式会社 お名前（全角） 必須 例 : コムシス 太郎 フリガナ（全角カタカナ） 必須 例 : コムシス タロウ メールアドレス（半角英数
- [公式ページ](https://www.comsys-hd.co.jp/secure/contact/ir/input)／[保存証拠](evidence/1721/03.json)（取得 2026-10-11T03:59:12.641292+00:00）：IR情報 お問い合わせ 1 内容のご入力 2 入力内容のご確認 3 送信完了 必須 項目は必ずご記入ください。 お問い合わせ内容 お問い合わせ内容 必須 1,000文字以内で入力してください。 お客様情報 お客様区分 必須 個人 法人 会社名 例 : コムシスホールディングス株式会社 お名前（全角） 必須 例 : コムシス 太郎 フリガナ（全角カタカナ） 必須 例 : コムシス タロウ メールアドレス（半角英数） 必須 例 : xxxxx@comsys.co.jp ご住所 郵便番号（半角数字） 必須 例 : 1410022 郵便番号から住所を検索する 都道府県 必須 都道府県を選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 市区町村 必須 例 : 品川区東五反田2-17-1 建物名等 例 : 品川コムシスビル お電話番号（半角数字） 必須 例 : 0334487100 お問い合わせについてのご注意 弊社のホームページにてご記入いただきました個人情報のお取り扱いについては、 プライバシーポリシー をご覧いただき、ご了承の上お問い合わせください。 営業時間外および土・日・祝日・GW・夏季休暇期間（8月中旬）・年末年始のお問い合わせについては、翌営業日以降に内容を確認させていただいております。 また、内容によっては回答にお時間を要する場合もございます。ご了承ください。 電子メール以外の方法で回答を差し上げる場合や回答ができない場合がございます。 弊社からお客さまへ送信する電子メールは、お客さま個人宛にお送りするものですので、回答内容の一部または全体を転用、二次利用することは著作権法上認められておりませんのでご遠慮ください。 フォームでの送信が行えない方は info@comsys.co.jp 宛てにお問い合わせください。

### 1723 日本電技

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 質問内容により回答できない場合がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://reg18.smp.ne.jp/regist/is?SMPFORM=mhki-qarfk-be9e4eaef3b0a40d9eb9b336706cdd81)／[保存証拠](evidence/1723/03.json)（取得 2026-10-11T03:59:15.674043+00:00）：お問い合わせフォーム ご注意事項の同意 必須 当フォームのご利用にあたっては、上記の「ご利用上の注意事項」にご同意いただく必要があります。 同意する お問い合わせ項目 必須 全般 IR 採用 ビルディング オートメーション インダストリー オートメーション お問い合わせ内容 必須 氏名 必須 フリガナ 必須 貴社名 郵便番号（半角） - 住所検索 都道府県 市区
- [公式ページ](https://reg18.smp.ne.jp/regist/is?SMPFORM=mhki-qarfk-be9e4eaef3b0a40d9eb9b336706cdd81)／[保存証拠](evidence/1723/03.json)（取得 2026-10-11T03:59:15.674043+00:00）：バシーポリシー をご覧ください。 お問い合わせには、当社営業時間内に順次対応させていただいておりますが、ご回答までに日数がかかる場合があります。 お問い合わせの内容によりましては、お答えしかねる場合がございますので、あらかじめご了承ください。 製品、工事、見積等に関するお問い合わせは、 最寄りの事業所 までご連絡ください。 お問い合わせフォーム ご注意事項の同意 必須 当フォームのご利用
- [公式ページ](https://www.nihondengi.co.jp/ir/)／[保存証拠](evidence/1723/02.json)（取得 2026-10-11T03:59:13.298700+00:00）：・基本方針 貢献しつづけるちから 閉じる 採用情報 採用情報 トップ 新卒採用 経験者採用 閉じる お問い合わせ EN 閉じる トップ 投資家の皆様へ 投資家の皆様へ 投資家の皆様へ日本電技のことをより知っていた

### 1724 シンクレイヤ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@synclayer.co.jp`。

取得範囲の受付条件：

- 土日祝・特別休業日の受付は翌営業日以降の返信。
- フォームが使えない場合の代替としてIRメールアドレスを案内。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.synclayer.co.jp/ir/contact/)／[保存証拠](evidence/1724/05.json)（取得 2026-10-11T03:59:17.344054+00:00）：IRに関するお問い合わせ｜IR情報｜シンクレイヤ株式会社 ニュース コラム お問い合わせ English TOP 導入事例 特長と強み SDGs宣言 ソリューション 製品情報 シンクレイヤについて IR情
- [公式ページ](https://www.synclayer.co.jp/ir/contact/)／[保存証拠](evidence/1724/05.json)（取得 2026-10-11T03:59:17.344054+00:00）：情報は、お問い合わせの返答以外に使用することはございません。（詳しくは「 本ページで収集する情報の扱いについて 」） 弊社休業日（土日祝日・特別休業日）にいただいたお問い合わせは、ご返答が翌営業日以降になります。またご質問内容によっては、返答にお時間をいただく場合がございます。予めご了承ください。 お急ぎの場合は、IR 窓口（経営企画室 052-242-7875）までお電話ください。 I
- [公式ページ](https://www.synclayer.co.jp/ir/contact/)／[保存証拠](evidence/1724/05.json)（取得 2026-10-11T03:59:17.344054+00:00）：は、各専用フォームよりお願い致します。（ 製品・システムに関するお問い合わせ（総合）はこちら 、 採用関連のお問い合わせはこちら ） フォームが正常に動作しない場合は、お手数ですがir@synclayer.co.jp宛てに、フォーム入力項目をご記入の上送信ください。 お名前 ［必須］ 姓 名 住所 ［必須］ 〒 電話番号 ［必須］ FAX メールアドレス ［必須］ 取材申込 はい いいえ お問
- [公式ページ](https://www.synclayer.co.jp/ir/contact/)／[保存証拠](evidence/1724/05.json)（取得 2026-10-11T03:59:17.344054+00:00）：は、各専用フォームよりお願い致します。（ 製品・システムに関するお問い合わせ（総合）はこちら 、 採用関連のお問い合わせはこちら ） フォームが正常に動作しない場合は、お手数ですがir@synclayer.co.jp宛てに、フォーム入力項目をご記入の上送信ください。 お名前 ［必須］ 姓 名 住所 ［必須］ 〒 電話番号 ［必須］ FAX メールアドレス ［必須］ 取材申込 はい いいえ お問

### 173A ハンモック

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IR問い合わせページにフォーム案内があるが、保存取得のformsは検索欄だけでメールと質問本文欄を確認できない。
- 回答が遅れる・回答できない場合がある。電子メール以外で回答する場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://www.hammock.jp/ir/inquiry.html)／[保存証拠](evidence/173A/07.json)（取得 2026-10-11T03:59:17.789896+00:00）：IRについてのお問い合わせ
- [公式ページ](https://www.hammock.jp/ir/inquiry.html)／[保存証拠](evidence/173A/07.json)（取得 2026-10-11T03:59:17.789896+00:00）：下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」 をクリックしてください。
- [公式ページ](https://www.hammock.jp/ir/inquiry.html)／[保存証拠](evidence/173A/07.json)（取得 2026-10-11T03:59:17.789896+00:00）：お問い合わせの内容によっては、回答に時間がかかる場合や回答できない場合がございます。
- [公式ページ](https://www.hammock.jp/ir/inquiry.html)／[保存証拠](evidence/173A/07.json)（取得 2026-10-11T03:59:17.789896+00:00）：また、電子メール以外の方法で回答を差し上げる場合がございます。

### 175A Ｗｉｌｌ　Ｓｍａｒｔ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IR問い合わせページでフォームを案内。保存GETではメール/質問本文の入力欄を確認できない。
- 営業・勧誘目的での利用は不可。製品・サービスの営業、人材紹介、協業は別フォームを案内。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://willsmart.co.jp/contact/ir-contact/)／[保存証拠](evidence/175A/05.json)（取得 2026-10-11T03:59:15.984472+00:00）：IRに関するお問い合わせ このフォームはお客様専用です。 営業及び勧誘目的でのご利用は固くお断りします 。

### 1762 高松コンストラクショングループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.takamatsu-cg.co.jp/inquiry/index.html)／[保存証拠](evidence/1762/03.json)（取得 2026-10-11T03:59:14.129431+00:00）：合わせ お問い合わせ ご質問やご要望など、お気軽にお問合わせください。 必要事項をご記入の上、「確認画面へ」をクリックして確認画面へ進んでください。 件名 必須 選択してください IR情報に関するお問い合わせ 株主優待・配当金に関するお問い合わせ グループ会社に関するお問い合わせ 報道に関するお問い合わせ 採用情報に関するお問い合わせ その他のお問い合わせ について お問合わせ内容 必

### 1766 東建コーポレーション

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 質問内容によって回答できない場合がある。土日祝は受付休業、回答は休み明け以降で時間がかかる場合がある。
- 回答期限指定や至急の要望には対応できない場合がある。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.token.co.jp/inquiry/)／[保存証拠](evidence/1766/04.json)（取得 2026-10-11T03:59:17.633422+00:00）：お客様相談室のご案内 メールでのご相談につきましては、下記よりお問い合わせください。 土地活用について 訪問営業について 建築施工現場について 建築商品について 設計・構造について 物件の仲介・管理について 入居・退去について 家賃・賃料支払いについて フランチャイズ店について IR情報について 広報について その他について
- [公式ページ](https://www.token.co.jp/inquiry/)／[保存証拠](evidence/1766/04.json)（取得 2026-10-11T03:59:17.633422+00:00）：お問い合わせ内容によっては回答できかねる場合もございますので、あらかじめご了承ください。

### 1770 藤田エンジニアリング

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.fujita-eng.co.jp/contact/)／[保存証拠](evidence/1770/03.json)（取得 2026-10-11T03:59:16.804188+00:00）：用情報 グループ会社 100周年 EN お問い合わせ お問い合わせ HOME お問い合わせ 以下のフォームに入力後、【入力内容を確認】ボタンをクリックしてください。 ご用件 必須 IRに関するお問い合わせ 株式に関するお問い合わせ 採用に関するお問い合わせ その他 内容 必須 お名前 必須 様 フリガナ 必須 様 貴社名 部署 電話番号 - - ご住所 郵便番号 - 都道府県 北海

### 177A コージンバイオ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://kohjin-bio.jp/contact/)／[保存証拠](evidence/177A/05.json)（取得 2026-10-11T03:59:19.395894+00:00）：IR・取材について お問い合わせ
- [公式ページ](https://kohjin-bio.jp/ir/otheririnformation/)／[保存証拠](evidence/177A/04.json)（取得 2026-10-11T03:59:18.145561+00:00）：IRに関するお問い合わせ

### 1780 ヤマウラ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://yamaura.co.jp/ir/contact/)／[保存証拠](evidence/1780/02.json)（取得 2026-10-11T03:59:18.757668+00:00）：株式・IRに関するお問い合わせ - 株式会社ヤマウラ MENU ホーム 企業情報 技術紹介 事業部門 施工実績 IR情報 新着情報 表彰実績・リリース 建設コラム 採用情報 お問い合わせ プライバシーポリシー 

### 1783 ｆａｎｔａｓｉｓｔａ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 一般フォームが使えない場合に Info@fantasista-tokyo.jp を案内。メール宛先単体がIR専用とは明示されていないため、確認済みチャンネルはIR選択肢を持つフォームに限定。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://fantasista-tokyo.jp/contact/)／[保存証拠](evidence/1783/03.json)（取得 2026-10-11T03:59:17.386399+00:00）：問い合わせ種別 商品・サービス等のご紹介 M&Aに関するご紹介 リアルエステート事業に関するご質問 不動産コンサルティング事業に関するご質問 EV（電気自動車）事業に関するご質問 IR情報に関するご質問 PR情報に関するご質問 株主優待に関するご質問 その他ご質問 お問い合わせ内容 プライバシーポリシーに同意する プライバシーポリシー に同意する pagetop メールマガジンを
- [公式ページ](https://fantasista-tokyo.jp/contact/)／[保存証拠](evidence/1783/03.json)（取得 2026-10-11T03:59:17.386399+00:00）：メールフォームでメールが送られない場合は、お手数ですがご利用のメールソフトにて「 Info@fantasista-tokyo.jp 」宛にお問い合わせをお願いいたします。 お名前 メールアドレス ※ 半角で入力してください お問い合わせ種別 商品・サービス等のご紹介 M&Aに関するご紹介 リアルエステート事業に関するご質問 不動産コンサルティング事業に関するご質問 EV（電気自動車）事業に関するご質問 IR情報に関するご質問

### 1787 ナカボーテック

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・電話番号・Eメールを必須表示。Eメールを持たない場合は「なし」と記入する案内。個人の会社名入力方法は未確認。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nakabohtec.co.jp/inquiry/)／[保存証拠](evidence/1787/03.json)（取得 2026-10-11T03:59:18.032167+00:00）：05 下記フォームよりお問い合わせください。 お問い合わせ内容 必 須 お問い合わせの内容を選んでください。 製品のお問い合わせ 技術内容に関するお問い合わせ 採用のお問い合わせ IRのお問い合わせ インボイス制度あるいは請求書様式のお問い合わせ その他のお問い合わせ ご担当者名 必 須 会 社 名 必 須 住 所 電 話 番 号 必 須 E メ ー ル 必 須 ※お持ちでな
- [公式ページ](https://www.nakabohtec.co.jp/inquiry/)／[保存証拠](evidence/1787/03.json)（取得 2026-10-11T03:59:18.032167+00:00）：製品のお問い合わせ 技術内容に関するお問い合わせ 採用のお問い合わせ IRのお問い合わせ インボイス制度あるいは請求書様式のお問い合わせ その他のお問い合わせ ご担当者名 必 須 会 社 名 必 須 住 所 電 話 番 号 必 須 E メ ー ル 必 須 ※お持ちでない場合は、「なし」とご記入ください お 問 い 合 わ せ 内 容 お問い合わせいただく前に 「個人情報保護方

### 1788 三東工業社

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.santo.co.jp/contact/)／[保存証拠](evidence/1788/03.json)（取得 2026-10-11T03:59:17.416344+00:00）：募集要項 先輩メッセージ キャリアパス ニュース お問い合わせ プライバシーポリシー お問い合わせ 確認・送信 完了 お問い合わせ種別 必須 当社とのお取引について 採用について IRについて その他お問い合わせ お名前 必須 フリガナ Japan 住所 必須 郵便番号 〒 住所 ビル・マンション名 メールアドレス 必須 メールアドレス（確認） 必須 お問い合わせ内容 

### 1799 第一建設工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.daiichi-kensetsu.co.jp/contact/form/?kind=30)／[保存証拠](evidence/1799/03.json)（取得 2026-10-11T03:59:19.181222+00:00）： ※必須 の付いている項目は必ず入力頂きますようお願いいたします。 お問い合わせ種類 ※必須 協力業者募集に関するお問い合わせ 採用についてのお問い合わせ 採用についての資料請求 IRについてのお問い合わせ 技術に関するお問い合わせ D-flip工法（任意深度定着型仮締切り工法）に関するお問い合わせ Sto乾式吹付けモルタル工法に関するお問い合わせ ZEB・ZEH-Mに関するお問い合

### 1801 大成建設

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.taisei.co.jp/contact/)／[保存証拠](evidence/1801/03.json)（取得 2026-10-11T03:59:23.798452+00:00）：大成建設のお問い合わせ窓口はこちらです。お問い合わせの種類をお選びください。 サービス・技術に関するお問い合わせ IRに関する お問い合わせ サステナビリティに関するお問い合わせ その他の お問い合わせ

### 1802 大林組

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 個人情報保護についてを読み同意した場合に進む。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.obayashi.co.jp/inquiry/disclaimer/ir.html)／[保存証拠](evidence/1802/03.json)（取得 2026-10-11T03:59:26.131540+00:00）：IR（株主・投資家情報）についてのお問い合わせ 免責事項 お問い合わせフォームをご記入いただくにあたって、当社の「 個人情報保護について 」をご一読ください。 当社の「個人情報保護について」に同意いただける場合は「はい」をクリックしてお進みください。 いいえ はい

### 1803 清水建設

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 質問により回答に時間を要するか回答できない場合がある。売り込み提案には回答しない。
- 回答の一部・全部の転載・二次利用を控える。
- 窓口営業時間は 8:30～17:10、土日祝・GW・お盆・年末年始は休業。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.shimz.co.jp/inquiry/)／[保存証拠](evidence/1803/03.json)（取得 2026-10-11T03:59:22.747720+00:00）：お問い合わせについては下記の各種フォームからお願いいたします。
- [公式ページ](https://www.shimz.co.jp/inquiry/)／[保存証拠](evidence/1803/03.json)（取得 2026-10-11T03:59:22.747720+00:00）：技術に関するお問い合わせ 採用に関するお問い合わせ IRに関するお問い合わせ 公正な研究活動に関するお問い合わせ その他のお問い合わせ
- [公式ページ](https://www.shimz.co.jp/inquiry/)／[保存証拠](evidence/1803/03.json)（取得 2026-10-11T03:59:22.747720+00:00）：お問い合わせへの回答と注意事項について メールまたは電話にて回答させていただきます。お問い合わせの内容によっては、回答にお時間をいただく場合やお答えしかねる場合があります。また、当社への営業活動ならびに各種商品・サービスの提供など、売り込みに関するご提案には回答いたしかねますので、あらかじめご了承ください。 こちらの窓口部署の営業時間は午前8：30～午後5：10です。 定休日は土曜・日曜・祝日。ゴールデンウィーク、お盆、年末年始は休業としております。 当社から回答としてお送りした内容は、お問い合わせいただいた方個人への回答となります。その一部または全部を転載・二次利用することはご遠慮ください。

### 1812 鹿島建設

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.kajima.co.jp/contact/)／[保存証拠](evidence/1812/03.json)（取得 2026-10-11T03:59:29.184542+00:00）：IRに関するお問い合わせ 問い合わせをする

### 1813 不動テトラ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.fudotetra.co.jp/contact/)／[保存証拠](evidence/1813/04.json)（取得 2026-10-11T03:59:25.494017+00:00）：IRに関するお問い合わせ お問い合わせフォーム

### 1820 西松建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 問い合わせ内容は 2,000 文字以内。

注意・未確認：個人投資家の明示受付条件、必要入力の全必須判定、沈黙期間・実送信・返信は未確認。

根拠：

- [公式ページ](https://www.nishimatsu.co.jp/contact/input?type=2)／[保存証拠](evidence/1820/05.json)（取得 2026-10-11T03:59:28.563648+00:00）：お問い合わせ区分 総合お問い合わせ IR情報お問い合わせ CSRお問い合わせ 技術お問い合わせ 調達お問い合わせ OKIPPA104お問い合わせ お問い合わせ内容 2,000文字以内でご入力ください。
- [公式ページ](https://www.nishimatsu.co.jp/contact/input?type=2)／[保存証拠](evidence/1820/05.json)（取得 2026-10-11T03:59:28.563648+00:00）：メールアドレス 例 dummy@dummy.co.jp

### 1822 大豊建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.daiho.co.jp/contact/)／[保存証拠](evidence/1822/03.json)（取得 2026-10-11T03:59:27.688259+00:00）：不明な場合、又は当社に対する誹謗中傷を目的としている場合等については、回答を行わないことがありますのでご了承ください。 お問い合わせ種別 技術・工法に関して ご取材・広報に関して IR関連 その他 採用に関して お名前 フリガナ 会社名 部署名 電話番号 ハイフンなし半角英数 メールアドレス お問い合わせ内容 個人情報保護に同意する 個人情報の取扱に同意するに チェ

### 1827 ナカノフドー建設

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 法人名は法人の場合のみ必須。本文は1000文字まで。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.wave-nakano.co.jp/contact/form/)／[保存証拠](evidence/1827/04.json)（取得 2026-10-11T03:59:28.308544+00:00）：の個人情報ならびにご相談の内容は、お問い合わせへの回答以外の目的には使用いたしません。 入力 確認 完了 必須 お客様について 個人 法人/団体 協力会社 必須 お問い合わせ項目 プレスリリース・IRについて サステナビリティについて 採用について ハラスメントについて 施工実績・技術について アフターフォローについて そのほか 必須 ご質問の件名を 入力ください。 ※30文字まで入力
- [公式ページ](https://www.wave-nakano.co.jp/contact/form/)／[保存証拠](evidence/1827/04.json)（取得 2026-10-11T03:59:28.308544+00:00）：い合わせフォーム 必須 がついている項目は必須入力項目です。 お客様の個人情報ならびにご相談の内容は、お問い合わせへの回答以外の目的には使用いたしません。 入力 確認 完了 必須 お客様について 個人 法人/団体 協力会社 必須 お問い合わせ項目 プレスリリース・IRについて サステナビリティについて 採用について ハラスメントについて 施工実績・技術について アフターフォローについて そのほか 必
- [公式ページ](https://www.wave-nakano.co.jp/contact/form/)／[保存証拠](evidence/1827/04.json)（取得 2026-10-11T03:59:28.308544+00:00）：テナビリティについて 採用について ハラスメントについて 施工実績・技術について アフターフォローについて そのほか 必須 ご質問の件名を 入力ください。 ※30文字まで入力可能 法人名 ※法人の場合必須入力 部署名 必須 お名前 必須 フリガナ 必須 メールアドレス 必須 お電話番号 ※ハイフン不要 郵便番号 ※ハイフン不要 〒 住所自動入力 ご住所 必須 お問い合わせ内容 ※100

### 1828 田辺工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.tanabe-ind.co.jp/contact/)／[保存証拠](evidence/1828/03.json)（取得 2026-10-11T03:59:27.709708+00:00）：設や施設の電気設備設計・メンテナンス 田辺工業株式会社 購買・協力会社の皆様へ サステナビリティ ニュース English お問い合わせ 会社情報 事業・技術 田辺工業の取り組み IR情報 採用情報 TOP お問い合わせ お問い合わせ お問い合わせありがとうございます。 後日、担当者よりご連絡させていただきます。 電話でお問い合わせ 電話でのお問い合わせは、以下

### 1833 奥村組

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 会社案内フォームをIRフォームと誤認した旧経路を除外。公式一覧に専用IRフォームへの別リンクがあるが、実IRフォームの保存証拠はない。

根拠：

- [公式ページ](https://www.okumuragumi.co.jp/inquiries/)／[保存証拠](evidence/1833/03.json)（取得 2026-10-11T03:59:27.797856+00:00）：するお問い合わせ 「建築技術」 に関するお問い合わせ 「環境技術」 に関するお問い合わせ 「ICTへの取り組み」 に関するお問い合わせ 「サステナビリティ」 に関するお問い合わせ 「IR情報」 に関するお問い合わせ 「採用情報」 に関するお問い合わせ 「土木・建築・環境に関する 計画のご相談」 に関するお問い合わせ 「奥村組協力会」 に関するお問い合わせ その他のお問い合わせ 企業情報 事業

### 1835 東鉄工業

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.totetsu.co.jp/ir/)／[保存証拠](evidence/1835/03.json)（取得 2026-10-11T03:59:30.252960+00:00）：IRに関するお問い合わせ メールでのお問い合わせ

### 1840 土屋ホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.tsuchiya.co.jp/contact/ir/)／[保存証拠](evidence/1840/04.json)（取得 2026-10-11T03:59:32.446237+00:00）：問い合わせ ホーム お問い合わせ お問い合わせフォーム お問い合わせフォーム お問い合わせ内容の確認 入力いただいた内容にお間違えないかご確認の上、「送信する」を押してください。 IR情報に関するお問い合わせ お名前 必須 フリガナ ご住所 必須 〒 - 都道府県 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 

### 1847 イチケン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・学校名欄は法人の場合に法人名を記入する案内。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ichiken.co.jp/contact/)／[保存証拠](evidence/1847/03.json)（取得 2026-10-11T03:59:35.467683+00:00）：「お問い合わせフォーム」から送信してください。 お問い合わせ項目 必須 土地活用、ビジネスに関するお問い合わせ ZEBに関するお問い合わせ 協力会社、資材調達に関するお問い合わせ IR情報に関するお問い合わせ 採用全般に関するお問い合わせ その他お問い合わせ お名前（全角） 必須 姓 名 フリガナ（全角） 必須 姓 名 E-MAIL 必須 E-MAIL（ご確認用） 必須 ※確認用に、も
- [公式ページ](https://www.ichiken.co.jp/contact/)／[保存証拠](evidence/1847/03.json)（取得 2026-10-11T03:59:35.467683+00:00）：須 姓 名 フリガナ（全角） 必須 姓 名 E-MAIL 必須 E-MAIL（ご確認用） 必須 ※確認用に、もう一度メールアドレスをご入力ください（半角英数） 会社名 / 学校名 ※法人の場合は、法人名をご記入ください 部署名 / 学科名 住所 〒 ※半角数字でご入力ください 電話番号 ※半角英数字でご入力ください ご相談内容 必須 個人情報の 保護方針について 必須 はじめに 現在の高度情報化

### 1848 富士ピー・エス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://contact.fujips.co.jp/contact/)／[保存証拠](evidence/1848/03.json)（取得 2026-10-11T03:59:32.602135+00:00）：部にお電話ください。 事業者一覧ページへ お問い合わせ種別 必須 選択してください 土木情報についてのお問い合わせ 建築情報についてのお問い合わせ 採用情報についてのお問い合わせ 投資家情報についてのお問い合わせ その他についてのお問い合わせ お名前 必須 フリガナ 必須 メールアドレス 必須 確認のためもう一度入力ください お電話番号 必須 ※半角数字（ハイフン不要）で入力ください。 貴
- [公式ページ](https://www.fujips.co.jp/ir/)／[保存証拠](evidence/1848/02.json)（取得 2026-10-11T03:59:30.459084+00:00）：ー・エス 個人投資家向けWEB説明会 採用情報 採用情報 新卒採用 キャリア採用 お取引先の皆様へ お問い合わせ 富士ピー・エスについて 技術情報 施工実績 CSR／社会・環境 IR情報 採用情報 お取引先の皆様

### 184A 学びエイド

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IRページの「IRについてのお問い合わせ」リンクがこの実入力フォームを指す。取得先の見出しはIRニュースとなっている。
- 氏名・ふりがな・メール・本文が必須表示。電話・手紙で回答する場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.manabi-aid.jp/service/contactIr)／[保存証拠](evidence/184A/05.json)（取得 2026-10-11T03:59:34.311868+00:00）：下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」 をクリックして下さい。
- [公式ページ](https://www.manabi-aid.jp/service/contactIr)／[保存証拠](evidence/184A/05.json)（取得 2026-10-11T03:59:34.311868+00:00）：氏名 必須 ふりがな 必須 メールアドレス 必須 電話番号 郵便番号 住所 お問い合わせ内容 必須
- [公式ページ](https://www.manabi-aid.jp/service/contactIr)／[保存証拠](evidence/184A/05.json)（取得 2026-10-11T03:59:34.311868+00:00）：お問い合せの内容によりましては、電話やお手紙でお返事する場合もございます
- [公式ページ](https://corp.manabi-aid.jp/ir/)／[保存証拠](evidence/184A/02.json)（取得 2026-10-11T03:59:30.800665+00:00）：IRについてのお問い合わせ
- [公式ページ](https://corp.manabi-aid.jp/ir/performance/)／[保存証拠](evidence/184A/04.json)（取得 2026-10-11T03:59:33.328172+00:00）：IRについてのお問い合わせ

### 1861 熊谷組

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式 IR フォームの案内は確認できたが対象ページは空シェル。メール・質問の実入力欄は未検証。 / 個人受付条件、字数制限、沈黙期間、送信後の到達や返信は未確認。

根拠：

- [公式ページ](https://www.kumagaigumi.co.jp/contact/ir/)／[保存証拠](evidence/1861/04.json)（取得 2026-10-11T03:59:35.433739+00:00）：IRに関するお問い合わせ（お問い合わせフォーム） \| お問い合わせ \| 株式会社熊谷組
- [公式ページ](https://www.kumagaigumi.co.jp/contact/)／[保存証拠](evidence/1861/03.json)（取得 2026-10-11T03:59:34.260072+00:00）：Inquiries about IR IRに関するお問い合わせ

### 1866 北野建設

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 個人を選択できる。保存URLには採用の初期選択クエリが付くため、IR区分を選び直す必要がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kitano.co.jp/contact/?inquiry=recruit)／[保存証拠](evidence/1866/03.json)（取得 2026-10-11T03:59:36.164997+00:00）：記の項目を入力の上、「同意して確認画面へ」ボタンを押してください。 ※必須項目は必ず入力をお願いします。 お問い合わせ種類 企業情報に関するお問い合わせ 技術に関するお問い合わせ IRに関するお問い合わせ 個人情報保護に関するお問い合わせ 取材・メディア掲載等に関するお問い合わせ 採用お問い合わせ その他のお問い合わせ 個人/法人・団体 個人 法人・団体 お名前 フリガナ メールア
- [公式ページ](https://www.kitano.co.jp/contact/?inquiry=recruit)／[保存証拠](evidence/1866/03.json)（取得 2026-10-11T03:59:36.164997+00:00）：問い合わせ 技術に関するお問い合わせ IRに関するお問い合わせ 個人情報保護に関するお問い合わせ 取材・メディア掲載等に関するお問い合わせ 採用お問い合わせ その他のお問い合わせ 個人/法人・団体 個人 法人・団体 お名前 フリガナ メールアドレス （半角英数記号） 電話番号 （半角数字、ハイフンなし） お問い合わせ内容 ファイルアップロード ファイルを追加 ※アップロード可能なファイルは3
- [公式ページ](https://www.kitano.co.jp/contact/?inquiry=recruit)／[保存証拠](evidence/1866/03.json)（取得 2026-10-11T03:59:36.164997+00:00）：問い合わせ 技術に関するお問い合わせ IRに関するお問い合わせ 個人情報保護に関するお問い合わせ 取材・メディア掲載等に関するお問い合わせ 採用お問い合わせ その他のお問い合わせ 個人/法人・団体 個人 法人・団体 お名前 フリガナ メールアドレス （半角英数記号） 電話番号 （半角数字、ハイフンなし） お問い合わせ内容 ファイルアップロード ファイルを追加 ※アップロード可能なファイルは3

### 1867 植木組

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.uekigumi.co.jp/form/inquiry/)／[保存証拠](evidence/1867/04.json)（取得 2026-10-11T03:59:36.756383+00:00）：溝撤去工法に関するお問い合わせ 土壌汚染調査・対策に関するお問い合わせ バックホウカメラシステムに関するお問い合わせ 保有船舶に関するお問い合わせ その他技術に関するお問い合わせ IRに関するお問い合わせ その他のお問い合わせ お名前 （必須） ※ご入力いただくと、フリガナは自動的に入力されます。 フリガナ （必須） 企業名 ご住所 ※郵便番号を半角数字でご入力いただくと、対応する

### 1870 矢作建設工業

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 必須項目を記入する案内あり。

注意・未確認：公式 IR フォームの案内は確認できたが保存対象ページに実 controls がなくメール・質問の実入力欄は未検証。 / 個人受付条件、字数制限、沈黙期間、送信後の到達や返信は未確認。

根拠：

- [公式ページ](https://www.yahagi.co.jp/contact/ir_contact/)／[保存証拠](evidence/1870/05.json)（取得 2026-10-11T03:59:37.610275+00:00）：IRに関するお問い合わせ 下記のフォームにご入力ください。 必須 の項目は必ず記入してください。
- [公式ページ](https://www.yahagi.co.jp/contact/)／[保存証拠](evidence/1870/03.json)（取得 2026-10-11T03:59:35.503095+00:00）：IRに関するお問い合わせ

### 1871 ピーエス・コンストラクション

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 必須項目を入力。機種依存文字を使用しない。
- 法人・団体等を選択した場合は法人・団体名と部署名を入力。
- 問い合わせ内容により回答できない場合がある。

注意・未確認：字数制限、沈黙期間、メール到達・返信は未確認。

根拠：

- [公式ページ](https://www.psc.co.jp/inquiry/)／[保存証拠](evidence/1871/03.json)（取得 2026-10-11T03:59:36.281031+00:00）：IRに関するお問い合わせ 管理本部 TEL： （03）6385-8002 FAX：（03）6316-2321 お問い合わせフォーム
- [公式ページ](https://www.psc.co.jp/form/input?message_type=4)／[保存証拠](evidence/1871/07.json)（取得 2026-10-11T03:59:40.611650+00:00）：お問い合わせ内容 お問い合わせ項目 （選択済み） 土木に関するお問い合わせ 建築に関するお問い合わせ 技術に関するお問い合わせ IRに関するお問い合わせ 採用に関するお問い合わせ その他のお問い合わせ
- [公式ページ](https://www.psc.co.jp/form/input?message_type=4)／[保存証拠](evidence/1871/07.json)（取得 2026-10-11T03:59:40.611650+00:00）：個人/法人・団体等 必須 ※ 「法人・団体等のお客様」を選択した場合は、次の「法人・団体名」「部署名」をご入力ください。 個人のお客様 法人・団体等のお客様
- [公式ページ](https://www.psc.co.jp/form/input?message_type=4)／[保存証拠](evidence/1871/07.json)（取得 2026-10-11T03:59:40.611650+00:00）：メールアドレス 必須 例：example@psc.co.jp 確認のためもう一度ご入力ください。
- [公式ページ](https://www.psc.co.jp/form/input?message_type=4)／[保存証拠](evidence/1871/07.json)（取得 2026-10-11T03:59:40.611650+00:00）：必須 の項目は必ずご入力ください。未入力の場合は、送信されません。

### 1879 新日本建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.shinnihon-c.co.jp/contact/)／[保存証拠](evidence/1879/03.json)（取得 2026-10-11T03:59:39.037031+00:00）：) 【メールアドレス】を入力してください。 【メールアドレス】に正しいメールアドレスを入力してください。 【メールアドレス】は255文字以内で入力してください。 お問い合わせ種類 IRに関するお問い合わせ 採用に関するお問い合わせ 工事に関するお問い合わせ エクセレントマンションに関するお問い合わせ 協力業者に関するお問い合わせ 上記以外に関するお問い合わせ 【お問い合わせ種類】を

### 1882 東亜道路工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- メールアドレスと電話番号の連絡先欄がある。メール返信を希望する場合は実メールアドレスを入力する必要がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.toadoro.co.jp/inquiry/index.html)／[保存証拠](evidence/1882/02.json)（取得 2026-10-11T03:59:36.651362+00:00）：お問合せ（会社・IR・CSR・事業所、その他のお問合せ）｜東亜道路工業株式会社 企業サイト 企業サイト 事業サイト 採用サイト English 企業情報 株主・投資家情報 CSR情報 事業所一覧 取引企業様へ お問合
- [公式ページ](https://www.toadoro.co.jp/inquiry/index.html)／[保存証拠](evidence/1882/02.json)（取得 2026-10-11T03:59:36.651362+00:00）：問合せ内容 ※ ご返答のあて先 お名前 ※ フリガナ Emailアドレス ※ ★ Emailまたはお電話番号のどちらかを必ずご記入ください。 確認用（再入力） ※ 電話番号 ※ ※メールアドレスをお持ちでない方は、必ずご記入ください。 会社名・団体名・学校名など 部署名 住所 〒 番地・ビル名・階数/部屋番号まで省略せずにご記入ください。 FAX番号 上記送信内容をご確認

### 1885 東亜建設工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 問い合わせ件名・内容・名前・ふりがな・メール・電話に必須表示。
- 質問内容により回答に時間がかかる場合がある。

注意・未確認：個人投資家の明示受付条件、字数制限、沈黙期間、送信後の到達や返信は未確認。

根拠：

- [公式ページ](https://inquiry.toa-const.co.jp/form/pub/toa/ir)／[保存証拠](evidence/1885/05.json)（取得 2026-10-11T03:59:41.641803+00:00）：IRについてのお問い合わせ このフォームにてお寄せいただくお客様の情報は、お問い合わせに対する回答を差し上げる以外の目的に利用することはありません。 お問い合わせの内容によっては、当社からの回答にお時間をいただく場合がございますので予めご了承ください。
- [公式ページ](https://inquiry.toa-const.co.jp/form/pub/toa/ir)／[保存証拠](evidence/1885/05.json)（取得 2026-10-11T03:59:41.641803+00:00）：お問い合わせ件名 必須 内容 必須 お名前 必須 ふりがな 必須 メールアドレス 必須 確認のため、再度入力してください。
- [公式ページ](https://www.toa-const.co.jp/ir/)／[保存証拠](evidence/1885/04.json)（取得 2026-10-11T03:59:38.984985+00:00）：・IRについてのお問い合わせ

### 1888 若築建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 質問内容による無回答、休業日等による返信遅延を案内。保存URLには別用途の初期選択クエリが付くためIRを選び直す必要がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.wakachiku.co.jp/contact/?m=reform)／[保存証拠](evidence/1888/03.json)（取得 2026-10-11T03:59:39.288793+00:00）：目的でご利用することはご遠慮ください。 弊社への営業活動ならびに各種商品・サービスの提供など、売り込みに関するご提案には回答いたしかねます。 ※ は必須記入項目です。 Japan お問い合わせ区分 IR 技術 わかちく史料館 その他 お問い合わせ内容 ※ お名前（漢字） ※ フリガナ ※ 貴社名・部署名 郵便番号 住所 電話番号 FAX番号 メールアドレス ※ 本サイトに設置しているフ
- [公式ページ](https://www.wakachiku.co.jp/contact/?m=reform)／[保存証拠](evidence/1888/03.json)（取得 2026-10-11T03:59:39.288793+00:00）：English 検索 キーワードを入力してください。 × 閉じる お問い合わせ CONTACT Home お問い合わせ お問い合わせの内容によっては、回答にお時間をいただく場合や、回答いたしかねる場合がございます。 土曜・日曜・祝日は定休日となり、ゴールデンウィーク、お盆、年末年始は休業としておりますので、回答にお時間をいただく場合がございます。 弊社からお客様へ差し上げる返信メールは、お

### 1897 金下建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名は法人の場合の任意欄。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kaneshita.co.jp/contact/)／[保存証拠](evidence/1897/03.json)（取得 2026-10-11T03:59:49.005364+00:00）：レス 必須 メールアドレス(確認用) 任意 郵便番号 任意 住所(自動入力) 任意 電話番号 必須 お問い合わせ種別 ホームページに関するお問い合わせ 仕事のご依頼または見積依頼 ＩＲに関するお問い合わせ 採用・インターンシップ等に関するお問い合わせ その他のお問い合わせ 必須 お問い合わせ本文 この内容で送信してよろしいですか。 Δ なお、ご入力いただきました個人情報は、お問い合
- [公式ページ](https://www.kaneshita.co.jp/contact/)／[保存証拠](evidence/1897/03.json)（取得 2026-10-11T03:59:49.005364+00:00）：は下記項目をご入力いただき、送信ボタンを押してください。 お問い合わせ内容によっては、回答に時間を要する場合がございます。あらかじめご了承ください。 必須 お名前 必須 ふりがな 任意 会社名（法人の場合） 必須 メールアドレス 必須 メールアドレス(確認用) 任意 郵便番号 任意 住所(自動入力) 任意 電話番号 必須 お問い合わせ種別 ホームページに関するお問い合わせ 仕事のご依

### 189A Ｄ＆Ｍカンパニー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。氏名・メール・問い合わせ本文・個人情報取扱い同意が必須表示。
- 確認後に担当者が連絡する案内。会社名欄は見当たらないが、個人投資家受付の明示条件は未確認。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.dmcompany.co.jp/ir/contact/)／[保存証拠](evidence/189A/02.json)（取得 2026-10-11T03:59:40.073405+00:00）：IRに関するお問い合わせ 下記フォームにご入力いただき、お問い合わせください。
- [公式ページ](https://www.dmcompany.co.jp/ir/contact/)／[保存証拠](evidence/189A/02.json)（取得 2026-10-11T03:59:40.073405+00:00）：お名前 ＊ お名前を入力してください メールアドレス ＊
- [公式ページ](https://www.dmcompany.co.jp/ir/contact/)／[保存証拠](evidence/189A/02.json)（取得 2026-10-11T03:59:40.073405+00:00）：お問い合わせ内容 ＊

### 1904 大成温調

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.taisei-oncho.co.jp/inquiry/)／[保存証拠](evidence/1904/03.json)（取得 2026-10-11T03:59:42.196198+00:00）：容を確認する」ボタンをクリックしてください。 ※ 印の項目は、入力必須項目です。 お問い合わせ項目・内容の入力 お問い合わせ項目 ※ ※入力してください PRに関するお問い合わせ IRに関するお問い合わせ その他の情報に関するお問い合わせ お問い合わせ内容 ※ ※入力してください お客様情報の入力 個人/法人・団体等 ※ ※法人を選択した場合、「法人・団体名」の入力は必須になります
- [公式ページ](https://www.taisei-oncho.co.jp/inquiry/)／[保存証拠](evidence/1904/03.json)（取得 2026-10-11T03:59:42.196198+00:00）：わせ項目 ※ ※入力してください PRに関するお問い合わせ IRに関するお問い合わせ その他の情報に関するお問い合わせ お問い合わせ内容 ※ ※入力してください お客様情報の入力 個人/法人・団体等 ※ ※法人を選択した場合、「法人・団体名」の入力は必須になります。 個人 法人 お名前 ※ ※入力してください 姓 名 ふりがな ※ ※入力してください せい めい メールアドレ

### 1905 テノックス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 一般の「その他」フォームを除外。英語IR窓口ページから専用IRフォームへの明示リンクを確認。対応する実フォームは未取得。

根拠：

- [公式ページ](https://www.tenox.co.jp/en/ir/contact/)／[保存証拠](evidence/1905/07.json)（取得 2026-10-11T03:59:55.577380+00:00）：tronic public notice IR News Current Stock Price FAQ Disclaimer IR Inquiries IR Inquiries Please direct inquiries related to IR to the following contact information. TEL：03-3455-7787 Click here to make inquiries via a form. Company Message Management Phil

### 190A Ｃｈｏｒｄｉａ　Ｔｈｅｒａｐｅｕｔｉｃｓ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：https://cloud.swcms.net/chordiatherapeuticsPublic/ja/contact/contact2/inquiry2.html: robots_access_denied_stopped / 公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://www.chordiatherapeutics.com/ja/contact.html)／[保存証拠](evidence/190A/04.json)（取得 2026-10-11T03:59:47.023809+00:00）：IRお問い合わせ
- [公式ページ](https://www.chordiatherapeutics.com/ja/contact/contact2.html)／[保存証拠](evidence/190A/07.json)（取得 2026-10-11T03:59:49.619027+00:00）：IRお問い合わせ

### 1911 住友林業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- ニックネーム・ハンドルネームでの質問をご遠慮との記載。本文は全角3000文字以内。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://inquire.sfc.jp/sfc/m/contact/)／[保存証拠](evidence/1911/04.json)（取得 2026-10-11T03:59:48.529335+00:00）： 住所1 住所2 電話番号（半角数字） FAX番号（半角数字） メールアドレス お問い合わせの種類 広告・宣伝（TV・新聞） 広告・宣伝（WEB） 採用活動 サステナビリティ活動 IR情報 ご意見・ご不満 その他 お問い合わせ内容 （全角3,000文字以内） 資料の添付 参考画像などございましたら添付ください。 JPG、GIF、PNG、PDFを、1ファイル（10MB
- [公式ページ](https://inquire.sfc.jp/sfc/m/contact/)／[保存証拠](evidence/1911/04.json)（取得 2026-10-11T03:59:48.529335+00:00）：業 広報・IR・商品・企業活動等に関するお問い合わせ 1 入力 2 確認 3 完了 下記のフォームにご相談、ご質問内容をご入力いただき、送信下さい。 必須項目は必ずご記入下さい。 ニックネーム、ハンドルネーム等でのご質問はご遠慮下さい。 お問い合わせ内容や担当部署の定休日等により、お時間をいただく場合がございます。予めご了承ください。 お名前（全角） 姓 名 フリガナ（全角） セイ メイ ご住所（全角） 日本国
- [公式ページ](https://sfc.jp/contact/)／[保存証拠](evidence/1911/03.json)（取得 2026-10-11T03:59:44.922247+00:00）：お問い合わせ リフォームに関するお問い合わせ 住友林業ホームテック リフォームに関するお問い合わせ 広報・IR・商品・企業活動等に関するお問い合わせ 広報・IR・商品・企業活動等に関するお問い合わせ 森林環境・緑化に関するお問い合わせ 木に関するト

### 1925 大和ハウス工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 本文は全角1000文字以内。氏名・フリガナ・メール・住所・電話等を必須表示。
- xxxxx@daiwahouse.co.jp は入力例であり公開IRメールではない。
- 回答の転載・二次利用をご遠慮との記載。質問内容による無回答・電話等の回答の可能性がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.daiwahouse.co.jp/qa/inquiry_form.asp?page=from_header)／[保存証拠](evidence/1925/05.json)（取得 2026-10-11T03:59:46.275596+00:00）：株主・投資家の皆さまへ ＩＲ情報に関するお問い合わせ｜大和ハウス 株主・投資家の皆さまへ ＩＲ情報に関するお問い合わせ お問い合わせ前にご一読ください ◆ 株式インフォメーション 株式の手続きなどについては、 こちら をご覧ください
- [公式ページ](https://www.daiwahouse.co.jp/qa/inquiry_form.asp?page=from_header)／[保存証拠](evidence/1925/05.json)（取得 2026-10-11T03:59:46.275596+00:00）：リリース関連についてのお問い合わせ 統合報告書 株主の皆さまへ（事業ご報告） その他IR資料 株主優待 その他 事業・グループ会社へのお問い合わせ ESGに関するお問い合わせ * お問い合わせ内容 （全角1000文字以内） ■お問い合わせいただいている方に関する情報 * お名前 姓： 名： （全角） * フリガナ セイ： メイ： （全角カタカナ） 性別 男性 女性 * メールアドレス 例)xxxxx
- [公式ページ](https://www.daiwahouse.co.jp/qa/inquiry_form.asp?page=from_header)／[保存証拠](evidence/1925/05.json)（取得 2026-10-11T03:59:46.275596+00:00）：00文字以内） ■お問い合わせいただいている方に関する情報 * お名前 姓： 名： （全角） * フリガナ セイ： メイ： （全角カタカナ） 性別 男性 女性 * メールアドレス 例)xxxxx@daiwahouse.co.jp ※メールアドレスの間違いが大変多いので、よくご確認ください。 * ご住所 郵便番号を入力後、「住所を表示する」ボタンを押してください。 ※住所が海外の方は最初の3桁に「000」と
- [公式ページ](https://www.daiwahouse.co.jp/qa/inquiry_form.asp?page=from_header)／[保存証拠](evidence/1925/05.json)（取得 2026-10-11T03:59:46.275596+00:00）：メール以外の方法で回答を差し上げる場合や回答ができない場合があります。 弊社からお客さまへ送信する電子メールは、お客さま個人宛にお送りするものですので、 回答内容の一部または全部を転載、二次利用することはご遠慮ください。 お客さまからいただきましたメールアドレスに誤りがあった場合やウイルスが検出された場合、 システム障害などの場合にはご回答できない場合があります。 【当社を騙った求人メールにご注

### 1926 ライト工業

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 会社・団体名を必須表示する一方、所属区分に個人を選択できる。個人選択時の入力条件は未確認。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.raito.co.jp/inquiry/)／[保存証拠](evidence/1926/03.json)（取得 2026-10-11T03:59:45.694475+00:00）：県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 市区町村 丁目番地 建物名 お問い合わせの種類をお選びください 必須 —以下から選択してください— 土木 建築 海外 会社・IR 採用 その他 お問い合わせの内容をご記入ください 必須 以下の内容でお間違えがないかご確認ください。 お名前 フリガナ 会社/団体情報 会社/団体（学校）名 : 部署名 : 役職
- [公式ページ](https://www.raito.co.jp/inquiry/)／[保存証拠](evidence/1926/03.json)（取得 2026-10-11T03:59:45.694475+00:00）：に関わる相談は、相談窓口にご連絡ください。相談窓口は こちら 。 お名前 必須 フリガナ 必須 会社/団体情報 会社/団体（学校）名 必須 部署名 任意 役職名 任意 所属 必須 会社/団体（学校） 個人 業種 必須 —以下から選択してください— 官公庁 コンサルタント 建設 その他 電話番号 必須 （半角数字） メールアドレス 必須 （半角数字） 確認のためもう一度ご入力ください
- [公式ページ](https://www.raito.co.jp/inquiry/)／[保存証拠](evidence/1926/03.json)（取得 2026-10-11T03:59:45.694475+00:00）：イト工業グループ事業活動におけるコンプライアンス、ハラスメント、人権に関わる相談は、相談窓口にご連絡ください。相談窓口は こちら 。 お名前 必須 フリガナ 必須 会社/団体情報 会社/団体（学校）名 必須 部署名 任意 役職名 任意 所属 必須 会社/団体（学校） 個人 業種 必須 —以下から選択してください— 官公庁 コンサルタント 建設 その他 電話番号 必須 （半角数字） メ

### 1928 積水ハウス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.sekisuihouse.co.jp/mail/form.html)／[保存証拠](evidence/1928/02.json)（取得 2026-10-11T03:59:43.842593+00:00）： 積水ハウスの対応についてのお問い合わせ 積水ハウスグループへのご意見・ご不満 お客さま個人情報に関するお問い合わせ 事業・取り組みについてのお問い合わせ 採用 広告・宣伝 広報 IR（株主・投資家情報） サステナビリティ 人権 国際事業 その他 氏名（漢字） 姓 名 フリガナ（全角カタカナ） セイ メイ メールアドレス 郵便番号（半角数字） - 住所 都道府県 選択してください 

### 1929 日特建設

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・職業は任意。住所・電話・メール・氏名等は必須表示。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nittoc.co.jp/contact/ir/)／[保存証拠](evidence/1929/07.json)（取得 2026-10-11T04:00:04.827459+00:00）：IRに関するお問い合わせ｜お問い合わせ｜日特建設株式会社 日特建設株式会社 JP EN 事業内容 技術情報 企業情報 IR情報 サステナビリティ ニュース 採用情報 お問い合わせ 営業カタログ トップ 事
- [公式ページ](https://www.nittoc.co.jp/contact/ir/)／[保存証拠](evidence/1929/07.json)（取得 2026-10-11T04:00:04.827459+00:00）：d. All rights reserved お問い合わせ Contact TOP お問い合わせ IRに関するお問い合わせ IRに関するお問い合わせ 必須 お名前 必須 フリガナ 任意 会社名・ご職業 必須 電話番号 任意 FAX番号 必須 メールアドレス 必須 確認用メールアドレス 必須 ご住所 郵便番号 - 都道府県 都道府県 北海道 青森県 岩手県 宮城県 秋田県 山形県

### 192A インテグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 下記の「個人情報利用等同意書」をお読みいただき、同意いただける方のみ送信してください。
- 確認のため、ご登録内容を記載した自動返信メールをお送りしますので、ご本人様しか見ることができないメールアドレスをご記入お願いいたします。

注意・未確認：実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://www.integroup.jp/ir/)／[保存証拠](evidence/192A/02.json)（取得 2026-10-11T03:59:47.490414+00:00）：IRお問い合わせ
- [公式ページ](https://ma.integroup.jp/l/830143/2024-04-30/38zf9b)／[保存証拠](evidence/192A/04.json)（取得 2026-10-11T03:59:50.535864+00:00）：お名前 電話番号 （例） 090-0000-0000 メールアドレス （例）●●●@●●● ご意見・質問 個人情報取扱いに関する同意 同意する
- [公式ページ](https://ma.integroup.jp/l/830143/2024-04-30/38zf9b)／[保存証拠](evidence/192A/04.json)（取得 2026-10-11T03:59:50.535864+00:00）：下記の「個人情報利用等同意書」をお読みいただき、同意いただける方のみ送信してください。
- [公式ページ](https://ma.integroup.jp/l/830143/2024-04-30/38zf9b)／[保存証拠](evidence/192A/04.json)（取得 2026-10-11T03:59:50.535864+00:00）：確認のため、ご登録内容を記載した自動返信メールをお送りしますので、ご本人様しか見ることができないメールアドレスをご記入お願いいたします。

### 1938 日本リーテック

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- Googleログイン案内は進捗保存のための表示。保存本文だけで送信にログイン必須とは断定しない。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式サイトに埋め込まれたGoogleフォーム。ログイン・送信の要否や同意条件の画面動作は未検証。

根拠：

- [公式ページ](https://docs.google.com/forms/d/e/1FAIpQLSdLFPghc6NeHyvVytAnYDxj2Q0XjpMql_R6YDb980wzdgRG7g/viewform?embedded=true)／[保存証拠](evidence/1938/07.json)（取得 2026-10-11T03:59:53.857245+00:00）：い合わせ種別 * Choose 鉄道電気設備事業に関するお問い合わせ 道路設備事業に関するお問い合わせ 屋内外電気設備事業に関するお問い合わせ 送電線設備事業に関するお問い合わせ ＩＲに関するお問い合わせ 採用に関するお問い合わせ その他 お問い合わせ内容 * お問い合わせ内容を入力してください。 Your answer 会社・学校名（任意） Your answer ご住所（任意）
- [公式ページ](https://docs.google.com/forms/d/e/1FAIpQLSdLFPghc6NeHyvVytAnYDxj2Q0XjpMql_R6YDb980wzdgRG7g/viewform?embedded=true)／[保存証拠](evidence/1938/07.json)（取得 2026-10-11T03:59:53.857245+00:00）：お預かりした個人情報については、ご質問、ご意見に対する回答またはご連絡を差し上げる目的以外では利用いたしません。 Sign in to Google to save your progress. Learn more * Indicates required question Email * Your email お名前 * Your answer フリガナ * Your
- [公式ページ](https://www.j-rietec.co.jp/contact/input/)／[保存証拠](evidence/1938/06.json)（取得 2026-10-11T03:59:52.612930+00:00）：組み ニュース 協力会社紹介 マスコット紹介 よくあるご質問 会社案内 採用情報 総合研修センター CONTACT お問い合わせフォーム 読み込んでいます… トップページ お問い合わせ 入力 PAGE TOP TOP 会社情報 トップメッセージ NRグルー
- [公式ページ](https://docs.google.com/forms/d/e/1FAIpQLSdLFPghc6NeHyvVytAnYDxj2Q0XjpMql_R6YDb980wzdgRG7g/viewform?embedded=true)／[保存証拠](evidence/1938/07.json)（取得 2026-10-11T03:59:53.857245+00:00）：This form was created inside of 日本リーテック株式会社.

### 1939 四電工

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.yondenko.co.jp/inquiry/form.php?type=ir)／[保存証拠](evidence/1939/06.json)（取得 2026-10-11T03:59:56.673777+00:00）： JA / EN お問い合わせ INQUIRY 入力 確認 完了 必須項目※は必ずご記入ください。 必要事項を入力のうえ「確認画面に進む」ボタンを押してください。 お問合わせ種類 IR・株式等について 貴社名 住所 ※必須 所属・部署 お名前 ※必須 お電話番号 ※必須 メールアドレス ※必須 お問い合わせ内容 ※必須 個人情報の利用について、弊社Webサイトの 「個人情報の取

### 1946 トーエネック

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 決算発表前 1 か月はクワイエット・ピリオドで IR 質問への回答を控える。
- 土日祝・12/29～1/3 は翌営業日以降に確認。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.toenec.co.jp/contact/)／[保存証拠](evidence/1946/03.json)（取得 2026-10-11T03:59:52.143734+00:00）：下記お問い合わせフォームよりお問い合わせください。
- [公式ページ](https://www.toenec.co.jp/contact/)／[保存証拠](evidence/1946/03.json)（取得 2026-10-11T03:59:52.143734+00:00）：IRに関するお問い合わせ
- [公式ページ](https://www.toenec.co.jp/ir/qa/)／[保存証拠](evidence/1946/02.json)（取得 2026-10-11T03:59:50.851561+00:00）：IRに関するお問い合わせに対して、決算発表前の1ヶ月をクワイエット・ピリオド（IR活動自粛期間）と定め、この期間中は回答を控えさせていただきますので、予めご了承願います。

### 1950 日本電設工業

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.densetsuko.co.jp/contact/)／[保存証拠](evidence/1950/03.json)（取得 2026-10-11T03:59:55.039277+00:00）： 鹿児島県 沖縄県 住所（市区町村） 住所（番地・ビル名・部屋番号） お問合せの種類 選択してください 技術開発に関するお問合せ 人材・採用に関するお問合せ 技術に関するお問合せ IRに関するお問合せ その他のお問合せ お問合せの内容 プライバシーポリシー プライバシーポリシーに同意する 企業情報 事業案内 実績紹介 採用情報 お問合せ English Privacy poli
- [公式ページ](https://www.densetsuko.co.jp/contact/)／[保存証拠](evidence/1950/03.json)（取得 2026-10-11T03:59:55.039277+00:00）：て下記項目にご記入いただき、 【入力内容の確認】 ボタンを押してください。 「必須」 の項目は必ず入力してください。 このページはTLSに対応し、暗号化して情報を送信いたします。 法人/個人 法人のお客様 法人名 部署・役職 個人のお客様 お名前 お名前（フリガナ） メールアドレス 半角英数で入力してください 電話番号 いずれか 会社 / 自宅 携帯電話 半角数字で入力してください ハイフンは不要です 郵便番号 半

### 1952 新日本空調

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。

根拠：

- [公式ページ](https://www.snk.co.jp/info/)／[保存証拠](evidence/1952/03.json)（取得 2026-10-11T03:59:55.149161+00:00）：お問合わせになりたい項目を以下よりお選びいただき、各フォームをご利用ください。 技術に関するお問い合わせ リニューアルに関するお問い合わせ CSR・環境保全に関するお問い合わせ 微粒子可視化システムに関するお問い合わせ EnergyQuestに関するお問い合わせ ニュースリリースに関するお問い合わせ IRに関するお問い合わせ
- [公式ページ](https://www.snk.co.jp/ir/stock/faq/)／[保存証拠](evidence/1952/04.json)（取得 2026-10-11T03:59:56.317048+00:00）：IRに関する問い合わせはどこにすればいいですか？ 「IRに関するお問い合わせ」よりお問い合わせください。 （ https://www.snk.co.jp/info/form.html?frmid=11 ）

### 1960 サンテック

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 実フォームの保存本文に文字化けがある。mail / mail:cf と本文 inquiry の実入力欄および公式IR親リンクは確認したが、個人区分・必須表示等の詳細条件は判読できない。

根拠：

- [公式ページ](https://www.suntec-sec.co.jp/ir/contact/)／[保存証拠](evidence/1960/02.json)（取得 2026-10-11T03:59:55.208895+00:00）：り組み （社会貢献活動） ガバナンス コーポレートガバナンス 外部評価・認証・表彰 採用情報 お問い合わせ English HOME IR情報 IRお問い合わせ IRお問い合わせ IRに関するお問い合わせは、下記窓口で受付します。 お問い合わせの内容などにより、ご返答に日時を要する場合があります。あらかじめご了解いただきますよう、お願い申し上げます。 また、内容によっては、お答えできない場合がございます。 
- [公式ページ](https://reg31.smp.ne.jp/regist/is?SMPFORM=oboi-lfpaog-d3727284489b172114627fe9b1c1ca7f&type=3)／[保存証拠](evidence/1960/04.json)（取得 2026-10-11T03:59:59.374044+00:00）：���������B ���₢���킹 ���e�̓��� ���͓��e�� �m�F ���� ���₢���킹�̎�� �Z�p�E�H���֘A �̗p�E���l�֘A IR�֘A ���i�J�^���O�֘A ZEB�֘A ���̑����ӌ��A���₢���킹 ���₢���킹���e �����O �� �� �ӂ肪�� ���S�p�Ђ炪�

### 1963 日揮ホールディングス

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.jgc.com/jp/inquiries/general/input/?kind=2)／[保存証拠](evidence/1963/04.json)（取得 2026-10-11T03:59:59.785139+00:00）： お問い合わせ 内容のご入力 入力内容の ご確認 お問い合わせ 完了 お問い合わせの種類 サイト全般、各種プラントについて 先端技術産業（半導体・データセンター・蓄電池）について IRについて 採用について サステナビリティの協創について 件名 お問い合わせ内容 お名前 会社名(または個人・学生など) 部署名 住所 電話番号 メールアドレス お問い合わせの前に「日揮グル
- [公式ページ](https://www.jgc.com/jp/inquiries/general/input/?kind=2)／[保存証拠](evidence/1963/04.json)（取得 2026-10-11T03:59:59.785139+00:00）：イト全般、各種プラントについて 先端技術産業（半導体・データセンター・蓄電池）について IRについて 採用について サステナビリティの協創について 件名 お問い合わせ内容 お名前 会社名(または個人・学生など) 部署名 住所 電話番号 メールアドレス お問い合わせの前に「日揮グループ個人情報保護方針」をお読みください。 日揮グループ個人情報保護方針 日揮グループ各社は、個人情報保護の重要

### 1964 中外炉工業

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式の IR フォーム案内は確認したが、IR 対象先の実メール入力・質問欄は保存証拠では未検証。 / 個人受付条件、字数制限、送信後の到達・返信は未確認。 / 対象先では「このページには直接アクセスできません。」と表示。IR 用質問が入力できるか再確認が必要。

根拠：

- [公式ページ](https://www.chugai.co.jp/ir/faq/)／[保存証拠](evidence/1964/03.json)（取得 2026-10-11T04:00:02.678172+00:00）：その他、業績・事業戦略等に関する問い合わせをしたいのですが。 「お問い合わせメールフォーム」 のページをご覧ください。

### 1968 太平電業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.taihei-dengyo.co.jp/inquiry/)／[保存証拠](evidence/1968/04.json)（取得 2026-10-11T04:00:04.643487+00:00）： 当社施工における御社サービス・商品のご提案 テクノロジーページ（技術／工法一覧）に関するお問い合わせ 西風新都バイオマス発電所見学に関するお問い合わせ 採用に関するお問い合わせ 財務・IRに関するお問い合わせ 会社全般(総務面・広報面)に関するお問い合わせ 会社名（店舗、団体名） 部署名 お名前 必須 お名前(ふりがな) 必須 電話番号 - - 住所 〒 - E-mail 必須 ホーム

### 196A ＭＦＳ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IR専用ページにフォーム案内があるが、保存GETでは実入力欄を確認できない。
- 問い合わせ内容により電話・書面で回答する場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://ir.mortgagefss.jp/inquiry/)／[保存証拠](evidence/196A/05.json)（取得 2026-10-11T04:00:06.315919+00:00）：IRについてのお問い合わせ
- [公式ページ](https://ir.mortgagefss.jp/inquiry/)／[保存証拠](evidence/196A/05.json)（取得 2026-10-11T04:00:06.315919+00:00）：下記のフォームに必要事項を入力の上、「入力内容を確認」 をクリックして下さい。
- [公式ページ](https://ir.mortgagefss.jp/inquiry/)／[保存証拠](evidence/196A/05.json)（取得 2026-10-11T04:00:06.315919+00:00）：お問い合せの内容によっては電話や書面で回答を差し上げる場合もございます

### 1975 朝日工業社

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.asahikogyosha.co.jp/contact/ir/)／[保存証拠](evidence/1975/07.json)（取得 2026-10-11T04:00:19.665003+00:00）：IR \| お問い合わせ \| 空調設備工事の朝日工業社 CONTACT お問い合わせ MENU 朝日工業社について 朝日工業社について トップ トップメッセージ ASAHI-PHILOSOPHY コーポレ
- [公式ページ](https://www.asahikogyosha.co.jp/contact/ir/)／[保存証拠](evidence/1975/07.json)（取得 2026-10-11T04:00:19.665003+00:00）： お問い合わせの内容によっては回答に時間がかかり、または回答しかねる場合がございますので、あらかじめご了承ください。 お問い合わせ内容 必須 お客さま情報 個人／法人・団体 必須 個人 法人 会社名 部署名 お名前 必須 メールアドレス(半角英数) 必須 電話番号 郵便番号 ご住所 必須 お問い合わせにあたってのご注意 ・お客さまからいただく個人情報は、お問い合わせへ

### 1976 明星工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 名前・ふりがな・メール・電話・問い合わせ内容に必須表示。プライバシーポリシーへの同意が必要。

注意・未確認：個人投資家の明示受付条件、字数制限・沈黙期間・送信後の到達や返信は未確認。

根拠：

- [公式ページ](https://www.meisei-kogyo.co.jp/inquiry/)／[保存証拠](evidence/1976/03.json)（取得 2026-10-11T04:00:04.179632+00:00）：お問い合わせ項目 必須 事業内容について 製品について IRについて 採用について その他のお問い合わせ
- [公式ページ](https://www.meisei-kogyo.co.jp/inquiry/)／[保存証拠](evidence/1976/03.json)（取得 2026-10-11T04:00:04.179632+00:00）：お名前 必須 フリガナ 必須 法人名 メールアドレス 必須 電話番号 必須 FAX番号 郵便番号 住所 お問い合わせ内容 必須
- [公式ページ](https://www.meisei-kogyo.co.jp/inquiry/)／[保存証拠](evidence/1976/03.json)（取得 2026-10-11T04:00:04.179632+00:00）：当社 プライバシーポリシー をご覧いただき、ご同意の上、お問い合わせください。

### 197A タウンズ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 株主・投資家向けのIR問い合わせフォーム案内がある。実入力欄は保存取得では未確認。
- 非公開情報、株式市場の値動き、営業・勧誘、誹謗中傷への回答は控える。内容により回答が遅れる・回答しない場合がある。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 公式のIR窓口案内までの確認。メールと質問本文の実入力欄を結び付けた確認は完了していない。

根拠：

- [公式ページ](https://www.tauns.co.jp/investors/contact/)／[保存証拠](evidence/197A/03.json)（取得 2026-10-11T04:00:03.682776+00:00）：株主・投資家の皆さまからのお問い合わせ 株式やIR情報に関するご質問・ご要望は下記よりお問い合わせください。
- [公式ページ](https://www.tauns.co.jp/investors/contact/)／[保存証拠](evidence/197A/03.json)（取得 2026-10-11T04:00:03.682776+00:00）：非公開情報に関するご質問 株式市場の値動きに関するご質問 営業や勧誘のお問い合わせ 誹謗中傷に該当するメッセージ
- [公式ページ](https://www.tauns.co.jp/investors/contact/)／[保存証拠](evidence/197A/03.json)（取得 2026-10-11T04:00:03.682776+00:00）：株式やIR情報に関する お問い合わせ インターネットからのお問い合わせは 下記フォームよりご連絡ください。 お問い合わせフォーム

### 1980 ダイダン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・所属名は任意。氏名・メール・本文は必須表示。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.form.daidan.co.jp/n/form/c/v1/ojpb/forms/Gd6FS2t-Lak6HS5SSnEGX)／[保存証拠](evidence/1980/05.json)（取得 2026-10-11T04:00:11.294683+00:00）：IRへのお問い合わせ｜お問い合わせ｜ダイダン株式会社 技術とサービス 技術とサービス 技術とサービストップ 事業案内 ソリューション 施工実績 イノベーション 企業情報 企業情報 企業情報トップ ダイ
- [公式ページ](https://www.form.daidan.co.jp/n/form/c/v1/ojpb/forms/Gd6FS2t-Lak6HS5SSnEGX)／[保存証拠](evidence/1980/05.json)（取得 2026-10-11T04:00:11.294683+00:00）：uired fields are labeled. 入力 確認 完了 必須 Required お名前 Name 必須 Required メールアドレス Email address 任意 Optional 御社名（所属名） Company 任意 Optional 部署 Dept 任意 Optional 郵便番号 Zip 住所の自動入力 ※ハイフンなしの半角数字でご入力ください。 *Please enter numb
- [公式ページ](https://www.daidan.co.jp/ir/)／[保存証拠](evidence/1980/02.json)（取得 2026-10-11T04:00:08.041505+00:00）：NDAR IRカレンダー IRカレンダー ESG ESG経営 PUBLIC NOTICE 電子公告 CONTACT IRへのお問い合わせ DISCLAIMER 免責事項 DISCLOSURE ディスクロージャーポリシー 技術とサービス 

### 1981 協和日成

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@kyowa-nissei.co.jp`。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kyowa-nissei.co.jp/inquiry/)／[保存証拠](evidence/1981/03.json)（取得 2026-10-11T04:00:07.411382+00:00）：お知らせ一覧（アーカイブ） 採用情報 + 新卒採用情報 中途採用情報 電子公告 お問い合わせ プライバシーポリシー サイトマップ ホーム お問い合わせ お問い合わせ お問い合わせ IRに関するお問い合わせ ir@kyowa-nissei.co.jp 当社の工事・車両に対する苦情・トラブルのお問い合わせ kouji@kyowa-nissei.co.jp 内部通報・コンプライアンスに関するお問い合わせ helpline@kyow

### 198A ＰｏｓｔＰｒｉｍｅ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式企業IRページが専用ticket_form_id付きの外部Zendeskフォームを案内し、同じフォームにIR問い合わせの選択肢がある。
- メール・所属・会社名・住所・件名・問い合わせ内容の表示あり。個人の所属欄の記入方法・必須条件は保存証拠では未確認。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://help.postprime.com/hc/ja/requests/new?ticket_form_id=9766923764879)／[保存証拠](evidence/198A/05.json)（取得 2026-10-11T04:00:12.405158+00:00）：IRに関するお問い合わせ メールアドレス ご所属 会社名 ご住所 件名 問い合わせ内容
- [公式ページ](https://help.postprime.com/hc/ja/requests/new?ticket_form_id=9766923764879)／[保存証拠](evidence/198A/05.json)（取得 2026-10-11T04:00:12.405158+00:00）：速やかにご回答できるよう、お問い合わせ内容はできるかぎり具体的にご記入くださいますようお願いいたします。
- [公式ページ](https://corp.postprime.com/ir/)／[保存証拠](evidence/198A/02.json)（取得 2026-10-11T04:00:08.152525+00:00）：IRお問い合わせ
- [公式ページ](https://corp.postprime.com/contact/)／[保存証拠](evidence/198A/03.json)（取得 2026-10-11T04:00:08.986903+00:00）：IRに関する問合せ

### 1994 高橋カーテンウォール工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・所属を必須表示。IR選択時に個人が入力できる条件は未確認。法人限定とは断定しない。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://t-cw.co.jp/form/)／[保存証拠](evidence/1994/03.json)（取得 2026-10-11T04:00:10.417991+00:00）：ご確認の上、送信ボタンを押してください。 お問い合わせ内容 必須 PCカーテンウォールに関する問い合わせ PCカーテンウォール出張講習会に関する問い合わせ 採用に関する問い合わせ ＩＲ・その他に関する問い合わせ スパジオに関する問い合わせ・注文 会社名 会社名 必須 所属 必須 郵便番号 必須 住所 必須 電話番号 必須 お名前 必須 メールアドレス 必須 お問い合わせ内容 必須 高橋カ
- [公式ページ](https://t-cw.co.jp/form/)／[保存証拠](evidence/1994/03.json)（取得 2026-10-11T04:00:10.417991+00:00）：テンウォールに関する問い合わせ PCカーテンウォール出張講習会に関する問い合わせ 採用に関する問い合わせ ＩＲ・その他に関する問い合わせ スパジオに関する問い合わせ・注文 会社名 会社名 必須 所属 必須 郵便番号 必須 住所 必須 電話番号 必須 お名前 必須 メールアドレス 必須 お問い合わせ内容 必須 高橋カーテンウォール工業株式会社 CONTACT US PRIVACY P

### 2001 ニップン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お返事のメールはお客様個人宛てにお送りするものであり、弊社の許可なく一部または全部を転載、二次利用することはご遠慮ください。
- 回答は電話または手紙でご返答する場合もありますので、ご了承願います。
- 携帯電話のメ－ルアドレスには文字数の制約などお客様への充分なご回答を差し上げられない場合がありますのでご返信致しかねます。

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.nippn.co.jp/customer/inquiry/index.html)／[保存証拠](evidence/2001/07.json)（取得 2026-10-11T04:00:15.720990+00:00）：お問い合わせ内容 必須 家庭用商品について 健康食品・化粧品について 業務用商品について IR情報について CSR活動について 広報活動について SNSについて その他
- [公式ページ](https://www.nippn.co.jp/customer/inquiry/index.html)／[保存証拠](evidence/2001/07.json)（取得 2026-10-11T04:00:15.720990+00:00）：件名 必須 お問い合わせ詳細 必須
- [公式ページ](https://www.nippn.co.jp/customer/inquiry/index.html)／[保存証拠](evidence/2001/07.json)（取得 2026-10-11T04:00:15.720990+00:00）：メールアドレス 必須 （確認用）もう一度ご入力ください
- [公式ページ](https://www.nippn.co.jp/ir/investerfaq/index.html)／[保存証拠](evidence/2001/02.json)（取得 2026-10-11T04:00:09.075171+00:00）：株式会社ニップン 経理・財務部IR室
- [公式ページ](https://www.nippn.co.jp/customer/inquiry/index.html)／[保存証拠](evidence/2001/07.json)（取得 2026-10-11T04:00:15.720990+00:00）：お返事のメールはお客様個人宛てにお送りするものであり、弊社の許可なく一部または全部を転載、二次利用することはご遠慮ください。
- [公式ページ](https://www.nippn.co.jp/customer/inquiry/index.html)／[保存証拠](evidence/2001/07.json)（取得 2026-10-11T04:00:15.720990+00:00）：回答は電話または手紙でご返答する場合もありますので、ご了承願います。
- [公式ページ](https://www.nippn.co.jp/ir/investerfaq/index.html)／[保存証拠](evidence/2001/02.json)（取得 2026-10-11T04:00:09.075171+00:00）：携帯電話のメ－ルアドレスには文字数の制約などお客様への充分なご回答を差し上げられない場合がありますのでご返信致しかねます。

### 2002 日清製粉グループ本社

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 法人・団体の問い合わせは所属入力が必要。本文は500文字以内。
- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nisshin.com/inquiry/ir/?utm_source=nisshin_com&utm_medium=link_products&utm_campaign=23_cus-p-cat_ir)／[保存証拠](evidence/2002/04.json)（取得 2026-10-11T04:00:12.940785+00:00）：IR・投資家情報に関するお問い合わせ \| お問い合わせ \| 日清製粉グループお問い合わせ \| 日清製粉グループ 日清製粉グループ 健康と信頼をお届けする ニュースリリース 商品情報 採用情報 お問い合わせ Engli
- [公式ページ](https://www.nisshin.com/inquiry/ir/?utm_source=nisshin_com&utm_medium=link_products&utm_campaign=23_cus-p-cat_ir)／[保存証拠](evidence/2002/04.json)（取得 2026-10-11T04:00:12.940785+00:00）：ている項目は、入力必須項目です。 件名 ※ お問い合わせの内容 ※ 500文字以内でご入力ください お名前（漢字） ※ お名前（フリガナ） 全角でご入力ください 会社名（団体名） 法人、団体等の方は必ずご所属をご記入ください 性別 女 男 年齢 選択してください 10歳未満 10代 20代 30代 40代 50代 60代 70代 80代 90代 E-mailアドレス ※ 半角英数でご入力ください 電話
- [公式ページ](https://www.nisshin.com/inquiry/ir/?utm_source=nisshin_com&utm_medium=link_products&utm_campaign=23_cus-p-cat_ir)／[保存証拠](evidence/2002/04.json)（取得 2026-10-11T04:00:12.940785+00:00）：によりましては回答いたしかねる場合がございます。 お名前、電話番号、E-mailアドレスは正確にご記入ください。不備がある場合は対応いたしかねる事もございます。 弊社よりお送りしたメール回答内容の一部または全部の転載、二次利用はご遠慮ください。 お客様の個人情報およびお問い合わせ等の内容は、適切に取り扱います。お寄せいただいたご意見・ご質問等の内容は、お客様へのお返事および弊社の製品・サービスの向上と改善に活かすための

### 2003 日東富士製粉

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お客様からいただいたメールは平日9時～17時に拝読しております。
- 平日17時以降および土曜、日曜、祝日、年末年始などの弊社休業日にいただきましたメールは 翌営業日以降の拝読となります。
- ご返信にはお時間を頂戴する場合やご返信いたしかねる場合もございます。

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.nittofuji.co.jp/form/)／[保存証拠](evidence/2003/03.json)（取得 2026-10-11T04:00:11.287791+00:00）：お問い合わせ項目 * 業務用商品について 家庭用商品について IR（投資家情報について） その他 お問い合わせ内容 *
- [公式ページ](https://www.nittofuji.co.jp/form/)／[保存証拠](evidence/2003/03.json)（取得 2026-10-11T04:00:11.287791+00:00）：電話番号 * メールアドレス *
- [公式ページ](https://www.nittofuji.co.jp/form/)／[保存証拠](evidence/2003/03.json)（取得 2026-10-11T04:00:11.287791+00:00）：お客様からいただいたメールは平日9時～17時に拝読しております。
- [公式ページ](https://www.nittofuji.co.jp/form/)／[保存証拠](evidence/2003/03.json)（取得 2026-10-11T04:00:11.287791+00:00）：平日17時以降および土曜、日曜、祝日、年末年始などの弊社休業日にいただきましたメールは 翌営業日以降の拝読となります。
- [公式ページ](https://www.nittofuji.co.jp/form/)／[保存証拠](evidence/2003/03.json)（取得 2026-10-11T04:00:11.287791+00:00）：ご返信にはお時間を頂戴する場合やご返信いたしかねる場合もございます。

### 2004 昭和産業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせ内容によっては、お返事が数日かかる場合、もしくはお返事できない場合がございます。
- お問い合わせ内容によっては、直接お電話やお手紙にてお返事差し上げる場合がございます。
- お送りしましたメール回答内容の一部または全部の転載、二次利用はご遠慮ください。

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/)／[保存証拠](evidence/2004/04.json)（取得 2026-10-11T04:00:14.335880+00:00）：昭和産業(株)・IRについて 担当窓口 昭和産業(株) 企画部 コーポレート・コミュニケーション室 メールでのお問い合わせ 入力フォームへ
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：IR（投資家情報）について
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：お問い合わせ内容 必須 全角500文字以内でご記入ください。
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：メールアドレス 必須 メールアドレス確認 必須 確認の為、再度入力してください。
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：お問い合わせ内容によっては、お返事が数日かかる場合、もしくはお返事できない場合がございます。
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：お問い合わせ内容によっては、直接お電話やお手紙にてお返事差し上げる場合がございます。
- [公式ページ](https://www.showa-sangyo.co.jp/corporate/inquiry/form.html)／[保存証拠](evidence/2004/05.json)（取得 2026-10-11T04:00:15.516812+00:00）：お送りしましたメール回答内容の一部または全部の転載、二次利用はご遠慮ください。

### 205A ロゴスホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式英文IR専用フォーム。氏名・メール/確認用メール・電話・郵便番号・住所・本文欄がある。
- 内容により電話・手紙で回答する場合がある。メール受信は@logos-holdings.jpの許可設定を案内。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://logos-holdings.jp/english/ir/inquiry/)／[保存証拠](evidence/205A/04.json)（取得 2026-10-11T04:00:12.756882+00:00）：IR Inquiries – LOGOS HOLDINGS INC.
- [公式ページ](https://logos-holdings.jp/english/ir/inquiry/)／[保存証拠](evidence/205A/04.json)（取得 2026-10-11T04:00:12.756882+00:00）：Please fill in the required information in the contact form below and click “Confirm Your Input.”
- [公式ページ](https://logos-holdings.jp/english/ir/inquiry/)／[保存証拠](evidence/205A/04.json)（取得 2026-10-11T04:00:12.756882+00:00）：Depending on the nature of your inquiry, we may respond by phone or letter, so please ensure that your phone number and address are correct.
- [公式ページ](https://logos-holdings.jp/english/ir/inquiry/)／[保存証拠](evidence/205A/04.json)（取得 2026-10-11T04:00:12.756882+00:00）：Name Email Address
- [公式ページ](https://logos-holdings.jp/english/ir/inquiry/)／[保存証拠](evidence/205A/04.json)（取得 2026-10-11T04:00:12.756882+00:00）：Email Address Re-enter Telephone Number Post Code Address Inquiry Details

### 2060 フィード・ワン

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`info@feed-one.co.jp`。

取得範囲の受付条件：

- お問い合わせの際はご連絡先（ご住所、電話番号）の記載をお願い申し上げます。
- お問い合わせ内容により、ご回答までにお時間を頂戴する場合がございます。
- 弊社休業期間中（土日祝日など）は、お問い合わせの受付のみとさせていただきます。

注意・未確認：https://www.youtube.com/embed/U24atL7f6SE: ProxyError / https://www.youtube.com/embed/PVacoDKVDBM?si=xMgjFL5D-qUyQGnA: ProxyError / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.feed-one.co.jp/ir/faq.html)／[保存証拠](evidence/2060/02.json)（取得 2026-10-11T04:00:11.925193+00:00）：Q IRに関する問い合わせ先を教えてください。 A お問い合わせフォームは こちら 。
- [公式ページ](https://www.feed-one.co.jp/form/)／[保存証拠](evidence/2060/03.json)（取得 2026-10-11T04:00:12.609793+00:00）：お問い合わせ ※ info@feed-one.co.jp
- [公式ページ](https://www.feed-one.co.jp/form/)／[保存証拠](evidence/2060/03.json)（取得 2026-10-11T04:00:12.609793+00:00）：お問い合わせの際はご連絡先（ご住所、電話番号）の記載をお願い申し上げます。
- [公式ページ](https://www.feed-one.co.jp/form/)／[保存証拠](evidence/2060/03.json)（取得 2026-10-11T04:00:12.609793+00:00）：お問い合わせ内容により、ご回答までにお時間を頂戴する場合がございます。
- [公式ページ](https://www.feed-one.co.jp/form/)／[保存証拠](evidence/2060/03.json)（取得 2026-10-11T04:00:12.609793+00:00）：弊社休業期間中（土日祝日など）は、お問い合わせの受付のみとさせていただきます。

### 208A 構造計画研究所ホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://www.kke-hd.co.jp/inquiry/)／[保存証拠](evidence/208A/03.json)（取得 2026-10-11T04:01:52.439613+00:00）：IRお問い合わせ窓口 株式・投資、IRに関するお問い合わせはこちらへ。 お問い合わせフォーム

### 2108 日本甜菜製糖

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IR問合せ専用ページと注意事項は確認。保存本文にはメール・問い合わせ本文の実入力欄がなく、動的フォームの入力条件は未確認。

根拠：

- [公式ページ](https://www.nitten.co.jp/ir/inquiry/)／[保存証拠](evidence/2108/05.json)（取得 2026-10-11T04:00:18.114910+00:00）： IR情報 IRお問い合わせ IRお問い合わせ IR情報に関するお問い合わせを承っております。 お問い合わせ前に、 よくある質問 で解決できる場合がございます。ぜひご覧ください。 IRお問い合わせフォーム ご入力いただく前に いただきましたメールに対してご返事を差し上げられない場合がございます。 お問い合わせのご返事は営業時間内（土・日・祝日・年末年始を除く9:00～17:00）に

### 2109 ＤＭ三井製糖

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 法人の場合は氏名とともに法人名を記入。住所・電話等も必須表示。内容により電話で連絡する場合がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.msdm-hd.com/jp/contact/input)／[保存証拠](evidence/2109/06.json)（取得 2026-10-11T04:00:18.358783+00:00）：おります。 一部または全部の転載、2次利用などはご遠慮ください。 お問い合わせ内容の入力 分類 必須 商品について（砂糖関連商品） 商品について（スポーツ関連商品、その他の商品） IR情報関連について 株式手続き、株主優待関連について サステナビリティについて 採用について 上記以外について お問い合わせ内容タイトル 例）上白糖の賞味期限について お問い合わせ内容 必須 商品に
- [公式ページ](https://www.msdm-hd.com/jp/contact/input)／[保存証拠](evidence/2109/06.json)（取得 2026-10-11T04:00:18.358783+00:00）：の賞味期限について お問い合わせ内容 必須 商品についてのお問い合わせの場合は、商品名をご記入ください。 例）スプーン印上白糖1kg お客様情報の入力 お名前 必須 例）三井太郎 法人の方は法人名もご記入ください。 法人の方の例）DM三井製糖株式会社 三井太郎 ふりがな 必須 例）みついたろう メールアドレス 必須 例）sato@mitsui.XX.XX メールアドレス（確認用） 必須 電

### 2117 ウェルネオシュガー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 保存URLは機能性素材の初期選択クエリ付きのため「会社・IRについて」を選び直す必要がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.wellneo-sugar.co.jp/contact/contact/?type=%E6%A9%9F%E8%83%BD%E6%80%A7%E7%B4%A0%E6%9D%90%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6)／[保存証拠](evidence/2117/04.json)（取得 2026-10-11T04:00:18.927822+00:00）：することがございます。 また、商品の売り込みなど、内容によっては回答できない場合がございます。あらかじめご了承ください。 お問い合わせ内容 お問い合わせの種類 必須 商品について 会社・IRについて 機能性素材について その他 商品名 内容量 ロット番号または賞味期限 お問い合わせ内容 必須 お客様情報 お名前 必須 姓 名 ふりがな 必須 せい めい 会社・学校・機関名 会
- [公式ページ](https://www.wellneo-sugar.co.jp/contact/contact/?type=%E6%A9%9F%E8%83%BD%E6%80%A7%E7%B4%A0%E6%9D%90%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6)／[保存証拠](evidence/2117/04.json)（取得 2026-10-11T04:00:18.927822+00:00）：することがございます。 また、商品の売り込みなど、内容によっては回答できない場合がございます。あらかじめご了承ください。 お問い合わせ内容 お問い合わせの種類 必須 商品について 会社・IRについて 機能性素材について その他 商品名 内容量 ロット番号または賞味期限 お問い合わせ内容 必須 お客様情報 お名前 必須 姓 名 ふりがな 必須 せい めい 会社・学校・機関名 会

### 211A カドス・コーポレーション

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。会社名が必須表示だが個人の記入方法は未確認。希望連絡方法はメール・電話・どちらでもを選択できる。
- 内容により回答しない場合がある。売り込み・協業目的での利用は不可。reCAPTCHAあり。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。 / 所属を求める欄が必須表示だが、所属のない個人の記入方法・利用可否は未確認。

根拠：

- [公式ページ](https://cados.jp/ir/inquiry_ir/)／[保存証拠](evidence/211A/03.json)（取得 2026-10-11T04:00:19.856425+00:00）：IRについてのお問い合わせ 下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」をクリックしてください。
- [公式ページ](https://cados.jp/ir/inquiry_ir/)／[保存証拠](evidence/211A/03.json)（取得 2026-10-11T04:00:19.856425+00:00）：会社名 必須
- [公式ページ](https://cados.jp/ir/inquiry_ir/)／[保存証拠](evidence/211A/03.json)（取得 2026-10-11T04:00:19.856425+00:00）：売り込みや協業目的のお問い合わせはご遠慮ください。
- [公式ページ](https://cados.jp/ir/inquiry_ir/)／[保存証拠](evidence/211A/03.json)（取得 2026-10-11T04:00:19.856425+00:00）：ご希望の連絡方法 どちらでも メール 電話 必須 お問い合わせ内容 必須

### 2120 ＬＩＦＵＬＬ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 株主優待担当メールを事業IR窓口から除外。公式IRリンクの enqueteid=15 を採用し、別の19に対する robots_disallowed を混同していない。実フォームは未取得。

根拠：

- [公式ページ](https://lifull.com/)／[保存証拠](evidence/2120/01.json)（取得 2026-10-11T04:00:16.280976+00:00）：室 決算・その他資料 株主総会 アニュアルレポート 株式基本情報 株価情報 株主還元について 中期経営計画 事業概況 事業等のリスク 1ページでわかるLIFULL IRカレンダー IRに関するお問合せ ニュース サステナビリティ サステナビリティTOP サステナビリティ課題 サステナビリティ サステナビリティ経営 LIFULLグループのサステナビリティ経営 サステナビリティ課題

### 2121 ＭＩＸＩ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://mixi.co.jp/inquiry/ir/)／[保存証拠](evidence/2121/02.json)（取得 2026-10-11T04:00:17.718561+00:00）：IR・投資家関連についてのお問い合わせ \| お問い合わせ \| 株式会社MIXI 全てのメニュー MIXIについて 企業情報 ニュース 事業 IR情報 サステナビリティ 採用情報 お問い合わせ 企業情報 COMPANY 

### 2122 インタースペース

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`contact@interspace.inc`。

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。 / 公開メールは可視本文の原文ではなく、公開Cloudflare表示用hrefから復元した派生値。raw protected表示・元href・復号手法を別々に保持。

根拠：

- [公式ページ](https://www.interspace.ne.jp/)／[保存証拠](evidence/2122/01.json)（取得 2026-10-11T04:01:48.818570+00:00）：IRお問い合わせ
- [公式ページ](https://www.interspace.ne.jp/contact/)／[保存証拠](evidence/2122/02.json)（取得 2026-10-11T04:01:50.719660+00:00）：株式会社インタースペースに関するお問い合わせは [email protected]

### 2127 日本Ｍ＆Ａセンターホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答の転載・二次利用をご遠慮との記載。内容により電子メール以外の回答・無回答・遅延の可能性がある。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nihon-ma.co.jp/action/contact/?ctype=ir)／[保存証拠](evidence/2127/03.json)（取得 2026-10-11T04:01:51.611340+00:00）：だいた方に宛てたものです。 回答の一部または全部を転載、二次利用することはご遠慮願います。 1. 必要事項を入力する 2. 入力内容を確認する 3. 送信→完了 お問い合わせ種別 IR関連について IRに関するよくあるご質問 採用に関して 取材のご依頼 ※ M&A・事業承継について ※ 日本M&A協会について その他 貴社名・貴事務所名 部署 お役職 お名前 姓 名 Eメー
- [公式ページ](https://www.nihon-ma.co.jp/action/contact/?ctype=ir)／[保存証拠](evidence/2127/03.json)（取得 2026-10-11T04:01:51.611340+00:00）：い場合がございます。 個人情報の取り扱いについては個人情報保護方針をご覧ください。 尚、当社から返信するメールは、お問い合わせいただいた方に宛てたものです。 回答の一部または全部を転載、二次利用することはご遠慮願います。 1. 必要事項を入力する 2. 入力内容を確認する 3. 送信→完了 お問い合わせ種別 IR関連について IRに関するよくあるご質問 採用に関して 取材のご依頼 ※ M&A・事
- [公式ページ](https://www.nihon-ma.co.jp/groups/ir/)／[保存証拠](evidence/2127/02.json)（取得 2026-10-11T04:01:50.018030+00:00）：績概況発表（予定）​​​​ IRカレンダー一覧 よくあるご質問（IRについて） 電子公告 免責事項 IRに関するお問い合わせは、下記フォームより承ります。 IRに関するお問い合わせ 日本M&Aセンターホールディングス（東証プ

### 212A フィットイージー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。氏名・ふりがな・メール・質問本文が必須表示。JavaScript利用の案内あり。
- 非公開情報、重要事実、株式市場の値動き、誹謗中傷、営業・勧誘には回答できない場合がある。
- 決算期日の翌日から決算発表日までの一定期間が沈黙期間で、当該期間の質問・問い合わせへの対応を控える。本人・連絡先を確認できない場合も回答しない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://fiteasy.co.jp/contact/ir-inquiry/)／[保存証拠](evidence/212A/03.json)（取得 2026-10-11T04:01:50.715543+00:00）：※こちらはIR（投資家情報）に関するお問い合わせフォームです。
- [公式ページ](https://fiteasy.co.jp/contact/ir-inquiry/)／[保存証拠](evidence/212A/03.json)（取得 2026-10-11T04:01:50.715543+00:00）：非公開情報に関するご質問（業績予測など）
- [公式ページ](https://fiteasy.co.jp/contact/ir-inquiry/)／[保存証拠](evidence/212A/03.json)（取得 2026-10-11T04:01:50.715543+00:00）：当社は、決算情報の漏洩を防止し公平性を確保するため、決算期日の翌日から決算発表日までの一定期間を「沈黙期間」としております。 当該期間中のご質問・お問い合わせへの対応につきましては差し控えております。
- [公式ページ](https://fiteasy.co.jp/contact/ir-inquiry/)／[保存証拠](evidence/212A/03.json)（取得 2026-10-11T04:01:50.715543+00:00）：氏名 * ふりがな * メールアドレス *
- [公式ページ](https://fiteasy.co.jp/contact/ir-inquiry/)／[保存証拠](evidence/212A/03.json)（取得 2026-10-11T04:01:50.715543+00:00）：ご質問・ご意見 *

### 2130 メンバーズ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.members.co.jp/contact)／[保存証拠](evidence/2130/03.json)（取得 2026-10-11T04:01:50.676182+00:00）：広報／IR／当社及び当Webサイトに関するお問い合わせは、以下のお問い合わせフォームにて、受け付けております。

### 2134 北浜キャピタルパートナーズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://kitahamabank.co.jp/inquiry/)／[保存証拠](evidence/2134/04.json)（取得 2026-10-11T04:01:53.492864+00:00）：お問い合わせ \| 北浜キャピタルパートナーズ株式会社 メインコンテンツへ移動 会社情報 ガバナンス・社会的責任 PR情報 IR情報 株式情報 財務ハイライト 有報・四半期報 決算短信 免責事項について 電子公告 会長レポート 北浜インサイト 事業動画 JP/EN 会社情報 ガバナンス・社会的責任 PR情報

### 2136 ヒップ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 電話・メールのどちらかの連絡先を必須入力。希望がない場合は両方を記入する案内。メール返信を希望する場合は実メールアドレスを指定する。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.hip-pro.co.jp/form/form.html)／[保存証拠](evidence/2136/03.json)（取得 2026-10-11T04:01:53.604098+00:00）：o.co.jp 確認のため再度ご入力ください 任意 お問い合わせ項目 技術者派遣に関するお問い合わせ 業務請負（常駐請負・受託開発）に関するお問い合わせ 採用に関するお問い合わせ メディア掲載・IR情報に関するお問い合わせ その他 任意 お問い合わせ内容 お預かりする個人情報の取り扱いについて 当社はお預かりしたお客様情報 (氏名、住所、電話番号、メールアドレスなど)を、法令およびその他の規範を遵守
- [公式ページ](https://www.hip-pro.co.jp/form/form.html)／[保存証拠](evidence/2136/03.json)（取得 2026-10-11T04:01:53.604098+00:00）：内容の ご入力 2 ご入力内容の ご確認 3 お問い合わせ 完了 任意 御社名 例）株式会社ヒップ 任意 所属部署 例）営業部 必須 お名前 例）山田 太郎 姓 ： 名 ： 必須 ご希望連絡方法 ご希望連絡方法の情報を どれか一つ必ず入力 してください。連絡方法のご希望がない場合は両方ご入力ください。 電話番号 例）0453281000 メールアドレス 例）HybridI

### 2138 クルーズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://crooz.co.jp/contact-form/)／[保存証拠](evidence/2138/03.json)（取得 2026-10-11T04:01:51.767599+00:00）：す。本窓口では対応しかねますの で、ご了承ください。 配当・株式情報など IRページ 、よくあるご質問の FAQ にまとめておりますので、ご覧いただきますようお願い申し上げます。 当社のIR情報について 東京証券取引所が重要事実と定める事項や、それ以外で当社が重要と捉え、正確な情報を広く公平にお伝えすべきと判断したものは、随時Tdnet(東京証券取引事務所の提供する適時情報伝達シ

### 2146 ＵＴグループ

確認：案内・リンクのみ。個人受付の明示あり。窓口候補。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.ut-g.co.jp/inquiry/)／[保存証拠](evidence/2146/03.json)（取得 2026-10-11T04:01:51.550782+00:00）：■投資家情報に関するお問い合わせ先 個人投資家、機関投資家、アナリストの皆様からのお問い合わせ・資料請求 ＵＴグループ株式会社 IRファンクション 問い合わせフォーム

### 2148 アイティメディア

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせの内容によっては、ご回答にお時間をいただく場合やお答えしかねる場合がありますので、あらかじめご了承ください。

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://corp.itmedia.co.jp/ir/other/inquiry/)／[保存証拠](evidence/2148/03.json)（取得 2026-10-11T04:01:51.840007+00:00）：アイティメディア株式会社のIR、株主・投資家情報に関するお問い合わせを受け付けています。
- [公式ページ](https://corp.itmedia.co.jp/ir/other/inquiry/)／[保存証拠](evidence/2148/03.json)（取得 2026-10-11T04:01:51.840007+00:00）：お名前 ※ フリガナ メールアドレス ※ 電話番号 ※ 会社名 お問い合わせ内容 ※
- [公式ページ](https://corp.itmedia.co.jp/ir/other/inquiry/)／[保存証拠](evidence/2148/03.json)（取得 2026-10-11T04:01:51.840007+00:00）：お問い合わせの内容によっては、ご回答にお時間をいただく場合やお答えしかねる場合がありますので、あらかじめご了承ください。

### 2153 Ｅ・Ｊホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.ej-hds.co.jp/ir/)／[保存証拠](evidence/2153/02.json)（取得 2026-10-11T04:01:51.182360+00:00）：IRお問い合わせ

### 2158 ＦＲＯＮＴＥＯ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.fronteo.com/ir/results/)／[保存証拠](evidence/2158/06.json)（取得 2026-10-11T04:01:56.582869+00:00）：決算・IRに関するお問い合わせ

### 2160 ジーエヌアイグループ

確認：IRメール確認。個人条件の明示未確認。個別回答なし。

公開IRメール：`infojapan@gnipharma.com`。

取得範囲の受付条件：

- IRについてのご質問への回答につきましては、フェアディスクロージャー観点から、個別にご質問をいただいた方への回答という方法ではなく、株主共同の利益の確保の観点から投資家の皆様にお知らせすることが有用であると当社が判断した場合に、適時開示や当社ホームページのお知らせにて掲載させていただく方法に代えさせていただきます。
- 回答を掲載するまでにお時間を要する場合があり、「いつ掲載されるか」といった個別回答につきましてもお答えができかねますので、あらかじめご了承くださいませ。
- 業績動向などの非公開情報に関するお問い合わせ 株価対策など金融商品取引法 第 166 条「重要事実」に該当する可能性のあるお問い合わせ 株価動向など株式市場の値動に関するお問い合わせ 誹謗、中傷が含まれるお問い合わせ

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.gnipharma.com/inquiry/)／[保存証拠](evidence/2160/03.json)（取得 2026-10-11T04:01:51.771004+00:00）：メールで問い合わせる
- [公式ページ](https://www.gnipharma.com/inquiry/)／[保存証拠](evidence/2160/03.json)（取得 2026-10-11T04:01:51.771004+00:00）：IRについてのご質問への回答につきましては、フェアディスクロージャー観点から、個別にご質問をいただいた方への回答という方法ではなく、株主共同の利益の確保の観点から投資家の皆様にお知らせすることが有用であると当社が判断した場合に、適時開示や当社ホームページのお知らせにて掲載させていただく方法に代えさせていただきます。
- [公式ページ](https://www.gnipharma.com/inquiry/)／[保存証拠](evidence/2160/03.json)（取得 2026-10-11T04:01:51.771004+00:00）：IRについてのご質問への回答につきましては、フェアディスクロージャー観点から、個別にご質問をいただいた方への回答という方法ではなく、株主共同の利益の確保の観点から投資家の皆様にお知らせすることが有用であると当社が判断した場合に、適時開示や当社ホームページのお知らせにて掲載させていただく方法に代えさせていただきます。
- [公式ページ](https://www.gnipharma.com/inquiry/)／[保存証拠](evidence/2160/03.json)（取得 2026-10-11T04:01:51.771004+00:00）：回答を掲載するまでにお時間を要する場合があり、「いつ掲載されるか」といった個別回答につきましてもお答えができかねますので、あらかじめご了承くださいませ。
- [公式ページ](https://www.gnipharma.com/inquiry/)／[保存証拠](evidence/2160/03.json)（取得 2026-10-11T04:01:51.771004+00:00）：業績動向などの非公開情報に関するお問い合わせ 株価対策など金融商品取引法 第 166 条「重要事実」に該当する可能性のあるお問い合わせ 株価動向など株式市場の値動に関するお問い合わせ 誹謗、中傷が含まれるお問い合わせ

### 2163 アルトナー

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 職種に「個人投資家様」の選択肢。氏名・メール・件名・内容等が必須。
- 回答は既にWebサイト等に記載されている公開情報の範囲内。非公開業績、重要事実に該当し得る質問、株式市場の値動きへの質問は回答対象外。
- 決算情報の発表予定日までの3週間が沈黙期間で、その間は業績予想の情報提供・問い合わせへのコメントを差し控える。
- 2営業日経過後も返信がない場合は対応不可と理解するよう案内。全問い合わせへの回答保証はない。
- 営業・勧誘、IR支援や採用支援等は対応対象外。

注意・未確認：公開された連絡方法と入力項目のみの確認で、回答実績や回答速度を実測したものではない。 / 個別の業績・株価・流動性・現在の沈黙期間は未検証。

根拠：

- [公式ページ](https://www.artner.co.jp/ir/other/contact-form/)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-2163-form.json)（取得 2026-10-11T03:38:52.097948+00:00）：投資家情報・Webサイトに関するお問い合わせ・資料請求・ご要望は下記のフォームよりお問い合わせください。
- [公式ページ](https://www.artner.co.jp/ir/other/contact-form/)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-2163-form.json)（取得 2026-10-11T03:38:52.097948+00:00）：職種 * 個人投資家様 機関投資家様 アナリスト マスコミ関連 その他
- [公式ページ](https://www.artner.co.jp/ir/other/contact-form/)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-2163-form.json)（取得 2026-10-11T03:38:52.097948+00:00）：2営業日が経過して、当社より返信がない場合、対応いたしかねる状況とご理解ください。
- [公式ページ](https://www.artner.co.jp/ir/other/contact-form/)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-2163-form.json)（取得 2026-10-11T03:38:52.097948+00:00）：当該情報の発表予定日までの3週間を沈黙期間と定めております。

### 2168 パソナグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- ※印のついた項目は必ず入力してください。
- 個人情報の取り扱いについて ※ 同意する

注意・未確認：保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.pasonagroup.co.jp/contact/ir.html)／[保存証拠](evidence/2168/04.json)（取得 2026-10-11T04:01:54.593315+00:00）：IR（株主・投資家向け情報）に関するお問合せ パソナグループのＩＲ活動について、ご質問・ご意見・ご要望等がございましたら、お気軽にお問合せ下さい。
- [公式ページ](https://www.pasonagroup.co.jp/contact/ir.html)／[保存証拠](evidence/2168/04.json)（取得 2026-10-11T04:01:54.593315+00:00）：メールアドレス メールアドレス （確認用） お問合せ内容をご記入ください。 （1000文字以内でご入力ください）
- [公式ページ](https://www.pasonagroup.co.jp/contact/ir.html)／[保存証拠](evidence/2168/04.json)（取得 2026-10-11T04:01:54.593315+00:00）：※印のついた項目は必ず入力してください。
- [公式ページ](https://www.pasonagroup.co.jp/contact/ir.html)／[保存証拠](evidence/2168/04.json)（取得 2026-10-11T04:01:54.593315+00:00）：個人情報の取り扱いについて ※ 同意する

### 2169 ＣＤＳ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.cds-japan.jp/ja/ir_contact/)／[保存証拠](evidence/2169/02.json)（取得 2026-10-11T04:01:51.160350+00:00）：会・エントリーに関するお問い合わせは こちらから JP EN CONTACT IR情報に関するお問い合わせ ホーム IR情報に関するお問い合わせ どうぞお気軽にお問い合わせ下さい フォームからのお問い合わせ 【IR】 以下のお問い合わせフォームに必要事項をご記入頂き、送信確認へとお進みください。 自動返信にて受付完了メールを送信させて頂き、後日担当より改めてご連絡いたします。 ※メールアドレス

### 2170 リンクアンドモチベーション

確認：質問入力欄確認。個人等に制限あり。受付対象に制限。

取得範囲の受付条件：

- 同業者・個人の問い合わせをご遠慮と明示。個人投資家の返信検証用候補から除外する。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.lmi.ne.jp/ir/inquiry/entry.php)／[保存証拠](evidence/2170/05.json)（取得 2026-10-11T04:01:56.131049+00:00）：IRに関するお問い合わせ ｜ Link and Motivation Inc. 株式会社リンクアンドモチベーション 文字サイズ A A お問い合わせ JP EN ニュース 企業情報 支援内容 事例・知見 
- [公式ページ](https://www.lmi.ne.jp/ir/inquiry/entry.php)／[保存証拠](evidence/2170/05.json)（取得 2026-10-11T04:01:56.131049+00:00）：り、送信できない場合がありますので、半角カタカナのご使用はご遠慮いただきますようお願いいたします。 ※印のついている項目は、入力必須です。 お問い合わせ内容 お問い合わせ項目 ※ ※ご同業・個人の方の問い合わせはご遠慮ください。 IRに関するお問い合わせ お問い合わせ内容 ※ ご連絡先 会社名・団体名 ※ 部署名 役職 氏名 ※ 氏名（ふりがな） ※ 郵便番号 ※ （半角数字） 住所 ※ 電話番号 ※ （

### 2173 博展

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.hakuten.co.jp/contact)／[保存証拠](evidence/2173/03.json)（取得 2026-10-11T04:01:54.666324+00:00）：その他のお問い合わせ 各種パートナー企業様 広報・ＩＲ関連

### 2175 エス・エム・エス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.bm-sms.co.jp/contact/ir/)／[保存証拠](evidence/2175/02.json)（取得 2026-10-11T04:01:49.308990+00:00）：IRに関するお問い合わせ｜お問い合わせ｜株式会社エス・エム・エス 企業情報 企業情報TOP 理念 私たちが大切にしていること 私たちが目指していること 事業創造の歴史 トップメッセージ 会社概要 経営陣紹

### 2181 パーソルホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式お問い合わせ一覧の「IRについて」に専用フォームへのリンクを明記。よくいただくご質問も先に確認する。
- 取得本文には個人受付・返信条件の明記はなく、必須項目は取得できない。

注意・未確認：リンク先は公開GETでIR見出しとhoneypotのみを取得。実質問欄・メール欄等を確認できず、JS等による描画と思われる。フォーム本体・個人入力条件・送信の動作は未確認。

根拠：

- [公式ページ](https://www.persol-group.co.jp/inquires/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2181-contact.json)（取得 2026-10-11T03:42:03.361244+00:00）：IRについて 当社IRに関するお問い合わせはこちらから受け付けております。
- [公式ページ](https://www.persol-group.co.jp/inquires/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2181-contact.json)（取得 2026-10-11T03:42:03.361244+00:00）：よくいただくお問い合わせを「 よくいただくご質問 」ページにまとめて掲載しておりますので、そちらも併せてご覧ください。 お問い合わせフォームへ
- [公式ページ](https://contact.persol-group.co.jp/@investor-contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2181-form.json)（取得 2026-10-11T03:42:37.823303+00:00）：IRに関するお問い合わせ

### 2183 リニカル

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IR専用ページのフォーム案内を確認。メール・本文の実入力欄は保存されていない。臨床試験・創薬専用のビジネスフォームをIR受付に流用していない。

根拠：

- [公式ページ](https://www.linical.com/ja/investors-contact)／[保存証拠](evidence/2183/02.json)（取得 2026-10-11T04:01:50.713996+00:00）：信 説明会資料 有価証券報告書 株主・株式情報 株主総会 株式情報 配当状況 IRニュース一覧 IRカレンダー 株価情報 よくあるご質問 免責事項 投資家情報に関するお問い合わせ 投資家情報についてのお問い合わせは以下のフォームに入力してください。 Global グローバル規模でワンストップ リニカルは日本を中心にアジア、欧州、米国など世界各国でサービス提供しています。 リニカルとして約20か国/地域、パートナーを通じてサー

### 2185 シイエム・シイ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.cmc.co.jp/contact/)／[保存証拠](evidence/2185/03.json)（取得 2026-10-11T04:01:52.200659+00:00）：い合わせの種類をお選びください 当社が提供しているサービスに関するお問い合わせ 医療・医薬品マーケティングに関するお問い合わせ 不動産マーケティング・販売促進に関するお問い合わせ IRに関するお問い合わせ その他のお問い合わせ 内容 ご提出いただく個人情報は、お問い合わせ対応のために利用し、それ以外の目的には利用しません。 上記内容にご同意の上、お問い合わせください。 個人情報の取

### 2186 ソーバル

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 貴社名を必須表示。IR選択時に個人が入力できる条件分岐は未確認。
- 決算説明への質問・意見は次回説明会の参考にする受付。趣旨外・詳細調査・重複・権利侵害等の場合は回答を控える旨を明示。個別返信の保証とは扱わない。
- 本文は2000文字以内。株主番号・保有期間等の照会は証券会社を案内。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 保存HTMLには商談・採用・IR等の条件付き入力項目が混在する。IR選択時の必須項目をJavaScript実行後に再確認する必要がある。商談向け「ご返事は必ず」の文言をIR返信保証に流用していない。

根拠：

- [公式ページ](https://www.sobal.co.jp/contact/ir/)／[保存証拠](evidence/2186/02.json)（取得 2026-10-11T04:01:50.416335+00:00）：詳細は下記お問合せ内容にご記入ください） ※ ご留意事項：ご返事は必ずいたします。ただし、返答までに数日かかることがございます。 ご連絡先 お問合せの種類 必須 選択してください 広報・ＩＲに関するお問合せ 決算説明に関するご意見・ご質問・ご感想 姓 必須 名 必須 メールアドレス 必須 メールアドレス（確認） 必須 貴社名 必須 貴社ウェブサイトURL ご住所 電話番号 お問合せ内
- [公式ページ](https://www.sobal.co.jp/contact/ir/)／[保存証拠](evidence/2186/02.json)（取得 2026-10-11T04:01:50.416335+00:00）：お問合せの種類 必須 選択してください 広報・ＩＲに関するお問合せ 決算説明に関するご意見・ご質問・ご感想 姓 必須 名 必須 メールアドレス 必須 メールアドレス（確認） 必須 貴社名 必須 貴社ウェブサイトURL ご住所 電話番号 お問合せ内容 必須 2,000文字以内でご入力ください 株主様の株式保有期間や株主番号等の詳細につきましては、個人情報保護および厳正な管
- [公式ページ](https://www.sobal.co.jp/contact/ir/)／[保存証拠](evidence/2186/02.json)（取得 2026-10-11T04:01:50.416335+00:00）：認 送信完了 お問合せ内容の入力 決算説明に関するご意見・ご質問・ご感想について 決算説明に関するご意見・ご質問・ご感想などは、以下のフォームよりお寄せください。いただいた内容は、次回の決算説明会の参考とさせていただきます。 ご質問については、次のいずれかに該当する場合、お取り扱いできないこと、または回答を差し控えさせていただくことがありますので、あらかじめご了承ください。 決算説明会の趣旨にそぐわ
- [公式ページ](https://www.sobal.co.jp/contact/ir/)／[保存証拠](evidence/2186/02.json)（取得 2026-10-11T04:01:50.416335+00:00）：に関するご意見・ご質問・ご感想 姓 必須 名 必須 メールアドレス 必須 メールアドレス（確認） 必須 貴社名 必須 貴社ウェブサイトURL ご住所 電話番号 お問合せ内容 必須 2,000文字以内でご入力ください 株主様の株式保有期間や株主番号等の詳細につきましては、個人情報保護および厳正な管理の観点から、当社でお答えすることができかねます。誠に恐れ入りますが、ご不明な点はお取引のある証券

### 218A Ｌｉｂｅｒａｗａｒｅ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公式IR用途の案内と対象URLのみを確認。保存範囲に実入力欄がなく、フォーム機能の確認済み窓口とは数えない。 / 実際の返信・送信機能・未記載の個人受付条件は確認していない。窓口確認と投資適性は別の判断。

根拠：

- [公式ページ](https://liberaware.co.jp/ir/faq/)／[保存証拠](evidence/218A/06.json)（取得 2026-10-11T04:01:53.967810+00:00）：IRお問い合わせ
- [公式ページ](https://liberaware.co.jp/contact/)／[保存証拠](evidence/218A/03.json)（取得 2026-10-11T04:01:51.382481+00:00）：点検・産業用ドローンIBISに関する お問い合わせ、IR、採用に関するお問い合わせなど気軽にご相談ください。

### 2193 クックパッド

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://info.cookpad.com/contact/ir)／[保存証拠](evidence/2193/03.json)（取得 2026-10-11T04:01:50.495464+00:00）：IRに関するお問い合わせ \| クックパッド株式会社 IRに関するお問い合わせ お名前 ※ メールアドレス ※ 会社名 電話番号(半角数字) お問い合わせ内容 ※ ご入力いただいた個人情報は、 サービスプラ

### 2195 アミタホールディングス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@amita-net.co.jp`。

注意・未確認：公開 GET の保存本文と非 hidden 入力欄を点検。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.amita-hd.co.jp/contact/index.html)／[保存証拠](evidence/2195/04.json)（取得 2026-10-11T04:01:53.476788+00:00）：グス株式会社 広報担当 [電話] 075-277-0795 [FAX] 075-255-4527 [メール] press@amita-net.co.jp 広報お問い合わせフォーム IRお問い合わせ窓口 IRに関するお問い合わせは下記までご連絡ください。 アミタホールディングス株式会社 IR担当 [メール] ir@amita-net.co.jp IRお問い合わせフォーム 採用お問

### 219A Ｈｅａｒｔｓｅｅｄ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@heartseed.jp`。

取得範囲の受付条件：

- 戦略ファイナンス・IR室の問い合わせメール ir@heartseed.jp を公開。返信に時間がかかる場合がある。
- 個人の受付条件・返信期限は今回の保存窓口ページでは明示されていない。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://heartseed.jp/ir/Inquiries/index.html)／[保存証拠](evidence/219A/03.json)（取得 2026-10-11T04:01:52.737050+00:00）：IRに関するお問い合わせ先 戦略ファイナンス・IR室 IR担当者 メール ir@heartseed.jp
- [公式ページ](https://heartseed.jp/ir/Inquiries/index.html)／[保存証拠](evidence/219A/03.json)（取得 2026-10-11T04:01:52.737050+00:00）：お問い合わせの内容などにより、お返事に日時を頂戴する場合もございます

### 2204 中村屋

確認：案内・リンクのみ。個人等に制限あり。受付対象に制限。

取得範囲の受付条件：

- 当お問い合わせ先は企業情報（CSR・IR）に関するメディア関係の方からのお問い合わせ専用窓口です。
- 営業上の売り込み、商品やサービス等のご紹介、ご提案等はお控えください。

注意・未確認：公式のIR用途案内とリンク先URLのみを確認。対象フォーム本体の入力欄・作動・受付条件を未取得のため確認済みの窓口とは数えない。 / 保存された公開GET資料のオフライン監査。実際の返信、現在の送信機能、未記載の個人受付条件は確認していない。

根拠：

- [公式ページ](https://www.nakamuraya.co.jp/inquiry/contact.html)／[保存証拠](evidence/2204/05.json)（取得 2026-10-11T04:01:55.230144+00:00）：企業情報（CSR・IR等）に関するメディア関係の方からのお問い合わせ CSR・IR担当
- [公式ページ](https://www.nakamuraya.co.jp/inquiry/contact.html)／[保存証拠](evidence/2204/05.json)（取得 2026-10-11T04:01:55.230144+00:00）：当お問い合わせ先は企業情報（CSR・IR）に関するメディア関係の方からのお問い合わせ専用窓口です。
- [公式ページ](https://www.nakamuraya.co.jp/inquiry/contact.html)／[保存証拠](evidence/2204/05.json)（取得 2026-10-11T04:01:55.230144+00:00）：営業上の売り込み、商品やサービス等のご紹介、ご提案等はお控えください。

### 220A Ｆａｂｅｒ　Ｃｏｍｐａｎｙ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR専用フォーム。サービス、営業、取材は別窓口を案内。
- 非公開情報、重要事実、誹謗中傷、市場の値動き、営業・勧誘には回答しない。返信の転載・二次利用は遠慮する案内。
- 継続質問も改めてフォームから行う。確認画面なしで送信される。会社名・組織名欄の個人記入方法は未確認。

注意・未確認：公開ページの保存済みGET証拠による確認。フォーム入力・送信、メール到達、実返信は未検証。 / 窓口の確認は投資適性、業績・株価の評価や個人への回答保証を示さない。

根拠：

- [公式ページ](https://www.fabercompany.co.jp/ir/contact/)／[保存証拠](evidence/220A/02.json)（取得 2026-10-11T04:01:53.818790+00:00）：IRに関するお問い合わせ / IR情報 - Faber Company
- [公式ページ](https://www.fabercompany.co.jp/ir/contact/)／[保存証拠](evidence/220A/02.json)（取得 2026-10-11T04:01:53.818790+00:00）：非公開情報に関するご質問 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問 誹謗中傷に該当するメッセージ 株式市場の値動きに関するご質問 営業や勧誘のお問い合わせ
- [公式ページ](https://www.fabercompany.co.jp/ir/contact/)／[保存証拠](evidence/220A/02.json)（取得 2026-10-11T04:01:53.818790+00:00）：当社からのEメールは、皆様のお問い合わせにお答えするためのものです。一部または全部の転載、二次利用はご遠慮ください。
- [公式ページ](https://www.fabercompany.co.jp/ir/contact/)／[保存証拠](evidence/220A/02.json)（取得 2026-10-11T04:01:53.818790+00:00）：返信メールに対し、引き続きお問い合わせいただく場合も、恐れ入りますが下記フォームより改めてお問い合わせください。
- [公式ページ](https://www.fabercompany.co.jp/ir/contact/)／[保存証拠](evidence/220A/02.json)（取得 2026-10-11T04:01:53.818790+00:00）：※ 確認画面なしで送信されます。送信前に間違いがないかご確認ください。

### 2216 カンロ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://support.kanro.jp/hc/ja/requests/new?ticket_form_id=360008237675)／[保存証拠](evidence/2216/20261011T044640967120Z/04.json)（取得 2026-10-11T04:46:46.566408+00:00）：してください - デフォルトのチケットフォーム オンラインショップに関するお問い合わせ 商品に関するお問い合わせ 販売店のお問い合わせ 不都合品のお問い合わせ 会社・IR活動に関するお問い合わせ キャンペーンのお問い合わせ メールアドレス 性別 (オプション) 選択してください 年代 選択してください 確認用メールアドレス ※半角英数字 電話番号 ※半角数字・ハイフンなし お問い合わせ内容 
- [公式ページ](https://kanro.jp/pages/contact/)／[保存証拠](evidence/2216/20261011T044640967120Z/03.json)（取得 2026-10-11T04:46:44.452724+00:00）：ご質問 ホームページからのお問い合わせ オンラインショップに 関するお問い合わせ 商品に関する お問い合わせ 販売店の お問い合わせ 不都合品の お問い合わせ 会社・IR活動に 関するお問い合わせ キャンペーンの お問い合わせ 取り扱い企業の検索はこちら 販売店検索 お客様の声を社内の各部署に共有し、商品やサービスの改善・改良に活かす活動を推進しています。商品やサービスへのご意見があれば、ぜひ

### 2222 寿スピリッツ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 本文は最大2000文字。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kotobukispirits.co.jp/form/ja/agree_02/inquiry_02.html)／[保存証拠](evidence/2222/20261011T044647920734Z/05.json)（取得 2026-10-11T04:46:56.400825+00:00）：入力フォーム \| IRに関するお問い合わせ \| 寿スピリッツ株式会社 \| form お問い合わせ お問い合わせ Step1 入力 Step2 確認 Step3 完了 お問い合わせの内容によっては、返信に時間がかかる場合や回答を差し控えさせてい
- [公式ページ](https://www.kotobukispirits.co.jp/form/ja/agree_02/inquiry_02.html)／[保存証拠](evidence/2222/20261011T044647920734Z/05.json)（取得 2026-10-11T04:46:56.400825+00:00）：ください メールアドレス（確認用） 必須 ※半角英数で入力してください お電話番号 必須 ※ハイフンなしの半角数字で入力してください お問い合わせ内容 必須 ※最大2000文字で入力してください Copyright © KOTOBUKI SPIRITS Co.,LTD. All Rights Reserved.

### 2229 カルビー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://faq.calbee.co.jp/form/ir.html)／[保存証拠](evidence/2229/20261011T044650291877Z/04.json)（取得 2026-10-11T04:46:58.635959+00:00）：お問い合わせの種類 / Inquiry Type 必須 / Required 選択してください / Select 投資家、IR関連の問い合わせ / Investor, About IR 個人株主、SR関連の問い合わせ / Stockholder, About SR タイトル / Subject 必須 / Required 問い合わせ内容 /
- [公式ページ](https://faq.calbee.co.jp/form/ir.html)／[保存証拠](evidence/2229/20261011T044650291877Z/04.json)（取得 2026-10-11T04:46:58.635959+00:00）：頂戴する場合やお答えしかねる場合もございますので、あらかじめご了承ください。 ・弊社からお客様へのご返事は、お客様個人宛てにお送りするものです。一部または全部を転載、二次利用することはご遠慮ください。 We accept inquiries from shareholders and investors our online below. For inquiries about our prod
- [公式ページ](https://www.calbee.co.jp/ir/)／[保存証拠](evidence/2229/20261011T044650291877Z/03.json)（取得 2026-10-11T04:46:55.322690+00:00）：決算説明会資料 有価証券報告書 統合報告書 Human Capital Report 「旬」株主様へのご報告 ESGデータ IRカレンダー よくいただくご質問 IRお問い合わせ （別ウインドウで開く） IRポリシー 電子公告 企業情報 サステナビリティ 研究開発 Calbeeホーム 商品 商品情報 アレルゲン検索 ブランドサイト一覧 世界のカルビー商品 キャンペーン・動画 キャンペーン・ピックアッ

### 2264 森永乳業

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`irgroup@morinagamilk.co.jp`。

取得範囲の受付条件：

- アンケート・営業目的の問い合わせは受付対象外。内容により無回答・返信遅延がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.morinagamilk.co.jp/ir/contact/)／[保存証拠](evidence/2264/20261011T044655053238Z/02.json)（取得 2026-10-11T04:46:57.129869+00:00）：まへ 業績情報 株式情報 IR資料室 IRカレンダー IRに関するお問い合わせ 株価情報 東証P：2264 チャート IRに関するお問い合わせ お問い合わせ先 IRグループ お電話の場合 03-6281-4683 受付時間：9：30～16：30 (土日、祝日、ゴールデンウィーク、年末年始を除く） E-mail irgroup@morinagamilk.co.jp お問い
- [公式ページ](https://www.morinagamilk.co.jp/ir/contact/)／[保存証拠](evidence/2264/20261011T044655053238Z/02.json)（取得 2026-10-11T04:46:57.129869+00:00）：l irgroup@morinagamilk.co.jp お問い合わせの内容によっては返信に時間がかかる場合や、回答を差し控えさせていただく場合もございます。 各種アンケート、営業目的のお問い合わせ等につきましては、お受けできませんのであらかじめご了承ください。 関連コンテンツ IR情報 MENU IR情報TOP IRニュース 経営情報 個人投資家の皆さまへ 業績情報 株式情報 IR資料室 IRカレンダー IRに関するお問い合わ
- [公式ページ](https://www.morinagamilk.co.jp/ir/contact/)／[保存証拠](evidence/2264/20261011T044655053238Z/02.json)（取得 2026-10-11T04:46:57.129869+00:00）：TOP IRニュース 経営情報 個人投資家の皆さまへ 業績情報 株式情報 IR資料室 IRカレンダー IRに関するお問い合わせ 株価情報 東証P：2264 チャート IRに関するお問い合わせ お問い合わせ先 IRグループ お電話の場合 03-6281-4683 受付時間：9：30～16：30 (土日、祝日、ゴールデンウィーク、年末年始を除く） E-mail irgroup@morinagamilk.co.jp お問い合わせの内容によっては返信に時間がかかる場合や、回答を差し控えさせていただく場合もございます。 各種アンケート、営業目的のお問い合わせ等につきましては、お受けできませんのであらかじめご了承くだ
- [公式ページ](https://www.morinagamilk.co.jp/)／[保存証拠](evidence/2264/20261011T044655053238Z/01.json)（取得 2026-10-11T04:46:56.363759+00:00）：員紹介 事業所一覧 関係会社一覧 採用情報 閉じる IR 一覧へ IRニュース 経営情報 個人投資家の皆さまへ 業績情報 株式情報 IR資料室 IRカレンダー IRに関するお問い合わせ 閉じる 研究開発 一覧へ 私たちのミッション イノベーションストーリー 研究者インタビュー 研究開発領域 研究開発ヒストリー 論文・学会発表 閉じる お客さま相談室 一覧へ お電話でのお問い合わせ 

### 2281 プリマハム

確認：案内・リンクのみ。個人条件の明示未確認。未確認。

取得範囲の受付条件：

- IRフォームの一時閉鎖を明示。受付再開は保存証拠から確認できない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IRページがフォーム不具合・一時閉鎖を明示し、電話での連絡を案内。

根拠：

- [公式ページ](https://www.primaham.co.jp/ir/stock/inquiry/)／[保存証拠](evidence/2281/20261011T044659823908Z/03.json)（取得 2026-10-11T04:47:02.433174+00:00）：ム株式会社 総務・広報部 お問い合わせ先 〒140-8529 東京都品川区東品川4-12-2 プリマハム株式会社 総務・広報部 電話：03-6386-1800 お問い合わせフォームはこちら 一時的に閉鎖中です。ご不便をおかけし申し訳ございません。 株式・株主情報 株式基本情報 株式の状況 配当実績 IRカレンダー・イベント 単元未満株式の買取・買増請求制度 特別口座をご利用の株主様への
- [公式ページ](https://www.primaham.co.jp/ir/stock/inquiry/)／[保存証拠](evidence/2281/20261011T044659823908Z/03.json)（取得 2026-10-11T04:47:02.433174+00:00）：い合わせ先 〒140-8529 東京都品川区東品川4-12-2 プリマハム株式会社 総務・広報部 電話：03-6386-1800 お問い合わせフォームはこちら 一時的に閉鎖中です。ご不便をおかけし申し訳ございません。 株式・株主情報 株式基本情報 株式の状況 配当実績 IRカレンダー・イベント 単元未満株式の買取・買増請求制度 特別口座をご利用の株主様へのご案内 電子公告 格付
- [公式ページ](https://www.primaham.co.jp/ir/)／[保存証拠](evidence/2281/20261011T044659823908Z/02.json)（取得 2026-10-11T04:47:01.202853+00:00）：式基本情報 株式の状況 配当実績 IRカレンダー・イベント 株主総会 単元未満株式の買取・買増請求制度 特別口座をご利用の株主様へのご案内 電子公告 格付情報 IRに関するお問い合わせ EN 総合トップ 企業情報 CLOSE IR・投資家情報 Investor Relations 統合報告書 株主優待制度について Our Mission おいしさと感動で、 食文化と社会に貢献 トッ

### 2282 日本ハム

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IR案内から外部フォームへのリンクは確認したが、対応するメール・本文の実入力欄は保存証拠で未確認。

根拠：

- [公式ページ](https://www.nipponham.co.jp/corporate/ir/inquiry/)／[保存証拠](evidence/2282/20261011T044701760385Z/03.json)（取得 2026-10-11T04:47:04.410634+00:00）：ンダー 個人投資家説明会 株主総会 株主様向け情報 よくあるご質問 IRに関するお問い合わせ 電子公告 動画配信 免責事項 ニュース IRに関するお問い合わせ IRに関するお問い合わせは以下のページの入力フォームよりお願いします。 また、 よくあるご質問についてはこちら に掲載しています。 お問い合わせフォームはこちら ホーム IR情報 IRに関するお問い合わせ ページ上部へ ストーリー 企業情報 研究・開発 品質への取り組み
- [公式ページ](https://www.nipponham.co.jp/corporate/)／[保存証拠](evidence/2282/20261011T044701760385Z/02.json)（取得 2026-10-11T04:47:03.770547+00:00）：R情報 IR情報 トップ トップメッセージ 個人投資家の皆様へ 経営方針 財務・業績ハイライト 株式・株主情報 IRライブラリー IRイベント よくあるご質問 IRに関するお問い合わせ 電子公告 動画配信 免責事項 IRニュース一覧 企業・IR情報 商品・レシピ情報 採用情報 お問い合わせ 企業・IR情報 商品・レシピ情報 たんぱく質を、 もっと自由に。 Nipponham Gro

### 228A オプロ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページはフォーム受付を明示するが、保存本文には実メール・本文入力欄がない。動的フォームの表示後条件は未確認。

根拠：

- [公式ページ](https://corp.opro.net/contact/ir.html)／[保存証拠](evidence/228A/20261011T044707822253Z/02.json)（取得 2026-10-11T04:47:10.961727+00:00）：くあるご質問 電子公告 免責事項 採用情報 お問い合わせ ホーム お問い合わせ IRに関するお問い合わせ IRに関する お問い合わせ フォームでのお問い合わせ 下記のフォームに必要事項をご入力の上、送信してください。後日、担当者より折り返しご連絡させていただきます。 会社情報 会社情報 会社情報 TOP 経営理念 トップメッセージ 会社概要 事業内容 事業内容 事業内容 TOP データオプティ
- [公式ページ](https://corp.opro.net/)／[保存証拠](evidence/228A/20261011T044707822253Z/01.json)（取得 2026-10-11T04:47:10.279898+00:00）：ポリシー 財務ハイライト 財務ハイライト IRライブラリー 決算短信 決算説明資料 有価証券報告書 その他IR資料 株式について 株式情報 株主総会 株価情報 IRお問い合わせ IRカレンダー よくあるご質問 電子公告 免責事項 採用情報 お問い合わせ オプロは帳票を主体とした あらゆる分野で業務の流れを変革する会社です。 Scroll down 2026年10月06日 お

### 2291 福留ハム

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.fukutome.com/contact/company/)／[保存証拠](evidence/2291/20261011T044707946642Z/04.json)（取得 2026-10-11T04:47:13.185371+00:00）：株主個人情報保護方針 トップ > お問い合わせ > お問い合わせ – 会社情報・IR情報について Contact お問い合わせ - 会社情報・IR情報について 会社情報・IR情報に関するお問い合わせ 福留ハムの会社情報・IR情報に関するお問い合わせ等は、こちらのフォームよりお願い致します。 下記のお問い合わせフォームにご記入いただき、ご送信ください。送信完了後、受付け確認の自動応答メールをお送り
- [公式ページ](https://www.fukutome.com/contact/)／[保存証拠](evidence/2291/20261011T044707946642Z/03.json)（取得 2026-10-11T04:47:11.584297+00:00）：い。 福留ハムの製品に関する お問い合わせ・お申し出はこちら お客様相談室へ 福留ハムの採用情報に関する お問い合わせ・ご意見はこちら お問い合わせフォームへ 福留ハムの会社情報・IR情報に関する お問い合わせ・ご意見はこちら お問い合わせフォームへ その他の お問い合わせ・ご意見はこちら お問い合わせフォームへ お問い合わせの前にこちらもご確認ください。 よくある質問 PAGE TOP 福留ハム株式会社 〒731-0213 広島市安佐北区三入南

### 2296 伊藤ハム米久ホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページは取得済みだが、保存された非 hidden controls は同意ラジオと進むボタンだけ。送信・同意操作は行っておらず、次画面の入力条件は未確認。

根拠：

- [公式ページ](https://www.itoham-yonekyu-holdings.com/ir/inpuiry.html)／[保存証拠](evidence/2296/20261011T044710427959Z/02.json)（取得 2026-10-11T04:47:17.756153+00:00）：IRに関するお問い合わせフォーム \| IR情報 \| 伊藤ハム米久ホールディングス 本文へ 【全】ヘッダーリンク お問い合わせ 採用情報 English 伊藤ハム米久HD ホーム 会社情報 会社情報(Top) 目指す企業像 会社概要 
- [公式ページ](https://www.itoham-yonekyu-holdings.com/)／[保存証拠](evidence/2296/20261011T044710427959Z/01.json)（取得 2026-10-11T04:47:14.669204+00:00）：扱規則 格付情報 株価情報 財務・業績ハイライト 決算サマリー 業績ハイライト 主な財務指標 チャートジェネレーター 配当情報 IRスケジュール IRニュース IRに関するお問い合わせフォーム サステナビリティ サステナビリティ(Top) マテリアリティ 環境 気候変動への取り組み（TCFD提言への対応） 生物多様性への取り組み（TNFD提言への対応） 環境マネジメントと外部認証取得状況 

### 2303 ドーン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 団体名・会社名を必須表示。個人の記入方法は未確認。法人限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.dawn-corp.co.jp/contact/inquiry02form/)／[保存証拠](evidence/2303/20261011T044714678840Z/04.json)（取得 2026-10-11T04:47:21.079387+00:00）：上げることを利用目的とし、弊社にて適切に管理させていただきます。 「個人情報取扱い同意書」 にご同意いただいた上で、お問い合わせください。 連絡先 種別 必須 IRに関するお問い合わせ プレスリリースに関するお問い合わせ 求人採用に関するお問い合わせ その他のお問い合わせ 氏名 必須 フリガナ（カタカナ） 必須 団体名・会社名 必須 部署名 郵便番号 必須 〒 現住所 必須 北海道
- [公式ページ](https://www.dawn-corp.co.jp/contact/inquiry02form/)／[保存証拠](evidence/2303/20261011T044714678840Z/04.json)（取得 2026-10-11T04:47:21.079387+00:00）：必須 IRに関するお問い合わせ プレスリリースに関するお問い合わせ 求人採用に関するお問い合わせ その他のお問い合わせ 氏名 必須 フリガナ（カタカナ） 必須 団体名・会社名 必須 部署名 郵便番号 必須 〒 現住所 必須 北海道 青森県 秋田県 岩手県 山形県 宮城県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 山梨県 長野県 新潟県 富山県 石川県 福
- [公式ページ](https://www.dawn-corp.co.jp/contact/index-2/)／[保存証拠](evidence/2303/20261011T044714678840Z/03.json)（取得 2026-10-11T04:47:19.079365+00:00）：らくしても弊社からのお返事が届かない場合は、大変お手数ですが再度その旨をお問い合わせくださいますよう、お願いいたします。 製品・サービスに 関するお問い合わせ IR・プレスリリース 求人採用に関するお問い合わせ スタッフ募集に応募される方は、採用情報をご参照ください TOP ©2018-2026 Dawn corp. 会社情報 トップメッセージ 会社概要・沿革 主要取引先と加盟団体 アクセス 製品・サービス

### 2311 エプコ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.epco.co.jp/contact)／[保存証拠](evidence/2311/20261011T044718103207Z/03.json)（取得 2026-10-11T04:47:25.713403+00:00）：お問い合わせ内容 お問合わせ内容 必須 選択してください サービスについて 採用について IRについて 個人情報保護関連について 取材のお申込み その他 ご質問 必須 お客様情報 お名前 必須 姓 名 フリガナ 必須 セイ メイ メールアドレス 必須 電話番号 必須 会社名 部署名 郵便番号 ご住所 

### 2315 ＣＡＩＣＡ　ＤＩＧＩＴＡＬ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 本文は全角1000文字まで。
- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.caica.jp/ir-inquiry/)／[保存証拠](evidence/2315/20261011T044719000476Z/06.json)（取得 2026-10-11T04:47:26.241326+00:00）：名・役職 年齢 ※必須 -- 選択してください -- 10代 20代 30代 40代 50代 60代以上 属性 ※必須 -- 選択してください -- 当社株主 個人投資家 機関投資家 その他企業 その他個人 お問合わせ内容（全角1000文字まで） ※必須 同意確認 個人情報の取り扱い について同意する このフィールドは空のままにしてください。
- [公式ページ](https://www.caica.jp/ir-inquiry/)／[保存証拠](evidence/2315/20261011T044719000476Z/06.json)（取得 2026-10-11T04:47:26.241326+00:00）：郡町村・番地 電話番号 建物名 会社 / 団体名 部署名・役職 年齢 ※必須 -- 選択してください -- 10代 20代 30代 40代 50代 60代以上 属性 ※必須 -- 選択してください -- 当社株主 個人投資家 機関投資家 その他企業 その他個人 お問合わせ内容（全角1000文字まで） ※必須 同意確認 個人情報の取り扱い について同意する このフィールドは空のままにしてください。 PICKUP スペシャリ
- [公式ページ](https://www.caica.jp/ir-inquiry/)／[保存証拠](evidence/2315/20261011T044719000476Z/06.json)（取得 2026-10-11T04:47:26.241326+00:00）：0代 30代 40代 50代 60代以上 属性 ※必須 -- 選択してください -- 当社株主 個人投資家 機関投資家 その他企業 その他個人 お問合わせ内容（全角1000文字まで） ※必須 同意確認 個人情報の取り扱い について同意する このフィールドは空のままにしてください。 PICKUP スペシャリスト採用（ アジャイル開発 ） CAICA DIGITAL グループでは現
- [公式ページ](https://www.caica.jp/ir-inquiry/)／[保存証拠](evidence/2315/20261011T044719000476Z/06.json)（取得 2026-10-11T04:47:26.241326+00:00）：については、当社プライバシーポリシーに基づき、お問合わせに対応させていただく目的以外に使用することはございません。また、当社からお送りした内容の一部または全部を転載・二次利用することはご遠慮ください。 個人情報の入力 お名前 ※必須 お名前（フリガナ） ※必須 Email ※必須 Email（確認） ※必須 郵便番号 都道府県 -- 選択してください -- 北海道 青森県 岩手県 宮城県 秋田県
- [公式ページ](https://www.caica.jp/contact/)／[保存証拠](evidence/2315/20261011T044719000476Z/05.json)（取得 2026-10-11T04:47:24.990501+00:00）： その他 お問合わせ 個人情報保護方針 個人情報の取り扱い 保有個人データ又は第三者提供記録に関する周知 情報セキュリティ保護方針 ENGLISH お問合わせ IRに関するお問合わせ 個人情報に関するお問合わせ 中途採用へのエントリー PICKUP スペシャリスト採用（ アジャイル開発 ） CAICA DIGITAL グループでは現在、専門知識・スキルを有しており、即戦力として活

### 2317 システナ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答要求がない、公開済み、趣旨不明等、内容による無回答条件を案内。全ての個別問い合わせを拒否する方針ではない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.systena.co.jp/contact/ir/)／[保存証拠](evidence/2317/20261011T044722477168Z/02.json)（取得 2026-10-11T04:47:25.409557+00:00）：IRに関するお問い合わせ ｜株式会社システナ CONTACT IR｜お問い合わせ お問い合わせ内容 確認画面 お問い合わせ 完了 1. 入力画面 2. 確認 3. 完了 必須項目につきましては必ずご入力ください。 ※ 以下のフォーム各項目には機種依存文字を使用せず入力してください
- [公式ページ](https://www.systena.co.jp/contact/ir/)／[保存証拠](evidence/2317/20261011T044722477168Z/02.json)（取得 2026-10-11T04:47:25.409557+00:00）：信いたしました。 お手数ですが、併せて完了メールもご確認お願いいたします。 内容によっては、回答または返信に時間を要する場合があることをご了承ください。 また、以下の場合返信を行わないことがあります。 当社からの回答や返信を要求していない場合。 当社ホームページに回答が掲載されている場合。 お問い合わせの内容や意図が不明な場合。 回答・返信することにより、第三者に不利益が及ぶ場合、もしくはその恐
- [公式ページ](https://www.systena.co.jp/)／[保存証拠](evidence/2317/20261011T044722477168Z/01.json)（取得 2026-10-11T04:47:23.642307+00:00）：ナルサービス ソリューションサービス 実績紹介 IR情報 IR情報 IRニュース 経営方針/戦略 IR資料室 業績ハイライト 株式関連情報 個人投資家の皆様へ IRお問い合わせ 採用情報 採用情報 新卒採用 イベント＆インターンシップ キャリア採用 ビジネスパートナー募集 お問い合わせ 会社情報 会社情報 経営理念・メッセージ 会社概要 システナのあゆみ グループ会社 サス

### 2325 ＮＪＳ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用同意ページの次画面への公式リンクのみ。対応する実メール・本文入力欄は保存されていない。

根拠：

- [公式ページ](https://www.njs.co.jp/form/ja/agree_03.html)／[保存証拠](evidence/2325/20261011T044726328746Z/04.json)（取得 2026-10-11T04:47:41.450399+00:00）：IRに関するお問い合わせ \| 株式会社NJS \| form IRに関するお問い合わせ IRに関するお問い合わせ お問い合わせをお送りいただく前に、下記の注意事項をお読みいただき、ご理解の上、お問い合わせ内容の入力にお進みくだ
- [公式ページ](https://www.njs.co.jp/ja/investors/ir-contact.html)／[保存証拠](evidence/2325/20261011T044726328746Z/03.json)（取得 2026-10-11T04:47:37.125561+00:00）：IRに関するお問い合わせ先 \| 株主・投資家情報 \| 株式会社NJS メインコンテンツへスキップする IRに関するお問い合わせ先 Investors Service サブ-ナビゲーション News Services Comp

### 2327 日鉄ソリューションズ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 会社名・所属部署は必須だが、個人の場合は「個人」と記入する明示案内がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nssol.nipponsteel.com/cgi-bin/form/inquiry.pl)／[保存証拠](evidence/2327/20261011T044726966823Z/03.json)（取得 2026-10-11T04:47:46.305443+00:00）：Japan お問い合わせ種別 【必須】 --- お選びください --- ソリューション・サービスについて 業務委託・派遣等の協業について 広報について IRについて 採用について 個人情報について その他について お問い合わせタイトル 【必須】 例）PPNソリューションについて お問い合わせ内容 【必須】 お名前 【必須】 例）日鉄 例）太郎 お名前(フリガナ)
- [公式ページ](https://www.nssol.nipponsteel.com/cgi-bin/form/inquiry.pl)／[保存証拠](evidence/2327/20261011T044726966823Z/03.json)（取得 2026-10-11T04:47:46.305443+00:00）：xample.com ※ 半角英数字でご入力ください。 メールアドレス（確認用） 【必須】 @ 会社名・団体名 【必須】 例）日鉄ソリューションズ株式会社 ※ 個人の場合は「個人」とご記入ください。 所属部署名 【必須】 例）営業本部 ※ 個人の場合は「個人」とご記入ください。 役職 例）部長 ※ 個人の場合は「個人」とご記入ください。 郵便番号 例）105 例）6417 ※ 半角数字でご入力く
- [公式ページ](https://www.nssol.nipponsteel.com/cgi-bin/form/inquiry.pl)／[保存証拠](evidence/2327/20261011T044726966823Z/03.json)（取得 2026-10-11T04:47:46.305443+00:00）：でご記入ください。 メールアドレス 【必須】 例）：mail@example.com ※ 半角英数字でご入力ください。 メールアドレス（確認用） 【必須】 @ 会社名・団体名 【必須】 例）日鉄ソリューションズ株式会社 ※ 個人の場合は「個人」とご記入ください。 所属部署名 【必須】 例）営業本部 ※ 個人の場合は「個人」とご記入ください。 役職 例）部長 ※ 個人の場合は「個人」

### 2329 東北新社

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.tfc.co.jp/contact/)／[保存証拠](evidence/2329/20261011T044727575535Z/02.json)（取得 2026-10-11T04:47:30.337188+00:00）：お問い合わせ種別 必須 選択してください 新規お取引やお見積りに関するお問い合わせ 二次利用に関するお問い合わせ IRに関するお問い合わせ 採用に関するお問い合わせ そのほか当社へのご意見・ご要望など 会社名 部署名/役職名 お名前 必須 お名前（フリガナ） 必須 メールアドレス 必須 電話番号 必須 お問い合わせ内容 必須 プライバシ
- [公式ページ](https://www.tfc.co.jp/)／[保存証拠](evidence/2329/20261011T044727575535Z/01.json)（取得 2026-10-11T04:47:28.822658+00:00）：のリスク 株主・株式関連 株式基本情報 株主還元・配当 株価状況 株主総会 定款 電子公告 業績ハイライト 個人投資家の皆さまへ IRカレンダー よくある質問 IRに関するお問い合わせ IRメール配信登録 免責事項 2026年度 決算短信／有価証券報告書等／決算説明資料 1Q 2Q 3Q 4Q 決算短信 - - - 有価証券報告書等 - - - - 決算説明資料 - - - - 過

### 2334 イオレ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.eole.co.jp/ir/inquiry/)／[保存証拠](evidence/2334/20261011T044730972010Z/02.json)（取得 2026-10-11T04:47:32.622192+00:00）：、お電話番号・ご住所は、よくご確認してくださいますようお願いします。 ※ は入力必須項目です 名前 ※ 名前(カナ) ※ 会社名 メールアドレス ※ 電話番号 お問い合わせ内容 ※ 利用規約 、 個人情報の取り扱いについて に同意する 資料請求 商品・出稿に関するお問い合わせ IRに関するお問い合わせ その他ご意見・お問い合わせ 事業紹介 pinpoint JOBOLE HR 
- [公式ページ](https://www.eole.co.jp/)／[保存証拠](evidence/2334/20261011T044730972010Z/01.json)（取得 2026-10-11T04:47:31.987610+00:00）：その他IR資料 適時開示情報 動画アーカイブ 株式情報 株式の状況 株主メモ 株価情報 IRカレンダー FAQ 電子公告 ディスクロージャーポリシー 免責事項 IRに関するお問い合わせ 導入事例 ソリューション事例 クリエイティブ制作事例 資料請求・お問い合わせ 資料請求 商品・出稿に関するお問い合わせ IRに関するお問い合わせ その他ご意見・お問い合わせ お役立ち情報 採用情報 

### 2337 いちご

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 保存URLには採用の初期選択クエリが付く。質問時は「業績、事業内容、IR、決算」を選び直す必要がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ichigo.gr.jp/contact/?category=recruit)／[保存証拠](evidence/2337/20261011T044732609428Z/03.json)（取得 2026-10-11T04:47:36.151048+00:00）：電話番号 必須 （番号とハイフンを含め、半角英数字を使用） ご住所 メールアドレス 必須 （半角英数字を使用） 確認用にもう一度ご入力ください。 お問い合わせ 業績、事業内容、IR、決算 営業に関して（不動産） 営業に関して（クリーンエネルギー） 広告、宣伝、メディア関連 スポーツ関連事業 当社グループの物件にご入居されている方のお問い合わせ ⼈財に関するお問い合わせ 株式手続 いち
- [公式ページ](https://www.ichigo.gr.jp/contact/?category=recruit)／[保存証拠](evidence/2337/20261011T044732609428Z/03.json)（取得 2026-10-11T04:47:36.151048+00:00）：電話番号 必須 （番号とハイフンを含め、半角英数字を使用） ご住所 メールアドレス 必須 （半角英数字を使用） 確認用にもう一度ご入力ください。 お問い合わせ 業績、事業内容、IR、決算 営業に関して（不動産） 営業に関して（クリーンエネルギー） 広告、宣伝、メディア関連 スポーツ関連事業 当社グループの物件にご入居されている方のお問い合わせ ⼈財に関するお問い合わせ 株式手続 いち

### 2351 ＡＳＪ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 質問内容により無回答・返信遅延やFAQで回答する場合を案内。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.asj.ad.jp/ascgi-bin/ir_inquiry.cgi)／[保存証拠](evidence/2351/20261011T044739354519Z/02.json)（取得 2026-10-11T04:47:42.144943+00:00）：氏名 法人名 役職名 電話番号 メールアドレス お問い合わせ内容 選択してください。 IRに関するお問い合わせ 株式に関するお問い合わせ サービスに関するお問い合わせ 各事業会社に関するお問い合わせ 業務提携・資本提携に関するお問い合わせ その他お問い合わせ 選択してください。 お問い合わせに関する個人情報の
- [公式ページ](https://www.asj.ad.jp/ascgi-bin/ir_inquiry.cgi)／[保存証拠](evidence/2351/20261011T044739354519Z/02.json)（取得 2026-10-11T04:47:42.144943+00:00）：にてご連絡させていただく場合がございます。 内容によってはご回答できない場合やご回答に時間を要する場合もございます。 また、数多く寄せられるご質問につきましてはFAQにて回答する場合もございます。 以上ご了承いただけますようお願いいたします。 企業情報 社長挨拶 企業理念 行動基準 会社概要 沿革 グループ会社 IR（投資家情報） コーポレート ガバナンス IRニュース 決算短信 有価証券報

### 2353 日本駐車場開発

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://n-p-d.co.jp/contact/form_ir/)／[保存証拠](evidence/2353/20261011T044740963304Z/07.json)（取得 2026-10-11T04:47:50.698639+00:00）：D Group official website JP EN お問い合わせ サイトマップ ホーム 会社情報 サービス一覧 ニュースリリース IR情報 採用情報 投資家情報に関するお問合せ お問い合わせ内容を入力してください。（*は必須入力項目です） お名前 * 姓： 名： フリガナ * セイ： メイ： ご住所 メールアドレス * メールアドレス確認用 * お問い合わせ内容 * お問い

### 2370 メディネット

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 許可のない回答の転載・二次利用・本人以外への開示を禁止する記載がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.medinet-inc.co.jp/contact/ir/)／[保存証拠](evidence/2370/20261011T044745023944Z/02.json)（取得 2026-10-11T04:47:48.553465+00:00）：株式会社メディネット \| お問い合わせ \| 株主・投資家情報に関するお問い合わせ サイトマップ ENGLISH 文字サイズ 大きく 小さく 検索 選ばれている理由 事業内容 製造拠点・体制 企業情報 株主・投資家情報 採用情報 メニュー HOME 選ばれている理由 選ばれている理
- [公式ページ](https://www.medinet-inc.co.jp/contact/ir/)／[保存証拠](evidence/2370/20261011T044745023944Z/02.json)（取得 2026-10-11T04:47:48.553465+00:00）：わせの内容によっては回答にお時間をいただく場合もございますので予めご了承ください。 当社からの回答のメールは、お問い合わせいただいたご本人にお送りするものです。当社の許可なく、一部または全部を転載、二次利用してご本人以外の方に開示することは固くお断りいたします。 株主・投資家の皆様からよくいただくご質問をまとめました。ご覧の上、お問い合わせください。 IRについてのFAQ IRポリシー 問い合わせカテゴ
- [公式ページ](https://www.medinet-inc.co.jp/)／[保存証拠](evidence/2370/20261011T044745023944Z/01.json)（取得 2026-10-11T04:47:47.519722+00:00）：のFAQ 採用情報 採用情報TOP 仕事紹介 募集要項 各種お問い合わせ 各種お問い合わせTOP 事業に関するお問い合わせ 自己がん組織バンクに関する資料請求 株主・投資家情報に関するお問い合わせ 採用に関するお問い合わせ 法令・企業倫理・研究倫理に関するお問い合わせ ENGLISH MEDINET 選ばれている理由 製造拠点・体制 事業内容 事業内容 BUSINESS 特定細胞加工物製造業 

### 2375 ギグワークス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページはフォーム受付を明示するが、実メール・本文の入力欄が保存されていない。

根拠：

- [公式ページ](https://www.gig.co.jp/contact/ir)／[保存証拠](evidence/2375/20261011T044748251833Z/03.json)（取得 2026-10-11T04:47:53.420425+00:00）： Basic CONTACT US IRに関するお問い合わせ HOME お問い合わせ IRに関するお問い合わせ CONTACT US IRに関するお問い合わせ 下記のフォームにてお問い合わせください。 ギグワークス 広報IR担当 〒105-0003 東京都港区西新橋二丁目11番6号 ニュー西新橋ビル3階 【TEL】 03-6832-3260 メディア関連お問い合わせ お問い合わせ エージェントマイ
- [公式ページ](https://www.gig.co.jp/ir)／[保存証拠](evidence/2375/20261011T044748251833Z/02.json)（取得 2026-10-11T04:47:51.939361+00:00）：社の 株主優待案内 ギグワークス株式会社の 事業概要 アナリスト・機関投資家向け 決算説明会資料 個人投資家の皆様へ グループ代表挨拶 ギグワークスの事業概要 IR お問い合わせ 経営方針 ギグワークスの経営理念 ディスクロージャーポリシー 株主・株式情報 株主情報 株式事務のご案内 電子公告 株主様の個人情報の取り扱いについて IRライブラリー 財務ハイライト 決算短信 有

### 2376 サイネックス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名を必須表示。個人の入力条件は未確認。法人限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.scinex.co.jp/ask/)／[保存証拠](evidence/2376/20261011T044748293621Z/04.json)（取得 2026-10-11T04:47:53.704695+00:00）：お名前 必須 会社名 必須 部署 電話番号 必須 FAX番号 必須 メールアドレス 必須 お問い合わせ内容 お問い合わせの種類 IRに関するお問い合わせ 情報メディア事業に関するお問い合わせ DXサポート事業に関するお問い合わせ 採用に関するお問い合わせ その他のお問い合わせ 確認メール 受け取る 受け取らない 当社のプライバシーポリシーに同意の上、
- [公式ページ](https://www.scinex.co.jp/ask/)／[保存証拠](evidence/2376/20261011T044748293621Z/04.json)（取得 2026-10-11T04:47:53.704695+00:00）：れた場合は除きます。 よくあるお問い合わせはこちら STEP 01 情報の ご入力 STEP 02 入力内容の ご確認 STEP 03 送信完了 お名前 必須 会社名 必須 部署 電話番号 必須 FAX番号 必須 メールアドレス 必須 お問い合わせ内容 お問い合わせの種類 IRに関するお問い合わせ 情報メディア事業に関するお問い合わせ DXサポート事業に関するお問い合わ

### 2378 ルネサンス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答メールの転用・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.s-renaissance.co.jp/contact/form/?s=1)／[保存証拠](evidence/2378/20261011T044749811826Z/02.json)（取得 2026-10-11T04:47:51.977736+00:00）：信完了 下記の項目を入力し、画面下部の「確認画面へ」ボタンをクリックしてください。 ［必須］ 項目は必ずご入力ください。 ■お問い合わせ種別 選択してください IR（投資家情報）に関するお問い合わせ 会社概要、事業概要に関するお問い合わせ 商品・サービス及び協業のご提案に関するお問い合わせ 採用情報に関するお問い合わせ トピックス・リリースに関するお問い合わせ 個人情報に関するお問い合わせ 店舗
- [公式ページ](https://www.s-renaissance.co.jp/contact/form/?s=1)／[保存証拠](evidence/2378/20261011T044749811826Z/02.json)（取得 2026-10-11T04:47:51.977736+00:00）：て電話での確認をさせていただく場合がありますので、必ず電話番号やお名前の明記をお願いいたします。 ・当社からのご回答の電子メールは、お客様個人に宛てたものです。電子メールの一部または全部の転用や二次利用はご遠慮ください。 ・上記をご了承いただき、送信してよろしければ下の確認画面へボタンを押してください。 確認画面へ ルネサンスについて ルネサンスについて トップメッセージ 企業理念 会社概要 事業概要 沿革 なるほ
- [公式ページ](https://www.s-renaissance.co.jp/)／[保存証拠](evidence/2378/20261011T044749811826Z/01.json)（取得 2026-10-11T04:47:50.431288+00:00）： IRリリース一覧 CFOメッセージ ESG経営 業績・財務情報 IRライブラリ 株式情報 株主優待制度 IRカレンダー 電子公告 現在の株価 よくあるご質問 IRお問い合わせ サステナビリティ サステナビリティトップ ルネサンスのサステナビリティ ［S］ステークホルダーとのつながり ［G］ガバナンス ［E］地球環境への配慮 社外からの評価 採用情報 採用情報トップ ルネサ

### 2379 ディップ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせ先で「IR」を選択する。IR・広報・採用・その他の共通フォーム。
- 必須表示の項目へ入力が必要。個人情報の取扱いを確認・同意してから送信する。

注意・未確認：公開GETでの窓口確認のみ。実際の回答可否・所要時間・フォーム送信の成功は未検証。

根拠：

- [公式ページ](https://www.dip-net.co.jp/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2379-contact.json)（取得 2026-10-11T03:43:00.454407+00:00）：IR・採用・広報・その他お問い合わせ 以下リンク先よりお問合せください。
- [公式ページ](https://www.dip-net.co.jp/contact/company)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2379-form.json)（取得 2026-10-11T03:43:42.118505+00:00）：お問い合わせ先 IR 広報 CM広告 新卒採用 中途採用 その他 企業名 お名前 フリガナ メールアドレス お電話番号 郵便番号 ご住所 お問い合わせ内容
- [公式ページ](https://www.dip-net.co.jp/contact/company)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2379-form.json)（取得 2026-10-11T03:43:42.118505+00:00）：上記【個人情報の取扱いについて】の内容をご確認いただき同意の上、送信してください。

### 2385 総医研ホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページにフォームの案内と注意事項はあるが、メール・本文の実入力欄が保存されていない。

根拠：

- [公式ページ](https://soiken.com/ir/inquiry/)／[保存証拠](evidence/2385/20261011T044751016970Z/02.json)（取得 2026-10-11T04:47:52.980160+00:00）：ませんようお願いいたします。 個人情報の取り扱いにつきまして、「個人情報保護方針」をご参照の上、同意いただいた上で「お問い合わせ」フォームを送信ください。なお、お問い合わせフォームにご記入いただいた個人情報を、お問い合わせに関する対応以外の目的に使用することはございません。 「個人情報保護方針」へ お問い合わせの内容は具体的にご記入ください。ご記入に不備がある場合や、お問い合わ
- [公式ページ](https://soiken.com/)／[保存証拠](evidence/2385/20261011T044751016970Z/01.json)（取得 2026-10-11T04:47:52.173234+00:00）：へ IRニュース 経営情報 財務ハイライト 株式について IRライブラリー 個人投資家の 皆様へ IRスケジュール 用語解説 IRポリシー 注意事項・免責事項 IRお問い合わせ 電子公告 CSR情報 トップメッセージ 基本方針 活動概要 情報開示方針 個人情報保護方針 注意事項・免責事項 カスタマーハラスメント基本方針 サイトマップ ページの先頭に戻る HOME 総医研ホー

### 2391 プラネット

確認：案内・リンクのみ。個人条件の明示未確認。未確認。

取得範囲の受付条件：

- 一般問い合わせフォームの業種に「投資家」を選択できる。個人投資家を明示する区分は確認していない。

注意・未確認：実メール・本文欄はあるが、IR専用問い合わせ区分や金融IR質問を受け付ける説明はない。公式IR FAQ内と共通フッターから一般フォームにリンクするだけではIR用途を断定できない。 / 送信・JavaScript・実返信は未検証。

根拠：

- [公式ページ](https://www.planet-service.jp/customer/contactHPInsInput.do;jsessionid=0B0BEA54C22369973343ED29DA4B3904.jvm1)／[保存証拠](evidence/2391/20261011T044751436666Z/03.json)（取得 2026-10-11T04:47:59.029222+00:00）：欄は必ずご入力ください。 お問い合わせ内容によっては時間をいただいたり、ご回答いたしかねる場合がございます。 どうぞあらかじめご了承ください。 会社名 部署名 業種 選択してください 投資家 メーカー 卸売業 資材サプライヤー 小売業 システムベンダー 官公庁 学校法人 マスメディア その他 お名前 ※ フリガナ 役職 E-Mail ※ （注）半角文字でご入力下さい。 TEL FAX ご住所 〒 - 件名 ※ 内容 ※ お問い
- [公式ページ](https://www.planet-van.co.jp/ir/faq.html)／[保存証拠](evidence/2391/20261011T044751436666Z/02.json)（取得 2026-10-11T04:47:54.131657+00:00）：料 適時開示情報 IRカレンダー 株式関連情報 株価情報 株式基本情報 株主還元 財務データ 経営成績 財政状態 キャッシュ・フローの状況 配当実績 経営指標 IRに関するご質問 お問い合わせ 免責事項 株主さまの個人情報の取り扱いについて 電子公告 サービス EDI（データ交換） コンセプト 基幹EDI 基幹EDI 接続パッケージ一覧 全データ一覧（20種類） EDIサポート機能 MITEOS(ミテオス) Web発注 FAX発注 販売レ

### 2408 ＫＧ情報

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kg-net.co.jp/contact/ir/)／[保存証拠](evidence/2408/20261011T044758573291Z/02.json)（取得 2026-10-11T04:48:00.337737+00:00）：IR情報お問い合わせ \| 株式会社KG情報 IR情報お問い合わせ 当社へのIRに関するお問い合わせを以下のフォームより承っております。 当社IRポリシーをよくご理解いただいた上で、ご質問をいただけますようにお願いいたしま

### 2410 キャリアデザインセンター

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://cdc.type.jp/contact/ir_index.php)／[保存証拠](evidence/2410/20261011T044759605050Z/04.json)（取得 2026-10-11T04:48:03.124909+00:00）：区分 必須 個人投資家 機関投資家 証券会社 商品・サービスのご提案 その他 会社名 任意 氏名（漢字） 必須 姓 名 氏名（フリガナ） 必須 セイ メイ メールアドレス 必須 電話番号 任意 件名 必須 お問い合わせ内容
- [公式ページ](https://cdc.type.jp/contact/ir_index.php)／[保存証拠](evidence/2410/20261011T044759605050Z/04.json)（取得 2026-10-11T04:48:03.124909+00:00）：問い合わせ IRに関するお問い合わせ IR情報に関するお問い合わせは、下記フォームよりお送りください。 必要事項をご記入の上、「送信」ボタンを押してください。 区分 必須 個人投資家 機関投資家 証券会社 商品・サービスのご提案 その他 会社名 任意 氏名（漢字） 必須 姓 名 氏名（フリガナ） 必須 セイ メイ メールアドレス 必須 電話番号 任意 件名 必須 お問い合わせ内容 必須 0 

### 2411 ゲンダイエージェンシー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.gendai-a.co.jp/ir/contact/)／[保存証拠](evidence/2411/20261011T044800122046Z/02.json)（取得 2026-10-11T04:48:04.929630+00:00）：IRに関するお問い合わせ \| ゲンダイエージェンシー株式会社｜GENDAI AGENCY INC. 新着情報 会社情報 会社情報トップ 代表メッセージ 企業理念 会社概要 グループ企業情報 沿革 組織図 役員紹介 事業所一覧
- [公式ページ](https://www.gendai-a.co.jp/)／[保存証拠](evidence/2411/20261011T044800122046Z/01.json)（取得 2026-10-11T04:48:02.447308+00:00）：配当等 財務ハイライト（連結） 株主・株式情報 コーポレートガバナンス IRカレンダー IRライブラリー 電子公告 ディスクロージャーポリシー よくあるご質問 IRお問い合わせ サステナビリティ サステナビリティトップ 環境 社会 ガバナンス 採用情報 お問い合わせ JP English 日本語 ニュースリリース 会社情報 事業・サービス紹介 IR・投資家情報 サステナビリ

### 241A ＲＯＸＸ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@roxx.co.jp`。

取得範囲の受付条件：

- 非公開情報、重要事実に該当し得る質問、株価動向、誹謗中傷、営業・勧誘等は回答対象外。
- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://roxx.co.jp/contact/)／[保存証拠](evidence/241A/20261011T044803886474Z/03.json)（取得 2026-10-11T04:48:07.009094+00:00）：.gle/vpUZErMi7CsL7DrV6 コーポレートについて ご取材のお申し込み、 プレスリリースについて pr@roxx.co.jp IR情報について 当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。以下の注意事項をご確認の上、下記メールアドレスにお問い合わせください。 ir@roxx.co.jp お問い合わせいただく際のお願いとご注意 サービスに関するお問い合わせ、営業
- [公式ページ](https://roxx.co.jp/contact/)／[保存証拠](evidence/241A/20261011T044803886474Z/03.json)（取得 2026-10-11T04:48:07.009094+00:00）：します。 お問い合わせ内容によってはお答えできない場合もございます。下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 非公開情報に関するご質問 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問 誹謗中傷に該当するメッセージ 株式市場の値動きに関するご質問 営業や勧誘のお問い合わせ 当社からご回答としてお送りするEメー
- [公式ページ](https://roxx.co.jp/contact/)／[保存証拠](evidence/241A/20261011T044803886474Z/03.json)（取得 2026-10-11T04:48:07.009094+00:00）：お送りするEメールは、株主・投資家の皆様からお寄せいただいたお問い合わせなどにお答えさせていただく目的で、皆様個人宛てにお送りするものです。その一部または全部を転載、二次利用することはご遠慮ください。 その他免責事項については「 免責事項 」をご確認ください。 お問い合わせフォームへご記入いただいた個人情報につきましては、厳重にお取り扱いいたします。当社の個人情報の取り扱いについては、 プライバ
- [公式ページ](https://roxx.co.jp/contact/)／[保存証拠](evidence/241A/20261011T044803886474Z/03.json)（取得 2026-10-11T04:48:07.009094+00:00）：: https://forms.gle/vpUZErMi7CsL7DrV6 コーポレートについて ご取材のお申し込み、 プレスリリースについて pr@roxx.co.jp IR情報について 当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。以下の注意事項をご確認の上、下記メールアドレスにお問い合わせください。 ir@roxx.co.jp お問い合わせいただく際のお願いとご注意 サービスに関するお問い合わせ、営業・ご取材等のご連絡はIR窓口では受け付けておりません。これらのお問い合わせにつきましては各窓口よりご連絡をお願いいたします。

### 2429 ワールドホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせ分類で「IR情報のお問い合わせ」を選択する。
- 個人情報の取扱いへの同意、名前・メール等の入力欄がある。必須と表示された項目への入力を求めている。
- 問い合わせ内容によっては回答できない場合がある。

注意・未確認：公開GETでの窓口確認のみ。実際の回答可否・所要時間・フォーム送信の成功は未検証。

根拠：

- [公式ページ](https://world-hd.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2429-contact.json)（取得 2026-10-11T03:42:03.361244+00:00）：お問い合わせ分類 一般のお問い合わせ IR情報のお問い合わせ 会社名 部署名 お名前 フリガナ Eメールアドレス Eメールアドレス（確認） 電話番号 - - お問い合わせ内容
- [公式ページ](https://world-hd.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2429-contact.json)（取得 2026-10-11T03:42:03.361244+00:00）：お問い合わせ内容によってはご回答できない場合がございます。あらかじめご了承ください。
- [公式ページ](https://world-hd.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2429-contact.json)（取得 2026-10-11T03:42:03.361244+00:00）：「必須」 のついた項目は、必ずご入力ください。

### 2436 共同ピーアール

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- フォームからの営業メールは受付対象外。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR問い合わせページのフォーム案内と注意事項のみ。保存された実入力欄はない。

根拠：

- [公式ページ](https://www.kyodo-pr.co.jp/investor/contact)／[保存証拠](evidence/2436/20261011T044808050790Z/02.json)（取得 2026-10-11T04:48:12.101893+00:00）：い。 お問い合わせいただいた内容によってはご返信までお時間がかかるものがございます。 また、内容によってはご返信できない場合がございます。予めご了承ください。 ＊お問い合わせフォームからの営業メールはお断りいたします＊ 共同ピーアール株式会社 〒104-0045 東京都中央区築地1-13-1 銀座松竹スクエア10階 PRとは サービス ニュース セミナー 各種お問い合わせ デジマナ PR TODAY PR ever
- [公式ページ](https://www.kyodo-pr.co.jp/investor/contact)／[保存証拠](evidence/2436/20261011T044808050790Z/02.json)（取得 2026-10-11T04:48:12.101893+00:00）：内容によってはご返信までお時間がかかるものがございます。 また、内容によってはご返信できない場合がございます。予めご了承ください。 ＊お問い合わせフォームからの営業メールはお断りいたします＊ 共同ピーアール株式会社 〒104-0045 東京都中央区築地1-13-1 銀座松竹スクエア10階 PRとは サービス ニュース セミナー 各種お問い合わせ デジマナ PR TODAY PR eve
- [公式ページ](https://www.kyodo-pr.co.jp/)／[保存証拠](evidence/2436/20261011T044808050790Z/01.json)（取得 2026-10-11T04:48:09.340463+00:00）：Rライブラリ 決算短信 決算補足資料 有価証券報告書 株主通信 IRイベント IRカレンダー 決算説明会 個人投資家向け説明会 株主総会 その他 よくある質問 IRに関するお問い合わせ IRメールマガジン登録フォーム 免責事項 PRとは PRとは PRの根幹：メディアリレーションズとは PR会社と広告会社の違いとは？ PR会社の市場推移 PRは人々との信頼関係を築く活動 全国の記者

### 2438 アスカネット

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 回答の転載は禁止する記載がある。
- 至急・回答期日指定には応じられない場合がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IRフォーム受付を本文に明示するが、メール・本文の実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.asukanet.co.jp/contents/ir/contact.html)／[保存証拠](evidence/2438/20261011T044808841987Z/04.json)（取得 2026-10-11T04:48:12.535910+00:00）：IRに関するお問い合わせ│投資家情報│アスカネット IRに関するお問い合わせ お問い合わせフォーム 投資家情報に関するお問い合わせは、下記のお問い合わせフォームで受け付けています。 ※入力項目はすべて必須です。 お問い合わせの際のご注意 当社は個人情報保護方針に基づき、個人情報を管理しております。問い合わせいただく際には、以下の点にご注意ください。 当社より送信するご返事の電子
- [公式ページ](https://www.asukanet.co.jp/contents/ir/contact.html)／[保存証拠](evidence/2438/20261011T044808841987Z/04.json)（取得 2026-10-11T04:48:12.535910+00:00）：さい。 当社より送信するご返事の電子メールは、お寄せいただいたお問い合わせ等にお答えさせていただく目的で、株主・投資家の皆様、個人宛てにお送りするものですので、転載はお断りいたします。 回答期日の指定や「至急」のご要望には、お応えできない場合がございます。 お問い合わせ等の内容は、できるだけ具体的にご記入をお願いします。 内容によってはお答えできない場合もありますので、ご了承くだ
- [公式ページ](https://www.asukanet.co.jp/contents/ir/contact.html)／[保存証拠](evidence/2438/20261011T044808841987Z/04.json)（取得 2026-10-11T04:48:12.535910+00:00）：、お寄せいただいたお問い合わせ等にお答えさせていただく目的で、株主・投資家の皆様、個人宛てにお送りするものですので、転載はお断りいたします。 回答期日の指定や「至急」のご要望には、お応えできない場合がございます。 お問い合わせ等の内容は、できるだけ具体的にご記入をお願いします。 内容によってはお答えできない場合もありますので、ご了承ください。 株式会社アスカネッ

### 244A グロースエクスパートナーズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社・法人名は法人の場合に必須。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.gxp-group.co.jp/contact/ir)／[保存証拠](evidence/244A/20261011T044814565523Z/03.json)（取得 2026-10-11T04:48:20.228648+00:00）： / 法人名（法人の場合は必須） star_rate メールアドレス star_rate 確認用メールアドレス 電話番号 star_rate お問い合わせ内容 IR（投資家情報）について 取材等のお申し込み（広報・PR関連）について その他 star_rate 件名 star_rate 内容（1,000字以内） 個人情報の取り扱いへの同意 ※個人情報の取り扱いについて、詳しくは弊社の
- [公式ページ](https://www.gxp-group.co.jp/contact/ir)／[保存証拠](evidence/244A/20261011T044814565523Z/03.json)（取得 2026-10-11T04:48:20.228648+00:00）：tar_rate は入力必須項目です。 star_rate 姓 star_rate 名 star_rate セイ star_rate メイ 貴社名 / 法人名（法人の場合は必須） star_rate メールアドレス star_rate 確認用メールアドレス 電話番号 star_rate お問い合わせ内容 IR（投資家情報）について 取材等のお申し込み（広報・PR関連）につい
- [公式ページ](https://www.gxp-group.co.jp/ir/stock-information)／[保存証拠](evidence/244A/20261011T044814565523Z/02.json)（取得 2026-10-11T04:48:16.761628+00:00）： 株式基本情報 株主総会 株価情報 launch IRカレンダー サステナビリティ 電子公告 免責事項 ディスクロージャーポリシー IR情報メール配信について IRに関するお問い合わせ Recruit 採用情報 GxPグループでは通年でキャリア採用を行っています。 募集職種・要項は下記採用サイトにてご確認ください。 皆さまとお会いできることを心より楽しみにしています。 採用サイトへ

### 2459 アウンコンサルティング

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

公開IRメール：`ir@auncon.co.jp`。

取得範囲の受付条件：

- 本文は1000文字まで。超過する場合はIRメールを案内。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.auncon.co.jp/ir/contact-ir/)／[保存証拠](evidence/2459/20261011T044815767208Z/02.json)（取得 2026-10-11T04:48:22.293290+00:00）：IRに関するお問い合わせ - グローバルマーケティング (海外SEO・海外広告)｜<東証上場・実績2,000社>アウンコンサルティング （証券番号：2459） Company Company 企業理念 会社概要 取締役紹介 沿革 認証・認定・受賞歴 講演
- [公式ページ](https://www.auncon.co.jp/ir/contact-ir/)／[保存証拠](evidence/2459/20261011T044815767208Z/02.json)（取得 2026-10-11T04:48:22.293290+00:00）：ださい 必須 メールアドレス 必須 メールアドレス（確認） 確認用のメールアドレスが一致していません 必須 電話番号 必須 職種 —以下から選択してください— 個人投資家 機関投資家 アナリスト マスコミ関連 その他 任意 会社・組織名 任意 住所（すべて） Japan 郵便番号 - 都道府県 —以下から選択してください— 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木
- [公式ページ](https://www.auncon.co.jp/ir/contact-ir/)／[保存証拠](evidence/2459/20261011T044815767208Z/02.json)（取得 2026-10-11T04:48:22.293290+00:00）：賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 市町村区 町域 以降の住所 任意 WebサイトURL 任意 お問合せ内容 残文字数 : 1000 文字 1000文字を超える場合は「ir@auncon.co.jp」まで連絡をお願い致します。 必須 個人情報保護方針 個人情報保護方針に同意する 当社の 個人情報保護方針 について同意される方のみ送信できます。 このサイトはreC
- [公式ページ](https://www.auncon.co.jp/ir/contact-ir/)／[保存証拠](evidence/2459/20261011T044815767208Z/02.json)（取得 2026-10-11T04:48:22.293290+00:00）：長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 市町村区 町域 以降の住所 任意 WebサイトURL 任意 お問合せ内容 残文字数 : 1000 文字 1000文字を超える場合は「ir@auncon.co.jp」まで連絡をお願い致します。 必須 個人情報保護方針 個人情報保護方針に同意する 当社の 個人情報保護方針 について同意される方のみ送信できます。 このサイトはreCAPTCHAによって保護されており
- [公式ページ](https://www.auncon.co.jp/)／[保存証拠](evidence/2459/20261011T044815767208Z/01.json)（取得 2026-10-11T04:48:18.739457+00:00）：umn Column News News IR IR 経営方針 IRリリース IRライブラリー 財務・業績 株式情報 IRカレンダー 株価情報 よくあるご質問 IRに関するお問い合わせ Recruit Recruit M&A M&A Contact Contact menu Marketing impact! マーケティングの力で日本を元気に！ Topics 2026.09.17 

### 245A ＩＮＧＳ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://ingsinc.co.jp/ir_contact)／[保存証拠](evidence/245A/20261011T044816488883Z/03.json)（取得 2026-10-11T04:48:21.019206+00:00）：IRについてのお問い合わせ – 株式会社INGS HOME ホーム NEWS お知らせ一覧 BRAND ブランド CONA 焼売のジョー ラーメン事業 FC/PRODUCE FC・プロデュース業 CONA 焼売のジョー ラーメ

### 2461 ファンコミュニケーションズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 決算関連の区分では機関投資家・証券アナリスト協会会員会社・アナリスト・報道の属性を選択。一方、その他の区分に「株式・IRに関するお問い合わせ」があるため、会社全体を機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.fancs.com/contact/)／[保存証拠](evidence/2461/20261011T044816497706Z/04.json)（取得 2026-10-11T04:48:22.765573+00:00）：証券アナリスト協会会員会社 アナリスト 報道関係者 その他お問い合わせ 必須 広報に関するお問い合わせ 採用に関するお問い合わせ 個人情報に関するお問い合わせ 株式・IRに関するお問い合わせ お名前 必須 フリガナ 必須 メールアドレス 必須 メールアドレス(再入力) 必須 お問い合わせ内容 必須 個人情報のお取り扱いについて 入力・送信頂いた個人情報は、株式会社ファンコミュニケーション
- [公式ページ](https://www.fancs.com/contact/)／[保存証拠](evidence/2461/20261011T044816497706Z/04.json)（取得 2026-10-11T04:48:22.765573+00:00）：t（メディア会員） A8.net（広告主会員） A8app GERA N-INE YOOR その他 「その他」を選択した方は下記にサービス名をご入力ください。 属性 必須 機関投資家 日本証券アナリスト協会会員会社 アナリスト 報道関係者 その他お問い合わせ 必須 広報に関するお問い合わせ 採用に関するお問い合わせ 個人情報に関するお問い合わせ 株式・IRに関するお問い合わせ お名前 必須 フリガナ 必須 メー

### 2462 ライク

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.like-gr.co.jp/inquiry/index.html)／[保存証拠](evidence/2462/20261011T044818406056Z/04.json)（取得 2026-10-11T04:48:23.171353+00:00）： 任意 氏名 全角文字 必須 氏名 カタカナ 必須 ご住所 全角文字 任意 お電話番号 半角数字 任意 メールアドレス 半角英数 必須 お問い合わせ内容 必須 IRに関するお問い合わせ ライク株式会社に関するお問い合わせ その他のお問い合わせ 当社ではM＆A・出資先を募集中です。募集の詳細は こちら をご参考ください。 本文 必須 ご登録いただいた個人情報は当社プライバシーポリシー

### 2469 ヒビノ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.hibino.co.jp/support/input-ir.html)／[保存証拠](evidence/2469/20261011T044822016731Z/04.json)（取得 2026-10-11T04:48:27.628357+00:00）：ヒビノGMC 経営企画グループ 広報課 IR担当｜お問い合わせ｜ヒビノ株式会社 HIBINO 製品・商品・サービス 製品・商品・サービス トップページ 業務用音響機器 LEDディスプレイ・システム 医療機関向け映像システム Hibino.com（オ

### 246A アスア

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.asua.ne.jp/contact/)／[保存証拠](evidence/246A/20261011T044822229918Z/04.json)（取得 2026-10-11T04:48:28.940769+00:00）：部署名 メールアドレス 必須 電話番号（ハイフンなし） 必須 郵便番号（ハイフンなし） 必須 ご住所 必須 お問い合わせ項目 必須 営業について 採用について IRについて その他（※自由項目欄にお書きください） 自由項目（質問等） プライバシーポリシー にご同意のうえ 下記の 送信ボタンをクリックして下さい プライバシーポリシーに同意する Δ

### 2471 エスプール

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- フォームの属性に個人投資家、機関投資家、アナリスト、その他を明記。氏名・フリガナ・メール・属性が必須表示。
- 非公開の業績動向、金融商品取引法166条の重要事実に関連する可能性のある質問、株価/市場動向、個別製品/サービス、誹謗中傷、営業/勧誘への回答は差し控える。
- 内容により返信に時間を要する。回答メールの一部/全部の転載・二次利用を遠慮する条項がある。
- よくある質問を先に確認し、個人情報取扱いの同意事項に同意してから確認画面へ進む。

注意・未確認：このページの人事本部メールは個人情報の相談窓口であり、IRメールとして一覧へ追加していない。 / 入力欄をGETで確認したのみで、送信・返信は未検証。

根拠：

- [公式ページ](https://www.spool.co.jp/contact_ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2471-contact.json)（取得 2026-10-11T03:43:00.461275+00:00）：メールアドレス 必須 属性 必須 個人投資家 機関投資家 アナリスト その他 お問合せ内容
- [公式ページ](https://www.spool.co.jp/contact_ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2471-contact.json)（取得 2026-10-11T03:43:00.461275+00:00）：下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 ・非公開情報に関するご質問（業績動向など） ・金融商品取引法 第166条の「重要事実」に関連する可能性のあるご質問 ・株価動向、株式市場の値動きに関するご質問
- [公式ページ](https://www.spool.co.jp/contact_ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2471-contact.json)（取得 2026-10-11T03:43:00.461275+00:00）：当社からご回答した内容について、その一部または全部を転載、2次利用することはご遠慮ください。
- [公式ページ](https://www.spool.co.jp/contact_ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-2471-contact.json)（取得 2026-10-11T03:43:00.461275+00:00）：上記の同意事項に同意の上、確認するボタンを押してください

### 2477 手間いらず

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.temairazu.co.jp/contact/inquiry?subject=ir)／[保存証拠](evidence/2477/20261011T044824300303Z/04.json)（取得 2026-10-11T04:48:27.936392+00:00）：お問い合わせ項目 IRに関するお問い合わせ 広報へのお問い合わせ 採用に関するお問い合わせ 広告掲載に関するお問い合わせ お名前 * メールアドレス * お問い合わせ内容 お問い合わせ内容を入力して下さい。 確認画面へ 戻る
- [公式ページ](https://www.temairazu.co.jp/contact)／[保存証拠](evidence/2477/20261011T044824300303Z/03.json)（取得 2026-10-11T04:48:27.508062+00:00）：lish] HOME お問い合わせ お問い合わせ 弊社に関するご質問等がございましたら、下記リンク先のフォームよりお問い合わせ下さい。 mail お問い合わせ IRに関するお問い合わせ 広報へのお問い合わせ 採用に関するお問い合わせ 広告掲載に関するお問い合わせ HOME お問い合わせ 利用規約 プライバシーポリシー 商標について サイトマップ 投資家向け情報 株式情報 株価情報 

### 247A Ａｉロボティクス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@ai-robotics.co.jp`。

取得範囲の受付条件：

- 回答の転載・二次利用について注意事項がある。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://ai-robotics.co.jp/ir/inquiry/)／[保存証拠](evidence/247A/20261011T044824516673Z/05.json)（取得 2026-10-11T04:48:28.674352+00:00）：部または全部を無断で転載・二次利用することは禁止されております。 上記ご理解のほど、何卒よろしくお願いいたします。 お問い合わせ先： Aiロボティクス株式会社 IR担当 Email： ir@ai-robotics.co.jp IR IRトップ IRライブラリ IRニュース 業績・財務情報 経営情報 株式情報 電子公告 お問い合わせ よくあるご質問 IRカレンダー 免責事項 BUSINESS COMPANY RECRUIT
- [公式ページ](https://ai-robotics.co.jp/ir/inquiry/)／[保存証拠](evidence/247A/20261011T044824516673Z/05.json)（取得 2026-10-11T04:48:28.674352+00:00）：たします。 当社の個人情報の取り扱いについては、 プライバシーポリシー をご確認ください。 また、当社から回答した内容について、その一部または全部を無断で転載・二次利用することは禁止されております。 上記ご理解のほど、何卒よろしくお願いいたします。 お問い合わせ先： Aiロボティクス株式会社 IR担当 Email： ir@ai-robotics.co.jp IR I
- [公式ページ](https://ai-robotics.co.jp/ir/inquiry/)／[保存証拠](evidence/247A/20261011T044824516673Z/05.json)（取得 2026-10-11T04:48:28.674352+00:00）：個人情報につきましては、厳重にお取り扱いいたします。 当社の個人情報の取り扱いについては、 プライバシーポリシー をご確認ください。 また、当社から回答した内容について、その一部または全部を無断で転載・二次利用することは禁止されております。 上記ご理解のほど、何卒よろしくお願いいたします。 お問い合わせ先： Aiロボティクス株式会社 IR担当 Email： ir@ai-robotics.co.jp IR IRトップ IRライブラリ IRニュース 業績・財務情報 経営情報 株式情報 電子公告 お問い合わせ よくあるご質問 IRカレンダー 免責事項 BUSINESS COMPANY RECRUIT

### 2480 システム・ロケーション

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://slc.jp/inquiry/)／[保存証拠](evidence/2480/20261011T044826119917Z/03.json)（取得 2026-10-11T04:48:32.111789+00:00）：お問合せ内容 サービスについて IRについて 氏名 ふりがな 会社名 役職 メールアドレス 電話番号 関心のあるサービス 車種カタログDB（データベース） 車両価値算出システム（RV Doctor/PV Doctor/トラックRV Doctor

### 2483 翻訳センター

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.honyakuctr.com/inquiry/general/?place=ir)／[保存証拠](evidence/2483/20261011T044829284256Z/05.json)（取得 2026-10-11T04:48:35.297391+00:00）：お問い合わせ内容のご入力 お問い合わせ項目 必須 選択してください 会社概要 業務内容 当社IR情報 フリーランス登録 その他 お問い合わせ内容 必須 お客様情報のご入力 お名前 必須 例）翻訳 太郎 姓 名 お名前（フリガナ） 例）ホンヤク タロウ セイ(カタカナ) メイ(カタカナ) 法人名（団体
- [公式ページ](https://www.honyakuctr.com/contact/?from=gnavi)／[保存証拠](evidence/2483/20261011T044829284256Z/04.json)（取得 2026-10-11T04:48:33.099445+00:00）：トライアルお申し込み 校正者・ポイントチェッカー トライアルお申し込み Apply as a Translator Apply as a Translator 当社のIRに関するお問い合わせ WEBからのお問い合わせ 当社のIRに関するお問い合わせ その他全般のお問い合わせ WEBからのお問い合わせ その他全般のお問い合わせ Page top よくあるご質問 基本用語解説集 サイトマップ

### 2488 ＪＴＰ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページは内容の入力を案内するが、保存された実入力欄はない。

根拠：

- [公式ページ](https://www.jtp.co.jp/contactus/ir/)／[保存証拠](evidence/2488/20261011T044831402344Z/04.json)（取得 2026-10-11T04:48:36.021543+00:00）： ソリューションサイト JP EN 検索 IR Contact IRお問い合わせ お問い合わせをお送りいただく前に、下記の注意事項をお読みいただき、ご理解の上、お問い合わせ内容の入力にお進みください。 お問い合わせにあたってのご注意事項 お客様からいただく個人情報は、お問い合わせ・ご質問への回答、情報提供のために使用させていただきます。 お客様からいただいたeメールアドレスが違っている場合や、シス

### 2489 アドウェイズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名・部署名を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://ir.adways.net/inquiry.cgi)／[保存証拠](evidence/2489/20261011T044833359202Z/02.json)（取得 2026-10-11T04:48:36.558351+00:00）：IRお問い合わせ｜株式会社アドウェイズIR情報 MENU CLOSE ニュース・インフォ プレスリリース パブリシティ イベント情報 ブログ サービス エージェンシー事業 アドプラットフォーム事業 海外事業 ライフス
- [公式ページ](https://ir.adways.net/inquiry.cgi)／[保存証拠](evidence/2489/20261011T044833359202Z/02.json)（取得 2026-10-11T04:48:36.558351+00:00）：歳以上 職業 必須 ---- 選択してください ---- 金融機関(アナリスト) 金融機関(ファンドマネージャー) 金融機関(その他) 報道・編集関係 その他 会社名 必須 部署名 必須 Eメールアドレス 必須 Eメールアドレス (確認用) 必須 電話番号【携帯可】 件名 必須 お問い合わせ内容 必須 以下の文章をご確認・ご同意いただいた上で、お問い合わせいただきますよ
- [公式ページ](https://adways.net/)／[保存証拠](evidence/2489/20261011T044833359202Z/01.json)（取得 2026-10-11T04:48:34.798761+00:00）： 説明会資料 有価証券報告書 IRニュース INQUIRY お問い合わせ 広告（プロモーション）のご相談・お問い合せ M&A、投資に関するご相談・お問い合わせ IRに関するお問い合わせ プレスリリース（ニュース）に関するお問い合わせ 取材のお申し込み その他お問い合わせ JP / EN NEWS ニュース すべてのニュース プレスリリース パブリシティ イベント プレスキット BU

### 248A キッズスター

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 非公開情報・重要事実・株価動向・誹謗中傷・営業等の質問には回答を差し控える。
- 回答の転載・二次利用をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kidsstar.co.jp/contact/ir)／[保存証拠](evidence/248A/20261011T044833523091Z/02.json)（取得 2026-10-11T04:48:35.041208+00:00）：お客様サポート サービス一覧 採用情報 各種お問い合わせ IR情報 - 経営情報 - IRライブラリ - 業績ハイライト - 株式情報 - その他IR情報 - IRに関するお問い合わせ プライバシーポリシー 情報セキュリティに関する方針 © KIDS STAR Inc. All Rights Reserved. clear 企業・ブランドのエンゲージメントを高める体験を創出します。
- [公式ページ](https://www.kidsstar.co.jp/contact/ir)／[保存証拠](evidence/248A/20261011T044833523091Z/02.json)（取得 2026-10-11T04:48:35.041208+00:00）：当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 - 金融商品取引法第166条の「重要事実」に該当する可能性のあるご質問 - 非公開情報に関するご質問 - 株式市場の値動きに関するご質問 - 誹謗中傷に該当するメッセージ - その他、営業や勧誘など、IRに関係しないご質問 また、当社からご回答した内容の一部または全部を転載、二次利用することはご遠慮
- [公式ページ](https://www.kidsstar.co.jp/contact/ir)／[保存証拠](evidence/248A/20261011T044833523091Z/02.json)（取得 2026-10-11T04:48:35.041208+00:00）：市場の値動きに関するご質問 - 誹謗中傷に該当するメッセージ - その他、営業や勧誘など、IRに関係しないご質問 また、当社からご回答した内容の一部または全部を転載、二次利用することはご遠慮ください。 転載や二次利用が発覚した場合は削除依頼等の対応を行う場合がございます。 ▼ディスクロージャーポリシー https://ir.kidsstar.co.jp/other-ir-information/
- [公式ページ](https://www.kidsstar.co.jp/)／[保存証拠](evidence/248A/20261011T044833523091Z/01.json)（取得 2026-10-11T04:48:34.496533+00:00）：合わせ ごっこランド・ジモトガイド導入に関するお問い合わせ／その他のお問い合わせ お問い合わせフォームへ IRお問い合わせ 当社のIR情報に関するお問い合わせ IRお問い合わせフォームへ 株式会社キッズスター 〒150-0045 東京都渋谷区神泉町9-5 フジタ・インゼックスビル5F ごっこランド（企業向け） - 取り組み実績 - 出店目的・効果 - パビリオン一覧 - 出店事例イン

### 2493 イーサポートリンク

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.e-supportlink.com/contact/)／[保存証拠](evidence/2493/20261011T044836882759Z/03.json)（取得 2026-10-11T04:48:41.407317+00:00）：O） 生鮮MDシステム es-Marché（エスマルシェ） Marché⁺（マルシェプラス）に関するお問い合わせ 農産物の生産・調達・販売に関するお問い合わせ 企業情報・IRに関するお問い合わせ お問い合わせ内容 ※ 個人情報の利用目的 このお問い合わせフォームでご提供いただく個人情報は 当社の製品やサービスに関する情報をご提供する目的のほか お問い合わせに対する回答を行うために利用します。
- [公式ページ](https://www.e-supportlink.com/contact/)／[保存証拠](evidence/2493/20261011T044836882759Z/03.json)（取得 2026-10-11T04:48:41.407317+00:00）：トではプライバシーの保護のため、ＳＳＬサーバ証明書を使用し、暗号化通信を実現しています。 電話番号：03-5979-0666（代表） お名前 ※ ふりがな ※ 会社名 ※ 生産者の方は、生産物をご記入ください 郵便番号 ※ 半角数字でご記入ください 例）123-4567 - 住所 ※ ビル・アパート名もご記入ください 電話番号 ※ 半角数字でご記入ください ハイフン「

### 2497 ユナイテッド

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://united.jp/contact/)／[保存証拠](evidence/2497/20261011T044837730049Z/03.json)（取得 2026-10-11T04:48:40.513107+00:00）：※必須 お問い合わせ分類 事業に関するお問い合わせ 投資に関するお問い合わせ 広報に関するお問い合わせ IRに関するお問い合わせ 採用に関するお問い合わせ 個人情報に関するお問い合わせ 営業・新規お取引のお問い合わせ その他のお問い合わせ 営業・新規お取引のお問い合わせについては以下フォームより入力をお願いいたします。 htt

### 2498 オリエンタルコンサルタンツホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.oriconhd.jp/contact/)／[保存証拠](evidence/2498/20261011T044838339463Z/04.json)（取得 2026-10-11T04:48:43.064425+00:00）：お問い合わせ種別 株主・投資家情報 業務・技術 個人情報保護 報道・取材・広告 採用情報 その他 お名前 [必須] 必須項目です。 ふりがな [必須] 必須項目です。 職業 会社員 会社役員 公務員 自営・自由業 法人 主婦 学生 無

### 2502 アサヒグループホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 携帯電話のメールアドレスには返信しない旨を案内。別のメールアドレスを使う必要がある。
- 会社名・部署名は会社宛の郵送希望者について必須と記載。
- 実 input は ANSWER_4 と確認用 ANSWER_5、本文 textarea は ANSWER_3。 visible メール表示と実 controls を手動で照合。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://forms.asahigroup-holdings.com/web-service/asahig-hd/ir/contact_ir/form.wsp.html?CMD=onForm)／[保存証拠](evidence/2502/20261011T044840325888Z/06.json)（取得 2026-10-11T04:48:48.330186+00:00）：投資家情報（IR）についてのお問い合わせ \| アサヒグループホールディングス 投資家情報（IR）についてのお問い合わせ 下記内容をご確認いただき、フォームに必要事項をご入力の上【入力内容の確認】ボタンを押してください。 お客様からいただくご
- [公式ページ](https://forms.asahigroup-holdings.com/web-service/asahig-hd/ir/contact_ir/form.wsp.html?CMD=onForm)／[保存証拠](evidence/2502/20261011T044840325888Z/06.json)（取得 2026-10-11T04:48:48.330186+00:00）：ト」 統合報告書 ※環境への配慮から冊子版は発行しておりません。 件名 ご意見・ご質問がございましたらこちらへお願いします。 メールアドレス （半角英数字） ※携帯電話メール以外のアドレスをご記入ください。 確認用メールアドレス （半角英数字） ※確認のため、もう一度メールアドレスのご入力をお願いします。メールアドレスが誤っておりますと、ご回答を差し上げられない場合がございます。 お名
- [公式ページ](https://forms.asahigroup-holdings.com/web-service/asahig-hd/ir/contact_ir/form.wsp.html?CMD=onForm)／[保存証拠](evidence/2502/20261011T044840325888Z/06.json)（取得 2026-10-11T04:48:48.330186+00:00）：レスのご入力をお願いします。メールアドレスが誤っておりますと、ご回答を差し上げられない場合がございます。 お名前 （全角） ふりがな （全角ひらがな） 会社名（会社宛に郵送をご希望の方は必ず入力してください） 部署名（会社宛に郵送をご希望の方は必ず入力してください） 性別 男性 女性 年齢 20歳未満 20代 30代 40代 50代 60代 70歳以上 営業のメールではない はい 電話番号 
- [公式ページ](https://forms.asahigroup-holdings.com/web-service/asahig-hd/ir/contact_ir/form.wsp.html?CMD=onForm)／[保存証拠](evidence/2502/20261011T044840325888Z/06.json)（取得 2026-10-11T04:48:48.330186+00:00）：様への報告書「アサヒスーパーレポート」 統合報告書 ※環境への配慮から冊子版は発行しておりません。 件名 ご意見・ご質問がございましたらこちらへお願いします。 メールアドレス （半角英数字） ※携帯電話メール以外のアドレスをご記入ください。 確認用メールアドレス （半角英数字） ※確認のため、もう一度メールアドレスのご入力をお願いします。メールアドレスが誤っておりますと、ご回答を差し上げ

### 2503 キリンホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://faq.kirin.co.jp/form/kh_03.html)／[保存証拠](evidence/2503/20261011T044841375105Z/02.json)（取得 2026-10-11T04:48:44.171712+00:00）：、上記の「お問い合わせに関するご注意事項」にご同意いただく必要があります。 同意する お問い合わせ分類 必須 優待品について 配当金について 株式事務について 決算・IR全般について その他 タイトル（50文字以内） 必須 お問い合わせ内容（1,000文字以内） 必須 メールアドレス 必須 携帯メール以外のアドレスをご記入ください。 間違ったアドレスを記入されますとご返事ができな
- [公式ページ](https://www.kirinholdings.com/jp/)／[保存証拠](evidence/2503/20261011T044841375105Z/01.json)（取得 2026-10-11T04:48:41.941912+00:00）：・株式取扱規程 サステナビリティ関連情報 CSV担当役員メッセージ 環境報告書 外部評価 ESGデータブック サステナブルファイナンス その他 よくあるご質問 IRお問い合わせ 電子公告 免責事項 閉じる 採用情報 採用情報 グループ会社採用情報 閉じる ニュースルーム ニュースルーム メディアキット メディア・報道関係お問い合わせ先 閉じる お問い合わせ 商品情報サイト 

### 2531 宝ホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IRページから form と記載されたIR問い合わせページへの案内を確認。取得先は見出しだけで実入力欄はない。

根拠：

- [公式ページ](https://ir.takara.co.jp/form/ja/Contact.html)／[保存証拠](evidence/2531/20261011T044843160760Z/02.json)（取得 2026-10-11T04:48:47.044253+00:00）：IRお問合せ \| 宝ホールディングス株式会社 \| form IRお問合せ IRお問合せ Copyright(C) TAKARA HOLDINGS INC. All Right Reserved.
- [公式ページ](https://www.takara.co.jp/)／[保存証拠](evidence/2531/20261011T044843160760Z/01.json)（取得 2026-10-11T04:48:43.830037+00:00）：業績 財務データ 主要財務指標 セグメント別営業概況 IRニュース 個人投資家の皆様へ サポート よくあるご質問 ディスクロージャー ポリシー ご利用上の注意 IRお問い合わせ サステナビリティ 閉じる サステナビリティ トップメッセージ サステナビリティ・ポリシー 中長期目標 11の重要課題（マテリアリティ） 環境 酒類メーカーとしての責任 豊かな食生活 新規領域での価値

### 2533 オエノンホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IRお問い合わせ先ページが一般お客様フォームを直接案内。対応する実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.oenon.jp/ir/contact.html)／[保存証拠](evidence/2533/20261011T044843641428Z/03.json)（取得 2026-10-11T04:48:47.047383+00:00）：債情報 IRカレンダー 株主総会 定款・株式取扱規則 電子公告 個人投資家の皆様へ ホーム IR情報 IRお問い合わせ先 ここから本文です IRお問い合わせ先 ウェブサイトからのお問い合わせ お問い合わせフォームはこちら よくあるご質問 株主・投資家の皆様からいただくお問い合わせの中で、よくあるご質問をわかりやすく解説しています。 よくあるご質問はこちら 株式事務手続きのご案内 株式事務
- [公式ページ](https://www.oenon.jp/ir/information/)／[保存証拠](evidence/2533/20261011T044843641428Z/02.json)（取得 2026-10-11T04:48:45.785217+00:00）：。 定款・株式取扱規則 定款・株式取扱規則をご覧いただけます。 電子公告 電子公告をご覧いただけます。 株価情報 新着IR情報 最新の決算資料 よくあるご質問 IRお問い合わせ先 IRメール配信のご登録 ディスクロージャーポリシー 免責条項 IRサイトマップ 注目ページ TOP5 （2026年6月現在） 株主還元・配当金 最新の決算資料 個人投資家向け会社説明会 決算短信 決

### 254A ＡＩフュージョンキャピタルグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://aifcg.jp/contact/)／[保存証拠](evidence/254A/20261011T044845401677Z/05.json)（取得 2026-10-11T04:48:54.604638+00:00）：資本提携の検討に関するお問い合わせ 当社との事業提携の検討に関するお問い合わせ M&Aのパートナーの検討に関するお問い合わせ M&Aの検討に関するお問い合わせ IR・取材等に関するお問合せ 株主優待に関するお問い合わせ その他のお問い合わせ お問い合わせ内容 必須 check 個人情報の取り扱いについて にご同意頂いた上で、 下記ボタンよりお申し込みを完了ください。
- [公式ページ](https://aifcg.jp/contact/)／[保存証拠](evidence/254A/20261011T044845401677Z/05.json)（取得 2026-10-11T04:48:54.604638+00:00）：公告 決算情報等 報告書等 株主総会資料 代表メッセージ ロゴの由来 会社概要 TOP > お問い合わせ お問い合わせ Contact 氏名 必須 かな 必須 会社名 必須 電話番号 必須 E-mail 必須 確認用E-mail 必須 ご質問項目 必須 当社との資本提携の検討に関するお問い合わせ 当社との事業提携の検討に関するお問い合わせ M&Aのパートナーの検討に関す

### 2573 北海道コカ・コーラボトリング

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 12歳以下の利用には保護者についての案内がある。個人投資家全般の受付制限とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用フォームの公式案内はあるが、保存された実入力欄はない。

根拠：

- [公式ページ](https://www.hokkaido.ccbc.co.jp/form/ir-contact/)／[保存証拠](evidence/2573/20261011T044849539903Z/05.json)（取得 2026-10-11T04:49:02.790784+00:00）：IR情報に関するお問い合わせ｜北海道コカ･コーラボトリング株式会社 トップ 企業情報 企業情報TOP トップメッセージ ビジョン 会社概要 理念・指針 歴史/沿革 事業所一覧 グループ会社 コカ･コーラシステム KORE サプラ
- [公式ページ](https://www.hokkaido.ccbc.co.jp/form/ir-contact/)／[保存証拠](evidence/2573/20261011T044849539903Z/05.json)（取得 2026-10-11T04:49:02.790784+00:00）：お客さま個人宛にお送りするものですので、弊社からのお返事のメールにつきましては、一部または全部を転載、二次利用する事はご遠慮くださいますようお願いいたします。 12歳以下の方は、保護者の方を通じてお問い合わせいただきますようお願いいたします。 Contact お問い合わせ お問い合わせ・ご相談はこちらから トップ お知らせ ニュースリリース 採用情報 工場見学 お問い

### 2585 ライフドリンク　カンパニー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://form.movabletype.net/FFFE927C-1D05-11EC-A1F9-282636F7A6C0?embed=true)／[保存証拠](evidence/2585/20261011T044851636328Z/05.json)（取得 2026-10-11T04:48:59.133935+00:00）：上記の「IRに関するお問い合わせ ご注意事項」に同意しますか？ 必須 同意します。 タイトル（要点） 必須 30文字以内でご入力ください。 IRに関するお問合せ内容 必須 ※1500文字以内でご入力ください。 お名前 必須 郵便番号 必須 都道府県 必須 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千

### 2586 フルッタフルッタ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 決算発表前2週間の沈黙期間には決算・業績に関する問い合わせへの回答を差し控える。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.frutafruta.com/ir_info/ircontact/)／[保存証拠](evidence/2586/20261011T044853574799Z/02.json)（取得 2026-10-11T04:48:57.007304+00:00）：IRお問合わせ - アサイーのフルッタフルッタ オフィシャルサイト ｜ アサイーのフルッタフルッタ オフィシャルサイト IRお問合わせ - アサイーのフルッタフルッタ オフィシャルサイト JA EN MENU CL
- [公式ページ](https://www.frutafruta.com/ir_info/ircontact/)／[保存証拠](evidence/2586/20261011T044853574799Z/02.json)（取得 2026-10-11T04:48:57.007304+00:00）：転載、二次利用することは固くお断り致します。 当社は、決算発表準備期間中に未発表の決算情報が漏洩することを防ぎ、情報開示の公平性を確保するため、 決算発表日の前2週間を「沈黙期間」とし、決算や業績に関するお問合わせに対するコメントのご提供、 個別IRミーティングの実施を控えさせていただきます。ご理解いただけますようお願いします。 ただし、期間中に発生した事象が適時
- [公式ページ](https://www.frutafruta.com/)／[保存証拠](evidence/2586/20261011T044853574799Z/01.json)（取得 2026-10-11T04:48:55.370348+00:00）：AY OUR TOMORROW IR News CSVの取り組み 株主・投資家の皆様へ 会社案内 財務情報 株式情報 株価情報 IRライブラリ よくあるご質問 IRお問合わせ IR情報 IR 情報TOPページ OUR TODAY OUR YESTERDAY OUR TOMORROW IR News CSVの取り組み 株主・投資家の皆様へ 会社案内 財務情報 株式情報 株価

### 2587 サントリービバレッジ＆フード

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://ssl1.suntory.co.jp/apl/btcr/cp/CSUNF1307031/form)／[保存証拠](evidence/2587/20261011T044854351620Z/03.json)（取得 2026-10-11T04:48:57.199312+00:00）：IRお問い合わせ IRお問い合わせ お客様センター （Q&A・お問い合わせ） ※お返事までお時間をいただく場合や、お返事を差し上げられない場合がございます。 ●IRに関するお問い合わせ ご注意事項 ・受付時間内に順次対応させていただきます（メール受付時間：9:00～17:00、土・日・祝日を除く）。 お問い合わせの内容によりましては、お時間を頂戴する場合やお返事を差し上げられない場合、書面や電
- [公式ページ](https://www.suntory.co.jp/softdrink/ir/)／[保存証拠](evidence/2587/20261011T044854351620Z/02.json)（取得 2026-10-11T04:48:55.741044+00:00）： 株主・投資家の皆様へ 数字でひも解くサントリービバレッジ＆フード サントリービバレッジ＆フードとは 株主さま向けイベント 株主優待について IRよくある質問 IRお問い合わせ 免責事項 IRサイトマップ 電子公告 IRメール配信登録 環境活動 研究開発 事業内容 株主・投資家情報サイトマップ × 経営情報 トップメッセージ 役員一覧 企業理念・中期経営戦略・中期経営計画 

### 2588 プレミアムウォーターホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://premiumwater-hd.co.jp/contact/)／[保存証拠](evidence/2588/20261011T044855699127Z/03.json)（取得 2026-10-11T04:48:58.781972+00:00）：必須 お問い合わせ先 お問い合わせ先を選択してください IR（株主・投資家情報）について 広報・PRについて プレミアムウォーターについて その他当社グループの製品について 採用について 当社のビジネス（アライアンスのご提案など）について その他について 必須 お名前 必須 フリガナ 必

### 2593 伊藤園

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 商品やキャンペーンは別のお客様相談室を案内。IRフォームは優待専用とは記載されていない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.itoen.co.jp/form/inquiry-ir/)／[保存証拠](evidence/2593/20261011T044857501461Z/02.json)（取得 2026-10-11T04:48:59.412852+00:00）：ご注意事項] お問い合わせへのご回答は、営業時間内に対応させていただきます。 営業時間：9:00～17:00(土・日・祝日および夏期・年末年始の休業日を除く) IR以外のお問い合わせ（商品やキャンペーンなど）に関しては、 お客様相談室 のページをご参照ください。 内容によりお返事を差し上げられない場合、またはお返事にお時間をいただく場合があります。予めご了承いただきますようお願いします。 お問い合わせの内
- [公式ページ](https://www.itoen.co.jp/form/inquiry-ir/)／[保存証拠](evidence/2593/20261011T044857501461Z/02.json)（取得 2026-10-11T04:48:59.412852+00:00）：ご注意事項] お問い合わせへのご回答は、営業時間内に対応させていただきます。 営業時間：9:00～17:00(土・日・祝日および夏期・年末年始の休業日を除く) IR以外のお問い合わせ（商品やキャンペーンなど）に関しては、 お客様相談室 のページをご参照ください。 内容によりお返事を差し上げられない場合、またはお返事にお時間をいただく場合があります。予めご了承いただきますようお願い
- [公式ページ](https://www.itoen.co.jp/)／[保存証拠](evidence/2593/20261011T044857501461Z/01.json)（取得 2026-10-11T04:48:58.225387+00:00）：エールプロジェクト」 一覧を見る 一覧を見る IR・投資家情報 採用サイト 商品情報サイト 自動販売機 お問い合わせ 商品に関するお問い合わせ（お客様相談室） IRに関するお問い合わせ その他のお問い合わせ 企業情報 サステナビリティ 健康価値の創造 研究開発 IR・投資家情報 ニュースルーム ⾃動販売機設置のご提案 採用サイト プライバシーポリシー ソーシャルメディア・ポリシー 

### 2594 キーコーヒー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.keycoffee.co.jp/company/ir/contact/)／[保存証拠](evidence/2594/20261011T044858187691Z/03.json)（取得 2026-10-11T04:49:00.900479+00:00）：IR関連のお問い合わせ \| IR \| 企業・IR情報 \| キーコーヒー株式会社 商品 コーヒーを知る・楽しむ コミュニティ 店舗 セミナー サステナビリティ 企業・IR お取引をご検討のお客様 商品カテゴリから探す ブラン
- [公式ページ](https://www.keycoffee.co.jp/company/)／[保存証拠](evidence/2594/20261011T044858187691Z/02.json)（取得 2026-10-11T04:48:59.561341+00:00）：個人投資家の皆さまへ IRニュース IRライブラリ・IRイベント 財務・業績報告 株主優待制度 株式情報 コーポレート・ガバナンス ディスクロージャーポリシー IR関連のお問い合わせ お取引をご検討のお客様 採用情報 ENGLISH オンラインショップで 商品をご購入の方はこちら お問い合わせ 日本語 ／ ENGLISH 検索 公式オンラインショップ ログイン カート メニュー 

### 2612 かどや製油

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kadoya.com/contact/page01.html)／[保存証拠](evidence/2612/20261011T044900219491Z/04.json)（取得 2026-10-11T04:49:05.239405+00:00）：お名前 必須 ふりがな 必須 件名 必須 選択 商品に関して 広告・キャンペーンに関して IRに関して 個人情報に関して 人事・採用に関して その他 商品について 商品名： 容量： 賞味期限： メールアドレス 必須 ドメイン指定受信をされている方は「@kadoya.com」から受信できるよう設定をお願

### 261A 日水コン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 組織名を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://reg34.smp.ne.jp/regist/is?SMPFORM=qgki-mclfsb-7dba4524d69aec7e84d1aab3348cfb97)／[保存証拠](evidence/261A/20261011T044901603377Z/02.json)（取得 2026-10-11T04:49:04.558242+00:00）：ご質問区分 必須 選択してください 技術・サービス ニュースリリース IR 採用 その他 お問合せ内容（全角1,024文字以内） 必須 お名前（全角32文字以内） 必須 組織名（全角32文字以内） 必須 部署名（全角32文字以内） E-mailアドレス（半角文字） 必須 確認用 電話番号
- [公式ページ](https://reg34.smp.ne.jp/regist/is?SMPFORM=qgki-mclfsb-7dba4524d69aec7e84d1aab3348cfb97)／[保存証拠](evidence/261A/20261011T044901603377Z/02.json)（取得 2026-10-11T04:49:04.558242+00:00）： 必須 選択してください 技術・サービス ニュースリリース IR 採用 その他 お問合せ内容（全角1,024文字以内） 必須 お名前（全角32文字以内） 必須 組織名（全角32文字以内） 必須 部署名（全角32文字以内） E-mailアドレス（半角文字） 必須 確認用 電話番号（半角数字：ハイフン不要） ご登録いただいた情報は、 当社の 個人情報保護方針 に従って 管理いたします。 必ずご
- [公式ページ](https://www.nissuicon.co.jp/)／[保存証拠](evidence/261A/20261011T044901603377Z/01.json)（取得 2026-10-11T04:49:03.025103+00:00）：信 有価証券報告書 決算説明資料 その他IR資料 財務ハイライト 財務ハイライト IRカレンダー IRカレンダー よくあるご質問 よくあるご質問 IRニュース IRお問合せ 電子公告 免責事項 企業情報 企業情報 トップメッセージ 経営理念 経営戦略 数字で見る日水コン 経営資本 人的資本 知的資本 関係資本 経営基盤 ガバナンス マネジメントシステム 健康経営 技術情

### 265A Ｈｍｃｏｍｍ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://hmcom.co.jp/ir/inquiry/)／[保存証拠](evidence/265A/20261011T044908783363Z/03.json)（取得 2026-10-11T04:49:11.885272+00:00）：IR お問い合わせ \| Hmcomm株式会社 News Solution Company IR Careers Contact News TOP ブログ（AIコンサルティング） ブログ(異常検知) ブログ(音声認識) 
- [公式ページ](https://hmcom.co.jp/ir/)／[保存証拠](evidence/265A/20261011T044908783363Z/02.json)（取得 2026-10-11T04:49:10.598041+00:00）：報告書 決算説明資料 その他IR資料 株式について 株式情報 株主総会 株価情報 財務ハイライト More IRカレンダー More よくあるご質問 More IRお問い合わせ 電子公告 免責事項 Home IR情報 Contact お気軽にお問い合わせください Careers 一緒に「創出」しませんか？ Please follow our story on Faceboo

### 2667 イメージ　ワン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 企業名を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.imageone.co.jp/inquiry/general/)／[保存証拠](evidence/2667/20261011T044913861054Z/06.json)（取得 2026-10-11T04:49:20.571879+00:00）：お問合せ内容 必須 お問合せ内容を選択してください IRに関するお問合せ（IRに関して） 採用に関するお問合せ その他 お名前 必須 お名前（カナ） 必須 企業名 必須 メールアドレス 必須 電話番号 必須 備考 入力フォームにご入力いただいたお客さまのお名前・電話番号・E-mailアド
- [公式ページ](https://www.imageone.co.jp/inquiry/general/)／[保存証拠](evidence/2667/20261011T044913861054Z/06.json)（取得 2026-10-11T04:49:20.571879+00:00）：て お問合せ内容 必須 お問合せ内容を選択してください IRに関するお問合せ（IRに関して） 採用に関するお問合せ その他 お名前 必須 お名前（カナ） 必須 企業名 必須 メールアドレス 必須 電話番号 必須 備考 入力フォームにご入力いただいたお客さまのお名前・電話番号・E-mailアドレスなどの個人情報は、お客さまのお問い合せに対し、当社より回答させていただくため

### 2674 ハードオフコーポレーション

確認：IRメール確認。個人条件の明示未確認。未確認。

公開IRメール：`ir-info@hardoff.co.jp`。

注意・未確認：公式IRページに「IRに関する お問い合わせ」と表示された mailto の exact target でメール宛先を確認。本文にはアドレス自体が表示されていない。実送信・返信は未検証。 / IR表示の mailto 宛先は確認したが、保存ページに上場会社の日本語正式名称又は銘柄コードがなく、収集時の identity_status=unverified を解消できない。上場主体の同一性が追加確認待ち。

根拠：

- [公式ページ](https://www.hardoff.co.jp/ir/)／[保存証拠](evidence/2674/20261011T044920581927Z/02.json)（取得 2026-10-11T04:49:23.712949+00:00）：告書等 株主通信 決算説明会資料・動画 株主総会関連資料 月次売上高・出店状況 適時開示情報 電子公告 IRカレンダー ディスクロージャー ポリシー 免責事項 IRに関する お問い合わせ TOP IR情報 お客様相談室 店内撮影およびSNS投稿について サイトマップ リンク集 古物営業法に基づく表示 反社会的勢力に対する基本方針 プライバシーポリシー X English 中文 ©2021 HARD OFF CORPORAT

### 2678 アスクル

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.askul.co.jp/iqr/corpInquiryInputView/?inqKbn=2)／[保存証拠](evidence/2678/20261011T044924776296Z/03.json)（取得 2026-10-11T04:49:30.043193+00:00）：IRに関するお問い合わせ \| アスクル株式会社 企業サイト 企業情報トップへ 社長メッセージ アスクルWAY 沿革 会社概要 ガバナンス体制 主要事業所・地図 事業・サービストップへ ビジネスモデル サービス一覧 IR情報ト
- [公式ページ](https://www.askul.co.jp/corp/investor/)／[保存証拠](evidence/2678/20261011T044924776296Z/02.json)（取得 2026-10-11T04:49:29.580504+00:00）： 株価情報 電子公告 よりよく知って 頂くために よりよく知って頂くために IRニュース 個人投資家の皆さまへ IRカレンダー IRメール配信 用語集 FAQ IRに関するお問い合わせ 免責事項 個人投資家の 皆さまへ IRメール配信 ニュース 環境・社会活動 採用情報 search 検索ボックスを開く close 検索ボックスを閉じる En 検索キーワードを入力してください TO

### 2689 オルバディーブイエックスヘルスケア

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.olbadvx.jp/contact/)／[保存証拠](evidence/2689/20261011T044928951371Z/05.json)（取得 2026-10-11T04:49:40.056498+00:00）：お問い合わせ項目 必須 選択してください サービス・商品に関して 会社情報に関して IRに関して ウェブサイトに関して 採用について その他 氏名（漢字） 必須 氏名（かな） 必須 メールアドレス(半角英数字) 必須 メールアドレス(半角英数字)確認用 ＊コピー・貼り付け不可 必須 お問い合わせ

### 268A リガク・ホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://rigaku-holdings.com/contact/)／[保存証拠](evidence/268A/20261011T044929504141Z/03.json)（取得 2026-10-11T04:49:34.972597+00:00）：部署より回答させていただきます。 お問い合わせの内容によっては、回答が遅れることがあります。あらかじめご了承ください。 カテゴリ 選択してください 広報 採用 調達 IR 人権（差別/ハラスメント等） その他 ご所属 お名前 姓 名 ふりがな せい めい メールアドレス お電話番号 お問合せ内容
- [公式ページ](https://rigaku-holdings.com/ir/)／[保存証拠](evidence/268A/20261011T044929504141Z/02.json)（取得 2026-10-11T04:49:33.969071+00:00）：示資料 株主総会関連資料 適時開示情報 統合報告書 株式の状況 株主メモ 株主総会情報 株価情報 IRカレンダー FAQ ディスクロージャーポリシー 免責事項 IRについてのお問い合わせ IRメール配信 電子公告 経営情報 中期経営計画 コーポレート・ガバナンス 財務情報 経営成績 財政状態 キャッシュ・フローの状況 IRライブラリ IRライブラリ 決算関連資料一覧 決算短信 決算説

### 2700 木徳神糧

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 会社・商品・採用フォームとは別の【ＩＲ】フォームリンクを確認。対応する実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.kitoku-shinryo.co.jp/ja/contact.html)／[保存証拠](evidence/2700/20261011T044937482935Z/05.json)（取得 2026-10-11T04:49:45.021740+00:00）：お問い合わせ 新規お取引や広報・ＣＳＲ活動について 【会社】お問い合わせフォーム IR（投資）に関するお問い合わせ 経営計画や業績などＩＲ（投資）情報について 【ＩＲ】お問い合わせフォーム 商品に関するお問い合わせ 商品や販売店、品質や不具合について 【商品】お問い合わせフォーム →オンラインショップKOMETS(コメッツ)に 関する お問い合わせはこちら 採用に関するお問い合わせ 募

### 2708 久世

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kuze.co.jp/contact/form2.html)／[保存証拠](evidence/2708/20261011T044940979327Z/05.json)（取得 2026-10-11T04:49:45.732491+00:00）：お問い合わせ（IR情報について）｜株式会社久世 お問い合わせ IR情報について 情報の入力 入力 内容のご確認 送信完了 下記の項目にご記入いただき、「入力内容の確認」ボタンを押して確認画面へお進みください。 当フォームからのお問い
- [公式ページ](https://www.kuze.co.jp/contact/form2.html)／[保存証拠](evidence/2708/20261011T044940979327Z/05.json)（取得 2026-10-11T04:49:45.732491+00:00）：力内容の確認」ボタンを押して確認画面へお進みください。 当フォームからのお問い合わせにつきましては、お返事に数日かかる場合がございますので予めご了承ください。 個人／法人 個人のお客様 法人のお客様 会社名（店名）・部署名 ［例］株式会社久世 東京支店 営業部 お名前 ［例］久世 太郎 お名前フリガナ ［例］クゼ タロウ メールアドレス ご住所 郵便番号を入力すると市町村まで自動入力されます 郵
- [公式ページ](https://www.kuze.co.jp/contact/)／[保存証拠](evidence/2708/20261011T044940979327Z/03.json)（取得 2026-10-11T04:49:43.596069+00:00）：特徴 会社案内 IR情報 商品・サポート レシピ検索 採用情報 お問い合わせ はじめてのお客様 ご注文はこちら お問い合わせ お問い合わせ先 はじめてのお客様 IR情報について その他お問い合わせ プライバシーポリシー お問い合わせ はじめてのお客様 IR情報について その他お問い合わせ カスタマーハラスメントに対する基本方針 Home お問い合わせ このページの上部へ お

### 2730 エディオン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.edion.co.jp/contact/corporate)／[保存証拠](evidence/2730/20261011T044946090865Z/05.json)（取得 2026-10-11T04:49:52.471694+00:00）：るお問い合わせ お問い合わせいただきました内容には、迅速にお答えできるよう努めますが、ご返答までにお時間をいただく場合や、お答えできない場合がございます。また、お問い合わせ内容によっては、お電話にてご連絡させていただく場合もございますので、あらかじめご了承ください。 店舗の営業や商品に関するお問い合わせは、直接店舗にご連絡いただきますようお願い申し上げます。 ※【ご注意】こ
- [公式ページ](https://www.edion.co.jp/contact)／[保存証拠](evidence/2730/20261011T044946090865Z/04.json)（取得 2026-10-11T04:49:51.302199+00:00）：株主還元 株価情報 店舗一覧 店舗検索 オンラインショップ 採用情報 お問い合わせ 閉じる お問い合わせ お問い合わせ 株式会社エディオンに関するお問い合わせ 株式会社エディオンの「会社概要」「事業」「サービス」「ＣＳＲ・社会貢献活動」「投資家情報」「採用情報」等に関するお問い合わせはこちらからお願いいたします。 エディオンネットショップ・エディオンアプリに関するお問い合わせ エディオンネットショップ、エディオンアプリに関するお問い合わせは、こちらからお願いいたします。 リフォーム事業に関するお問い合わせ リ

### 2733 あらた

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir-info@arata-gr.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.arata-gr.jp/contact/)／[保存証拠](evidence/2733/20261011T044946557889Z/04.json)（取得 2026-10-11T04:49:50.781000+00:00）：IR以外のお問い合わせにつきましては、ご回答いたしかねます。 非公開情報・その他制限事項について お問い合わせの内容によってはお答えしかねる場合もございます。 株式会社あらた IR担当 E-mail：ir-info@arata-gr.jp 採用に関する お問い合わせ 氏名やお問い合わせ内容を記入の上、下記メールアドレスにお送りください。 ご回答について お問い合わせの内容、対応状況次第では、ご回答にお時間を頂く場合があります。 採用以
- [公式ページ](https://www.arata-gr.jp/contact/)／[保存証拠](evidence/2733/20261011T044946557889Z/04.json)（取得 2026-10-11T04:49:50.781000+00:00）：送りください。 ご回答について お問い合わせの内容、対応状況次第では、ご回答にお時間を頂く場合があります。 IR以外のお問い合わせについて 誠に恐れ入りますが、IR以外のお問い合わせにつきましては、ご回答いたしかねます。 非公開情報・その他制限事項について お問い合わせの内容によってはお答えしかねる場合もございます。 株式会社あらた IR担当 E-mail：ir-info@arata-gr.jp 採用に関する お問い合わせ 氏名やお問い合わせ内容を記入の上、下記メールアドレスにお送りください。 ご回答について お問い合わせの内容、対応状況次第では、ご回答にお時間を頂く場合があります。 採用以

### 2737 トーメンデバイス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@tomendevices.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.tomendevices.co.jp/inquiry/)／[保存証拠](evidence/2737/20261011T044951309926Z/03.json)（取得 2026-10-11T04:49:54.079429+00:00）：devices.co.jp AI向け商品に関するお問合せは、こちらから承ります。 aishohin@tomendevices.co.jp IRに関するお問合せ IR情報に関するお問合せは、こちらから承ります。 ir@tomendevices.co.jp 営業時間 ： 平日（月曜日～金曜日）9:00～17:30 ※土日、祝日および年末年始は休業となります。 企業情報 ご挨拶 MISSION・VISION・V
- [公式ページ](https://www.tomendevices.co.jp/inquiry/)／[保存証拠](evidence/2737/20261011T044951309926Z/03.json)（取得 2026-10-11T04:49:54.079429+00:00）：ます。 saiyo@tomendevices.co.jp 商品に関するお問合せ 商品に関するお問合せは、こちらから承ります。 shohin@tomendevices.co.jp AI向け商品に関するお問合せは、こちらから承ります。 aishohin@tomendevices.co.jp IRに関するお問合せ IR情報に関するお問合せは、こちらから承ります。 ir@tomendevices.co.jp 営業時間 ： 平日（月曜日～金曜日）9:00～17:30 ※土日、祝日および年末年始は休業となります。 企業情報 ご挨拶 MISSION・VISION・VALUE 会社概要 沿革 拠点 組織図 IS

### 2750 石光商事

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ishimitsu.co.jp/inquiry/)／[保存証拠](evidence/2750/20261011T044954473140Z/03.json)（取得 2026-10-11T04:49:58.377989+00:00）：78-861-7791 必須 ご用件 ご用件を選択してください。 コーヒー・飲料関連の取扱商品について 食品関連の取扱商品について 日本からの輸出商品について IR・会社全般について 採用について 必須 お問い合わせ内容 必須 送信確認 上記送信内容を確認したらチェックを入れてください 確認画面へ

### 2762 ＳＡＮＫＯ　ＭＡＲＫＥＴＩＮＧ　ＦＯＯＤＳ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.sankofoods.com/contact/index.php?type=2)／[保存証拠](evidence/2762/20261011T045002163959Z/03.json)（取得 2026-10-11T04:50:05.183976+00:00）：お問い合わせ種別 必須 お客様の声 IR・株主優待に関するお問い合わせ 採用に関するお問い合わせ FC加盟店に関するお問い合わせ 店舗物件情報提供 その他のお問い合わせ お名前 必須 姓 名 フリガナ 必須 セイ メイ 郵便番号 必須 - 住所 必須 都道府県 選択して
- [公式ページ](https://www.sankofoods.com/ir/information/)／[保存証拠](evidence/2762/20261011T045002163959Z/02.json)（取得 2026-10-11T04:50:04.007042+00:00）：ン 企業や店舗に関するリリースは ニュースリリース をご覧ください。 最新IR資料 一括ダウンロード IRサポート 電子公告 IRインフォメーション 免責事項 IRに関するお問い合わせ ページトップへ プライバシーポリシー サイトマップ Copyright© SANKO MARKETING FOODS All rights Reserved.

### 2764 ひらまつ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページはフォーム受付を明示するが、保存された実入力欄はない。

根拠：

- [公式ページ](https://www.hiramatsu.co.jp/ir/inquiry.html)／[保存証拠](evidence/2764/20261011T045003514554Z/03.json)（取得 2026-10-11T04:50:06.836624+00:00）：ITY IR情報 採用情報 企業情報 JP EN Investor Relations 投資家情報 お問合せ 下記お問合せフォームにご記入の上ご送信ください。 ひらまつIR お問合せフォーム お問い合わせ内容によっては、当社より回答できない、または回答にお時間をいただく場合がございますのでご注意ください。 当社からお送りした内容は、お問い合わせいただいた方個人への回答となります。その一部

### 2768 双日

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.sojitz.com/jp/contact/ir/input.html)／[保存証拠](evidence/2768/20261011T045007870180Z/04.json)（取得 2026-10-11T04:50:12.151451+00:00）：投資家情報に関するお問い合わせ｜お問い合わせ｜双日株式会社 Who we are 企業情報 企業情報 TOP 社長メッセージ 企業理念 経営戦略 中期経営計画 人材戦略 DX戦略 会社概要 役員 組織図 コーポレート・ガバナンス 
- [公式ページ](https://www.sojitz.com/jp/contact/)／[保存証拠](evidence/2768/20261011T045007870180Z/03.json)（取得 2026-10-11T04:50:11.134744+00:00）：せフォーム お問い合わせの内容にあわせ下記フォームからお問い合わせください。 事業・商品・サービス に関するお問い合わせ 双日全般・各営業本部へのお問い合わせ 投資家情報 に関するお問い合わせ 業績・決算発表など ニュースリリース に関するお問い合わせ サステナビリティ（CSR） に関するお問い合わせ ESG・社会貢献に関する取り組み 人権侵害に関する通報 詳細をみる コンプライアンス に

### 276A ククレブ・アドバイザーズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://ccreb.jp/contact/)／[保存証拠](evidence/276A/20261011T045008692134Z/03.json)（取得 2026-10-11T04:50:14.043519+00:00）：お問い合わせ種別 選択してください 会社について 広報・IRについて 弊社のサービスについて その他 お名前（漢字） お名前（フリガナ） 会社名（団体名） 会社部署名 メールアドレス 電話番号 お問い合わせ内容詳細 個人情報の取り扱いに関しては 「プライバシーポリシー

### 2778 パレモ・ホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://palemo.co.jp/contact)／[保存証拠](evidence/2778/20261011T045010650508Z/03.json)（取得 2026-10-11T04:50:15.691261+00:00）：お問い合わせ内容 必須 IR・株式関連 商品・ショップ関連 リクルート関連 その他 お名前 必須 ふりがな 必須 メールアドレス 必須 ※「@palemo.co.jp」からのメールを受信できるよう、あらかじめ受信許可設定をお願いいたします

### 2780 コメ兵ホールディングス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@komehyo.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://komehyohds.com/ir/ircontact/index.html)／[保存証拠](evidence/2780/20261011T045012538542Z/03.json)（取得 2026-10-11T04:50:16.509260+00:00）：問い合わせ 個人投資家の皆様へ 経営方針 コーポレート・ガバナンス IRイベント 業績・財務情報 IR資料室 株式・社債情報 よくあるご質問 IRお問い合わせ IRに関するお問い合わせ、取材のお申し込みは、下記財務企画部IRGまでお願いいたします。 株式会社コメ兵ホールディングス 財務企画部 IRG 電 話：052-249-5366 E-mail：ir@komehyo.co.jp 住 所：〒460-0011 名古屋市中区大
- [公式ページ](https://komehyohds.com/ir/ircontact/index.html)／[保存証拠](evidence/2780/20261011T045012538542Z/03.json)（取得 2026-10-11T04:50:16.509260+00:00）：） IRお問い合わせ 個人投資家の皆様へ 経営方針 コーポレート・ガバナンス IRイベント 業績・財務情報 IR資料室 株式・社債情報 よくあるご質問 IRお問い合わせ IRに関するお問い合わせ、取材のお申し込みは、下記財務企画部IRGまでお願いいたします。 株式会社コメ兵ホールディングス 財務企画部 IRG 電 話：052-249-5366 E-mail：ir@komehyo.co.jp 住 所：〒460-0011 名古屋市中区大須三丁目38番5号 See-Stepビル4F IRカレンダー IRサイトマップ IRお問い合わせ 免責事項 株価情報 電子公告 IRサイトの使い方
- [公式ページ](https://komehyohds.com/ir/)／[保存証拠](evidence/2780/20261011T045012538542Z/02.json)（取得 2026-10-11T04:50:15.841355+00:00）：株式基本情報 株主還元（配当等） 株主の状況 株式事務手続きのご案内 社債・格付情報 アナリスト・カバレッジ よくあるご質問 よくあるご質問 IRサイトマップ IRお問い合わせ 免責事項 株価情報 電子公告 IRサイトの使い方 IRカレンダー

### 2789 カルラ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`karula@re-marumatu.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](http://www.re-marumatu.co.jp/tousikajyouhou/IRotiawse.html)／[保存証拠](evidence/2789/20261011T045016118328Z/03.json)（取得 2026-10-11T04:50:18.747152+00:00）：t 店舗連絡先一覧 Shop Contact ホーム お問合せ ホーム > 投資家の皆様へ > IRお問合せ FINANCIER 投資家の皆様へ IRお問合せ ＩＲに関するお問合せ、ご要望は下記までお願いたします。 〒981-3341 宮城県富谷市成田9丁目2-9 株式会社カルラ 電話 022-351-5888 ＦＡＸ 022-351-6500 E-MAIL：karula@re-maruma
- [公式ページ](http://www.re-marumatu.co.jp/tousikajyouhou/IRotiawse.html)／[保存証拠](evidence/2789/20261011T045016118328Z/03.json)（取得 2026-10-11T04:50:18.747152+00:00）： 店舗連絡先一覧 Shop Contact ホーム お問合せ ホーム > 投資家の皆様へ > IRお問合せ FINANCIER 投資家の皆様へ IRお問合せ ＩＲに関するお問合せ、ご要望は下記までお願いたします。 〒981-3341 宮城県富谷市成田9丁目2-9 株式会社カルラ 電話 022-351-5888 ＦＡＸ 022-351-6500 E-MAIL：karula@re-marumatu.co.jp Eメールでのお問い合わせ内容は、できるだけ具体的にお願いたします。 内容によっては、お答えできない場合もありますのでご了承下さい。 尚、皆様からよくお問合せいただく質問を Ｑ＆Ａ にまとめましたので
- [公式ページ](http://www.re-marumatu.co.jp/tousikajyouhou/index.html)／[保存証拠](evidence/2789/20261011T045016118328Z/02.json)（取得 2026-10-11T04:50:17.910910+00:00）：支援いただきますよう、心よりお願い申し上げます。 株主の皆様へ What's New 決算短信 有価証券報告書 売上速報 株主優待 株主総会 電子公告 Q&A IRお問合せ その他重要な開示事項 会社情報 社長あいさつ コンセプト 会社概要 沿革 社名の由来 COMMISSARY 研修センター 投資家の皆様へ 協賛について お店を探す 総合アクセスマップ 事業一覧 和風

### 278A Ｔｅｒｒａ　Ｄｒｏｎｅ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 御社名・部署・担当課を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://terra-drone.net/contact/)／[保存証拠](evidence/278A/20261011T045016668940Z/06.json)（取得 2026-10-11T04:50:22.044829+00:00）：アドレス 必須 メールアドレス（確認） 必須 お問い合わせ項目 ハードウェア製造関連（部品サプライヤー様/商社様等） 取材依頼 広報・PR関連（取材依頼以外） IR・投資家関連 採用・人事関連 土木・測量事業（導入検討・ご利用中の問い合わせ） 点検事業（導入検討・ご利用中の問い合わせ） UTM事業（導入検討・ご利用中の問い合わせ） 防衛事業（導入検討・ご利用中の問い合わせ）
- [公式ページ](https://terra-drone.net/contact/)／[保存証拠](evidence/278A/20261011T045016668940Z/06.json)（取得 2026-10-11T04:50:22.044829+00:00）：問わず、業務上における問題や不正等の相談を受け付けております。 業務上の不正行為については、こちらのフォームのお問い合せ項目にチェックを入れてご連絡ください。 必須 御社名 必須 部署 必須 担当課 必須 お名前 必須 ふりがな 任意 お電話番号 必須 メールアドレス 必須 メールアドレス（確認） 必須 お問い合わせ項目 ハードウェア製造関連（部品サプライヤー様/商社様等） 取材依頼 広報・PR

### 2790 ナフコ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`nafco-ir@nms.nafco.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nafco.tv/contact/)／[保存証拠](evidence/2790/20261011T045017438513Z/04.json)（取得 2026-10-11T04:50:22.985391+00:00）： 採用に関するお問い合わせ recruit@nms.nafco.jp テナント・出店用地募集に関する お問い合わせ kaihatsu@nms.nafco.jp IRに関するお問い合わせ nafco-ir@nms.nafco.jp 電話でのお問い合わせ 店舗に関するお問い合わせ 株式会社ナフコ お客様サポート窓口 093-521-5155 受付時間：10:00～18:00（月～土） 採用に関するお問い合わせ ナフコチェーン本部
- [公式ページ](https://www.nafco.tv/contact/)／[保存証拠](evidence/2790/20261011T045017438513Z/04.json)（取得 2026-10-11T04:50:22.985391+00:00）：す。 商品・サービスの新規ご提案 info@mail.nafco.jp ※ お電話での受付は行っておりません。 店舗に関するお問い合わせ info@mail.nafco.jp 採用に関するお問い合わせ recruit@nms.nafco.jp テナント・出店用地募集に関する お問い合わせ kaihatsu@nms.nafco.jp IRに関するお問い合わせ nafco-ir@nms.nafco.jp 電話でのお問い合わせ 店舗に関するお問い合わせ 株式会社ナフコ お客様サポート窓口 093-521-5155 受付時間：10:00～18:00（月～土） 採用に関するお問い合わせ ナフコチェーン本部

### 2796 ファーマライズホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.pharmarise.com/ir/contact.html)／[保存証拠](evidence/2796/20261011T045019731907Z/02.json)（取得 2026-10-11T04:50:22.568164+00:00）：お問い合わせ内容 ＊ IRに関するお問い合わせ 店舗に関するお問い合わせ その他のお問い合わせ お名前 ＊ フリガナ ＊ ＜全角カナ＞ メールアドレス ＊ ＜半角英数字＞ 【例】abc123@example.com ▼ 確認のため、再入力をお願い
- [公式ページ](https://www.pharmarise.com/)／[保存証拠](evidence/2796/20261011T045019731907Z/01.json)（取得 2026-10-11T04:50:20.831682+00:00）： アナリストレポート IRスケジュール 株式情報 株式事務 株主総会 株主優待 株価情報 電子公告 ディスクロージャーポリシー リスク情報 IRに関するFAQ IRに関するお問合せ IR情報メール配信 採用情報 採用情報トップページ お問合せ 個人情報保護方針 サイトポリシー サイトマップ リンク集 English 健康と幸せを 支えるパートナー ファーマライズは皆様の健康と幸

### 2798 ワイズテーブルコーポレーション

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ystable.co.jp/corporate/contactform_ir.html)／[保存証拠](evidence/2798/20261011T045023033431Z/03.json)（取得 2026-10-11T04:50:25.701508+00:00）：川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 海外 住所2 電話番号 * メールアドレス * メールアドレス確認 * お問い合わせ内容 * ※ ご記入いただきました情報は、Y's table corporationに関する情報のご提供や事務局からのお知らせ以外の目的では使用いたしません。 ※ 個人情報の取扱いに関しては、 プライバシ
- [公式ページ](https://www.ystable.co.jp/corporate/ir/)／[保存証拠](evidence/2798/20261011T045023033431Z/02.json)（取得 2026-10-11T04:50:24.820713+00:00）：主優待に関する質問 株価情報 株式事務のご案内 株主総会 IRライブラリー 決算短信 有価証券報告書 事業報告書 決算説明資料 IRカレンダー よくあるご質問 IRお問い合わせ 電子公告 免責事項 各種お問い合わせ 個人情報取扱規程 株主・投資家の皆様へ 本物を追求し、楽しく心地よい時間と空間創造。 グローバルな感性をもって、 豊かなライフスタイルの提案を日本から世界へ。 

### 2804 ブルドックソース

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://contact.bulldog.jp/ir-contact/)／[保存証拠](evidence/2804/20261011T045023716558Z/06.json)（取得 2026-10-11T04:50:34.995909+00:00）：- - 性別 選択してください 男性 女性 年齢 選択してください 10代以下 20代 30代 40代 50代 60代 70代 80代以上 件名 50文字以内 お問い合わせ内容 2000文字以内 お客様からお預かりした個人情報は、販売管理、商品の発送、アフターサービス、お客様満足度調査、新商品のご案内のために使用いたします。 その他、個人情報の取り扱いに関しましては、 こちら をご覧ください
- [公式ページ](https://www.bulldog.co.jp/ir-contact/)／[保存証拠](evidence/2804/20261011T045023716558Z/04.json)（取得 2026-10-11T04:50:32.324558+00:00）：ます。 また、ご返答を差し上げられない場合もございますので、あらかじめご了承ください。 学園祭協賛 に関してはこちらをご確認ください。 学園祭応援プロジェクト お問い合わせフォームへ 新卒採用 お問い合わせ English 富留得客食品（上海） 有限公司（中文） HOME レシピ 商品情報 ブルドックソース フィロソフィー もっとソースを 知る・楽しむ 会社情報 株主・投資家の 
- [公式ページ](https://www.bulldog.co.jp/ir-contact/)／[保存証拠](evidence/2804/20261011T045023716558Z/04.json)（取得 2026-10-11T04:50:32.324558+00:00）：﻿ IRお問い合わせ｜ブルドックソース株式会社 ブルドックソース株式会社 株主・投資家のみなさまへ IRお問い合わせ IRお問い合わせ IRよくあるご質問 電話でのお問い合わせ インターネットでのお問い合わせ IRよくあ

### 280A ＴＭＨ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 決算日の翌日から決算発表日までの沈黙期間は決算内容の質問回答を差し控える。フォーム受付のみで電話の個別対応は行わない。
- 株主・投資家からの問い合わせへの返信を優先と明示。
- 無断での回答転載・二次利用を禁止する記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IRフォーム受付を明示するが、保存された実入力欄はない。

根拠：

- [公式ページ](https://www.tmh-inc.co.jp/ir/contact/index.html)／[保存証拠](evidence/280A/20261011T045030966942Z/03.json)（取得 2026-10-11T04:50:34.707567+00:00）：させていただきますので、ご理解いただきますようお願いします。 IRに関するお問い合わせにつきましては、公平な情報開示を維持するため、お電話での個別対応は行わず、下記のフォームからの受付のみとさせていただいております。 できる限り迅速に対応いたしますが、内容によってはお時間をいただく場合がございます。また、一部のご質問にはお答えできない場合もございますので、ご了承ください。 なお、以下に
- [公式ページ](https://www.tmh-inc.co.jp/ir/contact/index.html)／[保存証拠](evidence/280A/20261011T045030966942Z/03.json)（取得 2026-10-11T04:50:34.707567+00:00）：問 お問い合わせ メニューを開く お問い合わせ [CONTACT] 当社は、決算情報の漏洩を防ぎ、情報提供の公平性を確保するために、決算日（四半期決算を含む）の翌日から決算発表日までを沈黙期間として定め、IR活動を自粛しております。 当該期間中は、決算内容に関する情報提供や質問に対する回答を差し控えさせていただきますので、ご理解いただきますようお願いします。 IRに関するお問い合わせにつき
- [公式ページ](https://www.tmh-inc.co.jp/ir/contact/index.html)／[保存証拠](evidence/280A/20261011T045030966942Z/03.json)（取得 2026-10-11T04:50:34.707567+00:00）：合わせ 当社サイト以外に記載されている内容に関するご質問 当社の提供サービスに関するお問い合わせ なお、当社からの返信は、株主・投資家の皆様からのお問い合わせに優先して対応しております。回答内容の一部または全体を無断で転載・二次利用することは禁止されております。 Fill out my online form . HOME - お問い合わせ IRニュース IRカレンダー 経営方針・
- [公式ページ](https://www.tmh-inc.co.jp/ir/contact/index.html)／[保存証拠](evidence/280A/20261011T045030966942Z/03.json)（取得 2026-10-11T04:50:34.707567+00:00）：当社の提供サービスに関するお問い合わせ なお、当社からの返信は、株主・投資家の皆様からのお問い合わせに優先して対応しております。回答内容の一部または全体を無断で転載・二次利用することは禁止されております。 Fill out my online form . HOME - お問い合わせ IRニュース IRカレンダー 経営方針・成長戦略 株式について IRライブラリー よくあるご質問 お問
- [公式ページ](https://www.tmh-inc.co.jp/ir/)／[保存証拠](evidence/280A/20261011T045030966942Z/02.json)（取得 2026-10-11T04:50:33.743957+00:00）：rary] 決算短信 有価証券報告書 決算説明会資料 株式について [Stock Information] 株主総会 株価情報 IRカレンダー よくあるご質問 IRお問い合わせ IRニュース IRカレンダー 経営方針・成長戦略 株式について IRライブラリー よくあるご質問 お問い合わせ プライバシーポリシー © 2024 TMH Inc.

### 2810 ハウス食品グループ本社

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`hfg-ir@housefoods.co.jp`。

取得範囲の受付条件：

- 氏名（会社名）・メールアドレス・電話番号を本文に必ず記載と案内。決算発表に関わる業績問い合わせ用の宛先。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://housefoods-group.com/inquiry/index.html)／[保存証拠](evidence/2810/20261011T045031437427Z/07.json)（取得 2026-10-11T04:50:39.399508+00:00）：のお問い合わせやご意見は、内容を正確に承るために、録音させていただいております 業績・決算資料の内容について hfg-ir@housefoods.co.jp ※決算発表に関わる業績についてのお問い合わせ専用メールアドレスです。 ※お問い合わせの際、下記項目を必ず記載ください。 ・氏名（会社名） ・メールアドレス ・電話番号 ※すべてのお問い合わせにご返信できない場合がございます。 ※迷惑メール対策されている場合、またシステ
- [公式ページ](https://housefoods-group.com/inquiry/index.html)／[保存証拠](evidence/2810/20261011T045031437427Z/07.json)（取得 2026-10-11T04:50:39.399508+00:00）：r@housefoods.co.jp ※決算発表に関わる業績についてのお問い合わせ専用メールアドレスです。 ※お問い合わせの際、下記項目を必ず記載ください。 ・氏名（会社名） ・メールアドレス ・電話番号 ※すべてのお問い合わせにご返信できない場合がございます。 ※迷惑メール対策されている場合、またシステム障害の際には、ご返答が届かない可能性がございます。 よくあるご質問
- [公式ページ](https://housefoods-group.com/inquiry/index.html)／[保存証拠](evidence/2810/20261011T045031437427Z/07.json)（取得 2026-10-11T04:50:39.399508+00:00）：やご意見は、内容を正確に承るために、録音させていただいております 株主優待について 06-6788-1214 （総務部） 受付時間：平日の9時〜17時 ※土曜・日曜・祝祭日・夏期休暇・年末年始休暇および創業記念日（11月11日）を除きます ※お電話でのお問い合わせやご意見は、内容を正確に承るために、録音させていただいております 業績・決算資料の内容について hfg-ir@housefoods.co.jp ※決算発表に関わる業績についてのお問い合わせ専用メールアドレスです。 ※お問い合わせの際、下記項目を必ず記載ください。 ・氏名（会社名） ・メールアドレス ・電話番号 ※すべてのお問い合わせにご返信

### 2811 カゴメ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`info@kagome.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.kagome.co.jp/company/ir/contact/)／[保存証拠](evidence/2811/20261011T045031512806Z/03.json)（取得 2026-10-11T04:50:34.801681+00:00）：いたします。 なお、皆様からよくお寄せいただく質問をQ&A形式でまとめましたので、 よくあるご質問 ページも併せてご覧ください。 お問い合わせ先 財務経理本部 財務・IR部 住所 〒103-8461 東京都中央区日本橋浜町3丁目21番1日本橋浜町Ｆタワー 電話、FAX番号 03-5623-8501 （FAX：03-5623-2331） メールでのお問い合わせ info@
- [公式ページ](https://www.kagome.co.jp/company/ir/contact/)／[保存証拠](evidence/2811/20261011T045031512806Z/03.json)（取得 2026-10-11T04:50:34.801681+00:00）：たします。 なお、皆様からよくお寄せいただく質問をQ&A形式でまとめましたので、 よくあるご質問 ページも併せてご覧ください。 お問い合わせ先 財務経理本部 財務・IR部 住所 〒103-8461 東京都中央区日本橋浜町3丁目21番1日本橋浜町Ｆタワー 電話、FAX番号 03-5623-8501 （FAX：03-5623-2331） メールでのお問い合わせ info@kagome.co.jp IR情報 ファン株主のみなさまへ イベント カゴメ記念館見学会 加太菜園見学会 響灘菜園見学会 カゴメ健康応援セミナー 社長と語る会 いわき小名浜菜園見学会 工場見学会 料理教室 野菜生活ファーム富
- [公式ページ](https://www.kagome.co.jp/company/ir/)／[保存証拠](evidence/2811/20261011T045031512806Z/02.json)（取得 2026-10-11T04:50:33.942337+00:00）：主還元（配当等） 株主の状況 株式諸手続きのご案内 社債・格付情報 アナリスト・カバレッジ 電子公告 よくあるご質問 IRカレンダー 受賞歴 IRサイトマップ IRお問い合わせ 免責事項 IRサイトの使い方 ご利用ガイド プライバシーポリシー ソーシャルメディアポリシー コミュニティガイドライン 公式SNS CM・WEB動画ギャラリー ご利用ガイド プライバシーポリシー ソ

### 2814 佐藤食品工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.sato-foods.co.jp/other/contact.html)／[保存証拠](evidence/2814/20261011T045035228444Z/03.json)（取得 2026-10-11T04:50:39.482717+00:00）：。 また、お問い合わせの内容によりご連絡が出来ない場合もありますのでご了承ください。 ■お問い合わせの内容 ※ 製品・ＯＥＭ・お取引について 採用情報について ＩＲについて 通信販売について その他 ■お名前 ※ ■ふりがな ※ ■所属企業・団体名 ※ （“製品・ＯＥＭについて”の場合は必須入力項目となります） ■業種 ■部署 ※ （“製品・ＯＥＭについて”の場合は必須

### 2816 ダイショー

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式サイトのIRお問い合わせリンクと取得先の問い合わせ種類・入力ラベルは確認。実 forms/controls に保存されたのは検索欄だけで、送信フォームの実メール・本文入力欄は未確認。

根拠：

- [公式ページ](https://www.daisho-customer.jp/inquiry/media-shareholders)／[保存証拠](evidence/2816/20261011T045047806411Z/02.json)（取得 2026-10-11T04:50:52.135257+00:00）： \| メディア・株主様 お問い合わせTOP ダイショーHP お問い合わせTOP 商品情報 レシピ キャンペーン 企業情報 オンラインストア お問い合わせTOP お問い合わせフォーム メディア・株主様 メディア・株主様 必須 お問い合わせの種類 メディア・株主様 その他のお問い合わせ 必須 お問い合わせ内容 必須 お名前 姓 名 ふりがな 全角ひらがな せい めい 必須 メールアドレス 必須 メー
- [公式ページ](https://www.daisho.co.jp/)／[保存証拠](evidence/2816/20261011T045047806411Z/01.json)（取得 2026-10-11T04:50:49.183795+00:00）：IRニュース 投資家の皆様へ 経営情報 財務・業績情報 IRライブラリー 株式について IRカレンダー 個人投資家の皆様へ FAQ リスクファクター 電子公告 IRお問い合わせ ENGLISH 中文 Copyright © DAISHO Co., Ltd. All Rights Reserved.

### 2818 ピエトロ

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@pietro.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.pietro.co.jp/company/ir/faq.php)／[保存証拠](evidence/2818/20261011T045038264786Z/04.json)（取得 2026-10-11T04:50:42.461618+00:00）：様への対応を正確に行うために、お客様には電話番号の通知をお願いしております。 非通知の設定をされている場合、電話番号の最初に「186」をつけておかけください。 メールでのお問い合わせ ir@pietro.co.jp ※土・日・祝日、お盆、年末年始はお休みさせていただきます。 ※お問い合わせの内容によっては、お時間を頂戴する場合やお返事を差し上げられない場合がございます。 ※メールの受信制限をされている方は､下記
- [公式ページ](https://www.pietro.co.jp/company/ir/faq.php)／[保存証拠](evidence/2818/20261011T045038264786Z/04.json)（取得 2026-10-11T04:50:42.461618+00:00）：～金曜日 10:00～16:00 ※土・日・祝日、お盆、年末年始はお休みさせていただきます。 ※お客様とのお電話は、内容確認とサービス向上のため録音させていただきます。 ※お客様への対応を正確に行うために、お客様には電話番号の通知をお願いしております。 非通知の設定をされている場合、電話番号の最初に「186」をつけておかけください。 メールでのお問い合わせ ir@pietro.co.jp ※土・日・祝日、お盆、年末年始はお休みさせていただきます。 ※お問い合わせの内容によっては、お時間を頂戴する場合やお返事を差し上げられない場合がございます。 ※メールの受信制限をされている方は､下記
- [公式ページ](https://www.pietro.co.jp/company/ir/faq.php)／[保存証拠](evidence/2818/20261011T045038264786Z/04.json)（取得 2026-10-11T04:50:42.461618+00:00）：VISION オンラインストア 商品・レストラン情報 ホーム > IR情報 > お問い合わせ・よくあるご質問 お問い合わせ・よくあるご質問 当社のIRに関するお問い合わせはこちらからお願いいたします。 なお、皆様からよくお寄せいただく質問をQ&A形式でまとめましたので、下記の よくあるご質問 も併せてご覧ください。 お問い合わせ お電話でのお問い合わせ 0120-769-300 受付時間：月～金曜

### 285A キオクシアホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 企業一般・製品窓口と別の公式IRフォームリンクを確認。対応する実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.kioxia-holdings.com/ja-jp/contact.html)／[保存証拠](evidence/285A/20261011T045047811925Z/03.json)（取得 2026-10-11T04:50:52.345239+00:00）：グス株式会社） キオクシアグループの​企業・グループ情報、IRに関するご質問は、こちらからお問い合わせください。 お問い合わせフォーム （企業・グループ情報） お問い合わせフォーム （IR） キオクシア株式会社の企業情報、新製品・ニュース発表、イベント・展示会情報に関するご質問は、こちらからお問い合わせください。 キオクシア株式会社に関するお問い合わせ 製品・お取引に関するお問い合わせ（
- [公式ページ](https://www.kioxia-holdings.com/ja-jp/ir.html)／[保存証拠](evidence/285A/20261011T045047811925Z/02.json)（取得 2026-10-11T04:50:50.427766+00:00）：式・格付け情報 株式情報 格付け情報 アナリストカバレッジ 株主総会 コーポレートガバナンス ディスクロージャーポリシー IRサイトご利用上の留意点 電子公告 IRに関するお問い合わせ キオクシアグループについて 数字で見るキオクシア キオクシアグループの特徴を数字でご紹介します。 キオクシアグループのサステナビリティ 持続可能な社会の発展に貢献するためのキオクシアグループのサステ

### 286A ユカリア

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 所属団体・企業を必須表示。個人の入力方法は未確認で、機関限定とは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://eucalia.jp/inquiry_ir/)／[保存証拠](evidence/286A/20261011T045047815038Z/02.json)（取得 2026-10-11T04:50:51.215741+00:00）：EUCALIA \| IRに関するお問い合わせ 会社情報 会社概要 役員紹介 事業紹介 病院経営サポート コンサルティング 医療データ 医療・介護 DX 高齢者向け住宅 介護施設紹介 その他 事例紹介 ニュース 適時開示 プレスリリース インフォ
- [公式ページ](https://eucalia.jp/inquiry_ir/)／[保存証拠](evidence/286A/20261011T045047815038Z/02.json)（取得 2026-10-11T04:50:51.215741+00:00）：に関する FAQ を掲載しております。 よろしければお問い合わせいただく前にご確認ください。 FAQ 必須 は入力必須項目になります。 お名前 必須 フリガナ 所属団体・企業 必須 メールアドレス 必須 お問い合わせ内容 必須 個人情報保護方針 に同意する お問い合わせ Contact us お気軽にお問い合わせください。 採用情報 Recruit ヘルスケア産業におけるリーデ
- [公式ページ](https://eucalia.jp/)／[保存証拠](evidence/286A/20261011T045047815038Z/01.json)（取得 2026-10-11T04:50:49.220440+00:00）：インフォメーション メディア情報 社会的インパクト サステナビリティ ウェルビーイング コーポレート・ガバナンス IR IRニュース IRライブラリ 電子公告 IRお問い合わせ 採用情報 キャリア採用 新卒採用 お問い合わせ EN 変革を通じて医療・介護の あるべき姿を実現する 「インパクトレポート 2026 」を発刊 一橋大学大学院 野間 幹晴教授との対談などを収録 20

### 2871 ニチレイ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 本文は400字程度と案内。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.nichirei.co.jp/form/form_IR)／[保存証拠](evidence/2871/20261011T045047816026Z/02.json)（取得 2026-10-11T04:50:50.386545+00:00）：IR・投資家情報に関するお問い合わせ \| 株式会社ニチレイ メインコンテンツに移動 企業情報 トップメッセージ 会社概要 経営の考え方 コーポレートガバナンス コンプライアンス リスクマネジメント 人権への取り組み 早わかり ニチレイっ
- [公式ページ](https://www.nichirei.co.jp/form/form_IR)／[保存証拠](evidence/2871/20261011T045047816026Z/02.json)（取得 2026-10-11T04:50:50.386545+00:00）：外 その他 ... ※ 国外の方は「国外」をお選びください。 郡市区（島・国名）（全角） 必須 それ以降の住所（全角） 必須 会社名・勤務先（全角） 必須 ※ 個人の場合は「個人」とご入力ください。 お問い合わせ内容（全角） 必須 ※ 400字程度でご入力ください。 上記「お問い合わせに関する注意事項」に同意します。 必須 ニチレイTOP お問い合わせ IR・投資家情報に関するお問い合わせ 企業
- [公式ページ](https://www.nichirei.co.jp/form/form_IR)／[保存証拠](evidence/2871/20261011T045047816026Z/02.json)（取得 2026-10-11T04:50:50.386545+00:00）：名）（全角） 必須 それ以降の住所（全角） 必須 会社名・勤務先（全角） 必須 ※ 個人の場合は「個人」とご入力ください。 お問い合わせ内容（全角） 必須 ※ 400字程度でご入力ください。 上記「お問い合わせに関する注意事項」に同意します。 必須 ニチレイTOP お問い合わせ IR・投資家情報に関するお問い合わせ 企業情報 トップメッセージ 会社概要 経営の考え方 コ
- [公式ページ](https://www.nichirei.co.jp/)／[保存証拠](evidence/2871/20261011T045047816026Z/01.json)（取得 2026-10-11T04:50:48.860951+00:00）：営方針 業績・財務 株式関連情報 IRライブラリー ニチレイを知る ESG・サステナビリティ IRニュース IRカレンダー 電子公告 免責事項 よくあるご質問 IR・投資家情報に関するお問い合わせ 早わかり ニチレイってこんな会社 統合レポート・サステナビリティレポート イニシアチブ 個人投資家の皆様へ 食品の安全・信頼 品質基本方針 食品の安全Q&A 品質保証体制 検査体制 事業別の取り組み

### 2874 横浜冷凍

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / 公式IRページから専用の外部問い合わせフォームへのリンクを確認。対応する実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.yokorei.co.jp/ir/)／[保存証拠](evidence/2874/20261011T045047819810Z/02.json)（取得 2026-10-11T04:50:53.463891+00:00）： マテリアリティ 環境 （Environment） 社会 （Society） ガバナンス （Governance） IRカレンダー 今後のイベントなどはこちら 株主・投資家情報に関する お問い合わせフォーム 冷蔵倉庫事業 冷蔵倉庫事業とは？ 冷蔵倉庫事業の技術・強み 冷蔵倉庫拠点 通関事業 ICT・YISサービス 冷蔵倉庫内の設備保守 食品販売事業 食品販売事業とは？ 食品販売事業の特徴・強み 食品販売
- [公式ページ](https://www.yokorei.co.jp/)／[保存証拠](evidence/2874/20261011T045047819810Z/01.json)（取得 2026-10-11T04:50:50.523935+00:00）：品販売事業とは？ 食品販売事業の特徴・強み 食品販売事業所一覧 企業情報 トップメッセージ 経営理念 会社概要 グループ企業一覧 役員一覧 沿革 組織図 約款 株主・投資家情報 個人投資家の皆様へ 企業情報と経営方針 IRライブラリー 株式・債券情報 IRカレンダー IRニュース ディスクロージャーポリシー サステナビリティ マテリアリティ 環境 社会 ガバナンス SDGs

### 2875 東洋水産

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.maruchan.co.jp/customer/inquiry.php)／[保存証拠](evidence/2875/20261011T045047821050Z/05.json)（取得 2026-10-11T04:50:52.354904+00:00）：須 お問い合わせ区分 商品について 即席カップ麺・袋麺 チルド麺・チルド食品 その他の商品 商品以外のご質問について ウェブサイトについて テレビCMについて IR情報について その他 必須 お名前 必須 ふりがな 必須 Eメールアドレス 必須 Eメールアドレス(再入力) 郵便番号 - ご住所 必須 電話番号 - - 商品名 JANコード 必須 お問い合わせの内容 ご登録内

### 2882 イートアンドホールディングス

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR問い合わせ専用の外部フォームへの公式リンクのみ確認。対応する実入力欄は保存されていない。

根拠：

- [公式ページ](https://www.eat-and.jp/ir/contact.html)／[保存証拠](evidence/2882/20261011T045047830296Z/02.json)（取得 2026-10-11T04:50:50.480805+00:00）：つ適切な措置を講じるものとし、法令などに正当な理由がある場合を除き、お客様の同意なく目的外での利用および第三者への提供は行いません。 IRお問い合わせフォーム IRお問い合わせフォームへ IRお問い合わせ お電話でのお問い合わせ（受付時間 平日9時～17時 ※土日祝日を除く） 0120-311-928 IRサイトマップ IR SITEMAP 経営方針 株主の皆様へ 中期経営計画 コー
- [公式ページ](https://www.eat-and.jp/)／[保存証拠](evidence/2882/20261011T045047830296Z/01.json)（取得 2026-10-11T04:50:49.302297+00:00）： 株主様向け報告書 株式・社債情報 株式事務手続きのご案内 株式基本情報 株主還元（配当等） 株主優待情報 その他 IRカレンダー IRに関するよくあるご質問 IRお問い合わせ 免責事項 電子公告 メールマガジン登録 株価情報(yahoo!ファイナンス) 採用情報 採用情報 採用情報トップ 中途採用 新卒採用 採用ニュース ソーシャルメディア 個人情報保護方針 サイトマップ

### 2883 大冷

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`dairei_investor_relations2883@dai-rei.co.jp`。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.dai-rei.co.jp/ir_info/ir_inquiry.html)／[保存証拠](evidence/2883/20261011T045047831825Z/05.json)（取得 2026-10-11T04:50:53.925567+00:00）：らく匠味シリーズのレシピ トレースシステム IR情報 経営方針 財務・業績 IR資料室 株式について その他IR情報 会社案内 製造 商品開発 IRのお問合せ IRについてお問い合わせ先（IR担当）： dairei_investor_relations2883@dai-rei.co.jp PAGE TOP 個人情報について サイトポリシー サイトマップ Copyright © DAIREI CO
- [公式ページ](https://www.dai-rei.co.jp/ir_info/ir_inquiry.html)／[保存証拠](evidence/2883/20261011T045047831825Z/05.json)（取得 2026-10-11T04:50:53.925567+00:00）：ブラリ 大冷のこだわり 生産拠点 鮮度管理 品質管理 解凍方法 産地情報 おすすめレシピ ムッシュ小早川のスペシャルメニュー 楽らくクックシリーズのレシピ 楽らく匠味シリーズのレシピ トレースシステム IR情報 経営方針 財務・業績 IR資料室 株式について その他IR情報 会社案内 製造 商品開発 IRのお問合せ IRについてお問い合わせ先（IR担当）： dairei_investor_relations2883@dai-rei.co.jp PAGE TOP 個人情報について サイトポリシー サイトマップ Copyright © DAIREI CO., LTD. all rights reserved.

### 2884 ヨシムラ・フード・ホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.y-food-h.com/contact/)／[保存証拠](evidence/2884/20261011T045047832966Z/03.json)（取得 2026-10-11T04:50:52.829847+00:00）： お名前（フリガナ） 必須 社名 部署名・役職名 郵便番号 ご住所 電話番号 メールアドレス 必須 お問い合わせ内容 お問い合わせ種別 必須 選択してください IRについて 当社へのサービス・商品のご提案 当社製品・サービスについて 取材の申し込み その他 お問い合わせ内容 必須 プライバシーポリシー に同意する

### 288A ラクサス・テクノロジーズ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 重要事実・非公開情報・株価動向等の質問には回答を差し控える。
- 回答の転用・二次利用・本人以外への開示をご遠慮との記載。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://corp.laxus.co/inquiry/individual?from=ir)／[保存証拠](evidence/288A/20261011T045047834097Z/03.json)（取得 2026-10-11T04:50:51.031155+00:00）：区分 個人の方 お問い合わせ項目 選択してください ラクサスご利用前のお問合せ ラクサスご利用中のお問合せ 求人への応募について IRについて その他 お問い合わせの内容によっては、ご回答までお時間をいただく場合がございます。 また、下記に該当するご質問は、IRからの回答を差し控えておりますのであらかじめご了承ください。 ・金融商品取引法第
- [公式ページ](https://corp.laxus.co/inquiry/individual?from=ir)／[保存証拠](evidence/288A/20261011T045047834097Z/03.json)（取得 2026-10-11T04:50:51.031155+00:00）：nglish CONTACT お問い合わせ ラクサス・テクノロジーズ株式会社のお問い合わせページです。どうぞ、下記のフォームからお気軽にお問い合わせください。 区分 個人の方 お問い合わせ項目 選択してください ラクサスご利用前のお問合せ ラクサスご利用中のお問合せ 求人への応募について IRについて その他 お問い合わせの内容によっては、ご回答までお時間をいただく場合が
- [公式ページ](https://corp.laxus.co/inquiry/individual?from=ir)／[保存証拠](evidence/288A/20261011T045047834097Z/03.json)（取得 2026-10-11T04:50:51.031155+00:00）：記に該当するご質問は、IRからの回答を差し控えておりますのであらかじめご了承ください。 ・金融商品取引法第166条の「重要事実」に該当する可能性のあるご質問 ・非公開情報に関するご質問 ・株式市場の値動きに関するご質問 ・誹謗中傷に該当するメッセージ ・その他、IRに関係しないご質問 ▼ディスクロージャーポリシー https://corp.laxus.co/ir/managemen
- [公式ページ](https://corp.laxus.co/inquiry/individual?from=ir)／[保存証拠](evidence/288A/20261011T045047834097Z/03.json)（取得 2026-10-11T04:50:51.031155+00:00）：を確認」を押してください。 当社からのEメールでの回答は、当社へお問い合わせいただいたお客様個人にお送りするものです。当社の許可なく、回答内容の一部または全部を転用、二次利用、または当該お客様以外に開示することはご遠慮ください。 夜間、土日祝日、年末年始、夏季休業にいただいたお問い合わせ、お問い合わせ内容により、回答が遅れる場合があります。 迷惑メール等の対策をされている

### 2892 日本食品化工

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。 / IR専用ページはフォーム入力・送信を案内するが、保存された実入力欄はない。

根拠：

- [公式ページ](https://www.nisshoku.co.jp/ir/ir-contact.html)／[保存証拠](evidence/2892/20261011T045047837903Z/02.json)（取得 2026-10-11T04:50:50.723662+00:00）：教育制度紹介 福利厚生 募集要項 お問い合わせ ホーム IR情報 IRに関するお問い合わせ IR IR情報 IRに関するお問い合わせ IRに関するお問い合わせ 以下のフォームに必要な項目を入力のうえ、送信をクリックしてください。 TOP 日本食品化工について トップメッセージ トップメッセージ 理念とビジョン 企業理念 長期経営ビジョン 人事ビジョン 多様なWell-beingのために 日食行動
- [公式ページ](https://www.nisshoku.co.jp/)／[保存証拠](evidence/2892/20261011T045047837903Z/01.json)（取得 2026-10-11T04:50:49.258692+00:00）：報 採用メッセージ 社員インタビュー クロストーク プロジェクトストーリー 職場環境・教育制度紹介 福利厚生 募集要項 お問い合わせ 製品に関するお問い合わせ IR情報に関するお問い合わせ 採用に関するお問い合わせ コンプライアンス通報窓口 プライバシーポリシー サイトポリシー Copyright© NIHON SHOKUHIN KAKO CO.,LTD. All rights res

### 2894 石井食品

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ishiifood.co.jp/contact/form/)／[保存証拠](evidence/2894/20261011T045047839322Z/05.json)（取得 2026-10-11T04:50:54.141147+00:00）： 選択してください 商品・サービスに関するお問合せ 商品・サービスに関する不具合やご意見 販売店について 通信販売に関するお問合せ 企業方針・取り組みについて IR・財務について 株主優待について キャンペーンについて 取材や広報部門へのご連絡 採用について 協業・委託製造・新規取引について 工場見学について その他 商品カテゴリー 加工肉食品（ミートボール・チキンハンバーグ

### 2901 ウェルディッシュ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR質問に関する明示区分は「IRミーティングに関するお問い合わせ」。一般的なメールIR質問まで対応するとは断定しない。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://wel-dish.co.jp/contact/)／[保存証拠](evidence/2901/20261011T045047842645Z/03.json)（取得 2026-10-11T04:50:53.227956+00:00）：Japan * は必須入力項目になります お問い合わせ種別 製品について お取引のご相談 会社について OEMのご相談 IRミーティングに関するお問い合わせ その他 お名前 フリガナ 会社名 職種・役職など 郵便番号 郵便番号で検索 ※半角数字で入力 ※ハイフンは不要 住所 電話番号 ※半角数字で入力 ※ハイフンは不要 メールアドレス お問い合わせ内容 
- [公式ページ](https://wel-dish.co.jp/contact/)／[保存証拠](evidence/2901/20261011T045047842645Z/03.json)（取得 2026-10-11T04:50:53.227956+00:00）：確認後、折り返しご連絡させて頂きます。 Japan * は必須入力項目になります お問い合わせ種別 製品について お取引のご相談 会社について OEMのご相談 IRミーティングに関するお問い合わせ その他 お名前 フリガナ 会社名 職種・役職など 郵便番号 郵便番号で検索 ※半角数字で入力 ※ハイフンは不要 住所 電話番号 ※半角数字で入力 ※ハイフンは不要 メールアドレス お問い合わせ内容 

### 2903 シノブフーズ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.shinobufoods.co.jp/contact/)／[保存証拠](evidence/2903/20261011T045049207939Z/03.json)（取得 2026-10-11T04:50:56.011193+00:00）：お問い合わせの種類 必須 弊社商品に関するご意見・お問い合わせ 株式、IR情報、株主優待等に関するご意見・お問い合わせ 採用に関するお問い合わせ その他のご意見・お問い合わせ 「お問い合わせの種類」を選択してください。 企業・団体名 お名前 必須 「お名前」を入力してください。 メールアドレス 必須 半角英数でメール

### 2904 一正蒲鉾

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 一部フリーメールでは返信が届かない旨と、フリーメール以外のアドレス使用を案内。

注意・未確認：公開 GET の保存本文・非 hidden 入力欄による確認。送信、JavaScript・CAPTCHA の動作、実際の返信は未検証。

根拠：

- [公式ページ](https://www.ichimasa.co.jp/contact/)／[保存証拠](evidence/2904/20261011T045051988386Z/03.json)（取得 2026-10-11T04:50:55.395763+00:00）：お問い合わせの種類 必須 商品に関するお問い合わせ・ご意見 IR・投資情報に関するお問い合わせ・ご意見 株主優待に関するお問い合わせ・ご意見 一正蒲鉾(株)へのお問い合わせ・ご意見 公的研究費・研究活動に関するお問い合わせ・ご意見 その他 いずれかを選択してください。 商品名 お問い合わせ内容 必須 
- [公式ページ](https://www.ichimasa.co.jp/contact/)／[保存証拠](evidence/2904/20261011T045051988386Z/03.json)（取得 2026-10-11T04:50:55.395763+00:00）：りするものです。一部または全部を転載、二次利用することはご遠慮ください。 Yahooメールなど一部フリーメールの場合、返信のメールが届かないことがございます。 フリーメール以外のアドレスでお問い合わせください。 ドメイン指定受信をされている場合は、「@ichimasa.co.jp」ドメインからのメールを受信できるよう設定お願いします。 本窓口では、公的研究費および研究活動の適正な運用

### 3092 ＺＯＺＯ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 対象はIR・ESG・出資・M&Aに関する投資家・アナリストの問い合わせ。一般サービスの問い合わせは別窓口。
- 個人は会社名に「個人」と入力するとの明記。氏名、フリガナ、メール、電話、問い合わせ詳細、個人情報取扱同意等が必要。
- 未開示情報には回答しない。内容によって時間を要する場合や回答できない場合がある。

注意・未確認：公式ページ内に埋め込まれたmovabletype.netのフォームをGETで確認。入力・確認画面への遷移・送信は未実施。 / 返信・投資適性は未検証。

根拠：

- [公式ページ](https://form.movabletype.net/C97B77C6-C67F-11EE-A0CA-FCC38F3DDC9C?embed=true)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3092-form.json)（取得 2026-10-11T03:42:03.308761+00:00）：当ページは、株式会社ZOZOのIR・ESG・出資・M&Aに関する投資家・アナリストの皆様からのお問い合わせフォームです。
- [公式ページ](https://form.movabletype.net/C97B77C6-C67F-11EE-A0CA-FCC38F3DDC9C?embed=true)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3092-form.json)（取得 2026-10-11T03:42:03.308761+00:00）：会社名 必須 企業に所属の方は会社名を、個人の方は「個人」と入力してください
- [公式ページ](https://form.movabletype.net/C97B77C6-C67F-11EE-A0CA-FCC38F3DDC9C?embed=true)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3092-form.json)（取得 2026-10-11T03:42:03.308761+00:00）：氏名 必須 氏名（フリガナ） 必須 メールアドレス 必須 半角英数字で入力してください 電話番号 必須
- [公式ページ](https://corp.zozo.com/ir-info/inquiry/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3092-contact.json)（取得 2026-10-11T03:37:04.290395+00:00）：迅速な対応を心がけておりますが、内容によってはお答えするのに時間を要する場合もございます。また、開示していない情報に関しましては、お答えいたしかねます。

### 3134 Ｈａｍｅｅ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 株式/IRについての公式注意事項から専用フォームと埋め込みFormMailerへ誘導。個人限定/機関限定の明示は確認していない。
- IR以外・営業活動に類する問い合わせ、非公開情報には回答しない。内容により回答できないことがある。
- 沈黙期間中は対応を差し控える。具体的日数はこの窓口ページでは確認していない。
- 返信の一部または全部の転載・2次利用を控えるよう案内。自動で返信原文を公開・配信する運用へ使わない。
- 氏名・ふりがな・メール・電話番号・住所・本文・個人情報同意の入力欄を確認。会社名/団体名欄にはrequired属性なし。送信やフォームの動作試験はしていない。

注意・未確認：www付きの候補URLは接続失敗したため、取得できた公式トップの実リンクをたどって現行窓口を確認した。 / 入力情報が多く、沈黙期間・転載等の条件は送信前に再確認が必要。 / 企業業績・投資適性を検証したものではない。

根拠：

- [公式ページ](https://hamee.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-3134-ir-contact.json)（取得 2026-10-11T03:38:52.130404+00:00）：IRについてのお問い合わせ - Hamee株式会社
- [公式ページ](https://hamee.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-3134-ir-contact.json)（取得 2026-10-11T03:38:52.130404+00:00）：IR以外のお問合せ（営業活動に類するメッセージ等）にはご回答いたしかねます。予めご了承ください。
- [公式ページ](https://hamee.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-3134-ir-contact.json)（取得 2026-10-11T03:38:52.130404+00:00）：沈黙期間中のお問い合わせへの対応は差し控えさせて頂きます。
- [公式ページ](https://hamee.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-3134-ir-contact.json)（取得 2026-10-11T03:38:52.130404+00:00）：当社からご回答した内容について、その一部または全部を転載、2次利用することはご遠慮ください。
- [公式ページ](https://pro.form-mailer.jp/fms/1f7ac8dc230378)／[保存証拠](../ir-contacts-2026-10-11/evidence/root-3134-external-form.json)（取得 2026-10-11T03:40:06.177961+00:00）：IRお問い合わせフォーム 会社名 / 団体名

### 3197 すかいらーくホールディングス

確認：IRメール確認。個人等に制限あり。受付対象に制限。

公開IRメール：`IR_group@skylark.co.jp`。

取得範囲の受付条件：

- 財務本部の業績・財務諸表等の窓口は「機関投資家様・アナリストの皆様」と明記。
- 個人株主の「その他のお問い合わせ」は総務グループの別メールであり、個人向け業績IR受付を確認できたとは扱わない。

注意・未確認：個人が機関投資家・アナリスト向け窓口を利用できるという確認はない。

根拠：

- [公式ページ](https://corp.skylark.co.jp/ir/ir_inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3197-contact.json)（取得 2026-10-11T03:37:04.354009+00:00）：機関投資家様・アナリストの皆様からの業績・財務諸表等に関するお問い合わせ 株式会社すかいらーくホールディングス 財務本部 TEL：0422-37-5244 受付時間：午前9時00分～午後6時00分 （土曜・日曜・祝日を除く） EMAIL： IR_group@skylark.co.jp
- [公式ページ](https://corp.skylark.co.jp/ir/ir_inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-3197-contact.json)（取得 2026-10-11T03:37:04.354009+00:00）：個人株主様からのその他のお問い合わせ 株式会社すかいらーくホールディングス 総務グループ

### 3673 ブロードリーフ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- ご質問内容 必須 ご入力は全角1000文字以内でお願いします。
- お名前 必須 フリガナ 必須 会社名 必須
- メールアドレス 必須 メールアドレス（確認用） 必須

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 共通フォームの「株主優待・配当・株主総会・IRについて」を選ぶ。会社名必須だが個人投資家の記入方法は未記載。

根拠：

- [公式ページ](https://www.broadleaf.co.jp/form/input/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-3673-contact.json)（取得 2026-10-11T03:37:41.228294+00:00）：株主優待・配当・株主総会・IRについて
- [公式ページ](https://www.broadleaf.co.jp/form/input/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-3673-contact.json)（取得 2026-10-11T03:37:41.228294+00:00）：ご質問内容 必須 ご入力は全角1000文字以内でお願いします。 お名前 必須 フリガナ 必須 会社名 必須
- [公式ページ](https://www.broadleaf.co.jp/form/input/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-3673-contact.json)（取得 2026-10-11T03:37:41.228294+00:00）：メールアドレス 必須 メールアドレス（確認用） 必須

### 3923 ラクス

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@rakus.co.jp`。

取得範囲の受付条件：

- 株主・投資家の公平性を確保するため、各四半期の期末日の翌日から各決算発表日までを沈黙期間といたします。この期間中は、決算及び業績見通しに関する問い合わせへの回答やコメントはいたしません。ただし、沈黙期間中であっても、適時開示規則に基づき必要と判断される情報は適宜開示いたします。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 機関投資家・アナリスト向け取材申込みは別導線。一般のIRメールについて機関投資家限定とは記載されていない。 / 沈黙期間の具体的な終了日は、送信判断時に公式決算発表日と照合が必要。

根拠：

- [公式ページ](https://www.rakus.co.jp/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-3923-ir.json)（取得 2026-10-11T03:35:42.061331+00:00）：IRに関するお問い合わせ 広報IR部 IR課 E-mail ir@rakus.co.jp 機関投資家・アナリスト向け IR取材申し込みはこちら
- [公式ページ](https://www.rakus.co.jp/ir/disclosure-policy/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-3923-disclosure-policy.json)（取得 2026-10-11T03:40:22.948444+00:00）：株主・投資家の公平性を確保するため、各四半期の期末日の翌日から各決算発表日までを沈黙期間といたします。この期間中は、決算及び業績見通しに関する問い合わせへの回答やコメントはいたしません。ただし、沈黙期間中であっても、適時開示規則に基づき必要と判断される情報は適宜開示いたします。

### 4058 トヨクモ

確認：案内・リンクのみ。個人条件の明示未確認。個別回答なし。

取得範囲の受付条件：

- 当社では、IR活動について、効率的に業務を行うため、個別の問い合わせにつきましては取次も含めて回答しない方針としております。
- 上記ご了承の上、何かございましたら当社の プライバシーポリシー に同意の上、以下のフォームに必要事項をご記載いただき、ご連絡下さい。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 公式に個別問い合わせへ回答しないと明記。窓口が存在しても、返信を使う運用の候補には含めない。投資不可という評価ではない。 / 公式ページから埋込先の公開URLをGETしたが待機ページ（IR Contact）のみ。入力項目や必須条件は未確認。

根拠：

- [公式ページ](https://www.toyokumo.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4058-contact.json)（取得 2026-10-11T03:37:41.274706+00:00）：当社では、IR活動について、効率的に業務を行うため、個別の問い合わせにつきましては取次も含めて回答しない方針としております。
- [公式ページ](https://www.toyokumo.co.jp/ir/contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4058-contact.json)（取得 2026-10-11T03:37:41.274706+00:00）：上記ご了承の上、何かございましたら当社の プライバシーポリシー に同意の上、以下のフォームに必要事項をご記載いただき、ご連絡下さい。

### 4371 コアコンセプト・テクノロジー

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@cct-inc.co.jp`。

取得範囲の受付条件：

- 当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。
- 迅速な対応を心がけておりますが、お問い合わせ内容によっては回答にお時間をいただく場合がある他、お答えできない場合もございます。
- また、当社から回答した内容について、その一部または全部を転載、2次利用することはご遠慮ください。
- 非公開情報に関するご質問（業績動向など）
- 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など）
- 株式市場の値動きに関するご質問（株価動向、売買手口など）
- 誹謗中傷に該当するメッセージ（根拠のない悪口、名誉を棄損する言葉など）
- 営業や勧誘のお問い合わせ（○○サービスのご案内など）
- 当社サイト以外に記載されている内容についてのお問い合わせ

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 公開メールは公式ページの「ir★cct-inc.co.jp」と「★部分を@に置き換え」の指示に従い正規化。 / 返信の転載・二次利用を控える条件がある。取得した返信の再配布を前提にしない。

根拠：

- [公式ページ](https://www.cct-inc.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4371-contact.json)（取得 2026-10-11T03:36:22.990712+00:00）：IRに関するお問い合わせ先 当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。 お問い合わせEmail：ir★cct-inc.co.jp （お手数ですが★部分を@に置き換えてご送信ください）
- [公式ページ](https://www.cct-inc.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4371-contact.json)（取得 2026-10-11T03:36:22.990712+00:00）：お問い合わせいただく際のお願いとご注意 迅速な対応を心がけておりますが、お問い合わせ内容によっては回答にお時間をいただく場合がある他、お答えできない場合もございます。 下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 また、当社から回答した内容について、その一部または全部を転載、2次利用することはご遠慮ください。 非公開情報に関するご質問（業績動向など） 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など） 株式市場の値動きに関するご質問（株価動向、売買手口など） 誹謗中傷に該当するメッセージ（根拠のない悪口、名誉を棄損する言葉など） 営業や勧誘のお問い合わせ（○○サービスのご案内など） 当社サイト以外に記載されている内容についてのお問い合わせ

### 4413 ボードルア

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- ご氏名 必須 メールアドレス 必須 ※半角英数字 確認のため、もう一度入力してください。 電話番号 必須 ※半角数字 ご相談内容 必須
- 下記の個人情報の取り扱いに同意

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / IRページのリンクはホームの #contact を指すが、現行 /contact/ の選択肢と入力欄でIR受付を確認。 / 担当者から連絡する旨の案内はあるが、返信の保証や実際の応答を検証したものではない。

根拠：

- [公式ページ](https://www.baudroie.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4413-contact.json)（取得 2026-10-11T03:37:41.265376+00:00）：各項目をご入力の上、お問い合わせください。メール確認後、担当者より改めてご連絡させていただきます。
- [公式ページ](https://www.baudroie.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4413-contact.json)（取得 2026-10-11T03:37:41.265376+00:00）：お問い合わせ項目 必須 選択してください 仕事に関するお問い合わせ IRに関するお問い合わせ 採用に関するお問い合わせ
- [公式ページ](https://www.baudroie.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4413-contact.json)（取得 2026-10-11T03:37:41.265376+00:00）：ご氏名 必須 メールアドレス 必須 ※半角英数字 確認のため、もう一度入力してください。 電話番号 必須 ※半角数字 ご相談内容 必須 下記の個人情報の取り扱いに同意

### 4417 グローバルセキュリティエキスパート

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせの内容によっては、ご回答を差し控えさせていただく場合やご返信までにお時間を頂戴する場合がございますので、あらかじめご了承くださいませ。なお、下記に関するご質問は、回答を差し控えております。
- ・非公開情報（業績動向など）に関するご質問
- ・株式市場及び株価動向に関するご質問
- ・金融商品取引法第166条に定める「重要事実」に該当する可能性のあるご質問
- ・誹謗中傷に該当するメッセージ
- ・営業や勧誘のお問い合わせ
- 必須 お問い合わせ内容 お問い合わせ内容をご記入ください 全角1,000文字以内
- 必須 会社名 任意 部署名 必須 住所 必須 お名前 必須 メールアドレス 必須 電話番号 ハイフンなし
- 個人情報のお取り扱いに同意します

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 会社名・住所・電話番号が必須。個人投資家が会社名欄をどう記入するかは明記されていないため、個人対応可とは断定しない。 / サイト内の119@gsx.co.jpは別サービスの窓口でありIRメールとして採用していない。

根拠：

- [公式ページ](https://www.gsx.co.jp/ir/inquiry)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4417-contact.json)（取得 2026-10-11T03:36:22.824876+00:00）：IRに関するお問い合わせ IRに関するお問い合わせは、下記フォームよりお願いいたします。
- [公式ページ](https://www.gsx.co.jp/ir/inquiry)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4417-contact.json)（取得 2026-10-11T03:36:22.824876+00:00）：お問い合わせの内容によっては、ご回答を差し控えさせていただく場合やご返信までにお時間を頂戴する場合がございますので、あらかじめご了承くださいませ。なお、下記に関するご質問は、回答を差し控えております。 ・非公開情報（業績動向など）に関するご質問 ・株式市場及び株価動向に関するご質問 ・金融商品取引法第166条に定める「重要事実」に該当する可能性のあるご質問 ・誹謗中傷に該当するメッセージ ・営業や勧誘のお問い合わせ 必須 お問い合わせ内容 お問い合わせ内容をご記入ください 全角1,000文字以内 必須 会社名 任意 部署名 必須 住所 必須 お名前 必須 メールアドレス 必須 電話番号 ハイフンなし
- [公式ページ](https://www.gsx.co.jp/ir/inquiry)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4417-contact.json)（取得 2026-10-11T03:36:22.824876+00:00）：個人情報のお取り扱いに同意します

### 4475 ＨＥＮＮＧＥ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- ※お問い合わせはフォームでのみ受け付けております。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / IR専用フォームの案内は確認したが、公開GETのHTMLではformの入力項目を取得できなかった。入力項目・必須条件・送信先の確認は未了。

根拠：

- [公式ページ](https://hennge.com/jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4475-contact.json)（取得 2026-10-11T03:36:22.909850+00:00）：このフォームは業績・財務・株式等、IRに関するお問い合わせ専用です。その他のお問い合わせについては、 こちらのフォーム からお問い合わせください。 ※お問い合わせはフォームでのみ受け付けております。

### 4481 ベース

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@basenet.co.jp`。

取得範囲の受付条件：

- お問合せの内容などにより、返事に日時を要する場合もございますが、ご了解いただけますよう、お願い申し上げます。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。

根拠：

- [公式ページ](https://www.basenet.co.jp/ir/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4481-contact.json)（取得 2026-10-11T03:36:22.991469+00:00）：IRに関するお問い合わせは、下記アドレスまでお送りください。
- [公式ページ](https://www.basenet.co.jp/ir/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4481-contact.json)（取得 2026-10-11T03:36:22.991469+00:00）：お問い合わせ先： ir@basenet.co.jp
- [公式ページ](https://www.basenet.co.jp/ir/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4481-contact.json)（取得 2026-10-11T03:36:22.991469+00:00）：お問合せの内容などにより、返事に日時を要する場合もございますが、ご了解いただけますよう、お願い申し上げます。

### 4493 サイバーセキュリティクラウド

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 会社名 必須 所属部署 任意 氏名 必須 メールアドレス 必須 電話番号 必須 お問い合わせ内容 必須
- 個人情報保護方針に同意する

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 共通フォームの「IRに関するお問い合わせ」を選ぶ導線。会社名・電話番号が必須で、個人利用時の会社名欄の扱いは未記載。 / pr@cscloud.co.jpはフォーム不具合時の共通連絡先。IR専用メールとは記載されていないためpublic_ir_emailsに採用していない。 / サイトはreCAPTCHAの保護を明記。送信時の挙動は確認していない。

根拠：

- [公式ページ](https://www.cscloud.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4493-contact.json)（取得 2026-10-11T03:36:22.931761+00:00）：お問い合わせ 内容 必須 メディア取材・講演依頼・報道関係に関するお問い合わせ 採用に関するお問い合わせ IRに関するお問い合わせ
- [公式ページ](https://www.cscloud.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4493-contact.json)（取得 2026-10-11T03:36:22.931761+00:00）：会社名 必須 所属部署 任意 氏名 必須 メールアドレス 必須 電話番号 必須 お問い合わせ内容 必須 個人情報保護方針 個人情報保護方針に同意する
- [公式ページ](https://www.cscloud.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-4493-contact.json)（取得 2026-10-11T03:36:22.931761+00:00）：※フォームの送信が正しく行えない場合は、間をあけてもう一度お試しいただくか、 pr@cscloud.co.jp までお問い合わせください。

### 4971 メック

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 問い合わせ種別に投資家情報、個人／業務の区分に個人がある。業務の場合は社名・団体名と部署名の記入を求める。
- 広告・売り込み等を拒否。回答の一部または全部の無断転用・転載など二次使用を禁止。
- 内容によって回答不可または時間を要する場合があり、指定回答期日や至急要望に応じられない場合がある。
- 受付記録メールの自動送信を案内し、@mec-np.comの受信設定を求める。これは問い合わせ用メールアドレスではない。

注意・未確認：返信原文を他者向けレポートへ転載・共有する運用には、会社の二次使用禁止条件を反映する必要がある。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.mec-co.com/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-4971-contact.json)（取得 2026-10-11T03:36:18.814620+00:00）：お問い合わせ種別 会社全般について 投資家情報について 製品について
- [公式ページ](https://www.mec-co.com/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-4971-contact.json)（取得 2026-10-11T03:36:18.814620+00:00）：個人/業務 個人 業務
- [公式ページ](https://www.mec-co.com/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-4971-contact.json)（取得 2026-10-11T03:36:18.814620+00:00）：当社の許可なく回答内容の一部または全てを当社の許可なく転用、転載など二次的に使用することは固くお断りいたします。
- [公式ページ](https://www.mec-co.com/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-4971-contact.json)（取得 2026-10-11T03:36:18.814620+00:00）：お寄せいただきましたメッセージの内容によっては回答できかねる場合や、回答に時間がかかる場合がございます。
- [公式ページ](https://www.mec-co.com/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-4971-contact.json)（取得 2026-10-11T03:36:18.814620+00:00）：回答期日の指定や「至急」のご要望にはお答えできないこともございます

### 5132 ｐｌｕｓｚｅｒｏ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 当社は、IRに関するお問い合わせは、お問合せフォームからのみ受付けております。
- お問い合わせの内容により、回答にお時間をいただく場合やお答えしかねる場合がございます。
- ・非公開情報（足元の業績動向など）
- ・「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など）
- ・株価の値動きに関するご質問
- ・ご意見やご感想（社内で共有させていただきますが、個別の回答は差し控えさせていただきます）
- 当社から回答した内容について、その一部または全てを転載、2次利用することはご遠慮ください。
- 氏名 (必須) ふりがな (必須) メールアドレス (必須) メールアドレス再入力 (必須) 電話番号 郵便番号 住所 ご質問・ご意見 (必須)

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 返信の転載・二次利用を控える条件がある。取得した返信の再配布を前提にしない。

根拠：

- [公式ページ](https://plus-zero.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-5132-contact.json)（取得 2026-10-11T03:36:22.930891+00:00）：当社は、IRに関するお問い合わせは、お問合せフォームからのみ受付けております。
- [公式ページ](https://plus-zero.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-5132-contact.json)（取得 2026-10-11T03:36:22.930891+00:00）：お問い合わせの内容により、回答にお時間をいただく場合やお答えしかねる場合がございます。 下記に該当するお問い合わせは、回答を差し控えておりますので、あらかじめご了承ください。 ・非公開情報（足元の業績動向など） ・「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など） ・株価の値動きに関するご質問 ・ご意見やご感想（社内で共有させていただきますが、個別の回答は差し控えさせていただきます）
- [公式ページ](https://plus-zero.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-5132-contact.json)（取得 2026-10-11T03:36:22.930891+00:00）：当社から回答した内容について、その一部または全てを転載、2次利用することはご遠慮ください。
- [公式ページ](https://plus-zero.co.jp/ir/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-5132-contact.json)（取得 2026-10-11T03:36:22.930891+00:00）：氏名 (必須) ふりがな (必須) メールアドレス (必須) メールアドレス再入力 (必須) 電話番号 郵便番号 住所 ご質問・ご意見 (必須)

### 590A ギフティグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 上記内容でお問い合わせいただく場合は、「個人情報取扱い」に同意のうえ、送信をお願いいたします。
- お問い合わせの内容によっては、ご回答までにお時間を要する場合や、当社の判断により、内容に応じて個別のご回答を差し控えさせていただく場合がございます。何卒ご了承くださいますようお願い申し上げます。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 旧4449のギフティIR URLは現590Aのギフティグループへ公式転送。現コードは公式株式基本情報とJPX2026年9月末普通株一覧で照合。旧コードは対象として採用しない。 / 会社名・自治体名・部署名の欄はあるが、本文上では必須表示なし。これだけで個人投資家対応可と断定しない。

根拠：

- [公式ページ](https://giftee-group.com/contact/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-contact.json)（取得 2026-10-11T03:37:41.225203+00:00）：株式・IRに関するお問い合わせ ホーム お問い合わせ 株式・IRに関するお問い合わせ
- [公式ページ](https://giftee-group.com/contact/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-contact.json)（取得 2026-10-11T03:37:41.225203+00:00）：会社名・自治体名・部署名 例：ギフティグループ株式会社 お名前 必須
- [公式ページ](https://giftee-group.com/contact/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-contact.json)（取得 2026-10-11T03:37:41.225203+00:00）：メールアドレス 必須 例：example@giftee.co.jp メールアドレスを入力してください 件名 必須
- [公式ページ](https://giftee-group.com/contact/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-contact.json)（取得 2026-10-11T03:37:41.225203+00:00）：上記内容でお問い合わせいただく場合は、「個人情報取扱い」に同意のうえ、送信をお願いいたします。
- [公式ページ](https://giftee-group.com/contact/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-contact.json)（取得 2026-10-11T03:37:41.225203+00:00）：お問い合わせの内容によっては、ご回答までにお時間を要する場合や、当社の判断により、内容に応じて個別のご回答を差し控えさせていただく場合がございます。何卒ご了承くださいますようお願い申し上げます。
- [公式ページ](https://giftee-group.com/ir/stock/info/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-590A-stock.json)（取得 2026-10-11T03:40:54.671959+00:00）：証券コード ギフティグループ株式会社（コード：590A）

### 6226 守谷輸送機工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- お問い合わせ内容の選択肢に「IRに関するお問合わせ」がある。
- 貴社名／学校名（団体名）、氏名・カナ、郵便番号、住所、電話番号、Emailアドレス等が必須表示。
- プライバシーポリシー同意欄がある。

注意・未確認：個人IRの受付を明示する説明は今回の窓口ページに見当たらず、所属なしで必須団体名欄をどう記入するかは未確認。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://moriya-elevator.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6226-contact.json)（取得 2026-10-11T03:36:15.135625+00:00）：下記のフォームにご記入の上、確認・送信してください。
- [公式ページ](https://moriya-elevator.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6226-contact.json)（取得 2026-10-11T03:36:15.135625+00:00）：IRに関するお問合わせ ※必須
- [公式ページ](https://moriya-elevator.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6226-contact.json)（取得 2026-10-11T03:36:15.135625+00:00）：貴社名／学校名（団体名） ※必須
- [公式ページ](https://moriya-elevator.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6226-contact.json)（取得 2026-10-11T03:36:15.135625+00:00）：上記プライバシーポリシーに同意します

### 6240 ヤマシンフィルタ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式サイトに広報・IR担当と「IR等に関するお問い合わせフォーム」の案内がある。
- 電話窓口には平日9:00～16:00の対応時間が掲載されている。これはフォーム返信期限の保証ではない。

注意・未確認：公式フォーム中継ページの公開JavaScriptから外部受付URLを確認したが、外部ページGETは403。実入力欄、必須情報、個人向け条件は未検証。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.yamashin-filter.co.jp/ja/form.html#ca01)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6240-contact.json)（取得 2026-10-11T03:36:17.222128+00:00）：IR等に関するお問い合わせ 広報・IR担当 TEL：045-680-1680 (ご対応時間：平日9:00～16:00) IR等に関するお問い合わせフォーム
- [公式ページ](https://www.yamashin-filter.co.jp/ja/form/form_redirect7.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6240-public-redirect.json)（取得 2026-10-11T03:40:59.250153+00:00）：location.href="https://ssl.swcms.net/yamashin-filter-corpPublic/ja/contactus/inquiry58463.html"
- [公式ページ](https://ssl.swcms.net/yamashin-filter-corpPublic/ja/contactus/inquiry58463.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6240-external-form.json)（取得 2026-10-11T03:40:45.770100+00:00）：403 ERROR The request could not be satisfied. Request blocked.

### 6254 野村マイクロ・サイエンス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式お問い合わせ一覧の「IRについて」から専用フォームへ誘導。氏名、E-mail、質問内容が必須表示。
- メールアドレスが誤っていると返信できない場合がある。趣旨と無関係な問い合わせは連絡を差し控える場合がある。

注意・未確認：公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.nomura-nms.co.jp/contact/05_02.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6254-form.json)（取得 2026-10-11T03:37:28.350014+00:00）：IRについて 会社名 お名前 必須 E-mail 必須 電話番号 お問い合わせの内容 必須
- [公式ページ](https://www.nomura-nms.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6254-contact.json)（取得 2026-10-11T03:36:15.165979+00:00）：各情報に関するお問い合わせをフォームにて受け付けています。
- [公式ページ](https://www.nomura-nms.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6254-contact.json)（取得 2026-10-11T03:36:15.165979+00:00）：尚、お問い合わせいただいた内容が本フォームの趣旨と無関係と思われる際は、勝手ながら連絡を差し控えさせていただきます。

### 6266 タツモ

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- 職種に個人投資家／機関投資家／アナリスト・調査会社の選択肢がある。
- 貴社名・部署名も必須表示。氏名、メール確認、郵便番号、都道府県・市区町村・番地、電話番号、質問内容が必須表示。
- 個人情報保護方針同意と、売り込み目的でない旨の確認欄がある。売り込みは明確に拒否。

注意・未確認：個人投資家の選択肢はあるが、会社・部署が必須表示のため、個人の具体的な入力方法や検証動作は未確認。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://tazmo.co.jp/contact/form02/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6266-contact.json)（取得 2026-10-11T03:36:15.166093+00:00）：職種 必須 個人投資家 機関投資家 アナリスト／調査会社
- [公式ページ](https://tazmo.co.jp/contact/form02/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6266-contact.json)（取得 2026-10-11T03:36:15.166093+00:00）：貴社名 必須 部署名 必須
- [公式ページ](https://tazmo.co.jp/contact/form02/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6266-contact.json)（取得 2026-10-11T03:36:15.166093+00:00）：個人情報保護方針 を読み、同意いたします。 売り込みを目的としたお問い合わせではありません。

### 6278 ユニオンツール

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式お問い合わせ一覧にIR専用の問い合わせリンクがある。
- 内容によって回答に時間がかかる場合や回答できない場合がある。営業・セールス・勧誘は拒否。

注意・未確認：公式IRリンクはHTTP。GETで得たページはJavaScript読み込み案内だけで非hidden入力欄は0件。HTTPSの同一URL取得はTLS検証のupstream503で失敗。実入力欄と個人向け条件は未確認で、送信経路の運用確認が必要。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.uniontool.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6278-contact.json)（取得 2026-10-11T03:40:18.108984+00:00）：IRに関するお問い合わせ お問い合わせはこちら
- [公式ページ](https://www.uniontool.co.jp/contact/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6278-contact.json)（取得 2026-10-11T03:40:18.108984+00:00）：お問い合わせの内容によっては、回答に時間がかかる場合やお答えできない場合もございます。
- [公式ページ](http://ynirnem.uniontool.co.jp/info/Inqform.nsf/fmLoad?OpenForm&cd=ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6278-ir-form.json)（取得 2026-10-11T03:40:45.835873+00:00）：ただいま読み込み中です。しばらくお待ちください．．．

### 6339 新東工業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- IR情報専用フォームを総務・法務部が案内。会社名・部署名・役職・持ち株数は任意表示。
- 氏名・フリガナ、メールと確認欄、電話番号、質問内容、プライバシーポリシー同意が必須表示。
- 窓口に月～金9:00～12:00、13:00～17:00（祝祭日・会社休日除く）の受付時間がある。フォーム返信期限の保証ではない。

注意・未確認：公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.sinto.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6339-form.json)（取得 2026-10-11T03:37:28.363413+00:00）：IR情報に関するお問い合わせ 総務・法務部 IR情報に関するご相談は、私たちにお任せ下さい。
- [公式ページ](https://www.sinto.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6339-form.json)（取得 2026-10-11T03:37:28.363413+00:00）：メールフォーム 任意 会社名 任意 部署名 任意 役職 必須 お名前
- [公式ページ](https://www.sinto.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6339-form.json)（取得 2026-10-11T03:37:28.363413+00:00）：任意 持ち株数 株
- [公式ページ](https://www.sinto.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6339-form.json)（取得 2026-10-11T03:37:28.363413+00:00）：受付時間／月～金曜日 9:00～12:00、13:00～17:00（祝祭日・弊社休日を除く)
- [公式ページ](https://www.sinto.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6339-form.json)（取得 2026-10-11T03:37:28.363413+00:00）：必須 お問い合わせ内容 必須 送信確認

### 6387 サムコ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式ページがIR専用問い合わせフォームを案内し、担当部門が内容確認後に連絡すると説明。

注意・未確認：フォームはJavaScript経由の埋め込み。GETで取得したHTMLではIRの実入力欄を確認できず、取得したフォーム欄はサイト内検索のみ。必須欄・個人向け条件は未確認。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.samco.co.jp/contact/investor/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6387-contact.json)（取得 2026-10-11T03:36:16.203831+00:00）：IRに関する お問い合わせ
- [公式ページ](https://www.samco.co.jp/contact/investor/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6387-contact.json)（取得 2026-10-11T03:36:16.203831+00:00）：下記フォームにてお問い合わせいただくと、担当部門より内容を確認した後、ご連絡させていただきます。
- [公式ページ](https://www.samco.co.jp/contact/investor/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6387-contact.json)（取得 2026-10-11T03:36:16.203831+00:00）：必要事項をご入力の上、「確認画面へ進む」ボタンを押してください。

### 6532 ベイカレント

確認：IRメール確認。個人条件の明示未確認。窓口候補。

公開IRメール：`ir@baycurrent.co.jp`。

取得範囲の受付条件：

- 公式「お問い合わせ」ページにIR専用メールを明記。取得本文には個人受付制限・返信条件の明記はない。

注意・未確認：公開GETでの窓口確認のみ。実際の回答可否・所要時間・フォーム送信の成功は未検証。

根拠：

- [公式ページ](https://www.baycurrent.co.jp/contactus/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-6532-contact.json)（取得 2026-10-11T03:37:07.652847+00:00）：IRに関するお問い合わせ ir@baycurrent.co.jp

### 6914 オプテックスグループ

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式お問い合わせ一覧が「株式投資家情報およびオプテックスグループ」に関する用途として当フォームを指定。
- 個人情報保護の同意欄、メールアドレスと確認欄、質問本文欄がある。セキュリティ確認チェックの案内がある。
- フォーム内の説明は会社・Webサイト全般の問い合わせも含む。

注意・未確認：セキュリティ確認の実動作と個人IR受付の明示は未確認。IRメール配信登録は問い合わせ用メールアドレスとして扱っていない。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.optexgroup.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6914-contact.json)（取得 2026-10-11T03:36:16.408238+00:00）：株式投資家情報および オプテックスグループに関する お問い合わせ お問い合わせフォームへ
- [公式ページ](https://www.optexgroup.co.jp/inquiry/form.php)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6914-form.json)（取得 2026-10-11T03:37:28.413276+00:00）：個人情報の保護について 同意する
- [公式ページ](https://www.optexgroup.co.jp/inquiry/form.php)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6914-form.json)（取得 2026-10-11T03:37:28.413276+00:00）：E-mail アドレス (半角英数字) E-mail アドレス (確認用) お問い合わせ内容
- [公式ページ](https://www.optexgroup.co.jp/inquiry/form.php)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6914-form.json)（取得 2026-10-11T03:37:28.413276+00:00）：セキュリティ向上のため、下記に必ずチェックして下さい。

### 6947 図研

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IRサイトの問い合わせリンクはtype=IR付きフォーム。問い合わせ種別に「IR（投資家向け情報）について」がある。
- 質問内容、氏名・フリガナ、会社名／団体名、メールと確認欄、電話番号、個人情報同意が必須表示。
- 電子メールでの展示会・セミナー・新製品等の案内は任意のオプトインで、同意しない場合はチェックを外す案内。

注意・未確認：会社名／団体名が必須表示で、所属のない個人の記入方法は未確認。製品サポートは別窓口。入力例example@zuken.co.jpは公開IR受付メールとして扱っていない。 / 公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.zuken.co.jp/contact/?type=IR)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6947-ir-form.json)（取得 2026-10-11T03:40:18.103058+00:00）：お問い合わせ種別 必須 ▼選択▼ 製品/ソリューションについて IR（投資家向け情報）について
- [公式ページ](https://www.zuken.co.jp/contact/?type=IR)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6947-ir-form.json)（取得 2026-10-11T03:40:18.103058+00:00）：会社名/団体名 必須
- [公式ページ](https://www.zuken.co.jp/contact/?type=IR)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6947-ir-form.json)（取得 2026-10-11T03:40:18.103058+00:00）：メールでのご案内についての オプトイン 任意
- [公式ページ](https://www.zuken.co.jp/contact/?type=IR)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-6947-ir-form.json)（取得 2026-10-11T03:40:18.103058+00:00）：個人情報取扱いへの同意 必須 同意する

### 7071 アンビスホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IR問い合わせページの「入力に進む」からcloud.swcms.netのIR専用フォームへリンク。
- 氏名・ふりがな・メールと確認用メール・問い合わせ内容・会社/組織名・電話番号が必須。問い合わせ内容は最大2000文字。
- 時間を要する場合や回答を差し控える場合があり、土日祝・夏期・年末年始等は翌営業日以降。
- 回答は個人宛て。会社の許可なく、回答の一部/全部を問い合わせ目的以外で使用することを遠慮する条項がある。

注意・未確認：会社・組織名が必須だが、所属のない個人の記入方法や個人投資家受付の明示は確認できていない。虚偽の所属で入力しない。 / 公開GETで入力欄を確認したのみで、入力・送信・返信は未検証。

根拠：

- [公式ページ](https://ir.amvis.com/ja/ir.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7071-ir-current.json)（取得 2026-10-11T03:42:04.458699+00:00）：IRお問い合わせ フォームからのお問い合わせ
- [公式ページ](https://cloud.swcms.net/amvis-irPublic/ja/ir/inquiry1.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7071-form.json)（取得 2026-10-11T03:39:18.510712+00:00）：お問い合わせ内容 必須 ※最大2000文字で入力してください 会社・組織名 必須 部署名 役職名 電話番号 必須
- [公式ページ](https://cloud.swcms.net/amvis-irPublic/ja/ir/inquiry1.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7071-form.json)（取得 2026-10-11T03:39:18.510712+00:00）：お問い合わせの内容によっては、返信に時間がかかる場合や回答を差し控えさせていただく場合がございますので、あらかじめご了承ください。
- [公式ページ](https://ir.amvis.com/ja/ir/contact1.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7071-contact.json)（取得 2026-10-11T03:37:05.857302+00:00）：お問い合わせいただきました内容についての当社からの回答は、お客様個人に宛てたものです。弊社からの回答の一部または全てを、弊社の許可なくお問い合わせの目的以外でご使用になることはご遠慮ください。

### 7685 ＢｕｙＳｅｌｌ　Ｔｅｃｈｎｏｌｏｇｉｅｓ

確認：案内・リンクのみ。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 公式IRサイトから「IRに関するお問い合わせ」ページへのリンクを確認。個人受付・返信条件は取得本文には明記されていない。

注意・未確認：公開GETでIRページ見出しは確認できたが入力欄は取得できない。JS描画等の可能性がありフォーム本体・必須項目・実際の送信可否は未確認。 / 回答可否・返信条件・個人受付条件は未確認。

根拠：

- [公式ページ](https://buysell-technologies.com/contact/form-ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7685-contact.json)（取得 2026-10-11T03:37:05.129793+00:00）：IRに関するお問い合わせ \| 株式会社BuySell Technologies（バイセルテクノロジーズ）
- [公式ページ](https://buysell-technologies.com/contact/form-ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-7685-contact.json)（取得 2026-10-11T03:37:05.129793+00:00）：CONTACT お問い合わせ IRに関するお問い合わせ 株式会社BuySell Technologies

### 7734 理研計器

確認：質問入力欄確認。個人受付の明示あり。窓口候補。

取得範囲の受付条件：

- IR専用フォームの企業・団体名欄に、個人は「個人」と記入する指示がある。
- 氏名・フリガナ、Emailと確認欄、電話番号、企業・団体名、質問内容、個人情報同意が必須表示。

注意・未確認：公開ページのGETのみ。フォーム入力・送信・到達・実返信は未検証。 / 窓口の確認は投資適性や利益の事実を示さない。質問論点は公開資料で検証する前の案。 / 返信期限の保証と決算前の沈黙期間は、今回取得した窓口ページでは確認していない。

根拠：

- [公式ページ](https://www.rikenkeiki.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-7734-contact.json)（取得 2026-10-11T03:36:17.665069+00:00）：IRに関するお問い合わせ
- [公式ページ](https://www.rikenkeiki.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-7734-contact.json)（取得 2026-10-11T03:36:17.665069+00:00）：企業・団体名 必須 ※ 個人の方は [ 個人 ] と記入してください
- [公式ページ](https://www.rikenkeiki.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-7734-contact.json)（取得 2026-10-11T03:36:17.665069+00:00）：お名前 必須 フリガナ 必須 Email 必須 Email[確認入力] 必須 電話番号 必須
- [公式ページ](https://www.rikenkeiki.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/mfg-7734-contact.json)（取得 2026-10-11T03:36:17.665069+00:00）：お問い合わせ内容 必須 個人情報の取り扱い 必須 同意する

### 8078 阪和興業

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 中期経営計画 コーポレート・ガバナンス 財務ハイライト 経営指標の推移 事業セグメント情報 格付情報 株主・株式関連情報 株式基本情報 配当政策 株主総会情報 株価情報（外部リンク） 電子公告 IRライブラリー 決算短信 決算ハイライト 有価証券報告書 決算説明資料 事業報告書 統合報告書／ アニュアルレポート IR関連情報 ディスクロージャー・ ポリシー よくあるご質問 免責事項 お問い合わせ 個人のお客様用フォーム 法人のお客様用フォーム HANWA co.,LTD. 企業情報 Company Informatio

注意・未確認：自動抽出。個人の利用条件・会社名必須・返信条件は人の点検が必要。送信・回答実績は未確認。

根拠：

- [公式ページ](https://www.hanwa.co.jp/contact/form1/)／[保存証拠](evidence/8078/05.json)（取得 2026-10-11T04:03:53.375985+00:00）：※必須 お問い合わせ項目 営業について 投資家情報について 採用について その他 ※必須 お名前 （ 全角で記入 例：鈴木 一郎 ） 郵便番号 - （半角数字で記入 ） ご住所 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈
- [公式ページ](https://www.hanwa.co.jp/ir/)／[保存証拠](evidence/8078/04.json)（取得 2026-10-11T04:03:51.833629+00:00）：中期経営計画 コーポレート・ガバナンス 財務ハイライト 経営指標の推移 事業セグメント情報 格付情報 株主・株式関連情報 株式基本情報 配当政策 株主総会情報 株価情報（外部リンク） 電子公告 IRライブラリー 決算短信 決算ハイライト 有価証券報告書 決算説明資料 事業報告書 統合報告書／ アニュアルレポート IR関連情報 ディスクロージャー・ ポリシー よくあるご質問 免責事項 お問い合わせ 個人のお客様用フォーム 法人のお客様用フォーム HANWA co.,LTD. 企業情報 Company Informatio

### 9279 ギフトホールディングス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 「お問い合わせ内容」で「IRに関するお問い合わせ」を選択する。株主優待・eチケットは別窓口。
- お名前、メールアドレス、問い合わせ詳細等が必須。匿名・不正確な情報では返信できない。返信希望の選択肢がある。
- 電話での対応となる場合、返信に数日を要する場合、回答できない場合がある。送信時にIPアドレス取得、続行でプライバシーポリシー同意。

注意・未確認：公開GETでの窓口確認のみ。実際の回答可否・所要時間・フォーム送信の成功は未検証。

根拠：

- [公式ページ](https://www.gift-group.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9279-contact.json)（取得 2026-10-11T03:37:05.475297+00:00）：広報・IRに関するお問い合わせは、下記のお問い合わせフォームに必要事項をご入力のうえ、 送信ください。追って、担当よりご連絡いたします。
- [公式ページ](https://www.gift-group.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9279-contact.json)（取得 2026-10-11T03:37:05.475297+00:00）：お問い合わせ内容 * IRに関するお問い合わせ その他のお問い合わせ お名前 * メールアドレス * 電話番号 お問い合わせ詳細 *
- [公式ページ](https://www.gift-group.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9279-contact.json)（取得 2026-10-11T03:37:05.475297+00:00）：※ 匿名もしくは正確な情報が入力なされていない場合、返信は出来かねます。
- [公式ページ](https://www.gift-group.co.jp/contact/ir)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9279-contact.json)（取得 2026-10-11T03:37:05.475297+00:00）：※ 返信までに数日いただく場合や、お答えできない場合がございますので、あらかじめご了承ください。

### 9416 ビジョン

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 氏名、ふりがな、メール/確認用メール、電話番号、ご質問・ご意見、個人情報取扱同意が必須として表示。会社名・部署/役職欄もある。
- IR情報問い合わせの専用フォームを確認。個人限定/機関限定という受付条件は取得本文には見当たらない。

注意・未確認：公開本文のIRメール表示は[email protected]に置換されているため、アドレスを推測して一覧へ追加していない。 / フォームには状態確認の表示がある。公開GETで入力欄を確認したがJS実行・送信・返信の動作は未検証。

根拠：

- [公式ページ](https://www.vision-net.co.jp/ir/guide/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9416-contact.json)（取得 2026-10-11T03:37:06.548023+00:00）：IR情報お問い合わせ フォームの状態を確認しています... 氏名 必須 ふりがな 必須 会社名 部署・役職 メールアドレス 必須 確認のためもう一度入力してください 電話番号 必須
- [公式ページ](https://www.vision-net.co.jp/ir/guide/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9416-contact.json)（取得 2026-10-11T03:37:06.548023+00:00）：ご質問・ご意見 必須
- [公式ページ](https://www.vision-net.co.jp/ir/guide/contact.html)／[保存証拠](../ir-contacts-2026-10-11/evidence/svc-9416-contact.json)（取得 2026-10-11T03:37:06.548023+00:00）：個人情報の取り扱いについて 同意する 必須

### 9558 ジャパニアス

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- 私は、「 プライバシーポリシー 」の内容を理解、確認し、その内容に同意します。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / 会社名・部署・役職の欄は存在するが、今回のHTML本文や非隠しフィールド属性では必須性を確認できていない。 / https://jna.co.jp/ir/ はIR問い合わせページへ転送されるため、IRトップには現行の /investors を保存。

根拠：

- [公式ページ](https://jna.co.jp/ir_contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9558-ir.json)（取得 2026-10-11T03:35:43.279287+00:00）：IR情報に関するお問い合せ CONTACT HOME IR情報に関するお問い合せ
- [公式ページ](https://jna.co.jp/ir_contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9558-ir.json)（取得 2026-10-11T03:35:43.279287+00:00）：会社名 部署 役職 お名前 電話番号 メールアドレス お問合せ内容
- [公式ページ](https://jna.co.jp/ir_contact)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9558-ir.json)（取得 2026-10-11T03:35:43.279287+00:00）：私は、「 プライバシーポリシー 」の内容を理解、確認し、その内容に同意します。

### 9692 シーイーシー

確認：質問入力欄確認。個人条件の明示未確認。窓口候補。

取得範囲の受付条件：

- フォーム末尾の「個人情報の取り扱いへの同意」をご確認いただき、「同意する」にチェックのうえ、 内容確認画面へお進みください。
- ※誠に恐れ入りますが、売り込み・営業のご連絡はお断りをしております。
- お問い合わせの内容によって返信に時間がかかる場合や、回答を差し控えさせていただく場合がございます。 あらかじめご了承ください。

注意・未確認：公開ページのGET確認のみ。フォーム入力・送信、メール送付、返信の実在や所要時間は未検証。 / 個人投資家による窓口利用の可否は明記されていない。 / 質問論点は仮説案であり、現在の業績・成長性や投資適性を確認したものではない。 / プライバシー説明中のprivacy@cec-ltd.co.jpは個人情報窓口でありIRメールとして採用していない。 / 会社名・部署・住所等の欄はあるが、本文と非隠し属性だけでは全項目の必須性を確定していない。

根拠：

- [公式ページ](https://www.cec-ltd.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-contact.json)（取得 2026-10-11T03:39:52.893071+00:00）：INQUIRY IRに関するお問い合わせ TOP お問い合わせ IRに関するお問い合わせ
- [公式ページ](https://www.cec-ltd.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-contact.json)（取得 2026-10-11T03:39:52.893071+00:00）：フォーム末尾の「個人情報の取り扱いへの同意」をご確認いただき、「同意する」にチェックのうえ、 内容確認画面へお進みください。
- [公式ページ](https://www.cec-ltd.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-contact.json)（取得 2026-10-11T03:39:52.893071+00:00）：※誠に恐れ入りますが、売り込み・営業のご連絡はお断りをしております。
- [公式ページ](https://www.cec-ltd.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-contact.json)（取得 2026-10-11T03:39:52.893071+00:00）：お問い合わせ内容 会社名 部署名 お名前 メールアドレス 電話番号 ご住所 郵便番号
- [公式ページ](https://www.cec-ltd.co.jp/inquiry/ir/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-contact.json)（取得 2026-10-11T03:39:52.893071+00:00）：＊IRに関する問い合わせ対応
- [公式ページ](https://www.cec-ltd.co.jp/inquiry/)／[保存証拠](../ir-contacts-2026-10-11/evidence/it-9692-inquiry-directory.json)（取得 2026-10-11T03:37:41.222555+00:00）：お問い合わせの内容によって返信に時間がかかる場合や、回答を差し控えさせていただく場合がございます。 あらかじめご了承ください。

