# URL探索用seedの出典

取得日: 2026-10-11 UTC。母集団はJPX2026年9月末のプライム・スタンダード・グロース国内普通株3695社。5桁の優先株・社債型種類株式7行を除いた。

`official_url` は親担当指定のフィールド名であり、この初期ファイルでは第三者から見つけた会社サイトURL候補である。公式ページ本文・会社との同一性・IR窓口・個人受付・返信条件はまだ確認していない。`discovery_type=third_party_unverified` は受付証拠に使わない。

- https://memo.eightban.com/kabu/marketsprimeurl — 2026-04-18掲載、本文の20260331版。コード・名称・URLの一覧1569社。現在の普通株母集団との一致1542社。
- https://toushiro.com/url-list.html — 公開URL一覧Excelへの導線。2024-10-08更新版。
- https://toushiro.com/data/list_20241008.xlsx — 3857社のコード・名称・URL。現在の普通株母集団との一致3570社。古い会社名・移転URL・上場廃止等が含まれ得るためJPXコードで絞り、実際の公式GETで確認する。

両資料を合わせ初期seed3579社、不足116社。2資料にある場合は2026年3月末版を優先。素材・取得メタデータは [evidence/discovery](evidence/discovery/) に永続化し、SHA256と相対パスを [seed-manifest.json](seed-manifest.json) に保存した。

不足はJPX新規上場会社情報 https://www.jpx.co.jp/listing/stocks/new/index.html と2024/2025/2026バックナンバーで補完中。JPX公式注記:「当該会社のウェブサイト（ＵＲＬ）は上場承認日時点の情報であり、その後変更された場合はリンクの更新は行いません。」 この公式リンクも現会社サイトへGETし同一性を再確認する。

## 補完完了

不足116社は以下のJPX公式ページの会社名リンクから全件取得できた。`seed-additions-jpx-ipo.json` に116件、`seed-missing-after-ipo.json` は空配列、`seeds-complete.json` に合計3695件を保存。先行取得作業との読み取り競合を避けるため、初期3579件の `seeds.json` は更新していない。

- 2026年: https://www.jpx.co.jp/listing/stocks/new/index.html
- 2025年: https://www.jpx.co.jp/listing/stocks/new/00-archives-01.html
- 2024年: https://www.jpx.co.jp/listing/stocks/new/00-archives-02.html

3ページのコード・会社名リンクを行単位で読み、2026年9月末の普通株コードに一致する不足分だけ採用した。2026年10月以降の新規銘柄や将来の上場予定はこの母集団に混ぜていない。追加の `source_data_as_of` は各行の上場承認日で、今日の会社サイトやIR受付を確認した日時を意味しない。公式会社URLリンクでも、上場承認日時点のURLであり変更後に更新されないとのJPX注記があるため、現会社サイトのGET確認が必要。

検証: 3695の対象コードとseedコード集合の完全一致・4桁英数字保持・重複なし・HTTP(S)URL構文・認証情報なし・タイムゾーン付き取得時刻を確認。母集団の全社に入口候補があるという確認であり、全社のIR受付が確認できたという意味ではない。

## 現在のシードと証拠の保存

2026年10月11日までの新規上場3社（640A・641A・642A）を加え、上場廃止12社を除き、現在の国内普通株は3686社。`seeds-current.json` のコード集合を `universe.csv` と照合し、3695＋3－12との完全一致、欠落・重複なしを `seed-current-validation.json` に保存した。現在のシード本体・各社調査レコードはこの証拠保存作業では変更していない。

追加3社の上場日は2026年10月1日、承認日は同年9月1日。JPX公式の原文引用・会社サイトへのリンク・業種確認資料の参照を `seed-new-listing-evidence.json` に保持した。上場承認日を上場日として扱わない。

取得済みExcel、JPXのHTML、ページの本文抽出JSON、抽出した表、取得メタデータは `evidence/discovery/` にコピーした。manifestの `response_body_sha256` は元HTTP本文のハッシュ、`archive_file_sha256` はリポジトリ内の保存ファイルのハッシュ。ExcelとJPX HTMLでは一致する。eightbanの最初の採取器は本文抽出JSONだけを保存したため、JSONファイルのハッシュと元HTTP本文ハッシュは異なる。元の可視本文・リンク・非隠し入力欄を含むJSONを保持し、元HTMLバイト列が未保存であることを明記した。抽出JSONを元HTMLとみなしてハッシュ検証しない。

初期シード内の `discovery_snapshot` にある一時パスの移動先は `seed-discovery-path-map.json` に保存した。稼働中の取得処理が読む `seeds-current.json` は上書きしていない。
