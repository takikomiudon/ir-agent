# 2929 原公表連結EPS/BPS：訂正参照付き2facts

既存normalize-facts CLIだけで、原年次短信物理1の**連結実績EPS68.61円・BPS453.35円**をreported_fact/JPY-per-shareとして保存した。標準v1のdecimal tokenで、円銭複合表示を作らない。EPSは2025-08-01～2026-07-31のannualduration、BPSは2026-07-31のinstant。原p1の円 銭/対象期/連結scopeと、既読p21のordinary親会社利益・平均株数と期末純資産・普通株数の違いを引用参照で保持した。個別△8.20/535.45、会社予想75.75、丸めtotal再計算は使っていない。

原本と後発訂正sourceの全objectは不変。normalizerのネイティブ2source出力をnormalizer-output.json、原本・訂正・派生の3source引渡しbundleをnormalized-bundle.jsonとして分け、同じものと偽装しない。訂正refのID/nativeSHA/path/fileSHAと限定scopeは、既存契約のreview.rationaleを通して**派生metadata.review.rationale**にも保持し、各fact.scope.known_correctionには構造化した。派生metadataの手編集、新sourceID方式、訂正用nativeDAG辺は増やしていない。訂正を機械的に入力へ適用した/全source依存が自動検証されたとは主張しない。

訂正通知の表画像数値をテキストや新factへ変換せず、原EPS/BPSの現在妥当性・訂正後無影響も認証していない。financial_inputs_verified:false、meaning_review_required:true、独立meaning認証/金融採用/expectedvalueはfalse。raw/content/native/normalizercompactSHAを区別し、derivedの新取得時計を公表時刻や元HTTP時刻に戻さない。

model-input-audit-request.jsonは既存graham_numberの2入力pathと3sourceを明示した**入力準備のみ**。model-inputs関数は内部で評価式を計算するため今回実行せず、価格・評価額・閾値・結果は作成していない。訂正sourceは手動参照として同梱し、原本ベース派生sourceのnativeDAGが自動的に訂正をconsumeするとはしない。

再現は `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-case-studies-2026-10-15/2929/annual-per-share-disclosed-facts-2026-10-16/reproduce.py`。保存derived時計で元CLI結果bytesを再現し、3sourceの組合せ、引用/数値位置、旧25+26pinsと入力12pinsを点検する。GET・DB/Store・共有/旧file・索引更新・新規頁の意味読解・金融採用・IR送信0でfreeze。
