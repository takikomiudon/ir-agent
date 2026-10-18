# 著者論点record v2：独立の意味・版保持点検

修正必須の不一致は見つからなかった。旧case-recordの14項目はrecorded_atを除いて入れ子の内容まで完全に保持され、旧JSON/MDも元SHAに一致する。初回記録時刻と実v2時刻は別に残る。同じissue ID・著者・会社目標の帰属・未知の閾値・未採用・未解決を維持している。

preflight-v3の全file SHAと、質問本文・ABC・公開性・未推定情報価値・正式準備の5フィールドhashを照合した。質問の変更・同義草案追加はなく、金融path/EPS/感応度/評価/売買はnull、EVSIは未推定で0にせず、送信not readyのまま。

追加61〜63頁は、固定済みquarter-profit研究とその独立レビューをSHA付きで再利用した。原PDF/画像の再審査や棒合計の再計算はしていない。初回stable同名上書き・旧完全byte未保存の限界と、最終7ファイルだけを参照する境界も保持される。

追加解釈は適切に限定される。個別ロータリージョイントの販売変化や業界例は全オリジナル比率の新系列ではなく、業界セグメントの組替えは商品の比率分類/分母/内部消去の変更証拠ではない。売上増減棒、セグメント利益、全社営業利益を区別し、最新ratio・完全な分母・著者の停滞許容は未確認。関連する事業説明が増えても、著者の支持/反証を新たに認定していない。

既存p66のcompany-plan-and-exclusionsは保存textの**その1spanだけ**を照合し一致した。営業利益+19%・純利益−6%は、期初会社計画据置と前期特別利益反動の説明である。中東影響の売上未織込みと物価上昇の販管費織込みも引用に残る。QUICK独自予測・ratio→EPS感応度・株数逆算・達成保証にはしていない。同じ保存レポートの追加解釈で、新会社発表や独立source増ではない。

同一保存source objectへ2方式を適用し、`models.json_text`のSHA **8ad41657…** と、空白を省いた`canonical_json`の **1470109a…** を再現した。両JSONをparseすると同じsource objectとなる。これはserializationの違いで、metadata差や本文差を示すものではない。実DB/監視inventoryの完全snapshot同一性は確認していない。

[independent-record-v2.json](independent-record-v2.json)にv2固定SHA、旧入力23件の不変、p66位置/SHA、旧14項目保持、質問契約と意味の点検を保存した。GET/DB/code/tests/旧file変更/新fact/新金融規則/IR登録・送信は0。
