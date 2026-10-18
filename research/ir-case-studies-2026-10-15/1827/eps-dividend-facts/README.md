# 1827 公表EPS・年間配当予想の構造化候補

実抽出記録日時 2026-10-15T08:57:17.207072+00:00。原典は `source-bundle.json` の正式Q1短信、source ID `case-public:74e73ca9b427ed424b5ac315ff8c47b12e596412c6a31802fe52eede57e16e41`。原source snapshot・本文・取得時点・公表時刻nullをそのまま保持しました。

| 区分 | 原表示値（円/株） | 対象期間 |
| --- | ---: | --- |
| 基本EPS・実績 | 25.18 | 2026-04-01〜2026-06-30、Q1連結累計 |
| EPS・会社予想 | 84.39 | 2026-04-01〜2027-03-31、通期連結 |
| 年間配当・会社予想 | 25.00 | 2027年3月期、年間合計 |

表紙の連続引用は単位・期・実績/予想の行・基本/希薄化や年間合計の列を含めます。希薄化EPSのダッシュは数値にせず、Q1実績から年率化しません。前年配当38.00円を当期配当予想と混同しません。会社の通期業績予想は2026-05-14公表予想から変更なしという本文をscopeに逐語保存し、当該5月資料自体の独立確認はしていません。配当予想の最初の公表日が同じとは推定しません。

1827の当期年間配当合計は25.00円で、前年の38.00円ではありません。EPS予想と配当合計の意味を区別し、配当性向や成長率を独自算定していません。

`request.json`を既存CLI parser/純粋dispatcherで処理し（実Store/DBなし）、`bundle.json`を作成しました。libraryで同時点replay・原典からのreproduce・DecimalとFractionの独立値確認を行い、原PDFのpdftotext-layout再抽出byte一致、保存表紙画像、引用位置・原raw/text/capture SHAも照合しました。結果は`validation.json`。derived IDは `disclosed-facts:4c18006d4a191405174e5f7c9f616956f30eece2acd30e0fa7ee32068dfa3fa2`。

数値・期・主体・単位・列の意味対応は抽出担当の主張であり、`financial_inputs_verified=false` / `meaning_review_required=true`。モデル採用、価格判断、IR質問、長期DPS/成長予測、point-in-time保証はありません。公表日へ遡及せず実レビュー時刻と派生取得時刻を保存し、最新性は未確認です。新GET・DB読書込・既存資料変更は0です。
