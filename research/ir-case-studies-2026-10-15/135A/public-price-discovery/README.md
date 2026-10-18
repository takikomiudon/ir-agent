# 135A：株価の表示は取得、価格入力への採用は保留

保存済みの公式IR入口とFAQには、株価情報 `https://vrain.co.jp/ir/quote/` の実hrefがあった。保存robotsの許可を照合して公式株価頁を1 GETし、同頁が明示する `https://finance.yahoo.co.jp/quote/135A.T/chart` へ、Yahooのrobots確認を含む残り2 GETで到達した。**新規3 GET・すべて200**、リトライ・自動リダイレクト・JS実行・認証は0。旧資料・DB・モデル・質問・送信は変更していない。

静的な原HTMLとJSON文字列に、**銘柄135A / 表示価格4,195 / 表示時刻14:42**は見つかった。ただし価格に直接結びつく**JPY/円の単位と、日付・タイムゾーンを含む観測日時が確認できなかった**。4要素が揃わないため、`source-bundle.json` は作成しておらず、価格入力やmarket_data sourceとして登録していない。

| 必須要素 | 確認 | 保存field |
|---|---|---|
| 銘柄 | 135A / 135A.T、VRAIN Solutionの社名と一致 | record6 → `[3].preloadedStore.priceBoard.board.code` / `codeWithMarketExtension` |
| 価格 | 文字列 `4,195` | 同board → `price.value` |
| 通貨 | 未確認 | boardに通貨fieldなし。日本株という理由や配当等の円表記で補完しない |
| 観測日時 | `14:42` の時刻のみ | 同board → `japanUpdateTime`、HTMLは `<time>14:42</time>`。日付/offsetなし |

時価総額など他指標のHTMLには完全な日時属性もあるが、それを価格の日時として転用しない。`japanUpdateTime` というfield名だけでJSTを補ったり、取得日を当日にして結合したり、終値と認定したりしない。ページの「リアルタイム株価」という表示も、現在取引できる価格や取引所の独立確認を保証した事実にはしない。

新規ページの初回取得は `2026-10-15T06:08:27.580453+00:00`。これはページの取得時刻で、価格観測日時ではない。公表時刻はnull。抽出実施時刻も別に保存した。

JSONは既存原HTMLのinline `self.__next_f.push(<JSON>)` の**引数だけを厳密JSONとして読み**、record6の静的boardを照合した。JS・React参照・追加moduleは実行/解決していない。原HTML内位置とSHA、decoded payload、record6、候補field pathは `static-field-extraction.json`、短引用は `source-quotes.json`、欠損は `review.json` に保存した。価格以外のPE・EPS・株数やPTS等は採用していない。

Yahoo頁には株式情報の転用・販売禁止の注意書きがある。今回の限定公開調査を継続取得や再利用の許諾と扱わず、ライセンス・鮮度方針も採用していない。3 GETで終了し、別URL・SharedResearch・API・SDK・追加phaseへ広げていない。
