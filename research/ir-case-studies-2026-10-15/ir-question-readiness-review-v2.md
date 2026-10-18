# IR質問の準備状況 v2：保存済み8社の限定レビュー

公開資料で答えた問いを除く段階の整理であり、投資先・質問の順位付けや送信判断ではない。7社は窓口台帳内の研究、千葉銀行8331は窓口未確認の金融モデル研究として別区分とする。

作成UTC：`2026-10-15T05:30:57.376285+00:00`。旧[JSON](ir-question-readiness-review.json)と[Markdown](ir-question-readiness-review.md)は変更せず、旧4社の限定結論を参照継承した。1332の後続CF点検、1379の正式資料/公表5値/初期分類、5480の同一原典売上factと取得保留、1375の最終取得保留、8331の金融入力不足を反映した。

[日本株の仮説とIR質問スキル](../../.agents/skills/jp-equity-ir/SKILL.md)の公開情報先行と、[既存の判断フロー](../../docs/ir-decision-flow.md)・[方針](../../docs/decision-policy.md)に沿う。会社別分類はプロジェクトの適応であり、上流が当該企業や数値条件を推奨したという意味ではない。

新GET・DBアクセス/変更・旧research/productionの編集・質問登録は行っていない。actual-intake等は保存された実行記録を読み、現在DBの状態を独立に認定したものではない。

| 会社 | 保存公開根拠の現在地 | 実際の採用canonical path |
|---|---|---|
| インターネットイニシアティブ（IIJ） 3774 | CAPEX/リースの一般定義は公開解決。残る現金bridgeは未立証。 | `null` |
| パイオラックス 5988 | 一時費用と減損の包含/期間は未確認、配当の対象期/期限は公開解決。 | `null` |
| ニッスイ 1332 | 8公開解決、D&A/設備投資/WC/魚評価/期間・範囲の5bridgeは未確認。 | `null` |
| VRAIN Solution 135A | 継続売上式/累計単価は公開解決、90%指標は別定義。9公表値の対応は研究用。 | `null` |
| ホクト 1379 | 正式Q1/説明資料、5公表値と5source分類。季節性/DOE算式等は未確認。 | `null` |
| 日本冶金工業 5480 | 同一メッセージの通期売上/営業利益。正式比較資料の取得は503保留。 | `null` |
| ユキグニファクトリー 1375 | 事業/FAQはあるが財務本文0件、最終feed503で取得保留。 | `null` |
| 千葉銀行 8331 | 台帳外の金融研究。1期配当予想は構造化、DDM/資本の必要入力は未設定。 | `null` |

## モデル経路の読み方

以下の「概念上の経路」は、定義をどこに結び得るかという研究説明である。`eps_jpy`、`fcf_jpy`、DDMの入力名が出ても、シナリオと会社仮説へ採用されたtarget pathではない。8社とも `actual_canonical_model_path:null`、金融入力の検証と意味レビューは未完了のまま。

ニッスイの返済要因は**長期買掛金**であり長期借入金ではない。ホクトの**利益の季節性は限定資料では未確認**。同社の年間62円は2027/3期会社予想、DOE3.5%は2029/3期の会社目標で、投資閾値や将来配当列とは別である。

## インターネットイニシアティブ（IIJ）（3774）

v1の限定結論を参照継承。現Web・実DBの再確認や過去草案の変更はしていない。 [ir-question-readiness-review.json /companies/0](ir-question-readiness-review.json)

### 公開で既に答えた問い

- CAPEXの除外定義とIFRS16のCF分類とは何か：追加公開資料・FAQで回答済み [ir-question-readiness-review.json /companies/0/not_questions_now/0](ir-question-readiness-review.json)
- 運用フェーズは構築より高粗利か：公開Q&Aに一般的説明がある。将来の個別利益率の保証へ広げない [ir-question-readiness-review.json /companies/0/not_questions_now/1](ir-question-readiness-review.json)

### 次に必要な公開根拠

- Q1の管理CAPEX・法定有形/無形取得支出・助成金・リースを、各原文の対象期と連結範囲を付けて対照表にする。既に確認した一般定義を新たな未解決点に戻さない。 対象Q1資料と追加資料は保存済み、完全な対応表は保存レビューの範囲で未発見 [ir-question-readiness-review.json /companies/0/next_public_checks/0](ir-question-readiness-review.json)、[3774/additional-public-review.json](3774/additional-public-review.json)
- 前年度有報の現金CAPEX・非資金リース・単体助成金収入を、当期Q1の連結CFと混ぜていないか点検する。同額という理由だけで同じ経済事象・認識時期としない。 FY2025有報の連結/単体注記は保存済み [ir-question-readiness-review.json /companies/0/next_public_checks/1](ir-question-readiness-review.json)、[3774/additional-public-review.json](3774/additional-public-review.json)
- 次の実公表資料で同一定義のCAPEX/CFとSI構築・運用保守構成を比較する。保存caseの発表予定を公表済み資料へ読み替えない。 次の資料が実際に公表されたことは本レビューでは未確認 [ir-question-readiness-review.json /companies/0/next_public_checks/2](ir-question-readiness-review.json)

