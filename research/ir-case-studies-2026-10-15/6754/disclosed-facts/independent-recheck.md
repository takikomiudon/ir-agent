# 6754 公表7値の独立点検

記録: 2026-10-15T14:25:30.951121+00:00。実績3・会社予想4を対象に、引用のglobal/頁内半開offset、値/単位/期間token、億円→JPYの独立Decimal算術とAPI出力再現を確認した。追加問題はない。元sourceはinput/outputで原bundleと完全一致し、派生origin ID・本文hash・compact snapshot hash・stable ID・review/取得時刻も対応する。原sourceのmodels.json_text SHAと派生が保持するcompact canonical SHAは同じobjectのシリアライズ差である。

指定p6/9/12の値・表列/図凡例は直前の固定独立レビューを再利用し、20頁/5画像の全再監査はしていない。通信計測実績194/32/336億円と、連結通期会社予想1400/200/200/150億円は各対象行・列・期に対応する。JPY換算後も元の丸め精度を保持し、segment利益をNI/EPSへ、受注を売上へ、当期利益を親会社帰属へ強めない。

FY2026 1Q/4–6月と日本語の2027年3月期第1四半期、年間2027/3期の役割を区別する。p9受注のIFRSと全カレンダ境界はnull。p6の消去/未配賦費用注記、p12の4/27から据置・IFRS・丸め注記が保持され、会社掲載率を丸め整数から再計算していない。

normalize API全bundle replayと既存reproducerが一致し、入力不変・SQLite接続0を確認した。CLI/DB/Store/GET/コード/テスト/旧file変更、金融採用・IR作成/登録/送信は0。財務意味は未検証・モデル未採用のまま。固定4fileと旧33artifactのSHA不変。詳細は [independent-recheck.json](independent-recheck.json)。
