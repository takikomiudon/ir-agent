# パイオラックス（5988）：公表EPS・配当予想の意味の点検

会社予想EPS27.45円は2027年3月期の連結通期1株当たり当期純利益、配当92円は中間39円と期末53円の年間予想。会社は2027年3月期までの連結配当性向100%・年間92円以上の方針を公表している。期限後の数値下限は今回の保存資料から確認できない。

保存済み公開source 8件を横断し、項目別にsupported 9件・unknown 7件へ分けた。記録日時 `2026-10-15T02:33:08.715202+00:00`。これは保存資料内の意味の点検で、実予測や売買への採用ではない。

通期予想EPSの正確な将来加重平均株式数、自己株式取得/処分・増資の時期別織込みは未特定。四半期実績の期末/平均株式数を予想分母として流用せず、丸められた利益から逆算しない。単年の年間DPSを多年DPS配列や終価へ延長しない。EPSとDPSの大小から独自の安全/危険判断を作成していない。

## 項目一覧

| ID | status | 点検内容 | 参照した保存資料（PDF頁） |
|---|---|---|---|
| `forecast_eps_period_and_consolidation` | supported | 通期予想EPSの期間・範囲 | 20260805_2026-q1_tanshin.pdf p.1 |
| `forecast_annual_dps_and_installments` | supported | 年間配当予想の期間・合計・内訳 | 20260805_2026-q1_tanshin.pdf p.1 |
| `quarter_actual_share_counts` | supported | 当四半期期末株式数・自己株式数と期中平均 | 20260805_2026-q1_tanshin.pdf p.2 |
| `forecast_eps_weighted_average_share_count` | unknown | 通期予想EPSに使った将来加重平均株式数 | 20260805_2026-q1_tanshin.pdf p.1、20260805_2026-q1_tanshin.pdf p.2 |
| `forecast_uncertainty` | supported | 会社予想の不確実性 | 20260805_2026-q1_tanshin.pdf p.2 |
| `reported_eps_method` | supported | 直前通期実績EPSの計算基礎 | 20260618_2025-q4_report.pdf p.103 |
| `trust_treasury_shares_treatment` | supported | 信託保有株式の自己株式としての控除 | 20260805_2026-q1_tanshin.pdf p.2 |
| `reported_dilution_basis` | supported | 直前通期の潜在株式調整後EPSがない理由 | 20260618_2025-q4_report.pdf p.103 |
| `current_forecast_split_assumptions` | unknown | 現在の通期予想EPS/DPSの株式分割調整基準 | 20260805_2026-q1_tanshin.pdf p.1、20260805_2026-q1_tanshin.pdf p.2 |
| `dividend_basic_policy` | supported | 公表された配当基本方針・決定機関 | 20260618_2025-q4_report.pdf p.41、2025-2027_management-plan_R.pdf p.17 |
| `payout_and_dividend_floor_until_fy2027` | supported | 期限付きの連結配当性向・1株年間配当下限 | 20260618_2025-q4_report.pdf p.41、20260512_2025-q4_summary_R2.pdf p.10、2025-2027_management-plan_R.pdf p.17 |
| `dividend_floor_after_fy2027` | unknown | 2027年3月期後の数値下限・配当性向延長 | 2025-2027_management-plan_R.pdf p.17、20260618_2025-q4_report.pdf p.41 |
| `doe_policy` | unknown | DOEによる配当計算規則 | 20260618_2025-q4_report.pdf p.41、2025-2027_management-plan_R.pdf p.17 |
| `forecast_future_dilution_and_treasury_path` | unknown | 予想期の増資・自己株式取得処分と希薄化の全経路 | 20260805_2026-q1_tanshin.pdf p.1、20260805_2026-q1_tanshin.pdf p.2 |
| `forecast_dps_cashflow_calendar` | unknown | DDMへ使う場合の配当キャッシュフロー時点 | 20260805_2026-q1_tanshin.pdf p.1 |
| `multi_year_forecast_and_terminal_inputs` | unknown | 多年予測と終価の入力 | 20260805_2026-q1_tanshin.pdf p.1 |

supportedは引用に支持される当該範囲・時点の記述を表す。unknownは今回の保存資料で未確認であり、非公表や不存在の断定ではない。EPS/配当の会社予想値を独自予測・割引率・評価倍率・確率へ変更しない。`financial_inputs_verified: false` / `model_inputs_adopted: false` のまま。

## 公開資料で解決した点と残る点

supportedの項目は公開資料で定義・期間・基準が説明済みなので、同じ内容を未解決IR質問として扱わない。unknownの項目はJSONの `remaining_missing` に具体的不足を記録したが、新しいIR質問の登録・送信候補化を行っていない。必要なモデル入力か、追加の回答に判断価値があるかは別途の確認事項。

IIJ CAPEX質問のclosed/no-send、パイオラックスのnot-readyという保存済み結論は維持。既存case/原source/数値/manifestを変更せず、新GET・IR質問登録・モデル予測採用・企業状態変更なし。read-onlyのbundle builderで元資料の整合と保存bundle全体一致を確認。対象原ファイルの作成前後SHA-256一致を確認し、JSON `source_preservation` へ記録した。別担当がCLI実行記録を追記する派生extraction-notes.mdとnormalize出力bundleは原資料保持guardの対象外（当担当から変更なし）。

各引用は原source本文の逐語部分文字列で、PDF頁を改ページ区切りと照合。頁内の空白・改行・全角数字を保持し、表の読取り・過去/予想期の対応の限界を明示する。全sourceの一覧・初回取得日時・本文SHA-256はJSON `source_inventory` に記録。


項目ごとの逐語引用・PDF頁・確認範囲・残る不足・資料保持ハッシュは [financial-input-meaning-review.json](financial-input-meaning-review.json) に保存した。上表の項目IDで参照できる。