### IRに残り得る定義

- 残る当期Q1の管理指標と法定現金取得支出の公表項目対応 条件：公開対照を終え、実際に利用するモデルのどのCF分類が変わるかを先に示せた場合にだけ再点検する。 既存閉鎖済み草案の再起票や、質問の現在送信適格性を認定しない。 [ir-question-readiness-review.json /companies/0/conditional_ir_definition_room/0](ir-question-readiness-review.json)

### モデルへの採用がまだない理由

概念上の経路：公表対応を確認 → CF分類・重複調整の誤りが実際にあるか点検 → 一貫したリース/助成金処理のCF入力へ結合 実際の採用canonical pathは `null`。

- 採用する評価モデルと実際の入力path
- 質問前後で異なる入力と、その根拠・反証条件
- 同じ評価時点・市場価格・保有状態・採用方針での回答別比較
- 将来CF・割引率・再投資の根拠

[ir-question-readiness-review.json /companies/0/model_change_route](ir-question-readiness-review.json)

### 今質問登録に進まない理由

- 公開回答で解決済みの問いを重複登録しない。
- 残る定義が、採用済みモデルのどの入力をどう変えるかは未立証。
- 同じ時点の価格・保有履歴・採用方針に基づく回答A/B/曖昧・無回答の比較が未設定。
- 既存CAPEX草案のclosed_no_send_insufficient_incremental_valueは過去履歴として維持し、再起票しない。

反証/変更なし：公開対応から既存モデルの集計が正しいと分かる場合、分類修正も質問の寄与も不要となる。未解決という事実だけで価値があるとはしない。

## パイオラックス（5988）

v1の限定結論を参照継承。現Web・実DBの再確認や過去草案の変更はしていない。 [ir-question-readiness-review.json /companies/1](ir-question-readiness-review.json)

### 公開で既に答えた問い

- 一時費用と呼んでいるか、337百万円は何の損失か：公開資料で回答済み [ir-question-readiness-review.json /companies/1/not_questions_now/0](ir-question-readiness-review.json)
- 27.45円EPS/92円DPSの対象年度、年間92円以上/配当性向100%方針の期限：2027年3月期までという公表説明がある [ir-question-readiness-review.json /companies/1/not_questions_now/1](ir-question-readiness-review.json)

### 次に必要な公開根拠

- まず保存済み有報・中計・3Qの同じ費用項目を期間と会計区分で並べる。通期短信/2Q説明会や公開Q&Aが別の許可された取得枠で得られたら、残る対応関係が公開で説明されているか確認する。本レビューは再GETしない。 通期短信/2Q説明会は503応答のみ。追加3Q本文と有報/中計は保存済み [ir-question-readiness-review.json /companies/1/next_public_checks/0](ir-question-readiness-review.json)、[5988/followup-public-review/review.json](5988/followup-public-review/review.json)
- 約6億円の集計科目・子会社・期間、減損337百万円の区分、12月決算子会社と連結調整を分ける。3Qの重要事項なしをゼロや特定四半期の認識へ変換しない。 中計15頁、有報PDF65/70/79頁、追加3Q7/11頁は保存済み [ir-question-readiness-review.json /companies/1/next_public_checks/1](ir-question-readiness-review.json)、[5988/followup-public-review/review.json](5988/followup-public-review/review.json)

### IRに残り得る定義

- 約6億円と減損337百万円の集計範囲・包含・対象期間の公開説明への橋渡し 条件：未取得説明資料/Q&Aの確認を進め、どの採用済み利益/CF入力の二重計上を変えるか先に説明できた場合。 約6億円を正確な600百万円へ自動変換せず、減損を営業利益へ足し戻さず、翌期費用消失も仮定しない。 [ir-question-readiness-review.json /companies/1/conditional_ir_definition_room/0](ir-question-readiness-review.json)

### モデルへの採用がまだない理由

概念上の経路：公表集計範囲と認識期間を確認 → 過年度営業利益/特別損失/純利益の橋渡しを整理 → 税・非支配・株数・将来事業前提が別途そろった場合にだけモデルへの採否を点検 実際の採用canonical pathは `null`。

- 採用する評価モデルと実際の入力path
- 質問前後で異なる入力と、その根拠・反証条件
- 同じ評価時点・市場価格・保有状態・採用方針での回答別比較
- 正常化対象と税/非支配持分/株数・再投資の対応

[ir-question-readiness-review.json /companies/1/model_change_route](ir-question-readiness-review.json)

### 今質問登録に進まない理由

- 公開回答で解決済みの問いを重複登録しない。
- 残る定義が、採用済みモデルのどの入力をどう変えるかは未立証。
- 同じ時点の価格・保有履歴・採用方針に基づく回答A/B/曖昧・無回答の比較が未設定。
- 既存中国費用bridgeはresearch-only草案で、現モデル値と各valuation_changeはnull。未取得通期/説明会/Q&Aを公開非開示としない。

反証/変更なし：公表対応で重複や期間差が既に除かれていると判明すれば修正不要。費用の名称が一時的でも、将来費用が消える根拠とは別である。

