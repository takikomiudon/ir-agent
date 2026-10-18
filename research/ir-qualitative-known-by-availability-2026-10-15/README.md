# 定性レビューの legacy known-by 境界

初回保存時刻が不明な旧資料でも、正しい `legacy_presence` receipt によりレビュー時点までの存在が確認され、全原典 DAG の過去・現在の利用条件を満たす場合だけ、native 定性レビューに使えるようにした。変更は `QualitativeResearch._source_check` の wrapper 内のみ。実案件の登録・queue・claim・complete は実施していない。

## 既存契約と実装

根拠は `docs/historical-availability-design.md`「旧DBの移行」3 の既存 known-by 契約と、`src/ir_agent/availability.py:RecordAvailability.at` の SHA・receipt・時点検証。`docs/qualitative-research-jobs.md` の bootstrap 時点照合と queue/claim/complete の現在再照合を維持する。著者の投資規則・金融入力・分類方式は変更していない。

wrapper は monitor 結果が unknown、唯一の理由が `source_first_save_unknown`、historical_usability/current_use がともに matched の場合だけ root の検証済み availability を調べる。available=true、first_save_known=false、basis=legacy_presence、first_saved_at=null、known_by_at が boundary と current の両方以前という条件を満たす場合に matched とする。既存 reader が行う全 DAG の会社・synthetic・cycle・公開性・分類・receipt 検査を置き換えない。

変更枝だけに `known_by_at`、`review_availability_basis: legacy_presence_known_by`、`nonblocking_diagnostics: [source_first_save_unknown]` を加える。first_saved_at=null、first_save_known=false、旧 arrival はそのまま。正確な初回保存・fresh arrival・資料の正しさ・著者条件の成立を認証したわけではない。trusted receipt の枝は full JSON 不変。read-only monitor の実装・出力は変更していない。

## focused 検証

`focused-tests.log` の実実行は 83 tests 成功：qualitative 41（新規 11 を含む）、research_monitoring 16、catalyst_schedule 21、historical_availability 5。full suite は root 担当で未実行。独立レビューも root の後段手順。

新規テストはメモリ DB と一時ファイルだけの架空データ。legacy bootstrap→新 legacy source queue→claim→complete と receipt 不変、presence 同時刻の許可/前時点の拒否、欠損・壊れた・SHA 不一致の receipt、祖先後着/分類後着/receipt 欠損、祖先の会社・synthetic・cycle・公開性不備、後続分類の unresolved による claimable/complete/queue 保留を確認。company 等の fault は coherent な snapshot binding を持つメモリ内破損 fixture として注入した。現在公開性訂正のテスト 1 件は既存 reader 境界への synthetic hook で、実公開性訂正経路の新設や IR 対応を主張しない。

monitor と wrapper の差は許可枝の status/reason と上記診断 field だけであること、trusted 枝の full JSON 一致を確認した。初回の新規テスト試行では分類追加 fixture が必須 job_id を欠いて 1 error となり、その fixture のみを修正した。最終ログはその修正後の実実行。

## 凍結範囲

編集前の production 完全 bytes は `before/src/ir_agent/qualitative_research.py`、SHA/bytes は `before-files.json`。差分は `implementation.diff`、凍結 SHA は `freeze.json`。追加テストは新規 file のため編集前 file は存在しない。

actual DB/登録/receipt・source の修正、新規 GET、外部送信、共有 docs 編集はいずれも 0。テスト内の receipt/分類/source 変更は架空メモリ DB の故障注入に限定する。既存旧 capture/producer/request は変更していない。actual DB の状態や SHA はこの担当では開いて再検証しておらず、root の管理に委ねる。
