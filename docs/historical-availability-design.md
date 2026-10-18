# 保存来歴と過去時点の再現

2026-10-15時点の設計契約。**保存来歴library、Storeのstrict PIT/read-only retrospective、daily/claim/intakeの照合、CLIは実装済み。** [架空データによる未修正の再現](../research/ir-historical-availability-2026-10-15/README.md)を保存した。原文JSON、金融計算、売買条件は変更しない。

## 修正する問題

修正前の `Store.thesis(company_id, as_of=t)` は、JSON内の `recorded_at <= t` だけを見ていた。18:00に保存した仮説v2へ17:20という作成時刻を付けると、それまでv1を返していた17:30の照会がv2へ変わる。`daily(17:30)` の入力にも波及する。公表・取得・受信・作成という申告時刻と、DBに保存されたことを確認できる時刻が混同されている。

再現のdecision review自体には正しい `first_saved_at=18:00` がある。これは17:20に買い判断を保存した証明ではない。また18:00時点の新たな判断候補は、価格鮮度などの既存条件を満たせば有効であり、今回の不備とは分ける。

観測前に予測則を指定する動機は、[保存済みのGneiting–Raftery §7.1の引用G8](../research/probabilistic-evaluation-2026-10-15/README.md)に対応する。ただし、このSQL、receipt、IRの時点契約は本プロジェクトによる適応設計であり、著者のIR手法・DB仕様ではない。

## 二つの時計と照会モード

| 値 | 意味 |
| --- | --- |
| `as_of` | 調査・判断の対象時点。資料の公表、取得、返信受信、仮説作成などの既存条件を照合する締切。 |
| `knowledge_at` | そのデータがDBに存在したことを確認できる締切。原文JSONの日時から代用しない。 |
| `first_saved_at` | 新規INSERT時にサーバー時計から採取する保存観測時刻。利用者入力から受け取らない。 |
| `presence_observed_at` | 旧DBなどで、今回その行の存在を確認したサーバー時刻。過去の初回保存時刻を意味しない。 |

最小実装では次を分離する。

- `Store.thesis(company_id, as_of=t)` は **strict PIT** とし、`knowledge_at=t` に固定する。対象時点条件と保存来歴条件を両方満たす最新版を返す。
- `Store.thesis(company_id)` は現在の最新版を表示する。来歴不明の旧データを削除・非表示にしない。ただし、現在の表示だけで過去時点の利用可能性を認定しない。
- read-onlyの `thesis_view(company_id, *, as_of, knowledge_at, mode)` を設ける。`mode="pit"` は二時刻が等しい場合だけ許可する。`mode="retrospective"` は両時刻の明示を必須にし、後から保存した資料も参照できる再研究としてラベルを付ける。
- `as_of` を指定したのに `knowledge_at` を現在へ自動補完する挙動は設けない。現行の誤認を再導入するためである。

retrospectiveも既存の対象時点条件を免除しない。例えば原文の `retrieved_at > as_of` を公表日だけで利用可にする変更は含まない。公表時点だけを条件にした研究が必要なら、取得前の情報を利用した仮定と資料選定規則を別途明示する。

viewは少なくとも次のenvelopeを返す。返却された仮説JSONそのものに来歴欄を埋め込まない。

```json
{
  "temporal_mode": "pit",
  "as_of": "2026-10-09T17:30:00+09:00",
  "knowledge_at": "2026-10-09T17:30:00+09:00",
  "record": null,
  "availability_status": "unknown",
  "excluded": [
    {"kind": "thesis", "record_id": "example-company", "version": 2,
     "reason": "legacy_history_unknown"}
  ],
  "limitations": ["初回保存時刻を公表・取得・作成時刻から推定しない"]
}
```

`availability_status` は `known` / `partial` / `unknown` を区別する。保存済み後日版を除外して既知のv1を返す場合は、v1の来歴確認とv2除外の理由を併記する。来歴不明の版がある場合は、v1を返せても履歴全体を完全再現した成功とはしない。`record:null` だけで「当時は仮説なし」と断定しない。

## 接続した保存来歴library

