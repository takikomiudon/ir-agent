# 7157：保存FAQの独立点検

指定3引用とsource/native初登録を独立照合し、**93項目、不一致0**でした。[JSON](independent-recheck.json)に保存原本・offset・SHA・read-only DB照合と限界を残しました。

保存FAQは保険/資産運用の会社説明、連結IFRSと日本基準個別配当の区別を支持します。新契約費用繰延べは原文の「一般論」を保持しています。引受の法的主体、IFRS17/CSM/契約負債、規制資本/余剰、配当可能額、DDM/FCFE適合は未確認です。累積損失と配当実施時期未定の説明を現在の全Web最新へ読み替えず、将来配当0も推定していません。

source内容は元保存JSONのtextと完全一致し、3引用のUnicode/UTF8半開offsetを再現しました。sourceIDは保存JSON byte SHAで、旧HTTP entity SHAとは別です。原raw/HTMLは選択証拠内で利用されておらず、原HTML→text再現・raw SHA再照合・wire/native capture・現在freshnessを認定していません。旧identity flagも保持されています。

旧retrieved_at 2026-10-11T20:11:34.688917UTCはHTTP完了20:11:45.609803UTCより前ですが、原値とcaveatを保持しています。実DB初保存2026-10-15T20:15:40.848428UTCは別のtrusted_insert receiptで照合し、旧日時から歴史的DB利用可能性を認定しません。

実DBと直前backupを`mode=ro`/`query_only`で照合し、124source（公開123/市場1）、分類123、56job（intake53/定性3）、53attempt/106event/53receipt、15case/19版/70既読、legacy28/trusted96、全旧row保持を確認しました。15caseの保存queue0報告とread-only既読/管理日も対応し、DB前後byte SHAは不変です。queueは再実行していません。

producerのREADME/validation/case内の未独立点検・実DB未読等は当時の作業境界として保持し、後続root receiptと本点検を別記録にしています。新GET・DB書込み・Store初期化・既存file編集・金融採用・送信・注文は0。追加物は独立JSON/MDだけです。
