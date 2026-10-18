# 6754：指定7公表値のfile-only構造化

**3実績＋4会社予想だけ**を既存normalize-factsで構造化した。会社公表値であり、著者独自予想・金融意味検証済み・モデル採用ではない。原presentation source/ID/本文/metadata/取得時刻は完全保持し、原値と派生抽出sourceを分けた。

| 原頁・概念 | 原表示（億円） | 正規化JPY | kind |
|---|---:|---:|---|
| p6 通信計測Q1売上高 | 194 | 19,400,000,000 | reported_fact |
| p6 通信計測Q1営業利益 | 32 | 3,200,000,000 | reported_fact |
| p9 通信計測Q1受注高 | 336 | 33,600,000,000 | reported_fact |
| p12 連結通期売上高 | 1,400 | 140,000,000,000 | issuer_guidance |
| p12 連結通期営業利益 | 200 | 20,000,000,000 | issuer_guidance |
| p12 連結通期税引前利益 | 200 | 20,000,000,000 | issuer_guidance |
| p12 連結通期当期利益 | 150 | 15,000,000,000 | issuer_guidance |

単位換算は既存の億円→JPY×100,000,000。桁を増やす換算は丸め前の精密金額を得たことではない。p6の各欄四捨五入と費用/消去注記を保持し、通信segment利益を連結NI/EPSにしない。p9の336は原図の青色通信計測series/右端FY2026 1Qで確認した位置で、受注≠売上。p9にはIFRS表記がないためaccounting_standard:null。前倒し比率・取消・売上化時点等は未確認で、別頁IFRSを受注へ貼り付けない。

p6/p9はFY2026 1Q・4–6月を逐語labelとして保持し、日本語2027年3月期第1四半期という資料labelと並べた。p12は2027/3期通期予想。正確な期首/期末日は原表記から補完しない。p6/p12は同じ原文quote内にIFRS・単位・対象列/期を保持。p12当期利益を親会社帰属利益に強めず、四捨五入と4月27日公表値から据置を明示。会社予想を独立著者予測にしない。

`input.json`が既存CLI契約の入力、`normalized-bundle.json`が実CLI main/parser/dispatchの出力。実行中はStoreとsqlite3.connectを失敗ガードし、両呼出0を確認した。:memory:も作っていない。抽出review.authorはCodex、会社予想の主体はアンリツで別。元sourceのHTTP本文完了14:13:32.155129UTCと、今回の実review/派生retrieved時刻、未登録のDB first_savedを区別する。

同一引用内の値/単位/期token、原図の列対応、原文Unicode半開offset（保存改行保持）を記録。APIの全bundle replay、既存reproducer、独立Decimal算術、原source/全旧artifact不変はvalidation.jsonへ保存。機械一致は意味/表の列/期/範囲の独立認証ではなく、financial_inputs_verified:false・meaning_review_required:trueのまま。

モデル入力・著者条件比較・確率/株価/倍率/税率/将来EPS・新IR質問/送信・実DB・index・監視・code・旧files変更は0。この4fileを固定し、以後編集しない。