## ニッスイ（1332）

v1の対象期・連結/部分指標・予定と実施の区別を継承し、CF定義の不足は後続8公開解決/5bridgeへ更新。旧版は不変。 [ir-question-readiness-review.json /companies/2](ir-question-readiness-review.json)

### 公開で既に答えた問い

- この四半期に正式な四半期連結CF計算書を作成しているか。 → 作成していないと正式注記に明記。 [1332/cashflow-scope-review/review.json /resolved_without_ir/0](1332/cashflow-scope-review/review.json)
- 正式CF計算書がないので営業/投資/財務CFの公表情報は一切ないのか。 → 補足9頁に各CFとFCFの当期値がある。正式計算書と区別して引用する。 [1332/cashflow-scope-review/review.json /resolved_without_ir/1](1332/cashflow-scope-review/review.json)
- 補足のD&Aはのれんを含むか、正式注記のD&Aはのれんと別か。 → 補足はのれん込み、正式注記はのれんを除く無形償却を含むD&Aと、のれん償却額を別行表示。金額bridgeが解決済みという意味ではない。 [1332/cashflow-scope-review/review.json /resolved_without_ir/2](1332/cashflow-scope-review/review.json)
- 会社は営業CF/運転資本悪化の要因を何も説明していないのか。 → 長期買掛金返済と北米の売掛金増加を公表。要因の存在を再質問する必要はないが、全項目/金額内訳は未解決。 [1332/cashflow-scope-review/review.json /resolved_without_ir/3](1332/cashflow-scope-review/review.json)
- 補足9頁の返済要因は長期借入金返済と書かれているか。 → 原文は長期買掛金返済。長期借入金増減は財務CFの別行。 [1332/cashflow-scope-review/review.json /resolved_without_ir/4](1332/cashflow-scope-review/review.json)
- 設備投資額の表示ラベルと投資増加の大まかな説明は何か。 → 固定資産取得額という表示と、国内外工場投資による増加という説明がある。現金支出への一致は未解決。 [1332/cashflow-scope-review/review.json /resolved_without_ir/5](1332/cashflow-scope-review/review.json)
- 27頁の在池魚/未実現利益の意味と比較主体は何か。 → 注記で想定利益/在庫の未実現利益調整を説明し、前年SAと当年SA・Yadran計を明示。CF調整の定義とは異なる。 [1332/cashflow-scope-review/review.json /resolved_without_ir/6](1332/cashflow-scope-review/review.json)
- 海外食品工場が回収段階かという会社の見解を聞く必要があるか。 → 北米/欧州について公開Q&Aで既に説明。会社説明の存在自体を聞き直す必要はない。現金回収の確認済み事実にはしない。 [1332/cashflow-scope-review/review.json /resolved_without_ir/7](1332/cashflow-scope-review/review.json)

### 次に必要な公開根拠

- 補足D&A/のれんの原数値・丸めと正式注記の集計/定義のbridge 公開根拠の定義/区分対応は保存限定資料では未確認。不存在の判定ではない。 次の確認候補（所在/記載未確認）：補足CFの算定/丸め注記と、同一範囲・期間の償却/のれん開示。正式CFを作成する中間/年次資料の注記も比較候補とし、Q1との金額一致を前提にしない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/0](1332/cashflow-scope-review/review.json)
- 設備投資額（固定資産取得額）と資産取得に係る現金支出/投資CF全体とのbridge 公開根拠の定義/区分対応は保存限定資料では未確認。不存在の判定ではない。 次の確認候補（所在/記載未確認）：固定資産取得額の定義、資産取得に係る現金支出、リース/非現金取引・取得債務・他投資CF項目を分けた正式CF/注記と補足説明。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/1](1332/cashflow-scope-review/review.json)
- 運転資本の構成、長期買掛金返済と売掛金増加の金額/会計上の区分 公開根拠の定義/区分対応は保存限定資料では未確認。不存在の判定ではない。 次の確認候補（所在/記載未確認）：運転資本の構成/増減内訳、企業結合と取得関連長期買掛金の性質・区分、売掛金や借入金/CPを分ける公表CF/注記。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/2](1332/cashflow-scope-review/review.json)
- 在池魚評価/未実現利益の連結営業CF調整への対応 公開根拠の定義/区分対応は保存限定資料では未確認。不存在の判定ではない。 次の確認候補（所在/記載未確認）：在池魚/未実現利益の会計方針・連結調整と、正式営業CFの非現金調整の対応が分かる公表注記/説明資料。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/3](1332/cashflow-scope-review/review.json)
- 同四半期の表示と子会社集計期間、比較範囲、取得/換算を含む指標単位の整合 公開根拠の定義/区分対応は保存限定資料では未確認。不存在の判定ではない。 次の確認候補（所在/記載未確認）：海外子会社の決算/取込期間、取得・連結開始日、比較会社範囲、換算/連結調整を明記する正式注記。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/4](1332/cashflow-scope-review/review.json)

### IRに残り得る定義

