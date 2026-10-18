# 株式会社インターネットイニシアティブ（3774）：保存資料によるモデル点検

2026-10-15。[model-assessment.json](model-assessment.json)へ研究用テンプレートを適用した。**24項目中6項目に保存資料から確認できる値を記録し、18項目をnullのまま残した。結果は `needs_data` のみで、通常・金融・循環・younglossのどのモデルにも分類を確定していない。**

確認したのは会社資料の記述・表と、その値の符号である。個別企業の適正価格や評価入力の妥当性を確認した意味ではない。正の四半期EPSから通常モデルを選ばず、業種や赤字一期から専用モデルを選んでいない。

使ったのは [保存資料bundle](../../../data/case-source-bundle.json)と既存ケースの原文だけ。元のREADME・draft・manifest・raw・bundleを変更せず、新GET、会社状態/active更新、IR送信、買い・売り候補の作成、独自のEPS・倍率・確率の設定は0件。

## 実績と会社予想を分ける

最新の保存済み短信は2026-08-07公表、2027年3月期第1四半期（2026年4〜6月）、IFRS連結。表紙の実績は売上97,604百万円、営業利益6,588百万円、親会社利益4,395百万円、基本EPS24.79円。会社の通期予想EPS141.03円は**会社予想**として別記し、独自の予測値にしていない。四半期EPSの年率換算もしていない。

2026年3月期有報PDF6頁はネットワークサービス・SIとATM運営を説明し、1992年12月の設立を記載する。これらは事業と沿革の公表事実であり、「非金融会社」「全事業が安定期」との確定ではない。関連会社や事業別の構造、営業負債・規制資本の適合まで確認したことにはしない。

1Q短信PDF4頁（印刷2頁）の利益説明と、説明資料PDF19頁（表示18頁）のCAPEX控除定義を参照した。管理CAPEXと法定CFの全額対応や、将来CFへの適合が未解決である点を残した。

## 24項目の状態

`支持あり` は、保存した記述または表を支持する原文があるという意味。会社説明の因果関係や将来計画を独立に実証したという意味ではない。金融・循環・youngloss該当などの推論は、`tentative_interpretations` に未確認として分け、事実の確定値へ入れていない。

| fact ID | 値・確認範囲 |
|---|---|
| `entity_and_business_scope` | 支持あり。会社の事業記述と最新1Q会計範囲を資料別に保持。 |
| `financial_intermediation_core` | `null`。定義・適合・履歴等が未確認。 |
| `funding_liabilities_are_operating_inputs` | `null`。定義・適合・履歴等が未確認。 |
| `regulatory_capital_constrains_growth_or_distribution` | `null`。定義・適合・履歴等が未確認。 |
| `financing_debt_definition_compatible` | `null`。定義・適合・履歴等が未確認。 |
| `noncash_working_capital_definition_compatible` | `null`。定義・適合・履歴等が未確認。 |
| `reinvestment_definition_compatible` | `null`。定義・適合・履歴等が未確認。 |
| `current_earnings_measurements` | 支持あり。最新1Qの売上・営業利益・親会社利益・基本EPS。 |
| `current_operating_income_negative` | `false`。指定した最新1Qの営業利益が正、という算術観測のみ。 |
| `current_eps_nonpositive` | `false`。指定した最新1Qの基本EPSが正、という算術観測のみ。 |
| `earnings_change_or_loss_cause` | 支持あり。会社が説明した要因。独立した因果推定ではない。 |
| `cycle_or_commodity_dependency_supported` | `null`。定義・適合・履歴等が未確認。 |
| `history_covers_full_cycle` | `null`。定義・適合・履歴等が未確認。 |
| `history_scope_and_scale_comparable` | `null`。定義・適合・履歴等が未確認。 |
| `normalization_inputs_consistent` | `null`。定義・適合・履歴等が未確認。 |
| `finite_resource_life_relevant` | `null`。定義・適合・履歴等が未確認。 |
| `operating_history_and_commercial_stage` | 支持あり。法人設立の沿革。事業別の安定期判定は未確認。 |
| `monetization_path_evidenced` | `null`。定義・適合・履歴等が未確認。 |
| `growth_reinvestment_and_funding_consistent` | `null`。定義・適合・履歴等が未確認。 |
| `funding_gap_or_dilution_before_positive_cashflow` | `null`。定義・適合・履歴等が未確認。 |
| `survival_and_distress_inputs_supported` | `null`。定義・適合・履歴等が未確認。 |
| `tax_loss_and_terminal_conditions_supported` | `null`。定義・適合・履歴等が未確認。 |
| `earnings_multiple_comparability_reviewed` | `null`。定義・適合・履歴等が未確認。 |
| `ordinary_model_compatibility_supported` | `null`。定義・適合・履歴等が未確認。 |

