QuantConnect/Research公式公開repoの現在default branchを、GitHub REST APIで有限確認した。**指定名前条件の候補は0件**で終了。一般的な財務factor/stock-picking notebookへ条件を広げず、blobは取得していない。

- robots完全受信404・JSON106bytes。既存docs/data-sources.md:22のmissing-robots手順を使用し、JSONを規則や明示許可とは扱わない。
- repo metadata200：full_name QuantConnect/Research、private:false、default_branch master。返却されたtrees_urlのテンプレートへ返却branchを適用。
- recursive tree200：root tree object SHA `d89cf67bc37bc032f0de47089e16d825bcd8a65f`、truncated:false、60entry。commit SHAや全履歴を取得した意味ではない。
- Graham / NetNet・net-net・net_net・net net / NCAVの名前を大小文字非依存で照合し、該当entry0。買い/売り/保有期間/日本株への定義依存は未確認で、LLM記憶の数値規則を補わない。

metadataにApache-2.0の表示があるが、LICENSE本文・候補fileの許諾範囲は未確認。root tree内にLICENSEがあっても、このphaseの残り予算を追加取得へ使い切らない。採用・vendoring・コード実行は0。

[選定記録](tree-selection.json)、[原レスポンスcapture](capture.json)、[終了記録](outcome.json)、[検証](validation.json)を保持。新GET3/上限4、未使用1、blob0。再試行・redirect・host/UA変更・Cloud診断・別repo探索0。API routeの最初のローカルtemplate展開に切取り誤りがあり、GET前にliteral token置換へ修正した（誤URLへのGET0）。

確認結果は取得時点のmasterの名前に限る。file内容・過去履歴・別branch/別repoに実装がないとの証明ではない。保存research/docs/third_partyの事前検索では同repo/API経路の既存試行は未特定だったが、全raw-only履歴の不存在は認定しない。実DB・現SRC・共有docs・売買・外部連絡変更0。
