# 8151：2025年6月3日Astris著者E予測の構造化

保存済み [外部レポート](../external-report-review/README.md) のPDF sourceを**完全に同一のまま** `normalize_disclosed_facts` へ渡し、EPS/DPSの6項目をresearchデータへ構造化した。会社予想や公表実績と混ぜず、すべて `kind=external_estimate`。会社status・金融モデル・IR質問・DBは変更していない。

| p1原表の期ラベル | EPS（円） | 1 株当たり配当（円） |
|---|---:|---:|
| 9/25E | 80.88 | 69.00 |
| 9/26E | 103.69 | 72.00 |
| 9/27E | 147.83 | 80.00 |

小数表記も原文どおり保持し、提示の69/72/80で補完しない。原表の単位`円`から`JPY-per-share`への既存の明示1倍換算だけを行った。p5の`DPS (¥)`は補助照合であり、未対応の¥単位mappingを追加/推測しない。

p1のE列・EPS/配当行・著者出所と、p5の「アストリス・アドバイザリーの業績予想」/会社予想別列/注記を、保存画像と本文で確認した。各factにはp1の「当社業績予想」から表末尾の著者出所までの**単一連続quote**を保存し、unit・E期・列・著者を同一引用内に含める。広いquoteに他指標や歴史的PER13.7等が含まれても、それらをfactや公正倍率へ採用しない。FY25会社予想DPS69と著者DPS69は同値だが、会社列を著者列と取り違えない。

`scope.forecast_origin`はAstris組織、個人著者未確認、報酬関係、2025-06-03表示日を保持する。`review.author`は抽出担当Codexであり、外部予測の著者とは別。会社データ脚注・会社委託/支払を保ち、独立性や予測精度を確認済みとはしない。原表期ラベルと9月という表示だけを保持し、厳密な開始日/終了日を補わない。

## 検証範囲

- `request.json`：元PDF source exact、抽出担当/実review時刻、6facts。
- `bundle.json`：既存normalizerの戻り値。元PDF1＋派生抽出1、companies/theses空。
- `validation.json`：CLI parser→実`run` dispatch、独立Decimal1倍照合、低精度/丸めtrap下の再現、既知normalizer replay、元artifact hash不変、原表/画像照合結果。

DB0を守るためCLI `main`のStore初期化を避け、parserと`run`をSQL禁止sentinelに接続した。CLI時計は上記実処理時刻へ固定し、pure API出力と完全一致した。SQLを実行したテスト、実DBのingest、永続保存成功を意味しない。

replayは`reproduced`。原PDFの`published_at=null`、本文・metadata・sourceIDは不変。PDFの元親HTMLは[元source-bundle](../external-report-review/source-bundle.json)に保存されている。normalizerの戻り値2件だけで全親を持つとせず、後のgraph audit/importは元HTML親も解決する必要がある。

## 時点・未確認事項

外部予測の表示日は**2025年6月3日**、本文の実受信は2026年10月15日09:19:59.606249Z、抽出review/処理は同日09:31:10頃。現在最新の外部予測へ転用しない。一部対象期が既に終わっていても、当該結果を今回確認したわけではなく、結果判明前に予測を保存した記録や前向きの採点データにはならない。日付表示を公表timestampへ補完しない。

EPSの株数/希薄化、期・連結範囲、配当基準日/支払日/決議・投資家の権利・購入時点からの残余受取との対応は未確認。年次DPSを今からの12カ月受取やt1年末CFと同一視しない。最新価格、公正倍率、確率、割引率、終価、費用/判断方針は補完していない。金融的意味・モデル採用・投資判断・IR草案は未実施。
