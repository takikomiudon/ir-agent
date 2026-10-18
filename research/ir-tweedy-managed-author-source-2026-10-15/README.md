# Tweedy公式運用部門：条件付き売買方針の原典候補

**公式運用案内の原PDFを1件取得し、価格と推定本源価値を比較する買い・売り方針を確認した。具体的な割安率・接近の閾値・数カ月〜1年の利確期限は、この確認範囲では得られていない。** 継続保有の例外が明記されているため、自動売買ルールへ単純化せず、未採用の根拠候補として保存する。

## 取得経路と停止

保存済み `research/ir-tweedy-author-policy-discovery-2026-10-15/home-extraction.json` の公式運用部門への実リンクから開始した。成功した公式ポータルが指定する別の運用主体hostであり、失敗hostの迂回として選んだものではない。旧Tweedy成果物は変更していない。

新規GETは次の4件で終了した。全件HTTP200・本文完了、redirectとretryは0。

1. `https://www.tweedymanaged.com/robots.txt`
2. `https://www.tweedymanaged.com`
3. `https://www.tweedymanaged.com/commentary/?papers-perspectives`（rootの実リンク）
4. `https://www.tweedymanaged.com/wp-content/uploads/sites/15/2023/09/TB-General-Info-Managed-Accounts-06-30-26.pdf`（一覧の実リンク）

fresh robotsのwildcardは空の禁止指定で、固定UAによる対象pathの許可を既存parserで確認した。AGENTS、ローカルIR skill、workflow、hold v5の9 exact hostを照合し、対象hostは保留索引に含まれなかった。環境policyはunrestricted/state unknownの観測で、適用済みとは主張しない。通常proxy・CA・TLS検証と同一UAを維持した。

PDFは276,489bytes・8頁、原SHA-256 `bb123294926352e7055d0a8e76c186302dbc4d007fadc376cd285bb20da77dbd`。HTTP本文完了は2026-10-15T21:32:42.390448+00:00。公表日時はnull、6月30日は一覧の情報日付ラベルとp2の資産等の基準日で、公表日へ推定しない。取得時刻と実DB初回保存日時は別で、DB保存は行っていない。

## 原典が支持する内容と残る不足

意味を確認した範囲は物理p2–4だけで、各頁の画像も照合した。説明用の逐語引用は[quotes.json](quotes.json)の2件・合計85語に限定し、このREADMEでは重複引用しない。他の内容は以下の位置付き要約と[review.json](review.json)へ記録した。

| 原典位置 | 支持される内容 | 数値実装に残る不足 |
|---|---|---|
| p3左列・売買方針の段落 | 推定本源価値を大幅に下回ると考える価格で購入し、一般には価格が推定価値へ近づくと売却。ただし継続保有理由がある場合は例外。 | 割安度・接近の具体的な数値、例外の判定方法は未指定。等号比較や一定の安全余裕へ置換しない。 |
| p3左列・末尾段落 | 手法を四半期単位で評価せず、長期間の総収益で測るとの説明。 | 個別銘柄の固定保有期間・売却期限ではない。利用者の数カ月〜1年へ一致したとしない。 |
| p3右列・投資過程 | 世界の銘柄をデータベースで絞り、年次報告等・比較取引・会社や競合との対話・内部者取引等を調べ、委員会の合意で売買する。 | 質問必須やIR回答による価格保証ではない。研究手順を参考にすることと、数値方針の採用を分ける。 |
| p2右列・価値の分類 | 簿価、流動資産価値、利益価値、企業全体の私的市場価値という観点を説明。 | 会社ごとの評価方法・利益年度・公正倍率・その他入力を確定しない。 |
| p4左列・国際投資 | 米国外でも同じ原則を適用すると説明し、日本語による調査能力にも言及。 | 日本株個別保有・日本市場固有の閾値・現在の適格性の直接確認ではない。 |
| p3右列とp4左列・補助冊子への参照 | 過去に有効だった投資特性の冊子と、米国外研究の存在を説明。 | 冊子そのもの、日本研究の条件・結果・具体的売買数値は未取得。 |

## 未取得導線

対象の投資研究冊子への実PDF URLは、このrootと静的一覧には確認できなかった。追加表示は`#`であり、JS/APIやpathを推測しない。一覧には `https://insights.tweedy.com/insider-investment-factor` という別hostの実リンクがあるが、対象host追加禁止とGET上限に従い未取得候補として残した。別hostのrobotsも取得していない。後の取得を予約・承認したものではない。

[capture.json](capture.json)と`raw/`に原応答、`text/`に機械抽出、`images/`に確認3頁、[guard.json](guard.json)に制約とliteral来歴、[validation.json](validation.json)にSHA・引用offset照合を保存した。raw/textは取得証拠として保持する。新規GET4件、親担当の先行3件と合わせて今回のTweedy調達は7件で停止。ネットによる追加診断・外部連絡・発注・実DB操作・src変更・金融方針採用は0。
