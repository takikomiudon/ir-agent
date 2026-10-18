# 2315 会社別モデルscope研究（2026-10-16）

既存の 入力定義 `docs/model-routing-inputs.md`・`examples/model-routing-assessment.template.json`・固定Damodaran研究方針を使い、会社事実と著者の方法を分離した。新たな会社本文/画像の確認は保存短信の**物理6/7（印字4/5）だけ**。既受入の初回 [1,2,4,5] と別追補 [10,13,18] / [16,17] は引用を再利用し、原履歴を変えない。

**結論は `requested_valuation_method:null` / `needs_data`。投資除外でも、金融機関非該当の確定でもない。** 24項目のテンプレートを保持しつつ、支持事実を具体的に記入し、数値要求を全24項目へ広げていない。評価時点が未指定のため `as_of:null` とし、記録/取得時刻を代用しない。

## 得られた会社根拠と反証

- 金融segmentの本文はBitcoin売却損等、NFT販売高に応じる販売手数料、広い業界の顧客サポートを説明。金融売上△44百万円/損失125百万円を保持する。ただしgross/net・売却/評価/手数料の計算bridgeと自己/顧客資産・営業負債は未確認。提携先Zaifの交換業をCAICAのbank資本構造へ転用しない。
- 金融segment OP損失、営業外Fisco持分法投資損失、善光の特別損益、holding費用は別段階。Fisco適用開始時の投資差額一部減損という既受入説明は、Bitcoin売却損と混ぜない。足戻ししない。
- ITには既存の有償SI/DX/保守と正の利益があり、案件未受注・人材制約も記載。IoTは既存デバイス販売とPoC/商用化移行が併存し、部材高/調達悪化によるAIX-01NX生産終了も反対根拠。親株赤字一期から全社young-loss、価格リスクだけから循環モデルへ振り分けない。
- p6は8月の動きをQ3累計後と明記。既受入p4のJuly–August説明とp7のPoC完了記述は工程scopeを精査せず同じQ3実現売上にしない。DCFが不可とも、PoCが有償反復CFとも決めない。
- 実績OP111,568千円は正、実績EPS△0.75円は負という観測を記録。旧FYguide EPS0.66と現在株数のbasisは未確認で、NI/EPSの分母逆算や誤記認定は0。

## 先に必要な定義と役割

1. **会社の定義**：金融の負売上の会計範囲、資産/負債・法人/規制scopeを公開資料で先に確認。金融の原料としての資金負債や規制資本が関係するかも、この定義から判断する。まだ全社bank適合も非該当も確定しない。
2. **会社全体の価値scope**：IT/IoT/介護DX、運用/持分法投資、holding費用、税/NCI/株主claimの境界を定義し、収益と投資資産の二重計上を防ぐ。新しいSOTP engineは作らない。
3. **著者の予測**：選択した方法に必要な売上/マージン・人材/開発/設備/運転資本再投資・税cash・資金調達を別に整合させる。会社のPoC説明は予測や正常利益の代用ではない。今回は予測0。
4. **投資家の入力**：評価時点、対象普通株主・通貨・期間・リスク条件、必要なら比較倍率/割引率を別に設定する。会社へ外部著者の意図や価格織込を確定させない。

公開済みの損益分類・3か月取込み・全社OP調整は回答済みとして残し、再質問しない。[definition-research-backlog.json](definition-research-backlog.json) は次の定義確認先と役割の記録で、IR草案/送信ではない。金融・循環・young用の全数値を先に求めず、根拠が支持する選択方法に必要なものへ絞る。

## ファイル

[model-routing-assessment.json](model-routing-assessment.json) は既存テンプレート形式の会社別記録。6つの契約事実を実値で支持し、残余はnullのまま条件付き点検とする。routeごとに支持/反証/不足を明記し、欠損から通常defaultを作らない。

[company-quotes.json](company-quotes.json) は新規2頁と既受入引用の区別、無補正Unicode/UTF-8 offset・原SHA・旧quoteのJSONpointerを保持。[method-references.json](method-references.json) は固定原著15引用のJSONpointer・原PDF SHA・頁を別管理し、既存の空白正規化照合という検証範囲も保持する。原典は会社の金融構造の根拠ではなく、2009年例示値を転用しない。

[pins.json](pins.json) は原raw/native/source、元初期36・旧追補41ファイル、docs/template/方針の不変を固定。[extraction.json](extraction.json) と `text/` / `pdf/` / `images/` は2頁だけの再抽出・render origin、[image-review.json](image-review.json) は実読完了。[validation.json](validation.json) は引用/参照/未知値・役割分離の局所検証、[manifest.json](manifest.json) は新成果物のbytes/SHA。CLI未対応の研究用契約であり、自動振分け・会社status更新・金融入力・専用engine実装ではない。

新GET・DB・source登録・shared code・normalizer・case/job・金融採用・IR草案/送信・新予測/price/閾値・旧変更は0。2頁でfreeze停止しroot受入を待つ。

実装境界の注記：文書上の既存5 method（EPS倍率、DCF、explicit terminal、equity bridge、DDM）と、regulatory-fcfe / cycle-margin / stable-reinvestment の中間計算を区別して記録した。中間計算は専用の予測/終価/株価/自動振分けが完成した意味ではなく、今回の実行・入力採用は0。テンプレート原本とshared codeは変更していない。
