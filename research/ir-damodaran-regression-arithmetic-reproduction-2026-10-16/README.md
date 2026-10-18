# Damodaran掲載回帰式の有限な算術再現

保存済み公式ページの導入部にある**2022年1月のDisney・米国PBV例**だけを、表示係数と表示入力からDecimalで再現した。2026年1月の日本PE表とは年・地域・従属変数が異なるため分離した。原典4fileのSHA、式/入力/年/比率表記のUnicode・UTF8半開offset参照はresult.jsonへ固定している。引用対象の全文は固定したtext/04.txtで確認でき、新たな長文逐語転載はしていない。

Disney例の入力はg=.12、Payout=.20、ROE=.162、Beta=1.10。表示式の項は順に2.10、0.7284、0.7590、0.82458、−0.0660となり、厳密積和は**4.34598**。こちらで小数第2位へROUND_HALF_UPした結果は4.35で、著者表示に一致する。ただし、この丸め方法を著者が指定したとは認定していない。依頼時の未検算候補4.34698は原典値ではなく、計算へ使用していない。

日本PE表の解析上の偏微分は、gについて42.26、Payoutについて10.46、Betaについて4.28。他変数を固定した独立の変化として、g又はPayoutを比率の1percentage point（.01）だけ変える係数積はそれぞれ**0.4226倍、0.1046倍**。Betaを1単位変える係数積は**4.28倍**で、Betaの1単位を率の1ポイントとは呼ばない。定数を含む企業別PEや会社予測は計算していない。Disneyの係数・入力を日本表へ転用せず、R²や係数を予測成功確率にもしていない。

演算結果は公表decimal tokenに対する正確算術で、原回帰の未丸め精度や企業経済値の正確性を認証しない。「2026年1月」という表ラベルは2026年10月の最新性保証ではない。PEの分母、標本・除外、Beta期間、Payout期、会社別5年成長、比較適合などの未確認を原inventoryから保持した。株価・企業入力がない不足を新featureで隠さず、2983/価格/valuation/IR判断への代入・金融採用は0。著者の歴史例の投資結論を当方が現在判定したものでもない。

実行はリポジトリ直下から `.venv/bin/python research/ir-damodaran-regression-arithmetic-reproduction-2026-10-16/reproduce.py`。保存resultともう一度実行したstdoutが全bytes一致し、参照spanの文字/UTF8・substring SHAも独立照合した。script SHAは `d8d58ecc7e97d94d0d70b1bed0b1aa780c9e3e9a942247475b3b884019f3751f`、result SHAは `27281953ba9739689b3a3e9dd26f8ec98bf054744d05d4db82b9c37990af1a23`。新GET/DB/Store/旧docs・原典変更/production追加は0。3fileだけをfreezeしroot確認待ちで停止する。
