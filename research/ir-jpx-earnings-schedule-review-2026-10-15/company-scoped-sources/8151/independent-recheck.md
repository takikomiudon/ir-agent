# 8151 JPX決算発表予定の独立確認

**原ExcelのList行1617から、発表予定日2026-11-11、決算期末2026-09-30、種別「本決算」を独立再計算して照合した。** 共通原典チェック59/59、会社別チェック35/35、不一致0。詳細は[independent-recheck.json](independent-recheck.json)、共通の原取得・読取範囲は[元review](../../review.json)を参照。各参照fileのSHAを記録し、原文・Excelの複製は増やしていない。

原xlsx234,337bytesのZIP/XMLからworkbook→Listのrelationshipを辿り、date1904属性省略（既定false）、style5／numFmt176 `m/d;@`、sharedStringsとheader・全11セルの元token/型/styleを照合した。B1617は元の4文字`8151`と完全一致し、末尾削除・桁補正をしていない。予定A1617のserial46337、期末E1617のserial46295を、1900-01-01起点と架空閏日の調整で再計算した。年をfilename・現在日付から補っていない。

入口の実Excel anchor、capture/rawSHA、対象期、元表as-of「2026年10月8日 現在」、入口更新10/15、本文完了2026-10-15T11:11:18.128793UTCと、後の部分文字化時刻を分けて確認した。公表時刻はnull。会社sourceはadapterが作った**headerと1行の部分表現**であり、元多社xlsx全体を当該会社の逐語資料にしていない。保存本文・shared ID・fullschema・固定4source bundleと各projectionの完全一致を確認した。

予定のみで、時刻・timezone・scheduled_at・dueはnull、実施はnot_establishedのまま。JPXは未掲載会社や変更後の日程があり得ると明記し、135A/9765がこの選択ファイルに未発見でも「予定なし」としない。午後5時頃は翌日分一覧の更新時刻で、会社発表時刻には転用しない。DBの実初回保存・当時利用可能性を検証した記録でもない。

新GET・DB・旧file・code・金融判断・IR・数式／JS実行は0。これは保存原典と表現の独立点検であり、独立した予定情報が4件増えたという主張ではない。
