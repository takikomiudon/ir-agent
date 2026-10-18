# 1721：IRスケジュールの静的一覧は空、次回日程は未確認

保存会社予想HTMLのactualhref `/ir/schedule.html` から **本文1GET（上限2、HTTP200）** だけを取得しました。同日robotsの原rawSHA・同UA設定・実path許可を再照合し、robots再GETは0。36,353bytes、本文完了は2026-10-15T11:06:15.888813UTC、公表時刻nullです。

現在・過去カレンダーの領域は原HTMLに空のE-IR placeholderとして置かれ、静的本文に予定日程行がありません。JS・hiddenfeed・API・別hrefを追わず、ここで停止しました。次回決算の対象期・日付・時刻・timezone・scheduled_at・dueはnull、実施はnot_establishedです。日程が非公表という意味ではありません。研究管理日2027年1月15日も代入していません。

同じ本文には沈黙期間の一般方針が明示されています。「各決算期日の翌日より決算発表までの期間中」に、決算に関連するコメントや質問への回答を控えるという記述です。予想と大きく変わる事象のプレス開示例外も保持しました。ただし現在沈黙期間中か、具体的な開始終了日、現在の窓口・送信適格性は未確認です。この方針から次回決算日や送信可否を計算していません。

source-bundleはcanonical jp:1721、companies/theses空、calendar入口1sourceのみ。原raw/text/captureSHA、4引用/offset、shared ID/schema、本文完了とpubnull、旧8input不変を検証しました。metadataパスは `research/ir-case-studies-2026-10-15` 基準、新providerのgeneric verifierはunknown。DB/code/旧file/manifest・予測/モデル・IR操作は0です。
