# 明示単位「億円→JPY」の追加

保存済み `../ir-case-studies-2026-10-15/1721/initial-public-review/03.txt` の会社業績予想頁には `（単位：億円）` と実績・計画の別列がある。この記録は当該企業の数値抽出や予測採用ではなく、原文ラベルから金額を正規化するデータ契約の単一拡張である。新しいネット取得・DB登録は行っていない。

追加は `("億円", "JPY"): "100000000"` だけ。1億円は100,000,000円であり、推計式や金融判断基準ではない。億円から1株値・比率への変換、兆円・別表記への推測対応は加えない。原文の期間・予想主体・列・連結範囲・指標定義・著者の意味・モデル入力適合は未確認のままとする。

`baseline.json` はproduction編集前に作成した。既存13単位mapping×4kindの52合成requestについて、full bundleのcanonical SHA256・derived ID・derived content SHA256と編集前production file SHA256を保存した。実企業の財務数値をテスト入力として採用していない。比較はfull bundleを対象とするため、旧schema/version/default/metadata/limitationsも含めた出力の不変性を点検できる。

対象検証: `tests/test_oku_yen_facts.py`。換算・小数精度/符号・欠測と0の区別・非対応mapping・原文ラベル・時点制約・再抽出/改竄検出・52既存fixtureの不変性を点検する。全文引用の支持や財務的意味の独立検証を行ったとは扱わない。

親の全件検証は1,296件・37.103秒で成功（[tests.log](tests.log)）。1721の[実績・会社計画12項目](../ir-case-studies-2026-10-15/1721/actual-and-plan-facts/README.md)も原文引用・Decimal算術・再抽出で照合した。実企業の数値は研究ファイルでありモデル採用はない。