実装は [availability.py](../src/ir_agent/availability.py) の `SCHEMA` と `RecordAvailability`。`record_availability` はentity_type/entity_id/versionを主キーとし、元snapshotのcanonical JSON SHA、first_saved_at、presence_observed_at、basisを保存する。source/reply/questionはversion=0、thesisは実際の正整数版。元JSONを変更しない。

| API | 現行の契約 |
| --- | --- |
| `record_first_save(type,id,snapshot,*,version=None,now)` | 新規INSERTと同じ既存transaction内で、信頼できるruntime時計を渡す。snapshotの日時がruntimeより未来、または保存時計が逆行していたら新規証明を作らない。 |
| `observe_existing(type,id,snapshot,*,version=None,now)` | 旧行の存在だけを記録。既存receiptは保持し、再送で初回時刻を更新しない。時計逆行で新しい存在証明を作れない場合はunknown診断を返す。 |
| `get(type,id,*,version=None)` | receiptまたはnull。元JSONの時刻から補完しない。 |
| `at(type,id,snapshot,*,version=None,as_of,knowledge_at,now)` | 二締切、実存在、snapshot SHAを照合するread-only API。available/unavailable/unknown、理由とfirst_save_knownを返す。closureと公開性は呼出元が点検する。 |

`now` はengine/test runtimeの依存性であり、CLIやrequest JSONから保存時計を設定するfieldではない。top-levelの予約済み保存時刻欄を原文データに付けて制御しようとする入力は拒否する。新規recordとreceiptは一緒にcommit/rollbackし、元行の再送で旧firstsaveを変更しない。存在確認だけの旧行をexact firstsaveへ昇格させない。

Storeはsource/thesisの単独書込みにもtransaction/savepointを使い、Harnessはquestion/replyの新規INSERTとreceiptを同時に保存する。旧行の不正な申告日時は現在の元データ表示を妨げず、PIT照会でunknownにする。mutableな送信/取消状態の履歴をreceipt一つから復元しない。

[全1056テストの接続記録](../research/ir-availability-integration-2026-10-15/README.md)に独立再確認、原ログ、実DBの存在確認28件と元JSON群のhash不変を保存した。

## 対象と選択規則

| 対象 | 保存来歴と利用条件 |
| --- | --- |
| thesis | 各immutable版にreceipt。`recorded_at <= as_of` とknowledge条件を照合し、降順に選ぶ。現在版を過去へ投影しない。 |
| source | 各immutable sourceにreceipt。直接根拠だけでなく `models.source_origins` の全親DAGを閉包で確認する。共有親をcycleと誤判定せず、真のcycle・親欠損・別会社は既存検証どおり保留する。 |
| reply | 受信原文の初回INSERTにreceipt。`received_at` は受信の申告時刻として残す。返信から生成したsourceは生成時に別receiptを取り、受信時刻を保存時刻へ転用しない。 |
| question | 固定した質問本文・分岐・thesis snapshotの初回保存を記録する。`created_at` と実保存を分ける。 |
| policy / decision review | 既存の信頼できる `first_saved_at` を直接利用する。新しいside tableへ二重の真実を作らない。 |

StoreのPIT表示、daily、claim、intakeは同じlibraryで全原典を確認する。questionの固定契約と返信後の判断が使う申告評価日時/実保存時刻の表示は、既存first_savedを保持しつつ別途点検を進める。各入口の完全な接続が済んだとは扱わない。retrospective envelopeをそのままstrictな根拠として再利用できるAPIにはしない。

PITで利用するには、既存の会社・公開性・合成資料・公表/取得/観測時刻などの条件に加え、消費する各recordが `knowledge_at` 以前に存在した保存根拠が要る。派生sourceのreceiptだけで原典の保存来歴を代用しない。未保存のcaller snapshotを渡すpure計算は、DBでの当時の存在証明とは別である。

本改修では日次jobにretrospective modeを追加しない。日次・claim・complete・実判断はstrict側を使う。将来研究jobへ遡及modeを加える場合は、modeとknowledge締切をpacket/signatureへ固定し、PIT jobとの再利用を防ぐ別設計が必要になる。

## 旧DBの移行

