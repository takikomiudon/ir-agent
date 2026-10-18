# 完了バッチ7〜9の最終URL重複点検

2026-10-11の完了バッチ7・8・9を保存資料だけで点検した。180回の企業調査（177社）のうち、異なる入力URLが同じ正確な最終URLへ到達したものは8社・8組・16入力URLだった。再度の最終本文GETは8回で、実GET総数1,157回の約0.69%。この範囲では、重複取得が負荷の主因という説明は支持されない。収集ループの改修は提案しない。

8組のうち7組は保存本文のSHAも一致した。残る3543は本文SHAと抽出テキストが異なる。8回は観測できた最終本文の再GET下限であり、8回すべての安全な省略を保証しない。後続captureの別名URLへのredirect GETが4回付随するが、その4回まで事前に削減可能とは断定しない。

| バッチ | 対象UTC時刻 | 企業調査回数 | 一次snapshot | 実GET（事前確認込み） | 重複組／再本文GET | 本文SHA一致の再GET |
|---|---|---:|---:|---:|---:|---:|
| 7 | 08:05:51〜08:15:51 | 60 | 287 | 380 | 2／2 | 1 |
| 8 | 08:17:28〜08:35:09 | 60 | 256 | 372 | 4／4 | 4 |
| 9 | 08:35:14〜09:00:26 | 60 | 291 | 405 | 2／2 | 2 |
| 合計 | 08:05:51〜09:00:26（区間間の休止は別） | 180 | 834 | 1,157 | 8／8 | 7 |

3区間はすべてcompleted、共通transport 503は0。企業固有の失敗がなかったという意味ではない。各区間のseed、stdout、collection-run、選択した企業recordのパス・読取時SHA・対象attemptの時刻とfetches、834一次snapshotのファイルSHAを[固定JSON](adaptive-canonical-url-duplication.json)へ保存した。recordは実行区間内に開始・終了したattemptを選び、同じ企業の前後attemptを混ぜない。7件は参照されたarchiveを使用した。現行recordは後続監査で更新され得るため、使用した時刻・fetchesの値もJSONに固定している。検算時に11現行recordのファイルSHAが他の並行監査で変わっていたが、本分析に使用した会社・時刻・GET数・fetchesは11件すべて一致した。

| コード／会社 | 入力URLの相違 | 正確な最終URL | 原snapshot | 本文SHA比較 |
|---|---|---|---|---|
| 3543 コメダホールディングス | wwwあり／なし | `https://komeda-holdings.co.jp/` | [01.json](../evidence/3543/20261011T081012205063Z/01.json)・[02.json](../evidence/3543/20261011T081012205063Z/02.json) | 異なる（抽出本文も差あり） |
| 3583 オーベクス | /ir/ と /ir | `https://www.aubex.co.jp/ir/` | [02.json](../evidence/3583/20261011T081350061423Z/02.json)・[05.json](../evidence/3583/20261011T081350061423Z/05.json) | 一致 |
| 3663 セルシス | /irinfo_faq/ と /irinfo_faq | `https://www.celsys.com/irinfo_faq/` | [04.json](../evidence/3663/20261011T082515822557Z/04.json)・[05.json](../evidence/3663/20261011T082515822557Z/05.json) | 一致 |
| 3692 ＦＦＲＩセキュリティ | /contact と /contact/index.htm | `https://www.ffri.jp/contact` | [03.json](../evidence/3692/20261011T083150361097Z/03.json)・[06.json](../evidence/3692/20261011T083150361097Z/06.json) | 一致 |
| 3695 ＧＭＯプロダクトプラットフォーム | /contact/inquiry と /contact | `https://gmo-research.ai/contact/inquiry` | [03.json](../evidence/3695/20261011T083232391201Z/03.json)・[04.json](../evidence/3695/20261011T083232391201Z/04.json) | 一致 |
| 3698 ＣＲＩ・ミドルウェア | /contact/prir.html と /contact/form/?fid=prir | `https://www.cri-mw.co.jp/contact/form/?fid=prir` | [02.json](../evidence/3698/20261011T083401331303Z/02.json)・[04.json](../evidence/3698/20261011T083401331303Z/04.json) | 一致 |
| 3753 フライトソリューションズ | /ir/contact と /ir/contact/ | `https://www.flight.co.jp/ir/contact/` | [05.json](../evidence/3753/20261011T084032295405Z/05.json)・[06.json](../evidence/3753/20261011T084032295405Z/06.json) | 一致 |
| 3772 ウェルス・マネジメント | 公開HubSpot遷移URL と 直接form02 URL | `https://www.wealth-mngt.com/contact/form02?hsCtaAttrib=318986091223` | [04.json](../evidence/3772/20261011T084440359423Z/04.json)・[05.json](../evidence/3772/20261011T084440359423Z/05.json) | 一致 |

