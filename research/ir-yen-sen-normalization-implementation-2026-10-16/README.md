# 明示した円・銭表示の最小normalizer拡張

factに`raw_value_format: "jpy_yen_sen"`を明示した場合のみ、原文の連続表示（例`24 円 75 銭`）をDecimalで円へ合成する。原文raw_valueはそのまま残し、成分token・単位・相対span・全体符号を保存する。`-0円05銭`は`-0.05`、`99円00銭`は`99.00`、数値0だけ`"0"`。新形式はliteral円→JPYまたはJPY-per-shareだけ、許す内部空白はASCII space/tab/U+3000だけ。改行、別符号の切取り、部分numeric token、未知format、誤comma、100銭等は拒否する。

旧単一token形式へ新flagや既定formatを足していない。新形式を1件でも含むbundleだけnormalization_version2、それ以外は従来のversion1・JSON・IDを維持する。新形式はraw_numeric_token_verified:false/raw_display_verified:true、missing/empty/standalone dashは両flag false・components:null・値null。単一token倍率は複合へ流用しない。前後の円/銭も拒否することで重複単位を切り取らない。単位は算術の指定であって1株基準の認証ではない。

reproducerは厳密int1/2だけ許し、version1のformat-bearing factとversion2のfeatureなしを保留する。後者のreasonは従来のunsupported_normalization_versionを維持。新formatを再入力へ保持し、原文から値・成分/span/flagsを再計算する。モデル消費側は未変更で、再現・kind・来歴・時点の既存holdを維持する。

編集前にmodule/消費側module/関連7testの完全bytesをbefore/へ保存し、実DBはcontextlib.closing + SQLite URI mode=roのSELECTだけで171source全objects/全rowを凍結した。全33normalized・143factsのproducer/reproducerのwhole-reportを編集前後でbyte比較し完全一致、派生source全objectも保存値と一致した。report SHAは両方c12a56bedf1eec487ecc801979ab701ab7d6e0539dff454d34f97d66ea9b1e38。afterは凍結入力からのみ算出した。

新規11testと関連旧59testの計70testが成功。非ゼロ銭・全体負符号・Unicode/horizontal/partial境界・欠損・成分改変・version・混在・150桁のDecimal context隔離・既存model消費側保留を確認。既存億円/外部予測goldenを含む関連testsをそのまま通している。全suiteは実行していない。元1904 sixbundle SHA07e79894f6727dba572e63852bf7093e3fe805547742c832e48168e14efd0ea0不変。実DBの全171source rowも末尾のRO再照合で不変。

変更はsrc/ir_agent/disclosed_facts.pyと新tests/test_yen_sen_facts.pyのみ。before/after、module.diff、capture_compatibility.py、whole-report/frozen入力、focused-tests.log、implementation.jsonを本folderへ保存した。実会社の新numeric fact生成/再取込は0で、1904のraw表示候補も未変更。分割前/後/年間参考値の同値性、年間配当合算、DDM列、将来利益、財務採用は認定しない。GET/DB書込/金融gate弱体化/CLI変更/依存追加0。ここから独立レビューへ引き渡す。
