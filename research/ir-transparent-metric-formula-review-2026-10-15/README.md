# 指標の式・コード・日本株入力への不足

固定commit `00944e3b8fe853d8b82050f5ffb0f8c0fc6fb1b7`の指定3blobを3GETで取得し、Git blob SHAを再計算照合した。**定義の違いと未確認の計算境界は具体化したが、日本株の公表原典を使うROIC/ROC/EYの再現完了には至らない。** コードの静的読取のみで、候補コードのimport・導入・実行、依存・provider取得、金融値生成・採用は0。F-score等は今回の評価対象外。

原資料は[upstream-INDICATORS.md](upstream-INDICATORS.md)（以下I）、[upstream-ratios.py](upstream-ratios.py)（R）、[upstream-DATA-SOURCES.md](upstream-DATA-SOURCES.md)（D）。行は1起算。READMEや外部著者の一般説明で、未読実装の挙動を埋めない。

## 分子・分母・税・期間の対比

| 対象 | 文書で説明された定義 | 今回のコードで確認できる範囲／不足 |
|---|---|---|
| 税引後ROIC | EBITに税引前利益に対する税金費用率を適用したNOPATを、年間平均の「純資産＋負債−現金等」で除す。税率を0〜50%にclip、税引前赤字はNaN、投下資本が総資産の10%未満ならNaN、前年がない初年度はNaN。[I:783–807] | Rは旧名return_on_invested_capitalを、別物の式だという理由でdenylistにして出力しない。[R:32–49,178–179] 独立名roicの実装本体・税率clip・平均・小分母判定はこのfileにない。税引前利益ゼロ、ちょうど10%の境界、総資産非正・非有限時、連結税額と営業EBITの適合は未確定。文書の率やguardを当projectの採用値にしない。 |
| Greenblatt ROC | EBIT／（運転資本＋純有形固定資産）。税前で、上のROICの税・資本範囲とは異なる。資本分母が非正ならNaN。[I:169–200] | Rは流動資産・流動負債やEBIT等をaliasするが、このROCの演算は定義していない。運転資本に現金・有利子流動負債を含むか、期末/平均か、PPEの範囲・ゼロ/負EBITの扱いは実装未確認。ROICへの代用不可。 |
| EV | Rのenterprise_value引数は「価格×price_sharesの結果＋total_debt−cash_and_equivalents」。net_debtも負債−現金。[R:157–165] | price_sharesは未読のcanonicalからimport。少数株主持分・優先株・リース負債・非事業資産等の別調整をこの式へ勝手に加えない。この引数と、動的配線が別途出す可能性のある同名列を同一実装と断定しない。税はこの式には入らない。 |
| EY／EV倍率 | Greenblatt EYはEBIT/EV、EV非正ならNaNという文書。[I:174,191–200] 通常earnings_yieldは赤字の符号を保持する説明もあるため、同名風の指標を混ぜない。[I:677–681] | RのEV/EBIT用guardはEBIT>0、EV/EBITDA用は営業利益＋D&A>0だけを検査する。[R:55–67,154–155,196–201] EY本体・EV/EBITの依存関数自体は未読。EV/EBITとEYを無条件に逆数扱いしない。 |
| 期間・通貨・株数 | 年比較・平均は300–430日前の期。TTMは単独四半期4つ・期末間隔等の条件があり、YTDを勝手に差分化しない。価格は最新期のみ、報告通貨へ換算、EPSは加重平均株数、時価総額は期末株数を基本に代替規則がある。[I:602–632,668–704] | RはDataFrameの列を渡し平均・株数選択をimport helperへ委ねる。暦、初年度、価格の対応・FX・分割補正はここで実装されていない。[R:26,70–71,123–135,157–165] 文書がいう最新行は公表時点・保存時点のPIT適合を証明しない。 |

R:170–193はFinanceToolkitのget_関数をreflectionで拾い、required引数が解決すれば呼び、例外ならその列をskipする構造。実際の関数・依存versionまで未取得のため、このファイルの存在だけで全ratioの計算式が閉じたとは言えない。canonical DataFrameの多数の列はbuild_inputs内で無条件に参照される。列そのものの欠落を自動でNaN列へ補うコードではなく、値の欠損とschemaの欠落を区別する。

## 欠損・非有限・負値・ゼロ

- 文書は欠損伝播とsnapshotでの±∞排除を説明する。[I:1–6,677–681] 局所R._guardは指定された分母inputについて「>0である位置だけresultを残す」だけで、一般のisfinite検査やresultの∞除去をしない。[R:196–201] 非掲載columnはこのguardではそのまま。したがって全pipelineの非有限安全性を今回のfileだけで認定できない。
- 指定guardでは分母のゼロ・負値・NaNは保持条件を満たさない。一方、正の∞は>0だけでは排除されず、result自体の非有限も別処理が必要。除外処理が他moduleにあるかは未確認で、ただちに最終snapshotのバグと断定しない。
- ROICの税引前利益0、赤字の税便益・一時税額、ROCのEBIT0/負値、EV0/負値の扱いは、文書の個別説明と未読本体を分ける。欠損を0、赤字を黒字、∞を非常に高い正常値へ置き換える採用はしない。

