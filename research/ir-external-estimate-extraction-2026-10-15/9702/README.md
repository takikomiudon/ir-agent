# 9702：外部著者の新E・3期EPSを既存normalizerで構造化

保存済みAlpha-Winレポート18頁・図表Aの著者予測EPS3期を、既存`normalize_disclosed_facts`へ渡す[request.json](request.json)と、出力[bundle.json](bundle.json)へ保存した。比較用の会社予想CEも別factにした。実際の原文・入力・出力を揃えた研究用抽出で、金融モデルへの実入力や予測採用ではない。

| 期ラベル | 原表ラベル | kind | EPS（円/株） |
|---|---|---|---:|
| 2026/12 | 新E | `external_estimate` | 161.17 |
| 2027/12 | 新E | `external_estimate` | 181.21 |
| 2028/12 | 新E | `external_estimate` | 196.02 |
| 2026/12 | CE | `issuer_guidance` | 161.40 |

Eは**アルファ・ウイン調査部予想**、CEは会社予想という原表の定義を維持する。CEは当該外部レポートによる再掲であり、会社原典を直接確認した値とはしない。会社/著者の利益総額が同じという理由で161.40と161.17を統合せず、株数を逆算して差を埋めない。新Eの作者組織・ラベルは各factの`scope`/`definition`とsource metadataへ保存し、`review.author`はCodexの抽出担当者である。

## 原文・時刻・ID

原文は[既存探索](../../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/README.md)の[04.txt](../../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/04.txt)の全文をそのままsource.contentに置き、改頁・空白を変更していない。[sources.json](../../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/sources.json)・[review](../../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/review.json)・[親照合](../../ir-public-valuation-report-discovery-2026-10-15/9702-alpha-win/root-recheck.json)を参照した。原PDF SHA-256は`ecd0958729b0ac071ae808ff8136ecae5d0ec08eecb65ad034105bcb13f77525`（1,983,632 bytes）、本文SHAは`5e14766b3e71631cc92abc2bea592b0d034ce45e036375003327723c959f728d`。

source.retrieved_atは元GETの`2026-10-15T07:24:49.158157+00:00`を保持し、source.published_atはnull。表紙表示2026-08-24、会社告知2026-09-02、PDF作成/更新2026-08-30、末尾コード2026-08-28、表紙抽出の残存2019/8/1はmetadataの別欄に保存した。どれかを正しい初回公表日時へ選び直さず、正確な配信時刻・改訂履歴は未確認とする。抽出reviewと派生sourceの日時は実行時刻`2026-10-15T07:41:47.534667+00:00`で、元取得へ遡及しない。実DB初回保存や過去時点の利用可能性を実証した記録ではない。

元source IDは既存`ir_agent.adapters.common.stable_source_id`へprovider=`case-public`と、company_id/URL/全文content/metadataを渡して生成した。派生IDはnormalizer自身が生成した。新しいID生成規則やparserは作っていない。

- 元source：`case-public:2d9802ebe8614ea26cbb622ab2e89d6ee9e129fe6d742b515b13687a4d642cf4`
- 派生source：`disclosed-facts:8ddc2f01a3d80d2cba579575e77077ff3cc0e4ddfdeb98472a465e751f2284cf`

## 引用と検証の境界

各factの`basis_quote`は、物理18頁の図表A見出しからEPS/円のヘッダ、該当行、E/CE定義、2021年1月1:2分割の備考末尾までの**連続する3,418文字の逐語部分文字列**である。行だけを切って単位や期を別引用から補っていない。頁内Unicode開始/終了位置と各対象行をlocationに記録し、18頁の原図でも列・ラベル・備考を確認した。引用中には他の業績行も含むが、抽出対象は上の4factsだけ。

[validation.json](validation.json)に、原PDFからの再抽出と保存本文のバイト一致、quote/数値token/単位/期の存在、stable ID、入力不変、固定nowでの出力完全再現、派生sourceの`reproduce_disclosed_fact_source`による`reproduced`、旧19ファイルのhash不変を保存した。仮の後時点で再計算しても派生ID/content/metadataは同じで、派生retrieved_atだけが変わることも純粋関数の範囲で確認した。実際の追加取得や保存履歴を作った意味ではない。

これは逐語一致と明示単位の算術の検証で、正しい列・対象・期間・会計の金融的妥当性を自動認定するものではない。連結範囲、会計基準、正確な期首/期末日、基本/希薄化EPSの対応、将来加重平均株数、原表以降の株式分割/自己株式等は未確認を保持する。2021年split注記は原表の表示基準で、現在までの株式状態を証明しない。

全facts/sourceは`financial_inputs_verified:false`、`meaning_review_required:true`、自動採用false。採用PER・評価式、価値計算、確率、thesis、IR質問は作成していない。9702はconfirmed1819窓口台帳外・provisionalのままで、この構造化から投資候補や受付confirmedへ昇格しない。bundleのcompanies/thesesは空、DBへは登録していない。

## 保存結果の再現

リポジトリルートから実行する。元の実抽出時刻を固定して比較するだけで、新しい取得やDB保存とはしない。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import json
from pathlib import Path
from ir_agent.disclosed_facts import normalize_disclosed_facts, reproduce_disclosed_fact_source

path = Path('research/ir-external-estimate-extraction-2026-10-15/9702')
request = json.loads((path / 'request.json').read_text())
saved = json.loads((path / 'bundle.json').read_text())
actual = normalize_disclosed_facts(request, now=saved['sources'][1]['retrieved_at'])
assert actual == saved
result = reproduce_disclosed_fact_source(actual['sources'][1], {s['id']: s for s in actual['sources']})
assert result['status'] == 'reproduced'
print(result['status'])
PY
```

新規作成はrequest/bundle/validation/本READMEの4ファイルのみ。小さいnormalizer/再現関数の実行だけを行い、新GET・実DB・他ファイル編集・full suite・IR送信・契約・投資実行は0。
