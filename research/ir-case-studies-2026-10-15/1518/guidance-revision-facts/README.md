# 1518：同じ年度の旧・新会社予想を4factsとして保存

7月22日修正通知の元source snapshotをそのまま使い、既存`normalize_disclosed_facts`へ渡す[request.json](request.json)、出力[bundle.json](bundle.json)、[validation.json](validation.json)を保存した。会社通期EPSと年間DPSを旧・新で分け、同FYという理由で上書き・混合していない。4factsすべて`issuer_guidance`で、実績や外部著者予測ではない。

| 指標 | 通知が示す予想版 | 原表の額 | normalizerへ渡したraw_value / 出力value |
|---|---|---|---|
| 通期EPS | 前回・2026-05-13発表 | 185.40円 | `185.40` / `185.40` |
| 通期EPS | 今回修正・2026-07-22 | 229.67円 | `229.67` / `229.67` |
| 年間DPS・合計列 | 前回・2026-05-13発表 | 74 円 00 銭 | `74` / `74` |
| 年間DPS・合計列 | 今回修正・2026-07-22 | 130 円 00 銭 | `130` / `130` |

対象は2027年3月期の会社予想。各factのscope/period/definitionに版・参照発表日・今回の出典日を保持した。5/13は**7/22通知が前回発表日と記す日付**であり、5/13原通知の直接確認や、その時点でこのシステムに保存・利用可能だった証拠ではない。

## 原文表記と検証の限界

配当表には`74.00`/`130.00`という連続tokenがないため、原文をその形式へ改変していない。円の整数tokenだけをnormalizerに渡し、scope/definition/locationに「74 円 00 銭」「130 円 00 銭」、00銭、年間合計列を保持した。今回の00銭という表示では全額と数値が等しいことを人が原図で確認したものである。

normalizerが検証するのは、円token・逐語quote・単位/期ラベルの存在と1倍の明示単位換算で、**複合円銭表記を解析・検証する機能を追加していない**。非ゼロ銭の金額に円部分だけを同様に使えるとは一般化しない。この表示の意味確認と、株数分母・株式基準・金融入力適合の検証は別で、後者は未検証のまま。

4factsの引用は、物理PDF1頁の通知見出しから通期・EPS表、配当表の今回修正130円00銭までの連続1,492文字。表ヘッダ・期・円/銭・旧新行を同じ逐語quoteに保持し、頁内Unicode位置と対象表/列/版を記録した。中間/期末を別factにせず、4facts以外は抽出していない。追加の株式分割換算、株数逆算、年間DPSからDDM列への延長はない。

## 元snapshotと再現

元資料は[会社追補](../issuer-quarter-followup/README.md)の[source-bundle.json](../issuer-quarter-followup/source-bundle.json)にある7/22通知source。ID、全文、metadata、raw/text/capture、初回GET `2026-10-15T07:53:42.037552+00:00`、published_at:nullを変更せず、bundleにも同一snapshotを保持した。[親照合](../issuer-quarter-followup/root-recheck.json)と[実取り込み記録](../issuer-quarter-followup/actual-intake.json)を参照したが、今回の実DB照合・更新は0。

原source IDは`case-public:bd49125a131f709a6ff532a4da187195a1870d6b07bbcb54fa0a7c0277973997`。原PDF SHA-256は`1ac81e4918af0194f1eb2d5c691f9f21e32f7e28baaf6576518719111f6d556a`（207,591 bytes）、本文SHAは`cf154ea01ac400bd827f5367b41674e81f092db78b221b49c969eb2ad28657e2`。sourcebook/capture SHA一致、PDF再抽出と保存本文のバイト一致、固定nowでの出力完全一致、派生sourceの`reproduce_disclosed_fact_source`による`reproduced`、旧26ファイルhash不変を確認した。実抽出/派生retrieved_atは`2026-10-15T08:17:10.251430+00:00`で、元取得日へ遡及しない。

再現はリポジトリルートから、保存時刻を固定して比較するだけで行える。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import json
from pathlib import Path
from ir_agent.disclosed_facts import normalize_disclosed_facts

path = Path('research/ir-case-studies-2026-10-15/1518/guidance-revision-facts')
request = json.loads((path / 'request.json').read_text())
saved = json.loads((path / 'bundle.json').read_text())
assert normalize_disclosed_facts(request, now=saved['sources'][1]['retrieved_at']) == saved
print('reproduced')
PY
```

全factは`financial_inputs_verified:false`、`meaning_review_required:true`、金融モデル採用false。価値計算・確率・株数・IR質問は作成していない。作成はrequest/bundle/validation/本READMEの4ファイルのみ。GET・DBアクセス・旧file/code編集・全件テスト・索引更新は0。
