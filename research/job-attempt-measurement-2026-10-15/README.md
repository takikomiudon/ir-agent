# ジョブ試行計測の標準参照

OpenTelemetry公式のTrace APIとCommonの2 URLを各1 GET取得し、どちらもHTTP200。redirect追従・再試行・追加検索は行っていない。取得時刻、原バイト・抽出本文のSHA-256、7箇所の逐語引用は [sources.json](sources.json) に保存した。

Trace APIのSpan lifetimeが開始・終了・イベントの時刻を説明し、Commonは属性の型・キーと更新を説明する。Commonに独立したTime節はなかったため、その内容を確認済みとは扱わない。

この標準が提供するのは計測の語彙であり、lease経過をactive分析時間に変える規則や会社数の上限ではない。本プロジェクトの不変イベント・SQLiteトランザクション・capacityへの接続は [設計案](../../docs/job-attempt-measurement.md) で区別する。SDK導入、実ジョブ計測、モデル呼出、費用推定は行っていない。
