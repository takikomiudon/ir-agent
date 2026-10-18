# 株数単位の候補fact: 最小追加設計

結論は、既存`_UNIT_MULTIPLIERS`にcanonical `shares`への有限mappingを追加すればよい。現normalizerは135Aの`10,256,000株`をUnsupported explicit raw-unit/canonical-unit mappingで拒否する。一方、既存valuation/model_inputsは数値の株数・単位ラベル・原典fieldを扱える。consumer全体の作り直しは不要で、候補fact構造化だけが未解決である。コード・testsは変更していない。

提案する明示mappingは `shares→shares:1`、`株→shares:1`、`千株→shares:1000`、`万株→shares:10000`、`百万株→shares:1000000`。135A会社短信に株、保存外部レポートに万株の表示を確認した。千株・百万株はこの会社の原文に存在すると主張せず、明示表示された場合だけ適用する十進換算候補とする。曖昧なsuffix/英語ラベル/億株等の追加は行わない。

Damodaran保存原典TY12/PDF17頁は “dividing by the number of shares (3.448 billion)” として株主価値を株数で割る。既存`docs/explicit-equity-bridge-spec.md`も「金額はすべてJPY実単位、株数も実株数」とする。金融式がこの根拠であり、新しいunit名/mappingはprojectのデータ整形契約である。著者の歴史Toyotaの数値や株式定義を135Aへ採用する根拠にはしない。

## 135Aで保持する定義

会社保存短信の同じ表は、期末発行済株式数（自己株式を含む）10,256,000株、期末自己株式数－株、期中平均株式数（中間期）10,256,000株を別行で示す。期末発行済と期中平均が同値でも同じ概念ではない。ダッシュは0にせず、自己株控除後・希薄化後・EPS分母・現在評価用株数への転用は別の意味確認である。quote/offset/page/sourceID/rawSHAはdesign.jsonに保持した。

`unit:shares`は数量の次元だけであり、自動netshares、EPS/時価総額からの逆算、現在時点への持越し、モデル入力採用をしない。fact正規化の符号/欠損規則は維持し、負値/0/小数を新たに一律禁止しない。valuation側の正のshares_outstanding条件は既存通り局所的に残す。

## 互換・再現

旧mapping13×kind4の52合成fixtureを既存baselineの固定nowで現在APIへ再投入し、全bundle canonicalhash・派生IDの完全一致を確認した。これは変更前確認で、未実装変更後の一致を保証したとはしない。億円追加済みの現mappingも実装後の対象へ含める。

追加後もschema_version/normalization_versionを1のままとし、既存出力のlimitations/declarations/content/metadata等の文字列を変えない。IDは内容とmetadataから決まるため、表に新pairを足すだけなら旧入力へ新fieldや文言を混ぜる必要がない。内部docstringのみ対応単位を更新できる。旧保存source/IDは書き換えない。

既存reproduce_disclosed_fact_sourceは同じnormalizerで再現するので、新しい再現器は不要。旧buildは新sharespairを再現できないためneeds_reviewとして保留する。model_inputsはvalue_path数値・kind・原典closure/PIT・再現を点検できるが、unit/period/definitionの意味を未確認、financial_inputs_verified:falseのまま維持する。

## 受入条件

意味のある単位境界、符号/欠損、異次元reject、原文同一quote、決定的再現と改竄/欠損保留、合成9inputへの数値監査と意味未認定、旧全bundlehash/IDの完全一致をdesign.jsonに具体化した。sourceの将来時点/原典欠損等は既存guardを再利用する。金融予測・確率・価格・売買閾値・policy・IR送信へ進めない。

新GET/DB/既存file変更/production/test変更/全件testsは0。生成したのはこの設計2filesのみで、実装は親のレビュー待ち。
