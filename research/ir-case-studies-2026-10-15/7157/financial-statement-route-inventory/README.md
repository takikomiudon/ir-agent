7157の指定保存3件（04 FAQ・02 IR入口・05お問い合わせ）だけを点検した。05.jsonはnewsではなくcontact.htmlであり、別snapshotへ広げていない。新GET・実DBアクセス・既存編集0。

この保存範囲では、年次連結IFRS/日本基準個別の正式財務原本への直リンクは未特定。唯一の候補はFAQのliteral「決算短信」index：

`https://ir.lifenet-seimei.co.jp/ja/ir/library/results.html`

04.jsonのlinks[60]で、rawhref `/ja/ir/library/results.html` と保存resolved URLの両方を保持する。index本文は未読で、年次/連結/個別の収録を確認したとはしない。「IR資料」「配当」は資料・方針ページの導線として保持し、正式財務原本へ昇格しない。02.jsonの月次業績速報・資本コスト方針・人事PDFも会計/配当bridge資料に選ばない。

rootの次phaseはfresh exacthost robots→許可時このindex1GET→literalな適切原本が特定できた場合のみ原本1GET、合計最大3GET。PDF意味最大3頁/HTML最大3block。redirect・denial・TLS・同host保留で停止し、自動fallback・旧失敗TOP再GET・URL/API/JS推測0。indexの先でも原本が未特定なら有限終了する。

[route-inventory.json](route-inventory.json)へ旧JSONのSHA、href/index/label、引用offset、非選定理由、未確認範囲を固定した。[validation](validation.json)は保存導線の機械照合のみ。会社が資料を公開していないとの結論ではなく、モデル適合・資本余剰・投資判断も認定していない。
