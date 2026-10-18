# 円・銭の原表示を保持する最小拡張案

現APIで3表示すべてを忠実なnumeric factにする代替はない。`24.75`は原文に存在せず、`24`だけでは75銭を失う。00銭の99円・198円は既存の限定的な人手確認で整数tokenを抽出できるが、非ゼロ銭を扱う機能ではない。当面の正しい現状は既存raw-display候補の保持である。

**提案はfact単位の任意指定 `raw_value_format: "jpy_yen_sen"` のみ追加すること。** `raw_value`には原文の連続した`24 円 75 銭`全体を残す。原典・引用・単位と期間ラベル・位置・会社予想という主体は変えない。金額の合成結果は既存の`value`へ出し、原文にない小数をraw tokenとして追加しない。

## 現在確認した契約

`disclosed_facts.py`はstrict numeric tokenと固定倍率の対応表、Decimalのlocal contextを使う。複合表記/銭の対応はない。`reproduce_disclosed_fact_source`は現在version1だけを許可し、原典から入力を再構成して本文・metadata・IDを照合する。`model_inputs.py`はこの再現結果とkind/value pathを使うため、値だけ合わせた改変を通す設計にはしない。CLIの既存JSON転送で足り、新コマンド・パッケージは不要と考える。これはコードを読んだ結論で、実装済みの説明ではない。

## 提案する最小契約

- 未指定は旧処理を完全維持する。既定formatや新flagを旧出力へ足さない。null/未知formatも推測せず拒否する。
- 新形式は`円`→`JPY`または`JPY-per-share`だけ。円と銭の単位文字を含む単一行をfullmatchする。内部のASCII space/tab/全角空白だけを許し、改行・改ページ・NBSP・先頭末尾の余白は拒否する。銭はASCII1–2桁・0–99。円は整数と正しい3桁commaだけ。小数円、全角数字、指数、銭への符号、100銭の繰上げ、注記込みrawは扱わない。
- 符号は先頭の`+/-/△/▲`1個が全体に掛かる。`-0円05銭`も負の0.05円になる。`Decimal(円)+Decimal(銭)*Decimal("0.01")`を明示local context内で行い、float・分割調整・年間合算を使わない。数値0の表示だけ既存同様`"0"`へまとめる。
- 元表示と各成分のraw token・単位・raw_value内の相対位置を保存して再現する。複合では`raw_numeric_token_verified:false`と別の`raw_display_verified:true`を使う。旧単一tokenの`explicit_unit_multiplier`を複合へ流用せず、円1・銭0.01の成分倍率を記録する。null/空欄/独立dashは0にせず、両認証flagをfalseにする。

新形式が1件でもあるbundleだけ`normalization_version:2`にする案を推す。旧readerは現在これを保留する。新reproducerは1と2を区別し、formatを再入力へ保持して原表示から全成分・値・flagsを再計算する。全旧形式のbundleはversion1・JSON・IDを完全維持する。version1のまま新parserを混ぜる案は旧readerの再現能力を誤表示し、全件version2化は無関係な既存IDを変えるため採らない。混在bundleは2だが旧形式fact object自体は維持する。

## 1904で守る境界

保存p2画像を確認した。99円00銭は分割前の中間予想、24円75銭は分割後の期末予想、【198円00銭】は会社表示の分割前換算の年間参照である。会社は年間欄を単純合計できないと注記している。解析成功を同一株数基準の年間DPS、実施済分割、支払実績、将来DDM配当列へ変換しない。金額変換と期間/列/株式基準の意味確認は別であり、financial_inputs_verifiedはfalseのまま。

受入済み6factのbundle SHAは`07e79894f6727dba572e63852bf7093e3fe805547742c832e48168e14efd0ea0`、使用normalizer SHAは`0b65d28b6d8ad17824b364c4997f8f94b7aab987cd431a5657aa1b7ae6d57cca`。今後もこれを上書きせず、新形式は別の派生記録として作る。

## 検証と実装前の固定

`design.json`に文法/欠損/符号/単位/改行/部分一致/tamper/極端なDecimal context/旧ID不変のテスト案と、before/afterコード・固定replay計画を記録した。既存6factと旧golden fixtureを旧実装のまま保存し、同じnowで旧JSON/IDを比較する。再現による数値一致も金融的意味の認証にはしない。今回はテスト案の作成までで、normalizerやテストは実行していない。

`evidence.json`は原典/画像/既存コードと1904全既存ファイルのSHA、原文位置、読取範囲を持つ。`validation.json`はその不変性と文書内の整合だけを検証する。GET、DB接続、実装、旧ファイル変更、numeric fact生成、モデル採用、質問作成・送信はすべて0。
