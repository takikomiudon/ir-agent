# 1870の追加読解を次の正当なjobへ引き継ぐ

現行native packetは追補ファイルを自動認識しない。既存のworker引継ぎ→正当なjobの5項目結果→次版prior_reviewを優先できるため、今回のための新APIは不要とする。ただし、現時点でnativeへ保存済みになったとは報告しない。[worker-handoff.json](worker-handoff.json)に次担当へ渡す固定file/SHA・原source・既知/未解決・結果へ残す事項を用意した。この票はAPI入力でも未実行のjob結果でもない。

## 確認できた挙動

保存されたcase v2/config1は5source既読、直前jobは`qualitative-de2c7163f29747f560ce3758`（完了01:26:38 UTC）。追補read_atは01:34:19 UTCなので、その旧case文書と旧結果に追補がないのは時系列どおりである。原source `case-public:08da739…` はすでに既読だが、資料単位の既読は全14頁読了を意味しない。これは保存artifactとコードの静的追跡であり、現DB照会・新jobの実行による再現ではない。

| 経路 | 現行の処理と1870への影響 | 根拠 |
|---|---|---|
| queue | 当該社の公開sourceを調べ、未既読IDまたは実管理日の到来だけを起点にする。既読原典の12/13頁を後から読んだこと自体はtriggerではない | `src/ir_agent/qualitative_research.py:302–323` |
| packet | `sources`はpendingだけ、`case_snapshot`は保存case、`prior_review`は直前完了jobから作る。任意の会社フォルダは探索しない | 同`:136–161,333–345` |
| worker view | 固定case文書・参照とpending source・prior_reviewを投影するだけ。今回の追補を自動追加しない | 同`:106–134` |
| 完了 | pending全件をちょうど1回。旧原典を追加source_reviewへ入れると拒否し、観測evidenceもpending IDだけ。summary/rationaleは既存文字列欄なので日付付きの既知文脈を記録できる | 同`:414–475` |
| 次回への保存 | completeが版を追加しlast_review_idを更新。次のprior_reviewはsummaryとcase_observationを渡すが、source_reviewsの説明全文は渡さない | 同`:157–172,495–507` |
| 改版/保護 | 真の条件改版はCAS付きregisterだが、設定改版はlast_review_idをリセットし既読も明示再引継ぎになる。追補だけのための偽configには使わない。凍結fileの上書きはcase_file_changed/claim拒否へつながる | 同`:203–210,235–274,385–400` |

既存テストも「次packetは新sourceだけ/元case不変/直前観測SHAを保持」を確認する（`tests/test_qualitative_prior_review.py:16–29`）。「原文引用と全件処理」「完了結果不変」「期限到来でretain拒否」「case/job/attemptの原子的完了」は`tests/test_qualitative_research_integration.py:140–189`と`src/ir_agent/harness.py:293–304`。このタスクではテストを追加・実行していない。

## 具体的な既存経路

rootは次の**実際の新着または既存2027-01-16 Asia/Tokyo管理日**のjobを待ち、権限あるworkerへauthoritative packetと引継ぎ票/追補3fileを明示して渡す。旧jobを再完了せず、当時のpacketへ追補を後付けしない。workerは当時から公開されていた原典の追加読解と、新しい会社公表を区別する。

公表済みの現金対価/取得原価2,500百万円、取込05-01〜06-30、暫定のれん3,398百万円等は既知欄へ移す。04-01実施と05-01みなし取得を統合しない。取得CF純額/支払日、費用のPL科目/税、最終PPA、前年同一範囲寄与は残る。期首取得仮定の影響省略は0ではなく、取得対価と旧管理事業譲渡益1,000百万円も別取引である。正式IR問を今作らず、次の準備時にこれらの既答を除外する。

結果の**summaryとcase_observation.rationaleの両方**に追補の時刻・path/SHA・原source/native SHAと解消/残余の要旨を残す。source_reviewsだけへ書くと次のprior_reviewには要旨が出ない。pendingのquote/evidenceと、旧原典の補足文脈は区別する。旧IDをevidenceへ足したり新pendingの引用と偽ったりしない。管理日だけのjobならpending/ source_reviews/ evidenceは空になり得るため、旧資料だけを根拠にsupports/counterevidenceへ昇格させない。future outcomeや新管理日は今回決めない。

この完了後、次版のprior_reviewには保存されたsummary/観測が引き継がれる。ただし外部票を読むことやrefの存在は自動保証されない。現在のコードは、観測文字列中のfile/SHAをtyped evidenceとして凍結・再検証しない。rootの明示引継ぎと完了前の内容確認が必要であり、**nativeの結果SHA保証と、追補資料の機械的受領保証は別**である。

Anthropic DDの既知情報/懸念・資料差分とfollowup（`third_party/anthropic/skills/dd-meeting-prep/SKILL.md:10–21,70–76,87–100`）、JIRAの企業向け指針を公開先行へ適応した手順（`docs/ir-question-preparation.md:5–15,23–31`）、追加読解のfile-only境界（`docs/research-stage-monitoring.md:26–40`）に沿う運用提案であり、原著者がこのDBの経路を定めた意味ではない。新source化・管理日前倒し・source分類を追加意味レビューの代用にする処理は採らない。元case/result/原典・共有doc/コード/DBは不変、GET0。