- 補足D&A/のれんの原数値・丸めと正式注記の集計/定義のbridge 条件：公開資料の対応を先に確認し、それでも残り、採用する入力の分類差と反証/変更なし条件を説明できた場合のみ。 既公表指標の定義・集計・参照箇所の説明に限定。非公表将来CFや内訳の保証を求める段階ではない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/0](1332/cashflow-scope-review/review.json)
- 設備投資額（固定資産取得額）と資産取得に係る現金支出/投資CF全体とのbridge 条件：公開資料の対応を先に確認し、それでも残り、採用する入力の分類差と反証/変更なし条件を説明できた場合のみ。 既公表指標の定義・集計・参照箇所の説明に限定。非公表将来CFや内訳の保証を求める段階ではない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/1](1332/cashflow-scope-review/review.json)
- 運転資本の構成、長期買掛金返済と売掛金増加の金額/会計上の区分 条件：公開資料の対応を先に確認し、それでも残り、採用する入力の分類差と反証/変更なし条件を説明できた場合のみ。 既公表指標の定義・集計・参照箇所の説明に限定。非公表将来CFや内訳の保証を求める段階ではない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/2](1332/cashflow-scope-review/review.json)
- 在池魚評価/未実現利益の連結営業CF調整への対応 条件：公開資料の対応を先に確認し、それでも残り、採用する入力の分類差と反証/変更なし条件を説明できた場合のみ。 既公表指標の定義・集計・参照箇所の説明に限定。非公表将来CFや内訳の保証を求める段階ではない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/3](1332/cashflow-scope-review/review.json)
- 同四半期の表示と子会社集計期間、比較範囲、取得/換算を含む指標単位の整合 条件：公開資料の対応を先に確認し、それでも残り、採用する入力の分類差と反証/変更なし条件を説明できた場合のみ。 既公表指標の定義・集計・参照箇所の説明に限定。非公表将来CFや内訳の保証を求める段階ではない。 [1332/cashflow-scope-review/review.json /remaining_public_research_first/4](1332/cashflow-scope-review/review.json)

### モデルへの採用がまだない理由

概念上の経路：公表補足のD&A/設備投資/運転資本/魚評価と正式注記の区分・期間を照合する。 → 現金支出と評価/非現金/買収・連結範囲差を分け、将来アンレバードCFに必要な別根拠を点検する。 実際の採用canonical pathは `null`。

- 含有範囲の定義は解決したが、公表金額の完全なbridgeは未確認。
- 設備投資額（固定資産取得額）を現金支出や純再投資へ置換できない。
- 南米取得関連の長期買掛金返済と売掛金増加は公表説明だが、運転資本全構成・金額内訳はない。
- 在池魚評価から連結CF調整への対応、比較会社/期間、全サイクル・税・ROC・将来再投資が未確認。
- 採用されたvaluationのcanonical path、数値仮説、回答別の変更が未設定。

[1332/cashflow-scope-review/review.json](1332/cashflow-scope-review/review.json)

### 今質問登録に進まない理由

- 8つの既公開回答は質問対象から除く。
- 5つのbridgeは公開照合未了であり、公開情報全体にないと判定していない。
- 補足CFの定義確認から変更する実モデルpathと事前分岐が未設定。

反証/変更なし：公開注記でbridgeが解ければ同じIR照会は不要。解消した定義だけで将来CFや正常利益は変更しない。

## VRAIN Solution（135A）

v1の限定結論を参照継承。現Web・実DBの再確認や過去草案の変更はしていない。 [ir-question-readiness-review.json /companies/3](ir-question-readiness-review.json)

### 公開で既に答えた問い

- 最新短信の所在、正式な対象期/会計基準/範囲、CF本文の有無、単一セグメントか：library-followupの本文で回答済み。初期READMEの不足を最新状態として再使用しない [ir-question-readiness-review.json /companies/3/not_questions_now/0](ir-question-readiness-review.json)
- 会社通期予想は4月発表から変更されたか：短信に変更なしとの公開説明がある [ir-question-readiness-review.json /companies/3/not_questions_now/1](ir-question-readiness-review.json)
- 何を提供する会社か、カレンダーの一般的な月予定：初期公式ページで説明済み。月予定から次回具体日を捏造しない [ir-question-readiness-review.json /companies/3/not_questions_now/2](ir-question-readiness-review.json)
- 継続顧客売上高の算式、単価は四半期単独か/初回と追加導入で決まるか：追加説明資料5/6頁とFAQで公開説明を確認済み [ir-question-readiness-review.json /companies/3/not_questions_now/4](ir-question-readiness-review.json)
- 保守ストック収入・一般的納品期間・営業採用から初売上までの会社説明：一般FAQの説明がある。日付/母集団不明の平均を全案件・将来入力へ適用しない [ir-question-readiness-review.json /companies/3/not_questions_now/5](ir-question-readiness-review.json)
- 1Qの継続顧客売上比率や製造業顧客リスクに会社が説明しているか：7月の会社作成Q&Aにある。ただし中間期の最新回答・最新予測ではない [ir-question-readiness-review.json /companies/3/not_questions_now/6](ir-question-readiness-review.json)
- 中間期の案件構成/粗利率・採用/拠点費用変動の会社説明があるか：追加説明資料7頁に説明がある。一過性や持続性はまだ自動認定しない [ir-question-readiness-review.json /companies/3/not_questions_now/7](ir-question-readiness-review.json)

