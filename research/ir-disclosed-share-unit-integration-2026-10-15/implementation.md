# 明示株数単位の最小追加: 固定チェックポイント

既存normalizerの表へshares/株/千株/万株/百万株→sharesの5pairを追加し、内部docstringだけを更新した。schema/version/API・旧出力本文/metadata/limitations・消費側は変更していない。新docは旧workflowの単位列挙を補足し、旧参照資料を上書きしない。

新8testを含む対象5module **41件が0.110秒で成功**。旧52合成fixtureの全bundlehash/ID/contenthashと入力不変を検証し、既存億円4kindのbundleをbefore全文実装と完全比較した。新testが全mapping表の「旧14＋指定5pairだけ」を点検する。追加許可された既存億円testは名前とcurrency/ratio14pair比較だけを更新し、旧fixtureの全assert/loopはbyte同一である。

換算・再現・モデル数値一致は発行済/期中平均/自己株控除後/希薄化後の意味や評価用株数への採用ではない。値の符号/0/小数・欠損は既存規則を保持し、財務意味はfalse/unreviewed、確率なしは期待値未設定のままである。実135A数値の抽出/モデル採用は行っていない。

4変更file全文はsource-after/、hash/countはsource-after-manifest.json、実行結果はtargeted.log、詳細はimplementation.json。親保存before全6copyと現行の未変更5files、既存設計のSHA一致を確認した。DB/GET/旧レコード/外部送信/全件suiteは0。**編集停止・独立レビュー待ち**。
