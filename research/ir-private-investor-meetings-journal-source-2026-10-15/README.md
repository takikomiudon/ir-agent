# 個別面談論文の掲載誌：robotsで有限停止

**`www.journals.uchicago.edu` のfresh robotsにAI個別禁止を確認し、掲載ページ取得前に停止した。** GETはrobotsの1回だけで、残り2回を使っていない。本文の効果・方法・因果・日本の個人メール/フォームIRへの適用は今回未点検。

rootが選択したliteral掲載頁は `https://www.journals.uchicago.edu/doi/10.1086/684038`。Crossref journal recordのresource.primary.URLそのままで、選択元・JSON位置・SHAを[guard.json](guard.json)へ固定した。これは既存書誌の参照であり、今回の公式掲載頁から題名・著者・版を再確認した意味ではない。CrossrefのSSRN要旨を掲載版の内容として代用していない。

## 停止の原文と解釈

fresh robots `https://www.journals.uchicago.edu/robots.txt` はHTTP200、完全820bytes。該当groupは次の通り（生成引用は計5英語words相当未満）。

```text
User-agent: GPTBot
Disallow: /
```

原文byte/SHA、UTF8文字・byte offsetは[robots-rule-check.json](robots-rule-check.json)にある。Python標準RobotFileParserでは、設定UA `ir-agent-public-research/0.1` とwildcardの選択掲載URLへのcan_fetchはともにtrue、GPTBotではfalse。**GPTBotという名称が設定UAにliteral一致するとは述べない。wildcard全面禁止でもない。** 既存docs/data-sources.md:20と中央索引が区別している「AI個別禁止を受けた運用保留」を適用し、名前の非一致を使って先へ進めず有限停止した。UA変更はしていない。

HTTP403やrobots取得失敗による規則未知とは別の停止である。掲載頁のHTTP状態・会員限定/無料公開・PDF link・利用条件は未確認。今回の停止は論文が存在しない、本文非公開、個人IRに効果がない、投資対象外、他subdomainも禁止という結論ではない。exact hostの中央索引更新はrootへ引き渡し、本担当は共有索引を編集していない。

## 証跡と限界

[robots-capture.json](robots-capture.json)とraw entityを保存し、raw SHAは `821d8bfdedf96d4b1f86db2590302e0c743d1ca6fe782c4b38ecc6eca27f275c`、byte数820を再照合した。完全entity受信終了のローカル観測は **2026-10-15T23:27:25.818422+00:00**、HTTP呼出し終了は2026-10-15T23:27:25.828400+00:00。retrieved_atの申告時刻とは区別する。requests.iter_contentのresponse entityで、content-decodedの場合がありwire転送bytesではない。UAは既存collectorの設定で、wire上の独立確認はない。

中央holds-v7の11 exact hostにこのhostは含まれなかった。新停止の後続GET・再試行・redirect追跡・別host・UA変更・JS・Cloud診断・認証・課金・本文制限回避は0。code・実DB・共有file・外部送信・金融値採用も0。[outcome.json](outcome.json)と[validation.json](validation.json)に結果、quote offset、関連sourceとartifactのSHAを保存した。この有限調査を終了する。
