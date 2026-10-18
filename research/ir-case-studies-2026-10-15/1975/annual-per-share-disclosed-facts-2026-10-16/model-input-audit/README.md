# 1975：公表年次EPS/BPSのmodel-inputs接続

実行時刻/as_of/provenance.recorded_atは2026-10-16T09:52:28.620775+00:00。既存 `audit_model_inputs` APIを直接実行し、`reported_annual_reference` / `graham_number` / `aggregation: unweighted`の2入力だけを照合しました。EPS `358.13`、BPS `1965.51` は元facts[0/1].valueのままです。原典作者は `株式会社朝日工業社` で、抽出者・計算担当と区別しています。

結果は **source_values_matched / required2 / missing0**、`meaning_review_required:true`、`financial_inputs_verified:false`、`expected_value_available:false`。API全resultを保存し、意味確認を済ませたとせず各rowの`meaning_review_status:unreviewed`も保持しています。EPSのannual durationとBPSのbalance-sheet instantは、それぞれの元periodをprovenanceの文字列として保持しています。単位はJPY-per-share、両方reported_factです。

provenanceは派生source IDと `['content','facts',i,'value']` へ結合し、requestには元original/derived全objectを変更せず両方含めました。実runtimeは両sourceのretrieved_at以後です。保存原典からの値一致・同社・申告時点・公開lineage・normalizer再現を点検する単体APIであり、現在DBのfirstsaveや公開性訂正は読みません。本作業はDB保存済みと認定せず、親が後で実保存の完全object/receiptを別途照合します。

API内の数値検証用参照price=`1`は市場観測ではありません。requestに株価は供給せず、実株価/相場比較、MOS、合否、金融方針、買い/退出、シナリオ確率へ転用していません。この結果は投資価値や採用済み金融入力の認証ではありません。

同requestをAPIへ2回渡しresult全object一致、request全object不変、元正規化folderの全6filesと実行code5filesのSHA前後一致、source_snapshot_sha256がmodels.json_textによる両source完全objectのSHAと一致することを確認しました。CLI/Store/DB/GET/共有code・旧files編集は0、新3filesのみです。新normalizer呼出はこの既存監査APIが行う原典再現の範囲で、追加のfact生成・fact保存は行っていません。

source snapshots (models.json_text serialization; normalizer compactJSON hashとは区別):

- `case-public:f733d2deff739e7de2b2f93256929a68e1eb1d6b88ec50ef3c828e0f27f9036f`: `ee28585481c9692e9374aed4ebc15cb04e5b71757d6c56f2d739c7c7265a3e25`
- `disclosed-facts:9d7b21bfd8ffec2d0369103cfcdf945e6407dff6e690816edc895d115470d313`: `d6db7c7c2454470dba83cec46a48ba76814db7324ec1109c8b4e8e81d6f54bcf`

固定した旧入力files:

- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/README.md`: `4e756c9c8a2f773b280b7ab6cb1e2b64844525daa0852a839cf7cb441b7fe2e0`
- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/normalization-input.json`: `4506961a3b0ab927e83d2184d15cfad49d9027e476029a5cacaa68a89fb6f977`
- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/normalized-bundle.json`: `0defeba27b9f4538afd8d82c05c158918fcdfcaf455a64f1ea897eca7543e41e`
- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/parent-acceptance.json`: `530cab9bb4b2cfaecf9aadce084dfe78a239add8dbf70fc99bea9d099e29547f`
- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/quotes.json`: `b0cfc791745b8327bdcf2aadc1ac03ef8a3a0f3c9f70711f6a57f3d1cc1ff744`
- `research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/validation.json`: `e40961a61c795d00dbb2957769186b069f00666778d1e720b51c71cd75de3477`

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
value = json.loads(Path("research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/model-input-audit/request.json").read_bytes())
result = audit_model_inputs(value)
assert result == json.loads(Path("research/ir-case-studies-2026-10-15/1975/annual-per-share-disclosed-facts-2026-10-16/model-input-audit/result.json").read_bytes())
```

request SHA `f5c803ed257a1d3cb118d4486b2e2fda565551f9d0b255c5e359f9f3656a42bd`、result SHA `82262f630c2d32983c9509665efd67df32ef35b652be4a1beddca53da6a361cd`。この3fileを固定し、以降同名編集しません。
