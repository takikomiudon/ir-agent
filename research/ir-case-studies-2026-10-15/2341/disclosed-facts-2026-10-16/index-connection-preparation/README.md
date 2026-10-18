# 2341：公表数値索引v36の接続候補（file-only）

**共有索引は未変更。** 受入済み2341の12factsを、現行v35の旧39parent/202fact全objectを保ったまま1parentとして追加した候補を [proposed-index-v36.json](proposed-index-v36.json) に保存した。

| 候補の件数 | 値 |
| --- | ---: |
| 会社 | 27 |
| fact | 214 |
| parent entry | 40 |
| 解決先derived source | 42 |
| 会社/原典ペア | 33 |

新entryは原短信case-public:5bba6d…をoriginal_source_id、派生disclosed-facts:706384…をsource_idとして分けた。raw factsのsource_idは引用元の原短信であるため、indexのper-fact source overrideへ転記しない。新12factsはenclosing派生IDへ解決する。既存個別artifact/source overrideは旧objectごと不変。

2341の千円中間実績と基本EPS、当時通期会社予想5値、中間DPS0、年間予想合計5.00を、既存index形式のid/concept/kind/period/scope/unit/valueの全fieldで受入factsからそのまま写した。新正規化/丸め/単位変更/予測更新/株数逆算/金融採用は0。旧scope、配当日付/基準日/GAAP/連結null、利益段階・税NCI/特別利益の非正常化、0表示と支払確認の区別を保持した。

## 接続状態は未確定のまま

原短信の実初回保存は、既存root受入receiptが2026-10-16T06:27:32.516249+00:00・trusted_insertと記録する。この監査は保存済receiptを参照しただけでDBを照会していない。新派生は依頼時点でfile-only、firstsaveはnull、derived_source_imported_into_actual_database:false。別担当の未受入intake準備や将来receiptを依存へ含めず、**派生の実保存・分類をrootが受入した後にだけ正式接続**できる候補である。

v35のactual_research_source_connectionsは、旧時点のDB201source／接続39派生195fact・対象外2派生7factというhistorical snapshotを全fieldそのまま保持した。現在のDB再観測とは呼ばない。今回のcandidate_connection_stateで新12fact/1派生が未接続であることを別記し、候補としては旧対象外分と合わせ19fact/3派生が未接続になる。将来新派生の受入後に40派生207fact接続・対象外2派生7factとなる数は**条件付き期待**で、現在実現したとは主張しない。

## 検証と再現

input-pins.jsonに現v35、受入bundle/親receipt/原典・再現記録/保存済会社選択記録、native serializationの既存2moduleを固定した。原sourceのmodels.json_text native SHAは7d1775…、normalizerのcompact snapshot SHAはde8870…で、それぞれ既存receipt/metadataと一致する。異なるJSON serializationを同一SHAだと誤認しない。派生native SHAも記録した。親の既存再現receiptを再利用し、normalizer/reproducerを新規に実行していない。

build_candidate.pyはDB/Store/networkをimportせず、新候補はこの準備folderだけへ出力する。既定stdoutで再現でき、candidate/validation両JSON objectが保存結果と完全一致した。--writeは新規fileだけの排他作成なので既存candidateを上書きしない。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python research/ir-case-studies-2026-10-15/2341/disclosed-facts-2026-10-16/index-connection-preparation/build_candidate.py
```

新共有v36/旧v35/他社旧値・docs・productionは変更していない。DB/Store/GET/実intake/新金融値採用/IR/注文は0。候補と検証・原入力pinを固定し、rootの実保存受入待ちで停止する。
