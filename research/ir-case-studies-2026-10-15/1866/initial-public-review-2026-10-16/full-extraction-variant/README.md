# 北野建設（1866）：全文テキスト保存variant

**PDF全文を機械抽出し、既読範囲を広げずにsourceを作り直した。** 新GET・DBアクセス・新規の予測／財務数値・意味判断は0。旧partial source、引用、manifestを含む元成果物は変更していない。

| 旧PDF source | 新PDF source | 全抽出ページ | 意味・画像確認済みページ |
|---|---|---|---|
| `case-public:0648dcf6e2d3ba6971c180941b72c642db56cdf86f904f781889fcb3b4f59658` | `case-public:52347b3c8a8157bfc5874e644276ea0b40ec920537b44da2d062ba5b5fdf834b` | 11 | 1, 2, 4 |

`pdftotext -layout` による全ページ出力を `text/*-full.txt` に保存し、form-feed数とpdfinfoのページ数を照合した。全体抽出は後で保存原典の未読箇所を参照できるようにする保存処理であり、全冊の内容確認ではない。短信の意味／画像確認は1・2・4ページ、説明資料は1〜3ページのまま。目次の3ページを抽出しても本文読解の範囲には含めていない。

既存 `scripts/build_case_source_bundle.py` の `build_case_source_bundle()` に、原captureを保持するsnapshot key変換と、元rawの同一SHAコピー・全文テキストを渡した。中間出力は `shared-builder-output.json`、入力は `source-map.json` / `source-manifest-adapter.json` / `snapshot-adaptation.json`。その後、元作者・既読範囲・partial由来をmetadataに明示して共有stable IDを計算した。最終のsource-only bundleは `source-bundle.json`（3 source、companies/theses空）。HTML sourceは旧オブジェクトを完全保持する。

原URL・取得終了時刻・raw SHA・公表日を保持した。公表日はday精度、exactな公表時刻不明の `published_at:null` も同じであり、全文抽出時刻を公表／取得／DB初回保存時刻にはしていない。

`source-id-and-prefix-mapping.json` で旧→新IDを対応付けた。すべての旧部分contentが新全文のexact prefixとして一致し、既読7引用は全て同じ文字offsetで一致したためreboundは0。`source-quotes.json` は新ID・全文SHA・全文ファイル参照へ付け替え、旧ID／旧offsetも残した。既存6表示tokenの位置も一致し、数値・予測を追加／再評価していない。

`original-artifact-pins.json` は作業前の元成果物SHA、`validation.json` は旧成果物不変・raw/全文・source契約・prefix／引用対応のproducer検証。共有builderを使用したことはgeneric byte verifierのmatchedを意味しない。同verifierはこのvariantで未実行と明示した。金融入力の採用・真正性／意味の独立検証は別である。実台帳へ採用する場合の対象はこのvariantのbundleで、旧partial bundleはfile-only履歴のまま保持する。
