# 4社の公開Q&A：実保存と既存条件比較の完了

4318・6200・6814・7187の原4sourceを全オブジェクト同一で保存し、intake4件を完了した。既存native3caseの定性比較3件もrootが完了し、4318v4/config1・既読4、6200/6814各v5/config1・既読6へ進んだ。全case unresolved・内部管理Jan16retain、他caseと旧管理日不変・再queue0。7187のFAQ保存を新case登録とはしない。

[読取専用の最終照合](actual-verification.json)では261資料（公開260/市場1）・260分類/261availability、全179job完了（intake135/定性44）、176attempt/352event/176request receipt。native34case/79版/197既読は旧194＋既存3case各1sourceの比較である。Jan15=12case/Jan16=22case、公開資料あり55社/財務内容41社、legacy28/trusted233を実測した。[検証script](verify-actual.py)はバックアップと旧27tableのschema/全旧行を照合し、原4source・来歴/分類snapshot・worker request/completion/case-afterを全体一致で確認した。DB/backupの照合前後SHAは不変、Store/DB書込/GETは0。

4318の当時費用増見通し・ROE目標、6200のQ2会社説明、6814/7187の限定一般FAQを会社年度実績の訂正・予想実現や新たな投資家予測にしない。4318の一時利益/CFに関する既存読解は固定file/SHA/時刻でsummaryとcase観測へ手動引継ぎした。金融thesis・policy・正式質問・返信・明示保有・RDR・送信・注文は0。Graham7社集合・参考値・索引v42は不変で、索引の255資料/native32case snapshotは当時の履歴として保持する。新core変更/fullsuite再実行0、既存1,585testsの受入を保持した。成功した保存・completeは再実行しない。

## 接続前の準備記録（以下は当時のfile-only状態）

# 4社の公表Q&A原典：接続準備のみ

4318・6200・6814・7187の指定producer bundleから、新原典sourceを各1個、**全オブジェクト同一**で集約した。`source-bundle.json`はschema1、companies/thesesは空。6200のproducerに含まれるcompany stubは追加せず、旧原典・正規化facts・archive7FAQも加えていない。

分類案は全て`kind: qa`。4318/6200は既読の会社回答が当時の費用見通し・業績予想理由を含むためfinancial_content=true。6814/7187は一般FAQの限定2回答を読んだ範囲で、原sourceの選択外回答まで非金融とは認証しないためnullを保持する。引用・原文位置・根拠は分類案と`classification-quotes.json`、4producerのbundle/manifest/native/rawSHA・scopeは`aggregation-provenance.json`に保存した。

会社回答と質問者の前提を分ける。会合日・文書日・URL日・HTTP Dateから公表日時を補わず、当時の予想を現在最新予想や実現値へ移さない。会社のROE/配当等の目標を投資policy・売買条件へ採用せず、費目を合算した利益bridge・EPS/CFも作らない。

producerの読解範囲は不変で、追加Web/PDF頁の意味読解は0。原4bundle・source・contextとmanifest宣言pinsの前後一致、4source whole/native・rawSHA、4短引用のUnicode/UTF8位置を点検した。

**file-only**。DB接続・Store・CLI・GET・財務更新・normalize・新nativecase・IR・共有docs/index編集は0。rootが画像/引用/分類案を独立受入し、copy→actual保存/intakeを行う前の準備である。
