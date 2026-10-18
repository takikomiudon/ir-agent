# 8151：会社一次資料への保存済み明示経路

既存の公式evidence・会社record・contact CSVだけを読み、後日の著者予測対会社公表値の比較準備として5経路を保存した。**本文未取得・未比較・未採点**。GET/DBアクセス/旧artifact変更は0。

主な根拠は公式IRトップ `https://www.toyo.co.jp/ir/` の保存JSON（2026-10-11T23:55:47.593120Z受信）、SHA256 `359318f5e32c6446d876d259684c211f832c6e2d0980200907288f838d1e0009`。原JSONの`href`とresolved URL・ラベルをそのまま保持し、routeごとにjsonpath・SHA・支持する本文quote/offsetを付けた。

| 目的候補 | 保存labelの実href | 元JSON |
|---|---|---|
| FY2025/9通期実績・FY2026/9短信/会社予想の資料を探す入口 | https://www.toyo.co.jp/ir/library/earnings/ | `$.links[39]` 決算短信 |
| 同定義の会社公表財務表を探す入口 | https://www.toyo.co.jp/ir/highlight/ | `$.links[54]` 連結業績ハイライト |
| 会社説明/決算ダイジェスト | https://www.toyo.co.jp/ir/highlight/digest/ | `$.links[55]` 決算ダイジェスト |
| 会社の公表予定 | https://www.toyo.co.jp/ir/calendar/ | `$.links[25]` IRカレンダー |
| DPS実績/予想・権利/支払注記を探す入口 | https://www.toyo.co.jp/ir/stock/#c02 | `$.links[59]` 1株当たりの配当金 |

この保存範囲に直接の年度別PDF hrefは見つからず、FY2025/9通期・FY2026/9最新短信を特定したとは言えない。公式HTMLの財務表入口は明示されているが、表そのものが現在もあること・対象期/会計基準/株数調整等は未読。IRトップ本文の「2026年9月期第2四半期決算説明会」は保存時の表示として残し、最新が2Qと断定しない。IRカレンダーは保存linksのラベル/hrefが根拠で、保存可視本文に同ラベルがないためbody_context=null。開催日・発表実施は未確認。

既知ssl4・contents/webFISCO・SharedResearchの停止条件に該当する明示経路は、今回の保存links内では0件だった（blocked_routes=[]）。保持している停止条件は解除せず、別host/転載/推測PDFへ迂回しない。将来の入口取得でこれらに到達したら、そのrouteをblockedとして残す。今回選んだwww.toyo.co.jp経路の現在robots/アクセスも未検査。

会社recordのindividual_access=not_statedと後続contact CSVのexplicitは履歴の差として両方保存した。後者には会社IRフォーム・公式URLもあるが、この調査で窓口statusを更新したり、IR送信許可・投資適格性へ転用していない。

比較の元はAstrisの2025-06-03著者E予測であり、会社原典と分離する。本人著者は未確認のまま。後日の本文調査では、会社の同期間EPS/利益、期・連結範囲・株数/希薄化・訂正/株式分割、DPSの実績/予想・年次/中間・基準日/支払日を照合する必要がある。数値が得られても同定義とは自動認定しない。会社対象期が終わっていることとシステムが結果を知った時刻は別で、2026年に保存した外部予測を2025年時点の事前予測として採点しない。

`routes.json`に5候補と支持範囲/欠損、`validation.json`に元file SHAとhref/quoteの照合を保存。意味検証・会社予想/実績の抽出・新IR質問・valuation/金融モデル採用は0。
