# 8151：会社通期短信の取得はrobots確認で保留

公式短信入口 `https://www.toyo.co.jp/ir/library/earnings/` に進む前に、同hostのrobotsを1GETした。200で受信した原文は、`GPTBot`・`ClaudeBot`・`Claude-SearchBot`それぞれに`Disallow: /`を明示している。

固定の実UA `Codex-IR-Research/0.1`についてはwildcard Allowが字義上適用されるが、AI個別全面禁止がある場合はAI取得許可へ一般化しない既存の保守運用を採用した。UAを変更せず、**短信入口HTMLもPDFも取得せず終了**した。残予算3GETを使わず、JS・推測URL・別host・転載・別route・再試行は0。

## 保存と点検

- robots実受信完了: `2026-10-15T09:46:28.570909Z`。開始時刻やヘッダ受信とは分けてcaptureへ記録。
- raw SHA256: `4a352cfd2485fb217042b35036d6016c4ea1abd955efb6415a689dd00dfaaab7`。
- 保存response entityは9,641bytes。宣言Content-Length=2652はgzipされたHTTP表現で、requestsが復号した保存bytesと同一だと扱わない。元rawとrobots.txtのCRLFを保持して一致照合。
- `robots-review.json`と`quotes.json`に固定UAの字義上許可・個別AIの禁止を分け、原文の連続引用/文字offsetを保存。
- 共有2秒lockと既存proxy/CAを維持。case専用fetchは16MiB boundedstream、最大4GETだが、今回PDF取得/保存bytesは0。停止後の再実行も拒否する。

`source-bundle.json`は金融source0の空bundle。会社に実績資料が存在しないことや、FY2025/9実績が0だったことを意味しない。robotsを金融開示sourceとして登録していない。`validation.json`は狭いraw/引用/停止経路の点検であり、会社財務値・著者予測との一致・予測精度を確認した結果ではない。

## 比較可能性は未確定

2025-06-03のAstris EPS/DPS E予測は[別の原文と構造化記録](../external-estimate-facts/README.md)に保持されるが、今回会社の通期本文は未読。FY2025/9実績EPS/DPSと会社予想の区別、対象期・連結範囲・会計基準・株式分割/株数/希薄化・配当の年次/中間・基準日/支払日の対応は全てnull/未確認である。著者予測を会社実績に代入せず、期間が終わっていることを結果判明の証拠としない。2025時点でシステムが事前予測した記録・採点・売買・期待値は作成していない。

新規書込はこのcaseディレクトリと共有rate制御fileのみ。旧資料・production code・DBは変更しておらず、IR質問・送信・モデル採用は0。現在の認可範囲内ではここで区切る。
