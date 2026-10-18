# 6814：10月9日通知の旧新版・年次会社予想4項目

固定原典から**通期連結EPS旧411.28/新537.80円、年間予想DPS旧160.00/新210.00円の4factsだけ**を既存normalizerで抽出した。全て既存enum `issuer_guidance`（会社予想）、JPY-per-share。EPS conceptは既存2410、年間DPS conceptは既存1975例を再利用。4月9日版と10月9日版はscope/periodで分け、古い予想も10月9日通知で再掲された内容であって、4月当時の保存・利用を実証しない。

対象はFY2027/2（2026-03-01〜2027-02-28）。期間はp1通期連結表の明示日付で、同通知年間DPSへの対応は文書contextによるreviewer assertionとして保持し、配当の権利日・支払日とはしない。新年間210は中間115決定＋期末95予想という会社説明を保持するが、中間115は今回fact化しない。通知に会計基準名や未来EPS株数/分割basisが明示されない点を残し、年次平均株数から逆算しない。FY2026実績EPS529.53/BPS2826.61・旧bundleは変更0。

[normalization-input.json](normalization-input.json) が原文・表列・頁/原token位置・版を固定。[normalized-bundle.json](normalized-bundle.json) は原source全object不変＋派生1sourceで、同一原典の再表現は独立情報追加ではない。[audit.json](audit.json) にDecimal/再現/native・compact SHA方式/コードpinsを保存。normalizer固定SHA d434b41c…、CLIはSHA読取のみで未実行。

API wholebundle replay/reproducer、4token・unit・periodとUnicode/UTF8位置を確認済み。金融意味や入力採用・未来DPS列・価格/モデル/IRを認証しない。DB/Store/GET/CLI/index/code/旧file変更0、実DB初回保存は未確認。`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reproduce.py` でfile-only再現できる。成果を固定し停止。