### 次に必要な公開根拠

- 保存された継続顧客売上高の式、受注ベースの累計顧客数、年度内累計単価、案件構成/粗利率・採用/拠点費用の説明を、対象時点・期間・集計単位付きで並べる。7月の会社想定と10月実績/会社予想を分ける。 中間期説明資料49頁・FAQ・1Q会社作成Q&Aは追加保存済み [ir-question-readiness-review.json /companies/3/next_public_checks/0](ir-question-readiness-review.json)、[135A/presentation-followup/sources.json](135A/presentation-followup/sources.json)
- 半期/通期・実績/会社予想・基本/希薄化後EPS・株数・非連結範囲を対照する。中間CFの運転資本/有形取得と営業費用の説明を区別する。 中間P/L・CF・株数の本文と会社予想表は保存済み [ir-question-readiness-review.json /companies/3/next_public_checks/1](ir-question-readiness-review.json)、[135A/library-followup/sources.json](135A/library-followup/sources.json)
- 追加資料の継続顧客売上高とホームページのDXコンサル90%を分け、90%の分子・分母・期間・対象サービス/顧客コホートが明示されているか保存本文で照合する。画像/全公開資料の確認済みとはしない。 初期の90%会社表示、追加の別指標の式/単価定義は保存済み。90%そのものの定義は追加レビューでも未確定。 [ir-question-readiness-review.json /companies/3/next_public_checks/2](ir-question-readiness-review.json)、[135A/sources.json](135A/sources.json)

### IRに残り得る定義

- DXコンサル・リピート率90%以上の分子・分母・期間・対象顧客/サービスと、継続顧客売上高指標との関係 条件：取得済み追加資料とFAQを照合しても未解決で、実際にモデルへ使う売上分類/KPIへの変更経路を特定できた場合。 90%をARR/継続売上率へ変換せず、新規受注額・個別顧客単価・未公表契約・将来成長率を求めない。 [ir-question-readiness-review.json /companies/3/conditional_ir_definition_room/0](ir-question-readiness-review.json)

### モデルへの採用がまだない理由

概念上の経路：KPI・売上認識・サービス範囲を確認 → 反復性と案件納品の売上分類を整理 → 原価/固定費・税/株数・再投資と履歴がそろった場合に採用モデルを点検 実際の採用canonical pathは `null`。

- 採用する評価モデルと実際の入力path
- 質問前後で異なる入力と、その根拠・反証条件
- 同じ評価時点・市場価格・保有状態・採用方針での回答別比較
- 複数期間の事業/収益/再投資・資金調達履歴、予想株数/希薄化の前提
- 9公表値の研究用対応表はあるがtarget_path/scenarioはnull。通期会社予想EPS94.85等を採用済み将来入力と扱わない。

[ir-question-readiness-review.json /companies/3/model_change_route](ir-question-readiness-review.json)、[135A/model-input-mapping.json](135A/model-input-mapping.json)

### 今質問登録に進まない理由

- 公開回答で解決済みの問いを重複登録しない。
- 残る定義が、採用済みモデルのどの入力をどう変えるかは未立証。
- 同じ時点の価格・保有履歴・採用方針に基づく回答A/B/曖昧・無回答の比較が未設定。

反証/変更なし：公開された継続顧客売上高の式・単価期間・FAQのストック収入説明により、同じ定義質問は除く。未確定の90%が売上継続性を意味しなければ、将来売上の根拠に使わない。追加で定義が解けても採用済み評価入力の変更はまだ立証されていない。

## ホクト（1379）

保存実行記録は初期5sourceを索引2・正式短信1・説明資料1・予定1に分類したもの。抽出5factの派生bundleは研究ファイルであり、採用済みモデルではない。予定表の年度表記不整合は未修正。 [1379/public-definition-review/review.json](1379/public-definition-review/review.json)、[1379/disclosed-facts/README.md](1379/disclosed-facts/README.md)、[1379/actual-intake.json](1379/actual-intake.json)、[1379/review.json](1379/review.json)、[1379/selection.json](1379/selection.json)

### 公開で既に答えた問い

- 正式Q1は日本基準・連結、2026-04-01〜06-30。Q1基本EPS14.44円・営業利益418百万円は実績、通期EPS167.22円・営業利益7,260百万円・年間配当62.00円は会社予想として構造化済み。 [1379/disclosed-facts/README.md](1379/disclosed-facts/README.md)、[1379/disclosed-facts/meaning-review.json](1379/disclosed-facts/meaning-review.json)
- 年間62円（中間10/期末52）は2027/3期会社予想、DOE3.5%は2029/3期の目標。双方の対象期・概念は公開で説明されている。 [1379/public-definition-review/review.json /findings/3](1379/public-definition-review/review.json)
- Q1連結CF計算書は作成していない。減価償却費の説明には無形固定資産償却費を含む。 [1379/public-definition-review/review.json /findings/4](1379/public-definition-review/review.json)
- 価格・需要予測/生産調整・加工品の受注回復・化成品の仕入コスト/価格改定・利益bridgeとセグメント調整には公開説明がある。市場価格、自社単価、生産量は別指標。 [1379/public-definition-review/review.json /findings/1](1379/public-definition-review/review.json)、[1379/public-definition-review/review.json /findings/2](1379/public-definition-review/review.json)

