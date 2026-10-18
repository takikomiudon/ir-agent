# SBI公式S株条件：1経路の取得prepare-only

保存7150窓口の実リンクから、ゼロ革命LP→同LP links[24]の国内手数料詳細だけを取得しました。robotsを各実hostでfresh確認し、計4GET（上限6）。全200・完全受信、redirect/retry/JS/POST/認証/口座開設/注文0。残2枠は使わず停止しました。

手数料詳細はHTTP charset `Windows-31J`。初期抽出はPythonの未対応codec名で止まり、その履歴をcaptureに保持。保存原entityは変更せず、Windows日本語コードページのcp932 aliasでstrictローカル復号し、`decode.json`と`text/04-cp932-*`へ別保存しました。取り直しGET・置換文字補完なし。GET4はContent-Encoding:gzipをrequestsが復号したentityを保存しており、圧縮wire bytesではありません。GET1–3はContent-Encodingなし。HTTP完全受信と文字復号を分け、GET4 Content-Length未提示の比較はnullに保っています。

robots両方は完全UTF8 plain textでUser-agent:*とsitemapのみ、保留host/AI個別禁止なし。S株の手数料注記等のlocator 6件を保存しましたが、意味・利用者の適用可否は未レビューです。一般LPと詳細注記を混ぜて一律無料認定せず、spread/価格決定・最低単位・対象・執行時間・積立方式も未確認。S株専用サービスの実リンクをこの1経路では特定できず、一般ナビゲーションや口座操作へ広げませんでした。

`capture.json`にraw SHA/bytes/HTTP時刻/選択headers、`guard.json`に実host/robots原文SHA/完了時刻/判定、`link-provenance.json`に元literal pointerとLP raw href spanがあります。ページ更新日表示やLast-Modifiedを初公開時刻にせず、画面時計を市場時刻にしません。DB/Store/旧資料/共有code/docs/金融採用/送信0。この取得をfreezeして親担当の独立意味レビューへ渡します。
