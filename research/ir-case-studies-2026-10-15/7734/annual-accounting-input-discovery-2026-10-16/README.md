# 7734 年次入力経路：静的短信一覧で停止

理研計器（23社queue20、元fixed343行266）の旧保存resolved URLからfresh robots→公式決算短信一覧の2GETを行い、全200完全受信を保存しました。旧JSONにはrawhrefがなく、保存resolved URLとして区別しています。

静的HTMLは短信見出しとサイト案内を含みますが、具体的な財務PDF literalは0。共通フッターのDX・個人番号資料のPDF2件は非対象で未取得です。年次PDF試行0、source候補0、年度・会計・EPS/BPS・普通株基準は未確認です。

robots原文のBOM/CRLFを保持し、選択URLのcan_fetchもBOM対応復号で再照合しました。JS/feed/provider/別一覧・検索/URL推測へ進まず、上限5の残3GETを使わず停止。今回の静的範囲を全サイトの資料不存在・会社非開示・IR無回答・投資除外へ広げません。

raw/SHA/完了時計と正常UA/proxy/TLSはcapture/guard、短い見出し引用はsource-quotes、結果と元資料pinsはreview/manifestに保存。DB/Store/コード・共有変更/価格/予測/金融採用/IR0。root受入待ちです。