### 次に必要な公開根拠

- Previously linked official IR archive/financial history: dated annual or quarterly narrative about seasonality and comparable periods; none fetched in this task. 必要な公開参照先の候補。今回の資料範囲では未確認、追加取得はしていない。 [1379/public-definition-review/review.json /findings/0](1379/public-definition-review/review.json)
- Existing official IR/financial-history pointers: metric-definition footnotes, annual accounting/revenue-recognition note and segment definitions. Do not request undisclosed current orders. 必要な公開参照先の候補。今回の資料範囲では未確認、追加取得はしていない。 [1379/public-definition-review/review.json /findings/1](1379/public-definition-review/review.json)
- Existing archive links: official annual cost/inventory/accounting notes or explanatory bridge definitions; no added GET. 必要な公開参照先の候補。今回の資料範囲では未確認、追加取得はしていない。 [1379/public-definition-review/review.json /findings/2](1379/public-definition-review/review.json)
- 再利用FAQが実際に案内する配当金推移・株主還元資料でDOEの計算式/自己資本範囲を確認する。未取得。 必要な公開参照先の候補。今回の資料範囲では未確認、追加取得はしていない。 [1379/public-definition-review/review.json /findings/3](1379/public-definition-review/review.json)
- Official annual or interim statement where consolidatedCF is actually prepared, with matching period/unit and capex/working-capital definitions; no new GET here. 必要な公開参照先の候補。今回の資料範囲では未確認、追加取得はしていない。 [1379/public-definition-review/review.json /findings/4](1379/public-definition-review/review.json)

### IRに残り得る定義

- 自社平均販売単価の分母・加重方法・製品ミックスと、市場参考価格/生産数量との相違。 条件：公開注記を先に確認し、残る定義が採用入力を変えると示せた場合のみ。 [1379/public-definition-review/review.json /findings/1](1379/public-definition-review/review.json)
- 費用bridgeの項目範囲、DOEの分子/分母・連結/単体・期末/平均の定義と参照資料。 条件：公表参照先の確認と、会計範囲/採用モデル上の必要性の特定が先。将来配当や増益の保証を求めない。 [1379/public-definition-review/review.json /findings/2](1379/public-definition-review/review.json)、[1379/public-definition-review/review.json /findings/3](1379/public-definition-review/review.json)

### モデルへの採用がまだない理由

概念上の経路：正式実績/会社予想と価格・数量・原価・事業別範囲を分けて整理する。 → 定義・期間・再投資・資金条件を確認した後に、モデル適合と入力採否を別に点検する。 実際の採用canonical pathは `null`。

- 5factの抽出・初期分類は数値の金融的妥当性や将来予想への採用ではない。
- 利益の季節性は限定資料で未確認。月次卸売価格の変動を自社利益の季節性や冬季改善の保証へ変換しない。
- 自社平均販売単価の分母/加重/ミックス、費用区分/価格転嫁の遅れ、CF・再投資と全サイクルが未確認。
- DOEの算式/自己資本範囲は未確認。目標からDPS、DDM金利/成長率、投資閾値を逆算しない。
- 採用モデル/target path、将来各期入力と数値前提、採用policy/相場を使う事前比較が未設定。

[1379/public-definition-review/review.json](1379/public-definition-review/review.json)、[1379/disclosed-facts/README.md](1379/disclosed-facts/README.md)、[1379/actual-intake.json](1379/actual-intake.json)

### 今質問登録に進まない理由

- 公表済みの当期配当予想/DOE目標の時点やQ1CF未作成を再質問しない。
- 季節性・単価・DOE等は公開確認を残しており、全Webで解けないとの判定ではない。
- 現在モデルpath/判断への影響と事前の回答分岐がnullで、定義の不足だけでは質問登録理由にならない。

反証/変更なし：公開資料で定義や季節性が解ければ照会は削除する。会社説明の存在や5factの一致だけでは予測/採用モデルは変更しない。

## 日本冶金工業（5480）

annual-input-followupの3件目feed HTTP503で終了。未使用枠・別host・診断・retryは継続していない。 [5480/annual-input-followup/review.json](5480/annual-input-followup/review.json)、[5480/revenue-disclosed-facts/README.md](5480/revenue-disclosed-facts/README.md)、[5480/disclosed-facts/README.md](5480/disclosed-facts/README.md)

### 公開で既に答えた問い

- 保存メッセージの売上150,866百万円・営業利益10,973百万円は第144期連結通期実績という本文対応。対象期や公表金額を聞き直す必要はない。 [5480/annual-input-followup/review.json](5480/annual-input-followup/review.json)、[5480/revenue-disclosed-facts/README.md](5480/revenue-disclosed-facts/README.md)、[5480/disclosed-facts/README.md](5480/disclosed-facts/README.md)

