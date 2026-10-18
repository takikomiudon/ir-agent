# Anthropic DD面談準備：質問の組立て手順の候補

固定commit `574ed3624aebd0418c7e96cd101262f30210ab26` の公式recursive treeを取得し、609entry・`truncated:false`、指定path一致のSKILL.mdを5件確認した。複数一致のためrootへpathを返し、選択を待ってからprivate-equityの `dd-meeting-prep` 1件だけを取得した。他4件は未読。**fresh API robots404＋tree200＋literal blob200の計3GETで終了**し、追加探索はしない。保存済み旧treeの成功要約やarchiveの選択path22件を、完全tree本文の代わりにはしていない。

原文は[dd-meeting-prep-SKILL.md](dd-meeting-prep-SKILL.md)。質問準備の研究資料として読み、実行技能としてロードしていない。CIM・data room・顧客機密の要求や買収手続き、身体反応の評価は日本上場株のメールIRへ移さない。会議向けの質問数・所要時間もメール運用の制約にしない。

既存4技能に追加参照できる具体手順は、①既知情報・懸念・今回学ぶ目的を先に整理し優先質問へ対応させる、②非誘導の広い問いから必要な期/範囲/定義の具体確認へ進む、③資料間の特定の不一致とfollowupを対応させて短い準備文書へまとめる、の3点。公開済み事項を再質問する理由にはせず、未確認だけを質問価値と扱わない。原著は対面企業DDを主対象としており、このメールIRへの適応自体はproject判断となる。

回答分岐、曖昧・無回答の処理、返信からEPS/CFを変える規則、買い/売り条件やIR効果の実証は本文にない。したがって既存の事前分岐・公開性・未採用入力の保留を維持し、数値を埋めない。今回は意味ある手順差分の候補を得た段階で、採用・実装・実IR質問登録は行っていない。

[source-reference.json](source-reference.json)は正確なAPI URL・受信完了・raw/decoded SHA・固定commitを、[tree-selection.json](tree-selection.json)は5候補とroot選択を保存する。decoded4331bytesはtree/APIのGit blob SHAと一致した。既存root Apache-2.0 LICENSEのbytesも固定treeのLICENSE blob SHAと一致し、[license-reference.json](license-reference.json)へ参照を固定した。個人作者は本文に明記されていない。公開時刻は不明のまま、UAは設定/prepared requestの記録でwire認証ではない。

具体的差分と移植しない部分は[review.json](review.json)、必要最小の逐語引用・位置は[quotes.json](quotes.json)。新GETは3だけ、実DB・code・共有docs・third_party原文の変更・外部送信は0。原文内に書かれた行為は実行していない。
