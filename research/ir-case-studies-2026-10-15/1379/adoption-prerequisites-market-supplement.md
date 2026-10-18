# 1379：市場snapshot追加後の採用前提の追補

**提供者申告の価格候補が実DBへ保存された。ただし現在判断への価格採用、評価モデル、実行policyは未採用。** 先の[05:34採用前提packet](adoption-prerequisites.md)はそのまま保持し、今回解消した不足と残る不足を[追補JSON](adoption-prerequisites-market-supplement.json)に分けた。新コードは不要。

## 追加された証拠

Shared Research申告の価格は**2,048円**、quote時刻は`2026-10-14T06:30:00.000Z`、同じ瞬間をJSTで表示すると**10月14日15:30**。これはtimezoneの表示変換で、取引所の終値・約定時刻を独立確認したという意味ではない。非liveで、価格種別/調整基準/feed遅延・売買可能性も未確認。

新market sourceは`sharedresearch-stock:14c38b71b93e2f60a03c639c0071bbd8d21a10036b54969a1c3402a83be9639b`。canonical snapshot SHAは`25253843d4dfca32a037d35b72781dbdf9660b0e563b8db0f9fc6db7e1d8632c`。[親の独立照合](provider-market-snapshot/root-recheck.json)と[取り込み報告](provider-market-snapshot/actual-ingest.json)により1source追加を確認した。全61sources（公開60/市場1）・60classifications、intake系13job等は親報告の件数で、この追補では全DBを再集計していない。

| 時計 | 記録 |
|---|---|
| 提供者quote時刻 | 2026-10-14T06:30:00.000Z |
| 原HTML初回取得 | 2026-10-15T05:28:30.141744+00:00 |
| 派生sourceの実抽出/retrieved_at | 2026-10-15T05:40:23.213016+00:00 |
| 実DB初回保存/trusted_insert | 2026-10-15T05:43:42.850582+00:00 |
| 親の取り込み報告記録 | 2026-10-15T05:43:42.888417+00:00 |
| 価格source published_at | null |

DB初回保存はmode=ro/query_onlyの単一snapshotで既存receiptを読み、source JSONとbundleのcanonical一致を確認した。quote時刻を公表/取得/保存日時へ転用せず、後の保存を過去に遡らせない。

[価格候補とfield path](provider-market-snapshot/quote-candidate.json)および[raw証跡](provider-market-snapshot/stock-field-extraction.json)を参照する。親sourceは`case-public:a14372edbaf8c2897b8553a1a93dc1e4b1dc63859a14ce2f716bdb571a862e7b`。その本文はレポートだけなので、stockの支持は元HTML→window.state→embedded JSON→4fieldの連鎖で別に保持している。

## 解けた不足と残る不足

価格候補そのものの未取得と、quote fieldを保存sourceへ結ぶ来歴は一部解消した。`requires_research:false`の市場資料として保存され、仮説・質問・intake jobは追加されていない。

一方、評価日と`max_quote_age_seconds`の鮮度policyは未採用なので、fresh/staleや現在の購入・退出を判定していない。費用、最低期待上昇余地、最大下落幅、target scenarioもnull。会社公表のEPS/DPS候補、独立予測/公正倍率、将来FCFF・税/再投資・安定期、配当の権利と支払時点の不足は元packetどおりである。

PE12.2など除外指標を公正倍率へ変えず、株数/時価総額/PBR/ROEも採用しない。確率は未設定、比較形式はunweighted、期待値とEVSIはnullのまま。`financial_inputs_verified:false`、`model_adopted:false`、現在判断への採用falseを維持する。

この追補2ファイルだけを追加した。元packet・preview・market artifactsは変更せず、新GET・DB更新・コード/registry追加・valuation・仮説/質問・注文/送信は0件。