### 次に必要な公開根拠

- 正式年次資料の表紙/公表日、明示比較年度表、会計基準・連結範囲の継続性、実績/会社予想と単位を確認できる本文。 取得保留。必要資料の記録であり、再取得開始や接続診断の指示ではない。 [5480/annual-input-followup/review.json /remaining_needs](5480/annual-input-followup/review.json)
- 比較可能な年次利益/売上・現在規模・全サイクルを含む根拠、税・再投資・資本収益・資金調達の資料。固定年数を置かない。 保存1年要約では不足。全サイクル/正常利益は未確認。 [5480/annual-input-followup/review.json](5480/annual-input-followup/review.json)、[5480/revenue-disclosed-facts/README.md](5480/revenue-disclosed-facts/README.md)、[5480/disclosed-facts/README.md](5480/disclosed-facts/README.md)

### IRに残り得る定義

- 正式資料を得てからも残る場合の、営業利益の集計範囲・比較可能性・公表再投資指標の定義と参照箇所。 条件：現段階は資料取得不足。公開資料への対応と具体的な採用入力差の特定が先で、完成したIR質問ではない。 [5480/annual-input-followup/review.json](5480/annual-input-followup/review.json)、[5480/revenue-disclosed-facts/README.md](5480/revenue-disclosed-facts/README.md)、[5480/disclosed-facts/README.md](5480/disclosed-facts/README.md)

### モデルへの採用がまだない理由

概念上の経路：同じ原典の通期売上と営業利益を、正式資料と比較可能な履歴へ結ぶ。 → 規模・利益率・再投資/税/資金条件の整合を点検してから、正常化の採否と将来CFを別に検討する。 実際の採用canonical pathは `null`。

- 2つの派生factは同一メッセージ由来で、独立した裏付け2件ではない。
- 会計基準、正式比較表、最新性と全サイクルが未確認。1期の実績を正常利益へ置換できない。
- 将来再投資・NOPAT/税・ROC/成長/割引率と採用canonical pathは未設定。

[5480/annual-input-followup/review.json](5480/annual-input-followup/review.json)、[5480/revenue-disclosed-facts/README.md](5480/revenue-disclosed-facts/README.md)、[5480/disclosed-facts/README.md](5480/disclosed-facts/README.md)

### 今質問登録に進まない理由

- 対象期/値は既存メッセージで解決済み。
- 取得503を非開示やIR回答拒否、投資不適合の根拠にしない。正式資料の公開確認を終えていない。
- 正常化・採用モデルpath・回答別変更と反証条件が未設定。

反証/変更なし：正式資料で期/会計範囲差が判明すれば一致とみなさず照合し直す。1期の引用再現だけでは正常化・評価・質問価値は確定しない。

## ユキグニファクトリー（1375）

statement-followupはconfig200の後、primary feed503で終了。金融本文0件のまま取得保留。 [1375/review.json](1375/review.json)、[1375/financial-followup/review.json](1375/financial-followup/review.json)、[1375/statement-followup/review.json](1375/statement-followup/review.json)、[1375/actual-intake.json](1375/actual-intake.json)

### 公開で既に答えた問い

- 公式一般FAQの会社名/コード1375、茸・その他食品事業、毎年3月末決算、資料カテゴリー案内は公開で確認済み。 [1375/review.json /verified_public_facts](1375/review.json)
- 決算資料の案内先と一般的な配当基準日等のFAQはある。これらを最新財務本文・支払日・配当額と扱わない。 [1375/review.json /public_answers_do_not_send_questions](1375/review.json)

### 次に必要な公開根拠

- 日付付き公式財務一覧と実際の決算本文・比較期/基準/範囲/単位/実績・会社予想欄が必要。公開決算Q&Aと具体的予定も未取得。 最終feed503で取得保留。未使用枠・代替host/feed・retry・次phaseの実行提案ではない。 [1375/statement-followup/review.json /remaining_needs](1375/statement-followup/review.json)

### IRに残り得る定義

- 具体的な財務指標の定義照会はまだ特定できない。将来正式資料を確認しても残る項目がある場合にだけ再整理する。 条件：一般的な季節性やコスト構造を業種から推測して質問化せず、公開本文と採用入力が先。 [1375/review.json](1375/review.json)、[1375/financial-followup/review.json](1375/financial-followup/review.json)、[1375/statement-followup/review.json](1375/statement-followup/review.json)、[1375/actual-intake.json](1375/actual-intake.json)

### モデルへの採用がまだない理由

概念上の経路：正式財務資料を取得して、事業/利益/再投資/資金と履歴の事実を揃える。 → その後にモデル適合を確認し、採用pathと事前分岐を別に設計する。 実際の採用canonical pathは `null`。

- 現保存範囲の財務本文は0件で、最新期・会計基準・連結範囲と数値の基礎が未確認。
- 一般FAQ、きのこ事業や設立年だけでは通常/循環/赤字成長のrouteは確定しない。
- 採用モデル入力、将来各期CF/利益、反証・価格・方針と回答別変更が未設定。

