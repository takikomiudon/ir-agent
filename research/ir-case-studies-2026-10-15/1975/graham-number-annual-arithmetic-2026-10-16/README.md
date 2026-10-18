# 1975：通期実績によるGraham Number式の独立算術

maxgfr/crible固定commit00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7の保存式 `sqrt(22.5 × EPS × BVPS)` を、1975朝日工業社の会社公表済み2026年3月期連結実績（2025-04-01〜2026-03-31）へ2つの独立laneで適用しました。**Graham原著の適格条件の再現でも、価格比較・公正価値・買い/退出判断でもありません。**

| lane | EPS入力 | BVPS入力 | 60桁平方根の先頭 | 小数2桁の参考表示 |
| --- | --- | --- | --- | --- |
| A：会社直接表示 | 358.13円 | 1,965.51円 | 3979.689958621148668337… | 3979.69円 |
| B：丸め済み会社金額からの算術 | 9,240百万円÷25,802,361株 | 50,858百万円÷(27,200,000−1,324,317)株 | 3979.525105118539117638… | 3979.53円 |

Aの厳密radicandは63351728667/4000、Bは391606600000000000000/24727915329169です。BのBPS株数は25,875,683株で、EPSの年間平均25,802,361株とは分けています。A/Bの入力は混ぜず、Bで再計算したEPS/BPSを会社直接表示へ置換していません。百万円未満切捨て金額・1株値の公表精度は異なり、差を修復・整合化せずそのまま保ちます。実際の非表示元帳値を復元した値ではありません。

持分には物理15頁の「普通株式に係る純資産」50,858百万円を用い、OCIを含む会社表示の範囲を保持しました。物理7頁の日本基準「株主資本合計」44,745百万円を直訳で代用していません。注記千株表示をexact株数へ変換せず、物理2頁の株数を用いています。普通株主非帰属額の「－」や、優先株・非支配持分等の未確認項目を0と認定した計算でもありません。翌期会社予想EPS357.48（別Q1時点357.49）・個別実績357.13・Q1年率換算は除外しています。

原典は16頁の公式決算短信、原PDF SHA32edf5edbc228c24332811ad44795accf5926fac2709211e3d24ec3f9e0ba096、凍結manifest SHA cc1eb6339659164ee303a229702130f832532d5e65926943b8fe6a366c6a7c10。既存reviewの13引用を各保存頁本文のUnicode/UTF8半開offsetへ再照合しました。今回はPDF/画像の再読・再抽出はせず、親の1/2/7/15頁読解と既存reviewを使用しています。公表日5月14日は日精度、HTTP完了10月16日09:25:36は別時計です。実source登録やDBfirstsaveを先付けしていません。

`reproduce.py` はPython標準ライブラリのみでFractionの厳密radicand、120桁guard付き有理数変換、Decimal60桁平方根（ROUND_HALF_EVEN）を計算します。平方根が60有効桁の丸め中点範囲に入ることを元の厳密Fractionで検査しています。2桁表示だけROUND_HALF_UPの参考表示です。caller Decimal contextは前後不変。upstreamの価格非None blockや株数fallbackコードをimport/実行したとはしません。

実行: `.venv/bin/python -B research/ir-case-studies-2026-10-15/1975/graham-number-annual-arithmetic-2026-10-16/reproduce.py`。stdoutと保存結果の再実行bytes一致、26入力pin不変を確認しました。source-candidate未作成でも原raw/本文/固定reviewから再現でき、新たなsourceID・normalizer・DBは不要です。

価格/MOS/合否/現在株数/financial branch/採用方針は未設定。新GET・DB/Store・upstream実行・共有コード/旧資料編集・売買/IRは0です。新4fileを2026-10-16T09:34:18.383779+00:00に固定し、以後同名編集しません。

固定SHA（README自身を除く）:

- inputs.json: `78ff6076a0034865ddbe495506bbba35d19f7358aa46911d7dbf73e0c639ec67`
- reproduce.py: `5fa070cfe5fd5fd0cbc53e19f7f6eaea5746d2cdcc0a6d60d6c79b7493dde8be`
- stdout-calculation.json: `a0354dc1c4861bdf3f60a035aed0cc32753a1d441e47aa9eee4244a8bc5a83c0`
