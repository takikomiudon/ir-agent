# IIJ（3774）：公表EPS・配当予想の意味の点検

会社予想EPS141.03円は2027年3月期の連結・基本的1株当たり当期利益、配当43円は同年度の中間21.50円と期末21.50円の年間予想。配当の基本方針は内部留保への配慮と安定的な継続。30〜40%は中長期ビジョンの連結配当性向イメージで、現在の最低配当や永続規則ではない。

保存済み公開source 12件を横断し、項目別にsupported 9件・unknown 6件へ分けた。記録日時 `2026-10-15T02:33:08.715202+00:00`。これは保存資料内の意味の点検で、実予測や売買への採用ではない。

通期予想EPSの正確な将来加重平均株式数、自己株式取得/処分・増資の時期別織込みは未特定。四半期実績の期末/平均株式数を予想分母として流用せず、丸められた利益から逆算しない。単年の年間DPSを多年DPS配列や終価へ延長しない。EPSとDPSの大小から独自の安全/危険判断を作成していない。

## 項目一覧

| ID | status | 点検内容 | 参照した保存資料（PDF頁） |
|---|---|---|---|
| `forecast_eps_period_and_consolidation` | supported | 通期予想EPSの期間・範囲 | IIJ1Q26J.pdf p.1 |
| `forecast_annual_dps_and_installments` | supported | 年間配当予想の期間・合計・内訳 | IIJ1Q26J.pdf p.1 |
| `quarter_actual_share_counts` | supported | 当四半期期末株式数・自己株式数と期中平均 | IIJ1Q26J.pdf p.2 |
| `forecast_eps_weighted_average_share_count` | unknown | 通期予想EPSに使った将来加重平均株式数 | IIJ1Q26J.pdf p.1、IIJ1Q26J.pdf p.2 |
| `forecast_uncertainty` | supported | 会社予想の不確実性 | IIJ1Q26J.pdf p.2 |
| `reported_eps_method` | supported | 開示実績EPSの基本的/希薄化後の定義 | FY2025_End.pdf p.113 |
| `reported_dilution_basis` | supported | 直前通期実績における希薄化の基礎 | FY2025_End.pdf p.140 |
| `historical_split_adjustments` | supported | 確認できた過去の株式分割調整 | FY2025_End.pdf p.2、FY2025_End.pdf p.3 |
| `current_forecast_split_assumptions` | unknown | 現在の通期予想EPS/DPSの追加分割想定 | IIJ1Q26J.pdf p.1、FY2025_End.pdf p.2 |
| `dividend_basic_policy` | supported | 公表された配当基本方針 | IIJ1Q26J_presentation.pdf p.22、FY2025_End.pdf p.67 |
| `payout_target_scope` | supported | 公表された配当性向の期間・性質 | IIJ1Q26J_presentation.pdf p.43 |
| `doe_or_numeric_dividend_floor` | unknown | DOEまたは数値の最低配当条項 | IIJ1Q26J_presentation.pdf p.22、FY2025_End.pdf p.67、IIJ1Q26J_presentation.pdf p.43 |
| `forecast_future_dilution_and_treasury_path` | unknown | 予想期の増資・自己株式取得処分と希薄化の全経路 | IIJ1Q26J.pdf p.1、IIJ1Q26J.pdf p.2 |
| `forecast_dps_cashflow_calendar` | unknown | DDMへ使う場合の配当キャッシュフロー時点 | IIJ1Q26J.pdf p.1 |
| `multi_year_forecast_and_terminal_inputs` | unknown | 多年予測と終価の入力 | IIJ1Q26J.pdf p.1 |

supportedは引用に支持される当該範囲・時点の記述を表す。unknownは今回の保存資料で未確認であり、非公表や不存在の断定ではない。EPS/配当の会社予想値を独自予測・割引率・評価倍率・確率へ変更しない。`financial_inputs_verified: false` / `model_inputs_adopted: false` のまま。

## 公開資料で解決した点と残る点

supportedの項目は公開資料で定義・期間・基準が説明済みなので、同じ内容を未解決IR質問として扱わない。unknownの項目はJSONの `remaining_missing` に具体的不足を記録したが、新しいIR質問の登録・送信候補化を行っていない。必要なモデル入力か、追加の回答に判断価値があるかは別途の確認事項。

IIJ CAPEX質問のclosed/no-send、パイオラックスのnot-readyという保存済み結論は維持。既存case/原source/数値/manifestを変更せず、新GET・IR質問登録・モデル予測採用・企業状態変更なし。read-onlyのbundle builderで元資料の整合と保存bundle全体一致を確認。対象原ファイルの作成前後SHA-256一致を確認し、JSON `source_preservation` へ記録した。別担当がCLI実行記録を追記する派生extraction-notes.mdとnormalize出力bundleは原資料保持guardの対象外（当担当から変更なし）。

各引用は原source本文の逐語部分文字列で、PDF頁を改ページ区切りと照合。頁内の空白・改行・全角数字を保持し、表の読取り・過去/予想期の対応の限界を明示する。全sourceの一覧・初回取得日時・本文SHA-256はJSON `source_inventory` に記録。


項目ごとの逐語引用・PDF頁・確認範囲・残る不足・資料保持ハッシュは [financial-input-meaning-review.json](financial-input-meaning-review.json) に保存した。上表の項目IDで参照できる。
