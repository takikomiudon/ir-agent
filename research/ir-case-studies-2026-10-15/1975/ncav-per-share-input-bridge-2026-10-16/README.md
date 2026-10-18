# 1975 NCAVの期末普通株式数への対応

前段で受入済みの会社時価総額screen上限14,358,000,000円を、同じ2027年3月期1Qの期末普通株式数へ対応付けた。**今回の画像・意味確認は物理2ページだけ**で、旧EPS/NCAV作業の再実行ではない。

| 区分 | 公表値／計算 | 用途 |
|---|---:|---|
| 期末発行済普通株（自己株式を含む） | 27,200,000株 | 公表期末数 |
| 期末自己株式 | 1,324,717株 | 公表数を1回だけ控除 |
| 期末普通株数（会社表示自己株式控除後） | **25,875,283株** | 上記2欄の差 |
| 期中平均（四半期累計） | 25,875,312株 | **使わない**。EPS用の別期間量 |

分母の表示名は「期末普通株数（会社表示自己株式控除後）」。JPXの流通株式数・free floatへの対応付けはしない。分母のproject mappingは `shares_outstanding_end = 期末発行済普通株（自己株式含む）−期末自己株式`。cribleのperiod-end優先とprice×sharesの方法を参照したが、upstreamパーサー/関数は実行せず、平均fallbackは使わない。

歴史的な2/3 NCAV screen境界は、**14,358,000,000 / 25,875,283 円／株**（約**554.89円／株**）。判定に使える数学的な境界は保存した分数で、小数2桁はROUND_HALF_UPによる参考表示だけ。**fair value・買値・発注・利確・呼値・現在株価比較にはしない。**

p2の原ラベルは2027年3月期1Qであり、同短信の受入済みBS対象日2026年6月30日へ文脈対応させた。p2に6月30日が印字されているとはしない。比較の2026年3月期末自己株式1,324,317と、前年1Q平均25,755,491は別欄・別期間のまま保持する。

信託保有分の追加説明はp2では未確認で、ゼロ/不存在と認定したり二重控除したりしない。maintainer式の優先株別控除なし、NCI/普通株請求権・簿価回収性未検証、公表NCAVの百万円未満切捨てという限界を継承する。6月末以降のcorporate actions・現在株数・株価は不明で、比較/合否はnull。

[inputs.json](inputs.json)、[source-quotes.json](source-quotes.json)、[calculation.json](calculation.json)、[review.json](review.json)、[画像](images/physical-2.png)に根拠と限界を保存。再現は `.venv/bin/python -B research/ir-case-studies-2026-10-15/1975/ncav-per-share-input-bridge-2026-10-16/reproduce.py`（stdlib/stdoutのみ）。旧NCAV folder全11files不変、GET・DB/Store・normalizer・共有code/docs・IR・新予測0。1ページで凍結。
