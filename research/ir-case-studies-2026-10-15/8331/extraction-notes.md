# 保存済み配当資料からの数値抽出下書き

[disclosed-facts-draft.json](disclosed-facts-draft.json)は、数値の原文・単位・期間ラベルを出典点検へ渡すための`source`・`review`・`facts`形式の下書きである。新規GET、DB登録、normalizerの実行、予想の採用、DDM計算、IR送信は行っていない。

## 保存元と照合

対象は[元manifest](manifest.json)の配当ページ、既存source ID `chibabank.8331.05`。URLは `https://www.chibabank.co.jp/investor/services/stock/dividend`、会社IDは`jp:8331`。

- 元取得時刻：`2026-10-15T01:56:32.230904+00:00`。新しい点検時刻で上書きしていない。
- 原バイト：`evidence/3693f485ea9412f931089877196e9a262810119c312f7e6231d0d0660fa600dc.raw`。
- 原バイトSHA-256：`3693f485ea9412f931089877196e9a262810119c312f7e6231d0d0660fa600dc`。
- 再現した本文SHA-256：`d437b351019996ff69b682df9dd3f41b91ae1ae50d33d037ef1db40b40ba93a5`。
- 元manifest・`evidence/05.json`の原バイトSHAと取得時刻が一致。再抽出した本文も、`evidence/05.txt`・05.jsonの本文と一致した。
- 公表・更新日時は元記録で不明のため`published_at:null`。取得時刻を公表時刻としていない。

抽出は元調査時と同じ処理を保存原文へオフラインで適用した。UTF-8で読み、script/styleブロックを除き、残るHTMLタグを改行へ置換し、HTML実体参照を復元して空行をまとめる。ブラウザやJavaScriptは実行しない。再現の中心部分は次のとおり。

```python
raw = saved_raw_path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == original_raw_sha256
body = raw.decode("utf-8", errors="replace")
clean = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", body, flags=re.I | re.S)
content = unescape(re.sub(r"<[^>]+>", "\n", clean))
content = re.sub(r"\n[ \t\r\n]*\n", "\n", content)
assert content == saved_05_text
```

この処理は元のウェブページの可視表示・レイアウトを完全に再現するものではない。数値を抽出した範囲は「配当情報」の表ヘッダーと当期予想行であり、元ページの全項目を内容面で確認済みとは主張しない。HTMLなのでPDF頁番号はなく、各factに見出し・行・列を記録した。

## 点検へ渡す3項目

同じ逐語引用に、列見出し、当期の予想ラベル、数値と円/%がすべて入っている。

```text
数値表
決算期
1株あたりの年間配当額(円)(うち記念配当)
1株あたりの中間配当額(円)
配当性向(連結)
2027年3月期（予想）
64.0(-)
32.0
41.1%
```

| fact | 原文値・単位 | 原文の位置と解釈の範囲 |
|---|---|---|
| 年間DPS | `64.0`・`円` | 当期予想行の年間配当列。括弧内の`-`は「うち記念配当」欄の表示として残し、数値に含めていない。会社の年間予想で、実績や独自予測ではない。 |
| 中間DPS | `32.0`・`円` | 同じ行の中間配当列。年間64.0円へ別途加算する金額ではない。 |
| 連結配当性向 | `41.1`・`%` | 同じ行の「配当性向(連結)」列。`unit:ratio`で点検へ渡すが、資本コスト、配当利回り、規制資本比率ではない。分母利益の内容・算定方法は別途未点検。 |

3件とも`kind:issuer_guidance`。`raw_period_label`は逐語の「2027年3月期（予想）」とし、period descriptorには同じlabelと`fiscal_year_end_month:2027-03`を保存した。開始日・終了日を補わず、年間と中間を`portion`・scopeで分けた。descriptorを保存したこと自体は、他の資料・モデル期間との意味的一致を認定するものではない。

`review`のauthor・recorded_at・rationaleは今回の抽出点検の記録であり、利用者が数値を投資方針として承認した記録ではない。`source.content`内でbasis_quoteが一致し、その引用にraw_value・raw_unit_label・raw_period_labelが含まれることを3件とも確認した。`validate_source`でsource形状も検証した。

## 権利基準日・支払時期の有限確認

同じ抽出本文で「権利」「基準日」「支払」「支払い」「支払開始」「期末」をそれぞれ検索し、該当は0件。「中間」は表の列名と「中間配当に関する取締役会決議のお知らせ」の2箇所だった。リンク先の決議文書は今回開いていない。リンク名やURL中の年月日から、当期予想の権利基準日・支払開始日を作っていない。

したがって、以下は未確認のままである。

- 当期の中間・期末それぞれの権利基準日、権利付き最終日、配当の支払開始時期。
- 評価時点に新規取得した投資家が、会社年度のどの分配を受け取れるか。
- 株式種類、株式分割等の基準と、モデルが採用する1株単位との接続。

**会社年度の年間配当予想64.0円は、投資時点からの残余配当や「1年後に受け取る64.0円」と同じではない。** 中間32.0円を年間予想へ二重加算せず、年度予想をDDMの年末DPS配列へ自動採用しない。

## 維持する欠損

[既存の研究下書き](draft.json)で未充足としていた、最新決算本文、規制資本・資本配賦の期間対応、将来DPS系列、予測期と安定期それぞれの株主資本コスト、終価翌期DPS、永久配当成長率、現在株価、事前確率・返信尤度の欠損は解消していない。

この抽出は、そのうち「公表された当期予想値の出典を保持できる」ことだけを準備した。銀行の投資適格性、配当の保証、評価額、送信可能性を確認したものではなく、IR窓口未確認も維持している。

## 続く構造化の実行記録

上記の初期下書き作成後、`location` をHTMLの位置説明オブジェクトへ整え、`normalize-facts` を実行した。[disclosed-facts-normalized.json](disclosed-facts-normalized.json)に原典と派生資料のbundleを保存。派生資料の取得日時は `2026-10-15T02:20:16.567964+00:00` で、元資料の取得日時は保持した。

年間DPSは `64.0 JPY-per-share`、中間DPSは `32.0 JPY-per-share`、配当性向は `0.411 ratio` へ構造化された。引用とラベルの存在および換算を確認した結果であり、モデルへ採用した値ではない。`theses: []`、`financial_inputs_verified: false`、`forecast_values_automatically_adopted: false` を維持した。実DB登録・ネットワーク再取得・DDM評価・IR送信は行っていない。
