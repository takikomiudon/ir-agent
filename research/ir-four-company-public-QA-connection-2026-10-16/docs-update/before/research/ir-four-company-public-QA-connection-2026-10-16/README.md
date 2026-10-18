# 4社の公表Q&A原典：接続準備のみ

4318・6200・6814・7187の指定producer bundleから、新原典sourceを各1個、**全オブジェクト同一**で集約した。`source-bundle.json`はschema1、companies/thesesは空。6200のproducerに含まれるcompany stubは追加せず、旧原典・正規化facts・archive7FAQも加えていない。

分類案は全て`kind: qa`。4318/6200は既読の会社回答が当時の費用見通し・業績予想理由を含むためfinancial_content=true。6814/7187は一般FAQの限定2回答を読んだ範囲で、原sourceの選択外回答まで非金融とは認証しないためnullを保持する。引用・原文位置・根拠は分類案と`classification-quotes.json`、4producerのbundle/manifest/native/rawSHA・scopeは`aggregation-provenance.json`に保存した。

会社回答と質問者の前提を分ける。会合日・文書日・URL日・HTTP Dateから公表日時を補わず、当時の予想を現在最新予想や実現値へ移さない。会社のROE/配当等の目標を投資policy・売買条件へ採用せず、費目を合算した利益bridge・EPS/CFも作らない。

producerの読解範囲は不変で、追加Web/PDF頁の意味読解は0。原4bundle・source・contextとmanifest宣言pinsの前後一致、4source whole/native・rawSHA、4短引用のUnicode/UTF8位置を点検した。

**file-only**。DB接続・Store・CLI・GET・財務更新・normalize・新nativecase・IR・共有docs/index編集は0。rootが画像/引用/分類案を独立受入し、copy→actual保存/intakeを行う前の準備である。
