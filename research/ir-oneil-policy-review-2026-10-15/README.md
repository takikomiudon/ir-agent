# CAN SLIM / O’Neil公式方法の有限確認

公式本文の取得前に収集を止めたため、**entry/exit規則と本IR方式への適合は未確認**。記憶の数値・例外を規則として保存せず、日本株への採用・成績・既存方式との同一性も判定していない。

指定入口は `https://www.investors.com/how-to-invest/`。先に最新の[中央保留v2](../ir-source-access-holds-2026-10-15/README-v2.md)を照合し、このexact hostが旧6件にないことを確認した。`https://www.investors.com/robots.txt` を1GETし、2026-10-15 **11:48:51.455480 UTC**に本文受信完了。HTTP200・2509bytes、raw SHA `06cc6c122e3d105d743f33d3d2cbbc4a9ef248d756f1cd3323aded084a190f33`。開始・header受信・完了を[capture](capture.json)で分けている。HTTP Last-Modifiedは取得元のheaderであり、著者方法の公表日時ではない。

```text
User-agent: *
Disallow: /
```

この原文と固定UA `Codex-IR-Research/0.1` のliteral判定に基づき、入口・方法概要・売却規則の記事GETは0で終了した。名前付きUA向けの記載をこのUAへ移して許可扱いせず、UAを変更していない。原バイトのBOM/CRLFと逐語quoteの文字/byte位置は[quotes](quotes.json)、具体的な収集保留と限界は[access-guard](access-guard.json)を参照する。現在UAの設定とprepared headerは記録したが、wire headerの独立確認ではない。

最大4GETのうち未使用3GETを残した。再試行・redirect追跡・JS・認証/paywall回避・別site/転載/host・障害診断は0。この保存時点のexact-hostアクセス判断を、他hostの禁止・恒久禁止・銘柄の投資除外へ拡張しない。中央holdsの旧ファイルも変更していない。

[review.json](review.json)では売却range・例外・EPS成長条件・価格/相対強度/市場条件等をnullのまま区別する。会社の公表会計定義の確認と投資家側の売買/保有条件を別に扱うのはプロジェクトの工程上の区別で、今回確認できたO’Neilの規則ではない。IR質問・数値モデル・financial rule採用・DB操作・code変更・順位付け・送信は0。

[validation.json](validation.json)はraw/quote/時刻/予算/旧入力hashの有限照合。パスは原則repo root相対、captureのraw_fileだけはこのdirectory相対。本文未取得を本文不存在や方法の不適合と扱わず、このアクセス制約と未確認の範囲で完了する。
