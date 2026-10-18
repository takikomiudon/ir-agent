# 保留157社のIR受付再調査

集計時点: 2026-10-13T01:04:09.441433+09:00。前回保留した157社に限定して再調査し、全社の再取得結果と保存ページを点検した。未試行企業は0社。

| 結果 | 社数 |
| --- | ---: |
| 公式企業本文を復旧 | 27 |
| うちIRメール・フォームの確認済み候補に追加 | 11 |
| 本文は復旧したが一般IR受付の確認・条件で候補にできない | 16 |
| 公式企業本文の取得・解析がなお保留 | 130 |

全3,686社の累計で、IRメール・フォームの確認済み候補は **1819社**、うち個人受付の明示は **343社**。本文復旧は自社名とIR情報・公式IR導線等を根拠に判定し、受付確認とは分けた。

- [157社すべての今回結果](recovery-companies.csv)
- [今回追加した窓口候補](new-contact-candidates.csv)
- [まだ取得エラーで保留する企業](held-error-companies.csv)
- [更新した全社一覧](all-companies.csv) / [全窓口候補](contact-candidates.csv) / [個人受付の明示](individual-contact-candidates.csv)
- [URLごとの試行結果](url-attempts.csv) / [集計](summary.json) / [検証](verification.json)

## 今回追加した窓口

| コード | 企業 | 窓口 | 確認先 |
| --- | --- | --- | --- |
| 2345 | ＨＯＤＬ１ | form | https://hodl1.jp/contact/ |
| 3774 | インターネットイニシアティブ | email | https://www.iij.ad.jp/contact/ |
| 3810 | サイバーステップホールディングス | form | https://cshd.cyberstep.com/cshd/ir/inquiries/ |
| 4816 | 東映アニメーション | form | https://reg18.smp.ne.jp/regist/is?SMPFORM=mjs-ldrhth-01b398bc831c18d43ff53a577c10e3cd |
| 5891 | ＳＡＫＩＧＡＫＥホールディングス | form | http://www.sakigake-holdings.co.jp/contact/ir/ |
| 5988 | パイオラックス | form | https://www.piolax.co.jp/jp/shareholder/contact/form02/ |
| 6183 | ベルシステム２４ホールディングス | email | https://www.bell24.co.jp/ja/inquiry/ |
| 7460 | ヤギ | form | https://www.yaginet.co.jp/form/ja/contact3/inquiry3.html |
| 7864 | フジシールインターナショナル | form | https://www.fujiseal.com/jp/contact/index.html?お問い合わせ件名=IR（投資家情報）について |
| 7931 | 未来工業 | form | https://info.mirai.co.jp/ir-otoiawase |
| 9729 | トーカイ | form | https://www.tokai-corp.com/contact/entry.php |

## 確認方法と限界

前回の取得先を全157社について一度再確認し、文字コードやHTML解析で失われた本文は保存した原文から回復した。公式ページの実リンク・実転送、公開索引に掲載された移転候補を追い、移転候補は企業サイト自身で同定した。入力画面やメールの金融IR用途、返信用の欄、利用条件を確認した。問い合わせの送信は0件。

403・robots取得拒否・TLS失敗などは迂回せず保存した。取得できないことを窓口不存在とは判定していない。JSでのみ描画されるフォーム、一般消費者用、株主優待・株式事務だけのフォームは一般IR質問の確認済み候補に数えない。個人受付の明示がない場合は not_stated とし、個人からの回答実績は未検証。

`official_url` は前回の登録URLを残し、`verified_issuer_urls` に今回同定できた公式ページを記録した。引用・フォームの入力欄・取得日時・原文は evidence/ と raw/、各担当のレビューに保存。前回の[結果](../ir-intake-completion-2026-10-12/README.md)と元資料は保持した。公開索引は有限の取得範囲であり、全ウェブ上の別経路を尽くしたという意味ではない。
