# 2983 入口・著者レポートの独立点検

限定した不一致は1件です。review.jsonの純利益用英語キー2つが「10billion_JPY」となっていますが、p4/p8の原表単位は「10億円」（1 billion JPY）です。会社3.25・著者3.28の印字と帰属は正しく、元数値の誤りやモデル採用とはしません。旧記録を変更せず、finding 2983-R01-NI-unit-key として固定しました。

保存34ファイルのSHAを保持し、記録上は入口2GET・PDF側2GET、各hostのrobots・raw/capture/UTF8/sourceと実受信時計を照合しました。入口はapplication/json1 payload・4rowsを独立に再解析し、a要素のPDF hrefではないliteral URLを追跡。b09d26…入口sourceからcc1056…PDF sourceへのoriginal_source_idsと、索引2026.10.01/表紙2026年10月1日の対応が一致します。正確な公表時刻や歴史的初回保存はnullのままです。

PDFは11頁の機械抽出と778034entity bytesを確認し、18引用の頁内/全本文Unicode・UTF8位置が一致。入口18引用も一致しました。意味の点検は画像p1/4/7/8/11のみです。

会社EPS304.27と著者308.31/339.81/369.46を分離し、p8の著者予測改定と旧/新表を確認。p4の分割注記は配当比較のみで、実施日・倍率・EPS基準は未確認です。p1市場PER5.2とp7の12か月forward比較（2983行6.1）は別基準で、公正倍率/目標式にしません。事業前提は支持/反証や売買閾値へ昇格せず、p11の作成組織・会社委託費用負担・独自検証なしを実文範囲で確認しました。個人名・報酬額/契約詳細は未確認です。

既存byte verifierは入口がunsupported providerでunknown、PDFがnative宣言byte契約だけmatchedでした。両方を包括的passにせず、source-ID導出・金融意味の認証とも区別します。

新GET・DB・コード・旧file/index/monitor変更・IR/金融採用は0。8151の数値/著者名は使用せず、他6頁の意味監査も行っていません。後続の単位ラベル訂正は別記録で扱います。

点検日時: 2026-10-15T16:56:44.123446+00:00 / 2026-10-16T01:56:44.123446+09:00  
詳細: [independent-recheck.json](independent-recheck.json)
