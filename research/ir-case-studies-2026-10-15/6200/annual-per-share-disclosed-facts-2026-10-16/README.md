# 6200 公表年次EPS/BPS 2値の構造化準備

p1直接表示EPS49.20円（2024-10-01～2025-09-30年間連結実績）とBPS148.70円（2025-09-30期末）の2factだけ。原全objectは無変更。p2普通株期末85,243,000/自己株1,269,169とp18平均83,947,385株・普通株利益4,130,091千円を文脈参照として保持した。p1親NIの百万円精度と混ぜて再除算しない。

BPS詳細分母・普通株帰属調整は選定頁に明記されず未確認。期末発行－自己株を会社公式BPS分母と認定しない。希薄化EPSのdashは潜在株式不存在による省略で0にしない。当時guide55.15・未読Q3・現時点株式調整を年次実績へ混ぜない。

既存disclosed_facts.py固定SHA d434b41cfa19568d0cef1a2e6710365f447012d75a4b07ca950cc62b6bd9db51 の直接関数を固定nowで使用。通常小数v1でpure再生成wholebundle一致、標準reproducer reproduced、Decimal/原token/Unicode・UTF8span照合済み。reproduce.pyで再現できる。

model-input-audit-request.jsonは準備のみ。audit APIは内部でvaluationを計算するため実行していない。金融意味/著者式への採用・価格・予測・policy・IR・DB/Store/CLI/newGET 0。CLI/valuationは別phase編集中のため不変pinに含めない。原本+派生は独立確認2件という意味ではない。
