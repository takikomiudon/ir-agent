# 1866：Q1実績3・通期会社予想3の表示値

受領済みfull-extraction-variantの短信sourceを全objectのまま使い、既存normalizerで6表示値を構造化した。旧partial sourceで生成していない。会社が記載した百万円tokenからJPYへ換算しただけで、金融モデルへ採用していない。実DB登録は0、親レビュー待ち。

| 会社の表示項目 | Q1実績（百万円） | 通期会社予想（百万円） |
|---|---|---|
| 売上高 | 20,497 | 86,000 |
| 営業利益 | 1,205 | 5,000 |
| 親会社株主に帰属する純利益 | 1,082 | 3,500 |

実績3はreported_fact、通期3はissuer_guidance。前者は2026-04-01〜2026-06-30、後者は2026-04-01〜2027-03-31。元の令和表記をraw_period_labelに残し、西暦への変換はreviewerの解釈として明示した。短信p1の日本基準・連結、百万円未満切捨てを保持。未表示精度を正確経済額とは認定しない。

予想は2026-08-06短信で示された会社予想で、p4の「5月12日公表から変更なし」を文脈引用として保持した。5月12日原通知や当時のシステム保存を確認したことにはならない。株式分割と平均株数の既存注記も別の文脈引用として残したが、EPS/株数を新factにせず、追加分割換算や分母逆算は0。営業利益をEBIT/NOPAT、親会社純利益を正常利益/FCFFへ改名していない。

inputとbundleは各1件、原primary1件・派生1件。原source IDは `case-public:52347b3c8a8157bfc5874e644276ea0b40ec920537b44da2d062ba5b5fdf834b`、派生IDは `disclosed-facts:71d1174baadf1fd3d924a93dcc6433a6ddbe0ba391937fecf2ef1cab33122ebe`。原URL/metadata/全文/日付・時刻を変更していない。公表日は2026-08-06、公表時刻不明のpublished_at:nullを保持し、派生retrieved_atを元取得やDB firstsaveへ遡及していない。原著者は北野建設、抽出reviewはCodexとして区別した。

対象表p1画像を今回目視し、列とtokenを確認した。quotesには原全文の文字/UTF8 offsetと画像SHA、株式・連結範囲・予想据置の既読文脈参照を保持。full text保存は11頁の全冊読解ではなく、原variantの意味確認範囲を拡張していない。generic byte verifierのmatchedとも呼ばない。

`reproduce_disclosed_fact_source` はreproduced、原content matched、原snapshot matched_supplied_snapshot。同じ生成時刻でnormalizerを再実行したbundleも完全一致した。API時刻/値/再現結果はnormalization-reproduction.log、value pathはaudit-source-pathsに記録した。後者はモデル入力割当ではない。

旧50fileのSHA不変、6ID重複なし。全financial_inputs_verified=false/meaning_review_required=true、companies/theses空。EPS、前年比率、未知の将来利益、正常税、差額合成、価値計算は0。GET・DB接続・原file/production code/schema/共有文書/索引変更・IR質問作成・full suite再実行は0。
