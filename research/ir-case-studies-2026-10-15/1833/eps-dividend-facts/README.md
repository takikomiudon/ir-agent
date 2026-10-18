# 1833 公表EPS・年間配当予想の構造化候補

実抽出記録日時 2026-10-15T08:57:17.294500+00:00。原典は `ingest-bundle.json` の正式Q1短信、source ID `case-public:b3d7eae14ab4d5ea66c5b6161d9376583ea324c5bfb5946e98096f47ec0181ef`。原source snapshot・本文・取得時点・公表時刻nullをそのまま保持しました。

| 区分 | 原表示値（円/株） | 対象期間 |
| --- | ---: | --- |
| 基本EPS・実績 | 95.66 | 2026-04-01〜2026-06-30、Q1連結累計 |
| EPS・会社予想 | 428.91 | 2026-04-01〜2027-03-31、通期連結 |
| 年間配当・会社予想 | 300.00 | 2027年3月期、年間合計 |

表紙の連続引用は単位・期・実績/予想の行・基本/希薄化や年間合計の列を含めます。希薄化EPSのダッシュは数値にせず、Q1実績から年率化しません。前年配当297.00円を当期配当予想と混同しません。会社の通期業績予想は2026-05-15公表予想から変更なしという本文をscopeに逐語保存し、当該5月資料自体の独立確認はしていません。配当予想の最初の公表日が同じとは推定しません。

1833は従業員給付信託保有株の自己株式算入・四半期平均からの控除注記、および7月31日の譲渡制限付株式報酬自己株処分を通期EPS/配当予想へ考慮した会社注記をscopeへ保存しました。Q1平均株数を将来分母へ代入せず、EPSやDPSを再計算していません。

`request.json`を既存CLI parser/純粋dispatcherで処理し（実Store/DBなし）、`bundle.json`を作成しました。libraryで同時点replay・原典からのreproduce・DecimalとFractionの独立値確認を行い、原PDFのpdftotext-layout再抽出byte一致、保存表紙画像、引用位置・原raw/text/capture SHAも照合しました。結果は`validation.json`。derived IDは `disclosed-facts:cbcbb3a061e4b117782728462750f95eb85308bef6758e676d7be23777ea4148`。

数値・期・主体・単位・列の意味対応は抽出担当の主張であり、`financial_inputs_verified=false` / `meaning_review_required=true`。モデル採用、価格判断、IR質問、長期DPS/成長予測、point-in-time保証はありません。公表日へ遡及せず実レビュー時刻と派生取得時刻を保存し、最新性は未確認です。新GET・DB読書込・既存資料変更は0です。
