# state/signal固定入力packet（B）の実装準備点検

**既存APIは参照・原文・時点監査には足りるが、役割別packetの不変commitmentには足りない。** 現時点で必要なのは監査結果からの限定投影であり、別の観測台帳、分類器、scorer、尤度モデルを追加する根拠はない。Aはrecord-only registry、B/Cは未実装のまま。rootがscopeを決めるまで実装しない。

## 既存機能と重複させない範囲

| 部品 | 再利用できること | Bで同じものと扱えないこと |
|---|---|---|
| `evaluation_protocols.py` | protocol ID/版、元要求SHA、trusted初回保存、CAS、不変再送。 | `draft=false`も意味・採用・前向き性の確認ではない。cohort/source/model参照は未解決、規則は文章であり実行可能な選択規則ではない。 |
| `ObservationStore` / `PredictionStore` | design/観測版と予測の不変参照、実保存時刻、追記/CAS、予測登録時の事後観測排除。 | 観測snapshotには返信分類・verificationがある。予測の保存成功は訓練独立性・評価ラベルの真実性を保証しない。 |
| `report_prediction_bindings` | 同一read snapshot、観測左結合、原文/SHA/会社/質問/時刻、source全祖先・循環・synthetic、使用時点/as-of/現在の来歴と公開性、欠損の明示。 | 出力は**観測全snapshot、元/現signal、申告state、予測確率、質問全体、全source/返信原文**を含む。丸ごとの再利用は役割分離にならない。 |
| `RecordAvailability` / 情報review | 原snapshot SHA、実保存とlegacy known-byの区別、過去と現在の情報保留。 | entityはsource/thesis/reply/questionのみ。protocol/packetのreceiptを捏造しない。来歴一致だけで意味や独立性を認定しない。 |
| `prediction_readiness._signal_leakage` | 台帳に記録されたstate確認後のsignal訂正候補。 | 公開実績を先に見た、別担当から聞いた等の未記録露出や、初回分類自体の汚染を検出し尽くさない。候補0を漏洩なしにしない。 |

## 最小scopeの提案

最初は**明示した既存1観測版・1protocol版・1役割**を対象とし、役割別の許可情報を列挙する投影だけに限定できる。母集団全体の点検は既存reportを使い、未送信/未予測/未判定/保留を消さない。prose規則を自動解釈して資料や返信を選ぶ仕組みは追加しない。

固定に必要なのは、protocol要求SHA/版と保存時刻、観測ID/版/snapshot SHA/design SHA、役割、生成手順/設定の版、明示した入力参照と再現できる内容・SHA・来歴、適用したcutoff、生成時刻、除外情報の種類、欠損・保留理由である。protocol全本文を両担当へ配るのではなく、役割に必要な定義・手順を投影し、その投影もhashへ含める。元protocol/観測/source/返信と全祖先は内部監査manifestに残し、担当用payloadと分ける。

- **state担当**：事前state定義・対象期・比較基準、明示選択した後続公表資料・表位置・外部変化の根拠。対象IR原文、元/現signal、既存state結論、予測・売買・損益を渡さない。
- **signal担当**：質問の必要本文・定義、事前signals、明示選択した返信本文・受信/期限情報、必要な公開定義。後続実績・state結論、予測・売買・損益を渡さない。既存signalや訂正結論も自動同梱しない。

source祖先がIR由来なら、URLやsource IDが違うだけでstate独立根拠へ採用しない。内部の全祖先監査と、担当へ渡す本文の許可は別である。同じ公表資料に許可定義と後続結果が混在する場合、metadataのroleだけで安全とは扱えず、明示した本文範囲とその意味を別途点検する。根拠未解決は理由付き不足、SHA不一致や未知fieldは入力エラーであり、新sourceや別の観測へ自動付替えしない。

**既存bindingの境界**：公開APIはas-of可視の最新観測版にmappingを合わせ、state根拠は既存`verification.evidence`へ対応させる。未判定state用に新たに選んだ資料を、このAPIへ通すためだけに仮のverificationとして追記してはいけない。必要なら既存graph/availability照合を狭く共有するか、その資料のbinding未確認を残す。新しい状態ラベル・包括的な選択DSLは不要である。

