# 3817：公表年次EPS/BPSのmodel-inputs接続

実行時刻/as_of/provenance.recorded_atは2026-10-16T09:52:28.641309+00:00。既存 `audit_model_inputs` APIを直接実行し、`reported_annual_reference` / `graham_number` / `aggregation: unweighted`の2入力だけを照合しました。EPS `443.34`、BPS `2659.88` は元facts[0/1].valueのままです。原典作者は `株式会社ＳＲＡホールディングス` で、抽出者・計算担当と区別しています。

結果は **source_values_matched / required2 / missing0**、`meaning_review_required:true`、`financial_inputs_verified:false`、`expected_value_available:false`。API全resultを保存し、意味確認を済ませたとせず各rowの`meaning_review_status:unreviewed`も保持しています。EPSのannual durationとBPSのbalance-sheet instantは、それぞれの元periodをprovenanceの文字列として保持しています。単位はJPY-per-share、両方reported_factです。

provenanceは派生source IDと `['content','facts',i,'value']` へ結合し、requestには元original/derived全objectを変更せず両方含めました。実runtimeは両sourceのretrieved_at以後です。保存原典からの値一致・同社・申告時点・公開lineage・normalizer再現を点検する単体APIであり、現在DBのfirstsaveや公開性訂正は読みません。本作業はDB保存済みと認定せず、親が後で実保存の完全object/receiptを別途照合します。

API内の数値検証用参照price=`1`は市場観測ではありません。requestに株価は供給せず、実株価/相場比較、MOS、合否、金融方針、買い/退出、シナリオ確率へ転用していません。この結果は投資価値や採用済み金融入力の認証ではありません。

同requestをAPIへ2回渡しresult全object一致、request全object不変、元正規化folderの全6filesと実行code5filesのSHA前後一致、source_snapshot_sha256がmodels.json_textによる両source完全objectのSHAと一致することを確認しました。CLI/Store/DB/GET/共有code・旧files編集は0、新3filesのみです。新normalizer呼出はこの既存監査APIが行う原典再現の範囲で、追加のfact生成・fact保存は行っていません。

source snapshots (models.json_text serialization; normalizer compactJSON hashとは区別):

- `case-public:049f5867c00a555c66cc32cf539ff540a34a92e89cd9ef2058c30530bab73a7e`: `cdb77fd2cb0d201dd8fbcba84a200665e0912216981ea79e200a601558d7a616`
- `disclosed-facts:84c92721eb38270616b8b950310fe99807d0da323f438424710f435ddf574acf`: `2bd0faef543ce9659035c844d7d1722975b37e23fc2035a2a66a85c1e78940ce`

固定した旧入力files:

- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/README.md`: `89c300ad96ecb95f2f09a3aa01daa2bf02555a80b027c70562ebd622035a6719`
- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/input-pins.json`: `150238254440d82cd61e73a43b19d537cae7a7ca1313f8facf1bef207fd19a47`
- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/normalization-input.json`: `5a4323ccd815bc118f82e56b8f1e3943b9f4848e93d5e5f7658fd40363892150`
- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/normalized-bundle.json`: `9cb688305dc2a0582ee66f363f88efae03a5b677859adf1f07dd633d86fc2749`
- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/parent-acceptance.json`: `d69bcfb3a76f2142df856d70a554f110c4a35acbe782404a36bcea318eb42533`
- `research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/validation.json`: `10928b7ebce0c5f28f116f8a0e3e9d3e20eb30f45dad1048f3694faec6fbcc8d`

実行code pins:

- `src/ir_agent/decision.py`: `5243aa9c51d42d1abc9a2cd95cc65d8b9671be1625a30d8cdeaddfdade026614`
- `src/ir_agent/disclosed_facts.py`: `d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51`
- `src/ir_agent/model_inputs.py`: `23aa6ef4146a8bc1fb931f8df81a6914e1d345809f7617d0a37f913a25a6ffe2`
- `src/ir_agent/models.py`: `e0d0444fda0e730de6c6e9beaa110bbd796de00f3228c041daa016284a8e234e`
- `src/ir_agent/valuation.py`: `f9d179ddd3e73aee8d6a5f406141fbca969af39603730c9e36813532de7a4460`

API再現例（メモリ/実DBいずれも開かない）:

```python
import json
from pathlib import Path
from ir_agent.model_inputs import audit_model_inputs
value = json.loads(Path("research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/model-input-audit/request.json").read_bytes())
result = audit_model_inputs(value)
assert result == json.loads(Path("research/ir-case-studies-2026-10-15/3817/annual-per-share-disclosed-facts-2026-10-16/model-input-audit/result.json").read_bytes())
```

request SHA `d09da2051effd44b3bb8551a9b45857e17718228008b3882d1f53ff97d3be4b6`、result SHA `8c2ce5d4a2b4706eecf571872c78ebfc78974ff54b1ef2eef2f2fa71762f8ae2`。この3fileを固定し、以降同名編集しません。
