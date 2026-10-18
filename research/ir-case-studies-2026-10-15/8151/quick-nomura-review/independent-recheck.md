# 8151 QUICK/野村：限定独立再点検

**76チェック成功、不一致0件**。provider HTML＋PDFの2GET保存、source2件、引用14件を確認した。新GET・DBアクセス・既存code/旧file変更・IR/モデル採用は0。

## バイトと経路

HTMLは既存Page parserでtitle/text/links等の全抽出fieldを再現、PDFは`pdftotext -layout`をstdoutへ再実行して保存本文と全bytes一致。PDFはapplication/pdf・`%PDF-`・実6,694,954bytes・16MiB未満・物理89頁。gzipされた保存entity bytesでありwire captureではない。Content-Lengthは保存headerに無く、値を補わない。

canonical jp:8151/full bundleのsource schema・common stableID・raw/transport/extraction SHAとcontentを確認した。source.retrieved_atは各本文完了（HTML10:11:28.014060Z、PDF10:11:43.240269Z）、published_atは両方null。表紙9月25日表示、HTTP Last-Modified、実取得を同一視しない。

旧公式snapshotのlinks[66]・SHA→provider HTML、provider実anchor[53]→PDF要求URLが一致した。同日保存www.nomura-ir.co.jp robots200のraw/SHA/本文を読み、今回2pathの固定UA許可を確認した。旧制限prefix `/ja/service/research/coverage_stocks/qnresearch/` は今も同じparserで禁止となる。今回の許可を全host許可に拡大していない。新robotsGET・www.toyo.co.jp GETは0。

引用14件のsource ID・頁内文字offset/原文が一致。producerの旧5input commitmentと、今回点検前後の19file SHA不変を確認した。generic verifierは**unknown2/mismatch0**のまま、局所チェックをgeneric matchedへ昇格していない。

## 指定意味の確認

指定されたp1/47/49/55/56/61/88/89の抽出本文と、追加の既存p41quoteを点検。表紙とp55は保存画像を視認した。全89頁の精読・画像確認とはしない。

- **EPS124.53**：p1は連26/9期予想、会社純利益2,600百万円を基にQUICKが算出するとの明記がある。著者独自の将来純利益予測ではなく、会社が同じEPSを公表したとも未確認。p88の分母はQUICKが日々算出する普通株発行済株式数（自己株式除く）で、普通株主に帰属しない配当の控除もある。表紙の別欄発行済株数（p88では自己株式含む）で安易に割り戻していない。
- **資本コスト**：p55の7.0%はCAPM株主資本コストの26年8月直近値。6.3%は直近12カ月平均。5.6%程度はグロス有利子負債を使うWACC概算で、別の役割を持つ。負債コストは25/9期利息と期首期末平均有利子負債。WACCの独立した厳密参照月や平均期間の開始終了日は確認していない。リスクフリー/プレミアム/βの数値データやAppendix2全体は再現せず、project割引率には採用していない。
- **倍率/目標**：p47の株価=EPS×PER、PBR=ROE×PERは過去推移の分解。表紙PER15.14は9/24の文脈、p49のPER16は26年8月31日の同業比較。いずれも公正PER・目標価格・目標期間へ変換していない。
- **著者/評価/報酬**：QUICK企業価値研究所、佐久間聰・園田三保、Not Ratedを表紙で確認。p88は会社/QUICK/野村IRの3社契約とスポンサー料、執筆者の非独立性を開示する。p89の証券非保有は文書の申告であり、保有や契約を独立照合した結果ではない。
- **事業情報**：p56の期ずれ/M&A、p61の期初会社計画据置や投資抑制/遅延/中国リスクは後のレポート記載。旧Astrisの個別案件や予測の成否を確認したことにはならず、正式会社資料の同版確認にもしていない。自己設定の確率・売却条件は無い。

確認範囲での目標価格等の未特定を、全89頁/全公開資料に存在しないという結論へ拡張しない。今回のバイト・引用・帰属の一致は、金融値の適合、予測の精度、DB初回保存/PITや投資適格性の確認ではない。
