# Brazilian Magic Formula：年次入替の作者説明まで確認、実装は未確認

候補5 `crdcj/MagicFormula` を4GETだけ確認し、固定commit `ac05a3bd3e146aa924b2b5e11ebffa3484c2c81d` を保存した。default-branch commit metadata→返されたliteral root tree→README blob→rootに直接載る唯一のcode候補 `results.ipynb` の順。4件ともHTTP200・完全entity。直前のapi.github.com robots404を根拠付き再利用し、新robots GET・redirect・retry・別repo/host取得は0。

READMEはブラジル上場会社向けbacktest、作者表示はFelipe Costa/Carlos Carvalho。2022年の30銘柄表がある。選択notebookは10cell中9が説明markdown、残るcodeは空で出力0だった。独自module呼出もなく、実行可能な売買処理を確認したとは言えない。src subtreeは未読であり、repoに定期売却がないという結論ではない。

作者の説明には、毎年30銘柄、年の100日目以降の最初の取引日に年次rebalance、2011–2022の11rebalance、手数料/spread/税費用を含めない、という具体的なsimulation設計がある。説明で定期入替が述べられる点は単なるcurrent rank表示とは異なるが、非選択銘柄売却・継続保有/再等配分・lot/費用処理の実装は未確認。年次rebalanceを強制利確、全銘柄1年保有又は日本株の退出期限にはしない。全既保有売却かrank外だけの入替かは不明で、30銘柄でも等配分とは認証しない。年100日目の休日/市場・時点処理の実コードも未確認。

指標の冒頭説明はEBITと資本/EVの比率だが、実際のROICはDamodaran定義採用という注記があり、税・資本平均・EVのfield対応は未確認。負ROIC/EBIT/NetDebt除外の作者説明はあるものの、0分母・欠損/無限等の処理は不明。公益/金融/外国企業のほか国有会社を作者独自に除外する説明をGreenblatt原典の要件へ移さない。最低流動性の具体値や等配分も不明。負NetDebtのfield定義、具体的company-year/行の除外、符号条件の組合せはコード未読で不明で、net cash企業全部の除外というルールを補わない。

監査済連結財務と価格/配当の工程説明は、全社の公表日/利用可能version、上場廃止を含む当時universeやbias除去の検証ではない。結果図・return・IBOV比較を再計算/実行していない。詳細linkは別repo `AlgebraQuant/MagicFormula` を指すが、移転/alias/同一性を認定せず未取得のまま止めた。[source-reference.json](source-reference.json)には固定root treeに直接載る未読srcのliteral URL/GitSHAを残した。次に必要なsourceが特定できたことと、内部code実装を確認できたことを分ける。license metadataはnullで本文未取得、移植・依存導入0。Greenblatt/Damodaranの承認、日本適合、IR規則、金融policy採用はいずれも未確認/未採用。

[review.json](review.json)に項目別の位置と限界、[quotes.json](quotes.json)に必要最小の短い逐語引用とセル内offset、[guard.json](guard.json)に規則/固定URL/予算、[capture.json](capture.json)に完全entity SHAとローカル完了時刻を保存した。decoded `README.source.md` と `selected-code.source` はGit blob SHA1も照合した。API HTTP raw entityと復号blobは別SHAで、wire圧縮bytes/独立署名検証/元DB初回保存の証明ではない。公開GET前のruntime観測はconnected/runningだがnetwork policy state=unknownであり、適用readyを認証したとはしない。

生成説明用の英語引用は同notebook合計90語未満、Greenblatt原典の転載引用は追加していない。[validation.json](validation.json)のローカル整合確認で凍結し、GET予算は使い切り。新GET/DB/コード実行/共有file変更や旧closed探索を続ける予定はない。
