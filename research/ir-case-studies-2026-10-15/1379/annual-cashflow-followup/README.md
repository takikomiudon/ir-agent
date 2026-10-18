# 1379：通期CF・資金/CB資料への限定追補（取得経路で停止）

**通期CFとCB注記の本文は今回取得できていない。** 公式索引からの明示導線を追い、一覧scriptと配信先robotsの2 GETはいずれも200だったが、robotsの禁止規則を確認したためfeedへのHTTP前に停止した。会社財務資料のカバレッジ増加は0件で、実DB取り込みは推奨しない。

| capture | 取得したもの | 元取得UTC | 結果 |
| --- | --- | --- | --- |
| 01 | 公式短信索引がsrcで明示する`tanshin.js` | 2026-10-15T05:45:19.451193+00:00 | 200。テキスト保存のみ、実行なし。通期PDFの直接リンクはない。 |
| 02 | `https://ssl4.eir-parts.net/robots.txt` | 2026-10-15T05:47:01.557531+00:00 | 200。下記禁止を確認。 |

```text
User-agent: *
Disallow: /
```

元の3 GET上限は親の指示で、この成功導線のrobots/feed/PDFを含む最大4 GETへ限定変更された。実行は2 GETのみ。`press_1.js`への次URLは保存script内のリテラルと明示されたhttps固定置換から確認できたが、robots判定がfalseとなり**HTTP未実行**。通期PDFのURL自体は未確認で、PDFや追加CB資料へのGETもない。HTTP503等による本文失敗とは区別する。新host・別経路・検索・障害診断・追補phaseは行っていない。

このため2026/3期の年間CFO/投資CF/設備取得支出/現金税/利息/有利子負債/CB条件の正式資料中の頁・行は未確認である。存在しない、開示がない、値が0という結論ではない。[review.json](review.json)に各必要原文と埋めていない項目を個別に保存した。

既存のQ1短信（2027/3期、2026年4月1日〜6月30日）のPDF11頁は四半期連結CF未作成と減価償却費を明記する。これは過去通期CFとは別の期間/概念で、減価償却やQ1利益から年間CFOを補わない。現年度の通期会社予想も過去通期実績とは別であり、年間CFOを将来アンレバードFCFFへ、EPS基本/希薄化列を将来株数へ転用しない。原文未取得のCB条件も仮定しない。

[manifest.json](manifest.json)と各`01.json`/`02.json`に原バイト・元取得時刻・HTTP時刻/ヘッダー・本文・SHAを保存。[link-provenance.json](link-provenance.json)は保存済み公式索引rawのsrc位置と固定置換の原文を追跡する。[source-quotes.json](source-quotes.json)は短い逐語引用2件、[not-requested.json](not-requested.json)はHTTP前の禁止判断を記録する。[source-bundle.json](source-bundle.json)は取得経路の研究証跡2件だけで、金融本文ではない。

[validation.json](validation.json)で2 raw/text/snapshotのSHA、source ID/契約、引用位置、robots判断と既存94ファイル不変を確認した。今回確認したrobotsを、以前のPDF取得時点にも同じ規則が存在し認知していたという履歴へ後付けしない。旧保存済みPDF/原典は改変・削除していない。DBアクセス/production変更/正規化/モデル採用は0件、`financial_inputs_verified:false`、`meaning_review_required:true`、`model_adopted:false`を維持する。
