# 7325：事業構造資料の独立点検

指定3blockとsource/native初回登録を独立照合し、**80項目、不一致0**でした。[検証記録](independent-recheck.json)に入力SHA、offset、read-only DB照合と限界を保存しています。

会社原文は保険選択支援、FC運営支援、末尾4事業の紹介に対応し、3つの会社記載のsupportsは妥当です。グループ全体の引受不在、手数料/売上認識、規制資本適用、負債の役割、銀行型FCFE又は通常事業モデル適合は、この範囲ではunknownのままです。会社記載の正しさの外部監査や金融入力の認定ではありません。

原HTML→保存可視textの全機械再現、3引用のUnicode/UTF8半開offset、raw/text SHAを再現しました。HTTP完了20:06:17.141819UTC、producerの限定review20:09:15.908384UTC、実DB初保存20:11:43.639124UTCを分離して確認しています。公表日と過去の初回保存時刻は補完しません。

compact JSONのSHAとnative `models.json_text`のSHAは別domainです。同じsource objectから両値を再現し、旧caseとv2との差分がhash値・algorithm・旧compact hash宣言の3項目に限られることを確認しました。旧v1はproducer validationのSHAと一致し、active native登録はv2を参照します。保存旧scriptの失敗assertは実DB openより前にあり、再取得/二重source登録はありません。過去のshell実行そのものを再演した証明ではありません。

実DBと直前backupを`mode=ro`/`query_only`で読み、source123、case14、版18、既読entry69と全旧row保持を確認しました。新規1sourceの実保存receiptとnative初登録の凍結fileも一致し、DBの前後byte SHAは不変です。

意味確認は指定3blockのみで、他HTML/リンク先/財務原本/主体別規制/会計/利益mixは未点検です。新GET・DB書込み・既存file編集・金融採用・IR送信・注文は0。追加物は本MDと独立JSONだけです。
