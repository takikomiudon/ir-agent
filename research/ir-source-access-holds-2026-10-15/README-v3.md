# 収集保留索引 v3：保存済み7 exact host

[holds-v3.json](holds-v3.json) は [v2](holds-v2.json) の**旧6entryをJSON値として完全保持**し、`www.investors.com`を1件だけ追加した。旧ファイルやAGENTS／roles／ongoing等の入口は変更していない。新GET・DB・code・金融判断・IRは0。

旧6hostは`contents.xj-storage.jp`、`ssl4.eir-parts.net`、`web.fisco.jp`、`sharedresearch.jp`、`www.toyo.co.jp`、`www.xj-storage.jp`。理由・UA・原引用・時刻・不確実性はそのままで、区別は[README-v2](README-v2.md)を参照する。今回、旧6entryの原点検を再実行したという主張はない。

追加根拠は[O’Neil資料確認のaccess-guard](../ir-oneil-policy-review-2026-10-15/access-guard.json)。実取得originは`https://www.investors.com/robots.txt`、HTTP200・2,509bytes、本文完了は **2026-10-15T11:48:51.455480UTC**、原raw SHAは`06cc6c122e3d105d743f33d3d2cbbc4a9ef248d756f1cd3323aded084a190f33`。

```text
User-agent: *
Disallow: /
```

BOMとCRLFを保持した原rawについて、この引用の文字位置17–43・byte位置19–45（いずれもend exclusive）を独立照合した。固定UA`Codex-IR-Research/0.1`とprepared request header、実capture・原origin・開始／headers／完了時刻、access-guardのSHAを結び付けた。wire headerの独立確認ではない。名前付きUA向けの別規則を現在UAへ移して許可扱いせず、UAを変更しない。

予定していた`/how-to-invest/`は固定UAで禁止と判定され、元案件はrobots1GETのみ、入口／方法／売却規則の記事GET0、未使用3GETで停止した。この索引作成自体はGET0である。著者の投資規則・日本株への適合・成績は未確認のままで、記憶の数値を金融方針へ補わない。Last-Modifiedも方法の公表日時ではない。

workerはexact hostで保存制約を照合し、停止した要求の自動再試行、UA変更、別host／転載・JS・障害診断による回避をしない。この保存時点の収集制約を他host・恒久禁止・銘柄の投資除外へ一般化しない。利用者のドメイン許可はサイトrobots確認免除ではなく、旧取得・分類への後付けの無効判定もしない。runtime guardは新設していない。

[validation-v3.json](validation-v3.json) は25有限チェック成功・不一致0。旧6entryのcanonical JSON列のSHA一致、中央旧6ファイルとO’Neil旧8ファイルの不変、raw／quote／UA／origin／時計／data未取得の対応を保存した。追加はv3のJSON・README・validationの3ファイルのみ。