3543は08:10:45.574975UTCと08:10:52.242383UTCの2 GET。同じ最終URLでも保存本文は359,633 bytesと359,734 bytes、抽出テキストのブランド表記はそれぞれ「ジュリコ堂」「ジェリコ堂」だった。原snapshotの本文SHA・抽出テキストSHA・正確な引用をJSONへ残した。原bytesは保存されておらず、変更・cache・配信先などの原因は決められない。

最終URLのqueryは同一性に含めた。queryだけが違う同一pathの8組は診断例として別途保存し、重複件数には加えていない。次の例では用途と本文SHAも異なり、queryを落とすとIR窓口と一般・製品窓口を混ぜる。

| コード | query相違 | 原タイトル | 原snapshot |
|---|---|---|---|
| 3687 | `type=ir` | IR Inquiries \| Fixstars Corporation | [02.json](../evidence/3687/20261011T083049996607Z/02.json) |
| 3687 | `なし` | Contact Us \| Fixstars Corporation | [03.json](../evidence/3687/20261011T083049996607Z/03.json) |
| 3698 | `fid=prir` | IR・広報に関するお問い合わせ \| CRI Middleware | [02.json](../evidence/3698/20261011T083401331303Z/02.json) |
| 3698 | `fid=game` | お問い合わせ：ゲーム（音声・映像・リップシンク等） \| CRI Middleware | [07.json](../evidence/3698/20261011T083401331303Z/07.json) |
| 3837 | `id=ir` | IR情報に関するお問合せ - アドソル日進 | [03.json](../evidence/3837/20261011T085619267237Z/03.json) |
| 3837 | `id=company` | アドソル日進に関するお問合せ - アドソル日進 | [05.json](../evidence/3837/20261011T085619267237Z/05.json) |

実GETと再掲metadataを区別した。`http_get_attempted:true`、実送信開始の`http_get_started_at`、実URLを使って区間内の保存nodeを照合し、本文795回、本文redirect77回、robots226回、robots redirect12回の計1,110回を再構成した。cached robotsなどの同じ実GETの再掲646箇所は追加GETとして数えていない。ローカル停止・取得未着手も除いた。HTTP Dateや従来のretrieved_atは送信時刻に代用しない。

collection-runが報告する1,157 GETは事前確認3回と企業調査1,154回。保存nodeから再構成できた企業調査1,110回との差44回は、返却captureの保存範囲だけでは実GET全体を復元できない範囲として残す。途中originのrobotsが返却metadataに残らないことはあり得るが、差44回の原因をすべて特定したわけではなく、重複にも算入しない。割合の分母にはcollection-runの実GET総数を使う。

snapshotのファイルSHAは保存JSON bytesのハッシュ、本文SHAは保存source.sha256（charset decode前の応答content）である。Requestsで展開されたcontentである可能性があるため、圧縮された通信bytesと同一とは扱わない。検算で9バッチ入力ファイル・834一次snapshot・7archiveのSHA、対象時刻、集計合計を再確認し、原sourceから独立に組み直した重複8組も一致した。

追加GET、元record／snapshot／収集コードの変更はすべて0。本点検は3完了バッチの限定標本であり、全母集団・障害時・まだ保存されていないGETについての結論ではない。