[1375/review.json](1375/review.json)、[1375/financial-followup/review.json](1375/financial-followup/review.json)、[1375/statement-followup/review.json](1375/statement-followup/review.json)、[1375/actual-intake.json](1375/actual-intake.json)

### 今質問登録に進まない理由

- 公開済みの会社概要/決算月/資料所在を繰り返し聞かない。
- 情報不足の主因は財務本文の未取得で、会社が非開示と判定したわけではない。
- 具体的な定義差と採用model path・回答分岐が特定できず、取得失敗は質問の判断価値を証明しない。

反証/変更なし：正式本文が未取得なので将来財務値も質問価値も判定しない。取得保留のまま欠損を保存する。

## 千葉銀行（8331）

確認済み窓口台帳外の金融モデル研究。窓口・個人受付・沈黙期間は未確認で、7社の窓口対象に混ぜない。

### 公開で既に答えた問い

- 2026年4月〜2029年3月の方針は配当性向40%以上を目安、自己株式取得は機動的に実施。2027/3期年間DPS64.0円・中間32.0円・連結配当性向41.1%は会社予想。 [8331/draft.json /facts](8331/draft.json)、[8331/extraction-notes.md](8331/extraction-notes.md)
- 一般FAQの国際統一基準8%以上という説明と例年の発表月は公表済み。ただし当行の最新CET1/RWA・経営目標や次の具体日を示すものではない。 [8331/draft.json /facts](8331/draft.json)、[8331/README.md](8331/README.md)

### 次に必要な公開根拠

- 既に案内されている公式中計・バーゼル/規制資本開示・最新決算/説明会Q&Aで、同じ期間の普通株主利益、資本分子/RWA、連結/単体、最低水準と経営バッファ、資本配賦・分配制約を確認する。 公開導線は保存済み、本文未取得。今回は取得しない。 [8331/draft.json /questions/1/public_review_required_before_question](8331/draft.json)
- 中間/期末の権利基準日・支払時期・株式単位と、評価日から受け取れる分配の対応を公表決議等で確認する。 元配当表の年度予想だけでは未充足。 [8331/extraction-notes.md](8331/extraction-notes.md)

### IRに残り得る定義

- 公表還元方針と規制必要資本・経営バッファ・事業配賦の定義/連結・単体範囲を結ぶ公開資料名・頁。 条件：未取得の中計/バーゼル/決算/Q&Aを先に読み、なお残り、将来分配制約への具体的な入力変更を示せた場合だけ。 [8331/draft.json /questions/1](8331/draft.json)

### モデルへの採用がまだない理由

概念上の経路：会社年度の配当予想と投資時点からの分配系列を区別する。 → 規制資本留保/配賦と持続可能な株主分配を結び、DDM入力や金融FCFEの必要定義を別に点検する。 実際の採用canonical pathは `null`。

- DDMの予測DPS系列、予測期/安定期の株主資本コスト、n+1 DPS、永久成長率の5入力は未設定。
- 年間DPS64円は評価日から1年後の受取64円を意味せず、年間へ中間32円を加えない。
- 最新の期間対応利益/規制資本/RWA、最低水準と経営バッファ、資本配賦/再投資が不足。一般FAQ8%を実測・目標へ転用できない。
- 株式単位/希薄化、現在相場、採用方針と回答別変更が未設定。

[8331/draft.json](8331/draft.json)、[8331/extraction-notes.md](8331/extraction-notes.md)、[8331/disclosed-facts-normalized.json](8331/disclosed-facts-normalized.json)

### 今質問登録に進まない理由

- 配当性向方針と年度予想DPSは公開回答済み。
- 規制資本・将来DPSの公開確認とモデル準備が未了で、回答による判断差が立証されていない。
- 窓口は未確認で確認済み台帳外。沈黙期間を見つけなかった範囲は、沈黙期間なしや受付許可を意味しない。

反証/変更なし：公開資料で定義が解ければ照会を除く。定義だけの訂正なら将来DPSや採用金利は変更せず、未設定を保持する。

## 今回の更新の限界

5480/1375の「次に必要な公開根拠」は不足の記録であり、取得保留を解除して再試行/診断/別phaseへ進める指示ではない。資料の未取得を非開示・会社の投資不適合・IRの情報価値がある証拠にしない。

同一原典の表/説明文や複数派生factを独立証拠に数えない。公開定義・数値token・単位変換の一致は、将来CF/配当、正常化、株価や送信適格性の検証ではない。数値予測・閾値・確率・主観点数は追加していない。

公開確認で解決すれば照会を除く。なお残る場合も、同じ時点の採用仮説/モデルpath・回答A/B/曖昧/無回答・反証/変更なし・方針/価格を先に固定する必要がある。本レビューではそれらを補完せず、質問登録と投資判断を行っていない。

出典の相対path・JSON pointer・引用IDと、レビュー時の入力SHA/byte数は[JSON版](ir-question-readiness-review-v2.json)に記録した。
