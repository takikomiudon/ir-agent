# 1950 推奨参照版：scope内の重複引用だけを省略

**file-only推奨版生成済み、root受入待ち。** 旧9fact生成物は全bytesを保持したまま、各factのscope.source_context_references配下3件のbasis_quoteだけを削除した。9fact×3＝27箇所のみ。参照path/file_sha256/quote-idとなるkey/page/character start/end、主fact必須basis_quote、元source全object、全数値・kind/concept/period/definition/location・その他scopeとreviewは完全同一。逐語文は完全原sourceと既存source-quotes.jsonから読める。

この変更はデータ参照の重複削減であり、parser新版や意味判定の変更ではない。単一原decimal tokenだけを使う正規化版1を維持する。入力ファイルは168524から105614 UTF-8 bytesへ縮小した。旧bundleと推奨bundleは同じ9表示値を表す代替artifactであり、18個の独立開示や新予想ではない。実DB登録・索引追加はrootの後続処理に委ね、旧版を追加登録する意図はない。

Q1売上/営業利益/親会社NI、当時FY会社予想の同3値、Q1EPS/当時FYEPS/当時年間合計DPSの9件だけ。DPS合計欄（同額の期末欄とは別）、FY両端/recorddate/会計/連結null、当時予想据置・参照日不明、p2当時株数と未読の後日買付告知、p4季節性、p8利益/NCIの区別は旧版のまま。Q1年度化・現在EPS分母・正常利益・DDM列・採用予測を作らない。

`request-diff.json`は27削除のみを記録。生成前に参照先のSHA/quote-id/頁/位置と原全文の逐語一致をローカルで個別照合した。このfile-only証跡はnormalizerが外部参照を自動認証する機能ではなく、金融上の意味やscopeは引続き人/agentのレビュー宣言である。

`generate_once.py`で追加primary生成1回、`reproduce.py`で同now全文bundle/ID一致と既存reproducerを1回点検し成功した。新contentは旧contentから27文脈quoteを削ったものと完全一致し、主引用・金額/単位換算・期間・scope・元sourceは不変。derivedのid/content/retrievedだけが変わり、その他source fields/metadataは旧版と完全同一。再現内の明示normalize1回及びreproducer内部再構成はprimary生成数と分ける。

派生retrievedは **2026-10-16T03:18:43.385501+00:00** の実処理時刻。原HTTP03:08:13.157646UTC/原公表日2026-07-31/pubnullを保持し、レビュー・処理時刻をactual firstsave/known-byへ変換しない。DB接続・保存は0で新派生actual firstsaveは未登録。旧proof・原取得/引用成果物のpinと受入コードSHAを固定した。

詳細な原9値の意味・表・単位・境界は[旧版README](../README.md)、主引用は[quotes.json](../quotes.json)。旧版のfullscopeは履歴として残す。本推奨版でもfinancial_inputs_verified:false/meaning_review_required:true/financialadoption:false。新GET/DB/production code/共有docs/旧files編集/新予測/IR質問0。