## 時点・現在保留・不変性

protocolは将来の資料そのものではなく選択規則を事前固定する。state packetには後続公表資料が必要なので、全入力を質問時点以前に限定する単一cutoffは不適切。質問前の基準・protocolの保存、返信の発生/実保存、signal用情報締切、state根拠の公表/取得/実保存、packet生成、現在の点検時計を分ける。後日保存した資料を申告時刻だけで過去へ入れない。歴史再現はevent/knowledge cutoffを明示し、現在確認できる内容と混同しない。

既存reportの全祖先に対するusage/as-of/現在のavailability/publicityを再利用できる。raw snapshotのSHAと検証用default補完後コピーは区別する。古い資料と同IDの内容不一致、IR祖先の現在保留、synthetic混入は失敗・保留を残す。後からの公開分類で当時の保留を消さない。新しい訂正公表が旧資料を意味上置換するかは、現在のhelperが全Webから自動発見する機能ではなく、訂正対応の明示が別途必要である。

生成後に保留が追加されても、元packetの内容/hashを書き換えず、現在の利用可否を別のread-only点検として返す。再生成は新commitmentで、過去の分類を自動修正・採点へ昇格しない。

**read-only previewと保存の区別**：builderの返値にhashとtrusted実行時計があっても、trusted初回保存を記録したことにはならない。永続commitmentとしてBを完了させるなら、server側の保存・不変同ID再送・transaction・実保存時刻の契約をrootが別途確定する必要がある。まずpreviewだけなら新tableは不要だが、Bの保存完了と呼ばない。Aのprotocolや既存RecordAvailabilityへpacketを混ぜ込む拡張は不要。

## 技術的に保証できる範囲と採用判断

保証できるのは、明示した許可field/本文範囲だけを含むpayload、固定snapshotからの再現、hash/参照/記録された時点と公開性、不足の保持まで。stateとsignalの意味的独立、真値、未記録の知識、同一workspace/親履歴/別tool経由の露出は保証できない。別packetや別担当名だけでblindにせず、実アクセス制御がなければ「当該payloadから除外した」とだけ述べる。単語検出や`blind:true`で代用しない。

保存根拠のGneiting–Raftery **G1（PDF1/誌面359）、G8（PDF14/誌面372）**は実現観測との照合と観測前の予測則指定を支持するが、IRラベルの真実性やこのpacket方式を規定しない。scikit-learn公式 **C1/C2（§3.1.2.1）、C3（§3.1.2.4.1）、C5（§3.1.2.6）**は時間/group分割の注意を支持する。Bでsplit実行や標本数/期間幅を追加せず、protocolの既存group/time規則と各入力の利用可能時刻を保持する。企業分離だけで市場共通要因の独立性を認定しない。

現段階で既存の根拠監査・資料整理を続けるには新機能は不要。役割を分けた実レビューを開始する具体的必要があれば、上の限定投影と不足表示だけが追加候補となる。完全な盲検・ラベル判定・前向き採点を先回りして実装する根拠はない。実データでprotocolや必要資料が不足する場合は不足のまま進捗に残し、架空のstate/likelihood/数値や新policyで埋めない。

## 参照・未点検

[設計A/B/C](../../docs/evaluation-protocol-design.md)、[原文binding](../../docs/prediction-evidence-binding.md)、[予測保存](../../docs/probability-prediction-storage.md)、各対応module、[保存文献](../probabilistic-evaluation-2026-10-15/sources.json)の上記引用をread-only照合した。文献原PDF SHAは`d31a0c5f0ae8fec1a0a6544db5d056645b2d7296d71b44a2e8efb293c7d87ba2`、公式分割説明のraw SHAは`78d7587fa92ba3b3e480c9d841b50fedc14ac29d571ccb319d4068235154f0e2`。取得原典の全再監査・実データ/実DBの存在確認・テスト実行はしていない。ネット/DB操作・src/tests編集0、成果物は本READMEのみ。
