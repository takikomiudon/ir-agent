# JPX原表からの会社別部分抽出4sources

新GET0・DB0で、同じ原Excelのheader/時点と、B列Codeが完全一致する4行だけを会社別に文字化しました。対象は1518/1721/7525/8151、canonical `jp:CODE`。多社原典全体を各社の資料とせず、source.contentに**部分抽出**と明示しました。別々の独立確認が増えた記録でもありません。

元セルのraw serialと型/style、shared-string index、ヘッダー/対象期末・四半期種別、原XML SHA、1900日付系の扱いとISO変換方法、入口actualanchor、共通raw/captureをmetadataへ保持しています。ISOは印刷された文字そのものではなく、明示した変換です。原表10/8現在、入口更新10/15、原GET本文完了11:11:18.128793UTC、今回の文字化時刻は別に保持しました。source.retrieved_atは共通原GET完了、公表時刻はnullであり10/8を代入していません。

`source-bundle.json`はfullschemaでcompanies/theses空、4sourceは共有stable ID helperとvalidate_sourceを通しています。元全表のDB source IDは確認していないため、架空parent ID/原sourceを作らずcapture参照で結びました。金融入力・モデル・時刻zone/due・実施・送信適格性は検証/採用していません。

metadataパスは `research/ir-jpx-earnings-schedule-review-2026-10-15` 基準です。部分文字列と元Excel全体が同じ本文だという主張はせず、新providerのgeneric byte verifier対応はunknownを保持します。`representation-quotes.json`は部分source.content上のexact引用で、原表のセルと別途対応付けています。旧13入力不変、原バイト/cell/style/SHA、schema/IDsと本文を点検しました。DB/code/旧file/既存manifest・モデル/IR操作は0。予定monitorへ取り込む場合のDB来歴・分類・知識時点の確認はrootの後工程です。
