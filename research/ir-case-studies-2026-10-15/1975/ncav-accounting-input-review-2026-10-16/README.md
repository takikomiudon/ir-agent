# 1975 保存会計値によるNCAVの限定再現

maxgfr/crible maintainer文書の `NCAV = current_assets − total_liabilities` と「時価総額 ≤ NCAVの2/3」を、保存済み朝日工業社の会計入力へ限定的に当てた。Graham原典の検証や一般的投資基準の認定ではない。

**新たに意味・画像確認したのは、短信の物理5ページ（印字3）だけ。** 同頁に両入力があり、物理6へ進まなかった。連結・百万円・各残高日を同じ表で照合し、流動負債ではなく**負債合計**を使用した。

| 日付 | 流動資産合計 | 負債合計 | NCAV | 2/3 screen用の会社時価総額上限 |
|---|---:|---:|---:|---:|
| 2026-06-30 | 62,374 | 40,837 | 21,537 | 14,358 |
| 2026-03-31（比較） | 72,673 | 49,838 | 22,835 | 45,670/3 |

単位は百万円。6月末の上限は表示入力換算で**14,358,000,000円（143.58億円）**。比較期の分数は丸めず保持した。公表額は百万円未満切捨て（既存受入済み表紙引用を参照）なので、計算のexactは表示値に対してであり、隠れた端数を復元したものではない。

時価総額・価格・株数を取得していないため、**比較/合否/1株閾値はnull**。これはfair value、普通株の清算保証、買い判断ではない。maintainer式には優先株の別控除がなく、優先株の不存在・NCI/普通株請求権・簿価回収可能性・清算費用を確認したとはしない。全日本株への自動除外やscreen合格認定も行わない。

[inputs.json](inputs.json)に2会計項目と日付、[source-quotes.json](source-quotes.json)に原本/実native SHA、Unicode/UTF-8引用位置と算式の作者区分、[calculation.json](calculation.json)にDecimal/Fraction結果を保存した。[画像](images/physical-5.png)も保持。単純再実行は `.venv/bin/python -B research/ir-case-studies-2026-10-15/1975/ncav-accounting-input-review-2026-10-16/reproduce.py`（stdoutのみ）。upstreamコードは静的照合だけでimport・実行しない。

新GET・DB/Store・原source登録/更新・normalizer・共有code/docs・旧file変更・IR・予測/EPS年率化・価格取得は0。1ページで凍結。
