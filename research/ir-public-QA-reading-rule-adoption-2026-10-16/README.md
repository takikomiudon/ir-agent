公開Q&Aの誤読を減らす技能改善案を、現行ファイルへ適用せず準備した。

- [新doc本文案](proposed/docs/public-qa-reading.md)：質問者前提と会社回答、当時予想と将来中計、採用flowと人員stock、主な費目と完全bridge、文書/会合/URL日付を区別する短い手順。
- [最小patch](minimal-links.patch)：`.agents/skills/jp-equity-ir/SKILL.md` と `docs/ir-question-preparation.md` に各1段落のリンク/指示を挿入する案。旧文の削除や書換えはない。
- [根拠票](method-and-evidence.json)：DD/JIRAの短い逐語条件と境界、6200/4318の原source・native SHA・期・話者・quote pointer。会社原文は再転載しない。
- [意味検証票](meaning-validation.json)：before完全bytes/SHA、提案後SHA、2hunkの使い捨てコピー上dry-run、今回の具体的な誤割当を防ぐ項目。

6200の「質問3」はQ2説明会の質問番号であり、第3四半期のことではない。OJT負担、41%、40名は各質問文と回答を分ける。回答7の当時予想、回答8の将来中計、回答9の採用意向を同条件の矛盾や将来人件費削減率へ変えない。4318の翌FY2027費用見通しをFY2026実績・売却益の税後bridgeへ移さない。6200のMay11文書/会合日とURLMay13も区別する。

これらは既存DDの比較差/非誘導とJIRA企業向け推奨を公表QAへ適用した本プロジェクトの読解手順であり、著者の直接投資規則ではない。既答を再質問から除き、残る回答で何の比較・既存入力の意味が変わるかを絞るための改善である。新必須field・normalize/金融契約・普遍的な送信gate・金融式・予測・正式IRは追加しない。

GET/DB/Store・現core/技能/docs・旧原典/quote/sourceの編集は0。rootの独立レビュー・適用待ちでfreezeする。適用時にはbeforeSHAを再照合し、他変更があれば旧bytesで上書きせず最小差分を組み直す。新doc本文は将来の`docs/public-qa-reading.md`を基準に相対リンクを記述しているため、適用後の配置でリンクを照合する。今回のfreezeは実適用・root受入の記録ではない。