各確認値には、出典ID、逐語引用、PDF物理頁/印刷頁または節、対象主体・会計・対象期、公表日の精度、取得時刻、確認者を付けた。日付だけの公表資料に架空の公表時刻を補わず、利用可能な情報は元の取得時刻も踏まえて扱う。

## 7タスクの処理状態と不足

| タスク | 状態 | 残る入力・資料 |
|---|---|---|
| T01-entity-scope | 確認作業を処理済み | 対象範囲と実績表の保存確認は終了。モデル入力の採用とは別。 |
| T02-financial-structure | `needs_data` | 事業別の営業負債/財務借入の定義と適用範囲／規制資本制約の有無を判断できる会社/規制資料の該当箇所／使用するDCFの負債・運転資本・再投資定義との対応 |
| T03-earnings-causes | 確認作業を処理済み | 利益の持続性と単発/構造要因の金額対応は別途点検 |
| T04-cycle-history | `needs_data` | 景気/商品価格など特定ドライバーと利益・再投資の対応履歴／全サイクルを含む期間とその根拠／会計・連結範囲・企業規模変化と正常化方法 |
| T05-commercial-path | `needs_data` | 事業別の商用化・売上ドライバー・収益化経路の根拠／成長と必要再投資/資金の対応。該当性が否定できれば非該当根拠 |
| T06-funding-and-risk | `needs_data` | 将来CFと資金余力・満期・調達条件の照合／必要な場合の生存/失敗確率の期間と失敗時価値／適用する税/欠損金・安定期条件。モデル非該当ならその根拠 |
| T07-model-and-counterreview | `needs_data` | 負債/再投資/期間の適合判定／EPS・倍率の同期間/比較可能性と現在価格（本点検では未設定）／独立した反証点検と未解決の矛盾整理 |

調査パスを一巡したことと、必要入力が揃ったことを区別する。`needs_data` は同じ資料や取得失敗を無期限に再調査する指示ではない。モデルの適合を絞るには、まず負債・再投資・運転資本とその会計範囲を説明する保存注記等の確認が必要となる。サイクル点検を選ぶなら特定要因と全サイクル履歴、youngloss点検を選ぶなら事業別の移行と必要資金の根拠が必要で、該当性を確かめる前に全専用モデルの数値を要求しない。

通常モデルや専用モデルの検討先が決まっても、現在価格、根拠付きの評価入力、比較可能な倍率やCF前提は別に必要となる。今回の観測を既存 `eps_multiple` や `dcf` へそのまま投入していない。銀行のPERを禁止する規則も追加していない。

## IRの保存結論を維持

元のCAPEX質問は `closed_no_send_insufficient_incremental_value`、有効質問0件、送信しないという結論を維持した。モデル定義の不明点を記録したことを、質問の再開や新たな送信価値の立証に使っていない。

## 保存検証

9個の引用を指定した保存頁とbundle本文に照合し、参照した原本3件のSHA-256を検証した。24factのうち6件に値、18件はnull。タスクは2件の確認作業を処理済み、5件はneeds_data。テンプレートの方法引用ID・fact参照・task参照を確認し、元のケースファイルとbundleが同一バイトで保持されていることも確認した。

この結果は資料を使った研究入力の例であり、企業のモデル分類・適正価格・売買・IR送信を完了した報告ではない。
