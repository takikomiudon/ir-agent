# 3844 コムチュア：年次入力の有限探索

元台帳の社名と固定23社queueの保存literalを照合し、会社研究folderの重複なしを確認した。新GETはfresh robots200（完全84B）→公式決算短信index200（完全16,940B）の2回だけ。最大5GETの残り3回は使わず停止した。queueは当時snapshotのまま不変。

対象 `https://www.comture.com/ir/irlibrary/accounts.html` の保存静的本文・linksに年次PDFのhrefは0。HTMLにはプロネクサス提供表記と `//ssl4.eir-parts.net/Custom/public/parts/3844/ja/parts/tanshin.js` というliteral script参照がある。これは既存holds-v8のexacthostであり、script実行/取得、feed、provider、別一覧/検索/推測URLへ追跡しなかった。robotsは当該issuer indexを許容するが、配信先の保留を免除しない。

年次FY・実績EPS/BPS・普通株持分/平均・期末株数・分割・負値/dashは本文未取得のためnull。訂正告知もこの静的本文では確認できず、存在しないとは認定しない。全文extract対象は取得HTMLだけで、PDF取得/頁意味読解/金融sourcecandidate0。source-candidatesは空配列の理由を明示し、一覧shellを年次資料へ偽装しない。

raw2entity、HTTP開始/headers/完了/保存時計、同一UA・継承proxy/CA/TLS検証、既存共有2秒lock、最大40秒/10MiB、3つの原文引用とUnicodeUTF8位置/SHAを保存した。原HTTP entityはContent-Encoding展開後でwirecaptureではない。managedpolicy状態unknownを適用readyとしない。接続診断へ進んでいない。

既存窓口履歴を再開せず、欠損を非正入力・式適用外や会社の投資除外へ変えない。新DB/Store/価格/計算/共有code/docs/index/旧file変更/IR0。2GETの有限閉鎖としてfreezeしroot受入待ち。