1. 旧行は保持し、raw JSON、本文、既存hash、版番号を変えない。receiptがなければ今回のサーバー時刻で `legacy_presence` を保存する。
2. `first_saved_at` はNULLのままにする。`retrieved_at` / `received_at` / `recorded_at`、ファイルmtime、移行時刻を初回保存の証明へ変換しない。
3. presence観測は「その時までには存在した」というknown-byの上界を与える。`knowledge_at >= presence_observed_at` なら存在確認済みとして扱えるが、初回保存が判明したとは返さない。観測前は `legacy_history_unknown` としてstrict照会から除外し、unknownを明示する。
4. receipt自体がない、壊れている、またはidentityと一致しない場合も成功にしない。現在の一覧・最新版表示は維持し、利用可能性診断を別に返す。
5. 信頼できる既存列を再利用できるのは、その列が証明するrecordに限る。policy/reviewの実保存時刻を、同時期のsource/thesisの初回保存時刻へ一括コピーしない。

実保存時刻を持つreviewのsource hash、実完了時刻を持つjobの固定result、questionの `frozen_at` から、内容一致したsnapshotがその時までに存在したという追加証拠を得られる場合はある。これは初回保存の完全復元と異なる。最小移行では自動回収を行わず、別のknown-by証拠として明示する設計ができた場合に限って追加する。legacyの再ingestはこの不明を勝手にexact firstsaveへ昇格させない。

## 既存防御と保証範囲

- 新しい実案件のquestionは実保存 `frozen_at` より前に送信済みとできない。policyの実保存がquestion作成より後である場合も拒否される。これらは維持する。
- 正規化で新しく読み取った事実の派生sourceは、原文公表時刻とは別の生成・保存観測を持つ。古い原典からの決定的変換でも、変換前からDBに派生値があったとは扱わない。
- firstsave/presence receiptは存在の証拠であり、questionの可変 `status` / `sent_at` / closureやcompanyの現在状態の履歴ではない。固定snapshotと現在状態を区別し、receipt一つで全項目がPITになったと主張しない。
- 公開性の後日訂正、保有履歴、モデル版、予測の凍結、lease世代などは既存の別契約を維持する。availabilityを通っただけで投資判断や情報の正確性が検証済みになるわけではない。
- timestampはtransaction内のサーバーによる保存観測である。receiptはcommitとともに可視化されるが、独立したcommit時刻証明・過去のDB read snapshot・外部監査証明ではない。

## 実装後の最小受入条件

- 初回INSERTとreceiptの同時rollback、正常commit、重複再送でfirstsave不変を確認する。user指定保存時計・未来時計で証明を作れない。
- 再現の17:30 strict照会は18:00処理の前後でv1のまま。18:00の現在照会はv2を扱え、historical viewはv2を後日保存として除外した理由を返す。
- `retrospective(as_of=17:30, knowledge_at=18:00)` はv2を研究用に返せるが、非PIT表示が必須。knowledge締切の省略・PIT二時刻不一致を拒否する。
- sourceの第二親が後日保存の場合もPITを通さない。全親DAG、返信派生source、質問の固定snapshotの経路で同じ条件を確認する。
- legacy移行は原文とhashを保持する。現在表示を残し、観測前のPITでは不明理由を返し、観測後もfirstsaveは不明と示す。
- 架空fixtureが古い資料を今保存して過去日を照会している場合、共通fixtureのruntime時計を正直に設定する。公表時点への再研究を意図した例は明示retrospectiveへ移す。late-ingestの回帰だけ時計を戻して通すことや、syntheticを一律に保存来歴検証から免除することはしない。

ここではコードと既存テストを変更していない。後続のlibrary接続・fixture時計の整理・統合検証で、この設計と実装の差を確認する。


## CLIで二時刻を明示する

```bash
.venv/bin/ir-agent --db PATH thesis-view COMPANY_ID \
  --as-of TARGET_TIMESTAMP --knowledge-at TARGET_TIMESTAMP --mode pit
.venv/bin/ir-agent --db PATH thesis-view COMPANY_ID \
  --as-of TARGET_TIMESTAMP --knowledge-at LATER_KNOWLEDGE_TIMESTAMP --mode retrospective
```

全時刻はoffset付き。pitで二締切が違う場合やruntimeより未来の場合は拒否する。retrospectiveはread-only envelopeであり、日次jobを作らない。通常の `thesis --as-of` もstrict側で選ぶ。as_of省略時の現在最新版表示と、過去時点の存在確認を区別する。
