# 過去時点の保存来歴の欠落：未修正の再現

2026-10-15のread-only点検で確認した。**保存来歴libraryとPIT照会の修正は未実装。** 原因と実装契約は [設計文書](../../docs/historical-availability-design.md)にある。

[再現script](ir_historical_availability_repro.py)と[実行結果](ir_historical_availability_repro.json)は、`/tmp` に作成した元のファイルをそのままコピーした。すべて架空fixtureと `:memory:` DBを使う。外部通信、実台帳変更、企業への連絡、注文はない。`synthetic:false` は実案件側の保存契約を架空入力で検査する指定であり、実企業の分析であることを意味しない。

```bash
cd /workspace/ir-agent
.venv/bin/python research/ir-historical-availability-2026-10-15/ir_historical_availability_repro.py
```

scriptのrepoパスは `/workspace/ir-agent` 固定である。入力は既存の `tests/test_decision_lifecycle.py` と `examples/reply.json` を使い、runtime時計を各処理段階へ固定する。再実行は `/tmp/ir_historical_availability_repro.json` を更新し、この保存済みJSONや実台帳を書き換えない。コード修正後は、未修正状態をassertするこのscriptが失敗する可能性がある。保存結果を修正後の結果と混同しない。

時刻は日本時間で示す。

| 段階 | 結果 |
| --- | --- |
| 18:00の追加処理前に17:30を照会 | `Store.thesis(as_of=17:30)` はv1、日次packetもv1。 |
| 18:00に過去の返信・価格を取り込み、作成時刻17:20で返信を適用 | 仮説v2を新規保存。reviewの `first_saved_at` は正しく18:00。 |
| 同じ17:30をもう一度照会 | `Store.thesis` と日次packetがv2へ変わる。 |

不備は、実際には後から保存された入力を過去のDB時点の仮説へ混ぜる点にある。reviewを17:20に保存したという偽記録は確認していない。18:00時点で新しく計算した `buy_review` 候補も成立するfixtureなので、現在の候補自体を不備とはしていない。質問の実保存前へ送信時刻を戻す既存防御が有効であることも同時に確認した。

この成果は再現1件と設計契約に限定する。既存checkpointは983件成功だが、この未修正問題を解消した証明ではない。追加の全件テスト、ネット調査、実DB移行は行っていない。