## このfileだけで閉じる最小計算単位

**入力が既に定義・期間・通貨・単位まで整合済みで、price_sharesの返す期末相当株数Sも外部で確定している**という条件なら、R:157–165から、価格P・負債D・現金Cについて時価総額P×S、純負債D−C、EV=P×S+D−Cという算術単位は読み取れる。EPSは利益/加重平均株数で、Sとは別。これは欠損・非有限の全guardや日本株への適用を含む完成計算器ではない。average/price_shares/FinanceToolkitの未読実装まで再現した意味でもない。

独立確認用の**式の小例案**として、同通貨・同単位・同時点の架空P=2、S=3、D=4、C=1でEVを2×3+4−1と手計算して比べることはできる。ROICとROCなら同じ架空EBITを用い、税後分子と税前分子、平均資本と期末有形資本を別に置き、互いに一致するはずとはしない。実行・評価値の生成はしておらず、本番入力や既定値ではない。

## 日本株公表原典へのbindingで残るもの

D:102–109は、keyless運用方針を理由にEDINET/OpenDARTを削除し、JP/KR財務はYahooのscraped tierだけに依存すると記載する。したがってREADMEの世界universe宣伝は、日本の開示原典まで追える財務coverageの証拠ではない。これはmaintainer自身の記載の確認で、Yahooの現状・EDINETの公式利用条件や到達性を今回独立に調べた結果ではない。

D:14,29–38,84–92はYahooの非公式取得・再配布制限とassumed-risk tierを明示する。MITはソフトウェアの条件でありproviderデータの許諾を上書きしない。D記載の他providerの無料・公開・license評価も、今回その公式規約を再検証した意味ではない。文書中のアクセス/取得コマンドは実行していない。

必要なのは、既存の日本株原典ごとに、会社・連結/単体・JGAAP/IFRS・対象年/累計/単Q・通貨/倍率単位、EBITの会社定義と営業利益との差、税金費用/税前利益の主体・一時性、負債の範囲、現金、純資産と非支配持分、期首期末のPPE・資本、株式分母/分割をcanonical fieldへ対応させる根拠。さらに価格観測時点、原典公表精度、初回保存/known-by、後日訂正、評価時点の利用可能性を別に固定する。今回そこへ数値をbindingしておらず、公開データだけでの再現性・PIT妥当性・金融採用は未確認。

## 未取得のliteral候補を記録して停止

[next-literal-candidates.json](next-literal-candidates.json)は、前回の固定treeから次の最大3候補だけを保存した。追加GET0。

| path | 固定Git blob SHA | 必要性／未確認 |
|---|---|---|
| src/crible/compute/extras.py | 5e17b2a61f4f0b753ddea73a91e6a26a321d8ea9 | R:32–54のguard参照名とtreeに存在。repo独自ROIC/ROC/EY本体を探す優先候補だが、本体がここにあるとは未確認。 |
| src/crible/compute/canonical.py | 2173be43df1603a69077ad8fb6d913074b4f1128 | R:26の実import先。平均・年度境界・株数選択は今回の資本/EV解釈に不可欠。 |
| src/crible/compute/snapshot.py | fc248fd4fb9f4875212b39c5ef031db1a1865236 | I:677–681がいうsnapshotの非有限除去と実際の指標組立/import経路の候補。固定tree由来だがfile名だけでcleanupを認定しない。 |

ROIC本体と非有限の最終除去を優先し、TTMやFinanceToolkit一般ratioへは広げない。FinanceToolkitとpandasのimportも残るが、version/URLを推測して取得しない。今回は明確な定義差・public原典binding不足・未読計算箇所までを特定して終了する。ライブラリ導入や著者方式としての採用は提案していない。

## 保存と限界

[guard.json](guard.json)、01–03 capture、raw/、[acquisition-results.json](acquisition-results.json)、[validation.json](validation.json)にliteral選択・hold-v8/既存robots404・HTTP entity完了時計・SHA/byte/Git blob再計算を保存。新GET3、robots再GET0、retry/redirect/別path/他host/依存provider取得0。英語の生成逐語引用は新規0words、前回21wordsと累計21wordsで90未満。原資料copyは生成引用ではなく保存source。rawはrequests response entityでwire bytesとは言わない。

元MIT本文と他既存fileのSHAは保持。新成果物以外の編集、DBアクセス、共有docs編集、質問/外部送信、実装変更は0。定義透明性の確認を、Greenblatt本人方式との同一性・実データPIT正しさ・予測精度・投資成績・金融採用へ昇格しない。
