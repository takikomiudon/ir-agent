# 公開value戦略実装：固定repository検索の候補5件

GitHub repository searchを `q=magic formula investing`、`sort=stars`、`order=desc`、`per_page=5` で1回だけ実施した。fresh robots404は既存missing-robots契約で記録し、検索HTTP200を完全受信。新GETは計2で終了、README・コード・ライセンス本文のGETは0。total_countは28、incomplete_resultsはfalse。先頭5件だけを保存し、paging/他queryは行っていない。

| 所有者/name（公式metadata URL） | description（返値そのまま） | default_branch | stars | license metadata SPDX |
|---|---|---|---:|---|
| [rbhatia46/Greenblatt-Magic-Formula-Value-Investing](https://github.com/rbhatia46/Greenblatt-Magic-Formula-Value-Investing) | Implementation of Joel Greenblatt's magic formula, which he described in his book - "The Little Book That Still Beats the Market". | master | 81 | null（未確認） |
| [ginglis13/magic-formula-scraper](https://github.com/ginglis13/magic-formula-scraper) | scrapes names and tickers from magicformulainvesting.com every quarter, adds info to a google sheet which includes stock prices and a link to the first result of a google search of the company name | master | 33 | MIT |
| [laurenponsonby/Value-Investing-Greenblatt-s-Magic-Formula-in-Python](https://github.com/laurenponsonby/Value-Investing-Greenblatt-s-Magic-Formula-in-Python) | I have taken Joel Greenblatt's book and applied his magic formula to listed stock to identify under priced stocks. | master | 11 | null（未確認） |
| [maxgfr/crible](https://github.com/maxgfr/crible) | Self-hosted fundamental stock screener — 150k+ equities, zero API keys forever. Transparent scores: Piotroski, Altman, Ohlson, Zmijewski, Beneish, Montier, Greenblatt magic formula, Graham — full provenance, DuckDB-fast (<1s full-universe). | main | 6 | MIT |
| [crdcj/MagicFormula](https://github.com/crdcj/MagicFormula) | Backtesting Greenblatt’s “magic formula investing” for Brazilian listed companies | master | 3 | null（未確認） |

完全なlicense metadataと各API URLは[candidates.json](candidates.json)へ返値通り保持した。starsは検索時点の発見順で品質の証明ではない。descriptionの実装・データ件数・APIキー不要等の主張を検証した意味ではない。license metadataのMIT表示は本文確認/利用許諾採用とは区別し、nullもライセンス不在の断定ではない。

どの候補にも選別と定期売却/入替まで実装されているとは、metadataだけではまだ確認できない。5番は説明にBrazil上場企業のbacktestingとあるが、正確な市場/会計/期間・売却コードは未読。日本株適合・Greenblatt本人の推奨・原式との同一性・金融採用は認定していない。rootの候補選択を待ち、ここからのREADME/コード探索は開始しない。

検索本文完了は `2026-10-15T23:01:40.201664+00:00`。[capture.json](capture.json)とrawにHTTP状態・完全entity・SHA・開始/完了時刻を保存した。UAは設定値/prepared requestであり独立wire検証ではなく、保存bytesはrequests entityでwire圧縮bytesとは異なり得る。

事前の同query検索で一致したのは既存Greenblatt公式サイトの説明記録だけで、このGitHub queryの過去試行は見つからなかった。閉じた公式方法経路やQuantConnectを再開していない。URLのquery parameter順だけが事前allowlistと異なりローカルassertで停止した1呼出しは、ネットワーク到達前GET0。事前宣言の同じquery/値の正確URLを使い、HTTP再試行や別queryは0。

実DB・code編集/パッケージ実行・新policy・金融入力・銘柄選定・注文・外部連絡は0。このfolder以外の保存ファイルは変更していない。
