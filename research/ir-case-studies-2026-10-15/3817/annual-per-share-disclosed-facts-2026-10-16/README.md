# 3817 年次連結EPS・BPSの直接公表値2件

既存normalize-facts CLIで、保存済み年次短信の**連結実績EPS443.34円とBPS2659.88円**だけをfile-only正規化した。原表示は443.34／2,659.88、列ラベルは「円 銭」、canonical unitはJPY-per-share。443円34銭という複合表示へ作り替えず、既存のdecimal token・円単位契約を使用した。conceptは既存契約の非空stringであり、未存在のconcept enumを作っていない。

EPSは2025-04-01～2026-03-31のannual duration、BPSは2026-03-31のfinancial-position instant。両方のbasis_quoteに同一年度の連結業績・財政状態の見出し、対象日付、単位、該当行をそのまま保持した。instantの期末対応、列・普通株/連結scopeはreviewer assertionを保持し、mechanical normalizerが意味認証したとはしない。既読物理2/9/18の株数・親会社利益・普通株EPS注記へのcontext参照も固定。個別EPS253.08/BPS699.68、会社予想EPS435.34、親NI÷丸め株数の再計算は入力していない。

normalized-bundleは**既存原source1本（全19頁content・同ID/nativeSHA/取得時刻のまま）＋派生source1本（2facts）**。会社/thesis更新は空。原sourceの単なる再同梱を新原典と数えず、derived取得時刻を5月の公表日や元PDF取得時刻へ戻さない。正常利益・現在株式basis・Graham method適合/数値採用・現在価格はいずれも認証していない。financial_inputs_verified:false／meaning_review_required:trueのまま。

CLIはStoreを構築しない既存file command。入力・出力・引用offset・nativeSHAを検証し、保存済みderived.retrieved_atをnowにした純関数再現でbundle完全一致。rawSHA、contentSHA、native models.json_text SHAと、normalizerのcompact canonical_json original_snapshot_sha256は別のハッシュとして保持した。再現時に実DBへのingestはしない。

GET・DB/Store変更・共有/旧file編集・新しい頁の意味読解・金融採用・IR送信は0。原19頁sourceと旧28pinsを不変のままfreezeし、rootの原本＋派生一括保存を待つ。
