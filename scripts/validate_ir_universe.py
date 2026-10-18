#!/usr/bin/env python3
"""Validate a saved IR universe survey without networking or submitting forms.

Usage::

    python scripts/validate_ir_universe.py OUTPUT_DIRECTORY \
        --universe research/ir-contacts-2026-10-11/evidence/jpx-listing-universe.csv \
        --previous-root research/ir-contacts-2026-10-11 \
        --output OUTPUT_DIRECTORY/validation.json --require-complete
    python scripts/validate_ir_universe.py --self-test

Inputs are output/universe.csv, optional seeds.json, records/CODE.json, and
saved evidence JSON. The original Japanese JPX CSV is also supported. Only
Prime, Standard, and Growth domestic equities enter the denominator; an
alphanumeric security code remains a string. PRO Market, funds, foreign
equities, and subscription certificates are outside this declared scope.

Channel verification and suitability for individual correspondence are
independent. Confirmed requires evidence of the specific IR email or of actual
email/question form controls with an IR association. An official form link,
JavaScript shell, or inaccessible external form is provisional. An IR phone
next to a customer form, or a general/privacy/press email, is unconfirmed.
Restricted and no_individual_reply are eligibility states, not failed fetches.

This checks evidence consistency and conservative structural gates, not the
truth of arbitrary semantic claims. New automatically confirmed results still
require manual review. A recorded manual review may clear that flag, but never
substitutes for the saved channel evidence. No delivery or response is verified.

Coverage names deliberately have different numerators: terminal_record_coverage
counts saved terminal records, official_get_attempt_coverage counts evidence of
an actual official-site GET during this survey (including failures), and
channel_verified_coverage counts structurally valid confirmed channels. A
seed-missing terminal record never counts as an official GET attempt. Previous
verified evidence may support a channel without implying a new GET occurred.

The rules implement this repository's jp-equity-ir skill and docs/workflow.md.
Regression risks below cite the manually reviewed October 11, 2026 directory;
that purposive sample is not an estimate of detection accuracy over all issuers.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import unittest
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit


DOMESTIC_MARKETS = {
    "プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）"
}
MARKET_ALIASES = {"プライム": "プライム（内国株式）", "スタンダード": "スタンダード（内国株式）", "グロース": "グロース（内国株式）"}
STATUSES = {"confirmed", "provisional", "unconfirmed"}
LEVELS = {
    "previous_verified", "ir_email_verified", "form_fields_verified",
    "official_form_link_only", "none",
}
CODE = re.compile(r"[0-9]{3}[0-9A-Z]\Z")
EMAIL_FIELD = re.compile(r"email|e.mail|mail[_-]?address|(?:^|[_\[\]-])mail|メール", re.I)
QUESTION_FIELD = re.compile(
    r"question|query|message|inquir|comment|content|detail|body|naiyo|textarea|"
    r"subject|質問|相談|お問(?:い)?合(?:わ)?せ|お問い合わせ", re.I
)
IR_CONTACT = re.compile(
    r"(?:(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])(?:情報)?[^。]{0,80}(?:問(?:い)?合(?:わ)?せ|問い合わせ|フォーム|相談))|"
    r"(?:株式投資家|投資家)[^。]{0,65}(?:問(?:い)?合(?:わ)?せ|問い合わせ)|"
    r"(?:IR[（(]投資家向け情報[）)]について)|"
    r"(?:お問い合わせ(?:種別|内容|項目|の種類)[^。]{0,80}(?:(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])|投資家))|"
    r"(?:(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])[^.。]{0,55}(?:contact|inquir|form))|"
    r"(?:(?:contact|inquir|form)[^.。]{0,55}(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9]))|"
    r"(?:investor relations[^.]{0,55}(?:contact|inquir|form))|"
    r"(?:(?:contact|inquir|form)[^.]{0,55}investor relations)", re.I
)
IR_MARKER = re.compile(r"(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])|investor relations|投資家", re.I)
IR_SERVICE_OFFERING = re.compile(
    r"(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])\s*活動支援", re.I
)
OTHER_CONTACT = re.compile(
    r"製品|商品|サポート|採用|営業|勧誘|個人情報|プライバシー|報道|プレス|"
    r"privacy|support|press|recruit", re.I
)
PRIVACY_START = re.compile(
    r"個人情報保護方針|プライバシーポリシー|個人情報.{0,8}(?:取扱|取り扱|保護)|privacy policy", re.I
)
FORM_ATTRIBUTE_PATH = re.compile(
    r"forms\.([0-9]+)\.controls\.([0-9]+)\.(placeholder|aria-label|label|title)\Z"
)
NO_REPLY = re.compile(
    r"個別(?:の)?(?:お)?(?:問(?:い)?合(?:わ)?せ|問い合わせ)[^。]{0,75}"
    r"(?:回答しない|回答いたしません|回答を行わない|回答は行いません)|"
    r"個別にご質問[^。]{0,90}回答という方法ではなく[^。]{0,180}"
    r"(?:適時開示|ホームページ)[^。]{0,80}掲載[^。]{0,50}代え|"
    # An explicit fair-disclosure replacement can use "方法によるのではなく".
    # Keep the complete general-question scope and closing replacement, rather
    # than treating a topic restriction or a public/private reply exception as
    # a refusal of individual replies.
    r"(?<![^\s。])ご質問への回答につきましては、適切なフェアディスクロージャーに努める観点から、"
    r"個別にご質問をいただいた方への回答という方法によるのではなく、"
    r"当社の企業価値の適切な評価・理解に繋がると考えられる情報について、"
    r"株主共同の利益の確保の観点から投資家の皆様にお知らせすることが有用であると当社が判断した場合に、"
    r"開示資料や当社ホームページ「\s*よくあるご質問\s*」などに掲載させていただく方法によりご回答に代えさせていただきます[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))|"
    # This complete public-answer replacement differs from a delay, an
    # excluded question topic or a usual public answer with private exceptions.
    r"いただくお問い合わせに対しては、当社が回答すべきと判断した場合に"
    r"個別のご回答ではなく、ホームページ上で回答を公開することにしております[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))|"
    # The investment-inquiry policy explicitly replaces private replies with
    # press releases. Ordinary recipient-only reuse notices and newsletter
    # troubleshooting describe different purposes and do not override it.
    r"(?<![^\s。])現在、投資に関連するお問い合わせは、個別回答は実施せず、"
    r"まとめてプレスリリースにより回答する方針を定めています[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))|"
    # A complete shareholder/investor fairness policy declines individual
    # replies and replaces them with public disclosures. An excluded topic,
    # opinion-only refusal, delay or private-reply exception is not this rule.
    r"(?<![^\s。])株主・投資家の皆さまの間の公平性の観点から、"
    r"個別のご回答は差し控えさせていただいております[。.]\s*"
    r"皆さまに共通する重要な情報につきましては、適時開示や決算説明会・定時株主総会等を通じて、"
    r"当社サイトにて公平に開示してまいります[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))|"
    # An IR-contact FAQ states the ordinary response method explicitly.
    # "In principle" is retained in the cited conditions: it is not a promise
    # that exceptions never occur. A stated private-reply exception, topic
    # exclusion or delay does not establish this default public-answer policy.
    r"Q：IRのお問い合わせ先はどこですか[?？]\s*A：\s*フォーム\s*で「IR」を選択し、"
    r"お問い合わせください[。.]なお、原則として、個別での回答には対応しておりません[。.]"
    r"必要に応じて、IRサイトの「よくあるご質問」からご回答させていただきます[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))|"
    # This complete policy covers all IR/business/pipeline/disclosure queries
    # and publishes answers selected by the issuer. An automated receipt or a
    # recipient-only notice for another purpose is not a private IR answer.
    r"(?<![^\s。])[0-9]+）当社の事業活動、研究開発パイプラインの進捗状況、開示情報など、"
    r"IRに関する一切のお問い合わせは、投資家の皆様へ開示情報の公平性を確保しなければならない為、\s*"
    r"個別に回答をすることはございません\s*ので予めご了承ください[。.]\s*"
    r"お問い合わせをいただいた内容は当社にて公表の良否を諮り、回答すべきと判断した内容のみを"
    r"当社HPまたは開示情報にて公開いたします[。.]"
    r"(?!\s*(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信))", re.I
)
IR_FORM_DIRECTION = re.compile(
    r"(?:IR|ＩＲ)[^。]{0,80}(?:問(?:い)?合(?:わ)?せ|問い合わせ)(?:先|対応).{0,130}"
    r"(?:フォームに一本化|フォームは\s*こちら)", re.I
)

KNOWN_RISKS = [
    {"pattern": "ir_phone_adjacent_to_customer_form", "security_code": "3563",
     "snapshots": ["evidence/svc-3563-contact.json", "evidence/svc-3563-form.json"],
     "rule": "株式は電話案内、別フォームはブランド・店舗選択。全文のIR単語とany formを結合しない。"},
    {"pattern": "general_email_adjacent_to_ir_email", "security_code": "6532",
     "snapshots": ["evidence/svc-6532-contact.json"],
     "rule": "info@baycurrent.co.jpを、別見出しでIR指定されたir@と同じ用途にしない。"},
    {"pattern": "privacy_or_form_failure_email", "security_codes": ["9692", "4493"],
     "snapshots": ["evidence/it-9692-contact.json", "evidence/it-4493-contact.json"],
     "rule": "privacy@は個人情報窓口、pr@はフォーム不具合用。IRメールとは指定されていない。"},
    {"pattern": "institutional_scope_is_route_specific", "security_codes": ["3197", "3923"],
     "snapshots": ["evidence/svc-3197-contact.json", "evidence/it-3923-ir.json"],
     "rule": "すかいらーくの財務メールは機関向け。ラクスの機関向け取材導線を一般IRメールへ波及させない。"},
    {"pattern": "no_reply_policy_despite_form_link", "security_code": "4058",
     "snapshots": ["evidence/it-4058-contact.json"],
     "rule": "個別問い合わせには取次も含め回答しない方針。個人返信を使う運用から外す。"},
    {"pattern": "link_or_js_shell_is_not_verified_fields", "security_codes": ["4475", "6387", "6278", "6240"],
     "snapshots": ["evidence/it-4475-contact.json", "evidence/mfg-6387-contact.json",
                   "evidence/mfg-6278-ir-form.json", "evidence/mfg-6240-external-form.json"],
     "rule": "検索欄、空フォーム、読み込み画面、外部403からIR入力欄の実証へ昇格しない。"},
    {"pattern": "email_authentication_is_not_ir_question_form", "security_code": "7716",
     "snapshots": ["evidence/mfg-7716-form.json"],
     "rule": "認証用メール欄だけではIR用途・質問本文欄が確認できない。"},
    {"pattern": "global_navigation_or_example_email", "security_codes": ["9341", "6947", "590A"],
     "snapshots": ["evidence/svc-9341-contact.json", "evidence/mfg-6947-ir-form.json",
                   "evidence/it-590A-contact.json"],
     "rule": "個人投資家ナビは窓口受付条件の証拠ではない。example@等の入力例を公開IRアドレスにしない。"},
    {"pattern": "shareholder_perks_are_not_financial_ir", "security_codes": ["1417", "2120"],
     "snapshots": [],
     "rule": "全社pilotで優待type=04とyutai@を誤検知。株式手続・優待窓口と業績IRを別用途で扱う。"},
]


def url_key(value: object) -> str | None:
    """Ignore fragments, preserving queries that distinguish IR/product routes."""
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, ""))


def aware_time(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except ValueError:
        return False


def read_universe(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        market = row.get("market", row.get("市場・商品区分"))
        if "market" in row:
            market = MARKET_ALIASES.get(market, market)
        if market not in DOMESTIC_MARKETS:
            continue
        code = row.get("security_code", row.get("コード"))
        # The JPX domestic-equity product category also contains seven
        # five-digit share classes in the September 2026 file. Those do not
        # belong to the explicitly requested ordinary four-character universe.
        if isinstance(code, str) and re.fullmatch(r"[0-9]{5}", code):
            continue
        if not isinstance(code, str) or not CODE.fullmatch(code):
            raise ValueError(f"Invalid domestic security code: {code!r}")
        if code in result:
            raise ValueError(f"Duplicate universe security code: {code}")
        result[code] = {
            "security_code": code, "company_name": row.get("company_name", row.get("銘柄名")),
            "market": market, "jpx_sector": row.get("jpx_sector", row.get("33業種区分")),
        }
    if not result:
        raise ValueError("Universe contains no declared domestic ordinary equities")
    return result


def question_form(form: dict) -> bool:
    """Require both a reply email field and a question field in the SAME form."""
    if not isinstance(form, dict):
        return False
    controls = []
    for control in form.get("controls", []):
        if not isinstance(control, dict):
            continue
        kind = str(control.get("type", "")).lower()
        if kind in {"hidden", "submit", "button", "search", "checkbox", "radio", "reset"}:
            continue
        controls.append(control)
    email = any(
        str(c.get("type", "")).lower() == "email" or EMAIL_FIELD.search(str(c.get("name", "")))
        for c in controls
    )
    question = any(
        str(c.get("tag", c.get("type", ""))).lower() == "textarea"
        or QUESTION_FIELD.search(str(c.get("name", "")))
        for c in controls
    )
    return bool(email and question)


def legacy_question_form(form: dict, source: dict) -> bool:
    """Account for the old capture's omitted tag/label metadata, only for
    manually reviewed prior records. Opaque IDs never validate a NEW form.
    """
    if question_form(form):
        return True
    controls = [c for c in form.get("controls", []) if isinstance(c, dict) and
                str(c.get("type", "")).lower() not in {"hidden", "submit", "button", "checkbox", "radio", "search", "reset"}]
    if len(controls) < 3 or not any("tag" not in c and "type" not in c for c in controls):
        return False
    text = source.get("text", "")
    email = any(str(c.get("type", "")).lower() == "email" or EMAIL_FIELD.search(str(c.get("name", ""))) for c in controls)
    email = email or bool(re.search(r"メールアドレス|E-mail|Email", text, re.I))
    question = re.search(r"(?:お問い合わせ|お問合せ|お問い合せ|お問合わせ)(?:の)?内容|ご質問|ご相談内容", text)
    return bool(email and question)


def reviewed_question_form(form: dict) -> bool:
    """A recorded manual review can identify an opaque email field from its
    public label within the SAME form; actual input and textarea still exist.
    This fallback must never be used for an unreviewed automatic classification.
    """
    if question_form(form):
        return True
    if not isinstance(form, dict):
        return False
    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
    reply_input = any(c.get("tag") == "input" and str(c.get("type", "text")).lower() in {"text", "email"} for c in controls)
    question = any(c.get("tag") == "textarea" for c in controls)
    email_label = re.search(
        r"(?:\*|※|[【\[(（]?\s*必須(?:\s*Required)?\s*[】\])）]?)\s*(?:メールアドレス|E[- ]?mail|Email(?: address)?)|"
        r"(?:メールアドレス|E[- ]?mail|Email(?: address)?)(?:/E[- ]?mail)?\s*(?:\*|※|[【\[(（]?\s*必須\s*[】\])）]?|Required)",
        form.get("text", ""), re.I
    )
    email_label = email_label or re.search(
        r"(?:^|\s)(?:メールアドレス|E[- ]?mail|Email(?: address)?)(?:\s|$)", form_labels(form), re.I
    )
    # A reviewed form may label the numeric reply input simply "メール".
    # Its adjacent telephone FIELD distinguishes that label from a reply-
    # channel choice ("返信方法 メール 電話") or a privacy-policy example.
    email_label = email_label or re.search(r"(?:^|\s)メール\s+(?:電話番号|TEL)(?:\s|$)", form_labels(form), re.I)
    # ASP.NET may label a paired opaque reply field with a parenthesized
    # heading. Require both actual text inputs qN/conf_qN, not a privacy
    # example, an email delivery option, or one arbitrary numeric input.
    parenthesized_label = re.search(r"お客様情報[（(]メールアドレス[）)]\s*確認のため、再入力をお願いします[。.]", form_labels(form))
    if (not email_label and parenthesized_label and not re.search(
        r"入力例|記入例|例\s*[:：]|example\s*[:：]", form_labels(form)[max(0, parenthesized_label.start() - 30):parenthesized_label.start()], re.I
    )):
        reply_names = {str(c.get("name", "")) for c in controls
                       if c.get("tag") == "input" and str(c.get("type", "text")).lower() == "text"}
        email_label = any(re.fullmatch(r"q[0-9]+", name.rsplit("$", 1)[-1])
                          and (name.rsplit("$", 1)[0] + "$conf_" + name.rsplit("$", 1)[-1] if "$" in name else "conf_" + name) in reply_names
                          for name in reply_names)
    # Some IR forms put a re-entry prompt between an E-mail label and its
    # required marker. Bind that exact public block to adjacent opaque native
    # reply/confirmation inputs and a named opaque question textarea. The
    # explicit investor-question operation must begin this actual form.
    repeated_email_label = re.search(
        r"Eメールアドレス\s+もう一度入力ください\s+【必須】\s+もう一度入力ください\s+[（(]確認用[）)]",
        form_labels(form)
    )
    investor_operation = ("投資家・アナリスト・株主・その他の皆さまからのお問い合わせ "
                          "本お問い合わせフォームは、投資家・アナリスト・株主・その他の皆さまからの"
                          "IR情報・サステナビリティレポートに関するお問い合わせを目的として設置しています。")
    if (not email_label and repeated_email_label and form.get("text", "").startswith(investor_operation)
            and str(form.get("method", "")).lower() == "post"
            and re.search(r"ご質問内容・お問い合わせ内容\s+【必須】", form_labels(form))):
        paired_reply = any(c.get("tag") == "input" and c.get("type") == "text"
                           and re.fullmatch(r"c_q[0-9]+", str(c.get("name", ""))) and c.get("id") == c.get("name")
                           and i+1 < len(controls) and controls[i+1].get("tag") == "input"
                           and controls[i+1].get("type") == "text"
                           and controls[i+1].get("name") == c["name"] + "_confirm"
                           and controls[i+1].get("id") == controls[i+1].get("name")
                           for i, c in enumerate(controls))
        named_question = any(c.get("tag") == "textarea" and c.get("type") != "hidden"
                             and re.fullmatch(r"c_q[0-9]+", str(c.get("name", ""))) and c.get("id") == c.get("name")
                             for c in controls)
        email_label = paired_reply and named_question
    return bool(reply_input and question and email_label)


def manual_review_valid(record: dict) -> bool:
    review = record.get("manual_review")
    return bool(record.get("manual_review_required") is False and isinstance(review, dict)
                and aware_time(review.get("reviewed_at"))
                and all(isinstance(review.get(f), str) and review[f].strip() for f in ("reviewer", "notes")))


def form_labels(form: dict) -> str:
    parts = [form.get("text", ""), form.get("visible_text", "")]
    for control in form.get("controls", []):
        if not isinstance(control, dict):
            continue
        parts.extend([control.get("label", ""), control.get("text", "")])
        for option in control.get("options", []):
            if isinstance(option, str):
                parts.append(option)
            elif isinstance(option, dict):
                parts.append(option.get("label", option.get("text", "")))
    result = " ".join(p for p in parts if isinstance(p, str))
    # A privacy inquiry OPTION or a short data-use INTRODUCTION is not the
    # beginning of a policy block. Cutting at every mention hides later IR
    # choices (Sekisui House/PostPrime) and Google Forms fields.
    return PRIVACY_START.split(result, maxsplit=1)[0]


def form_ir_scope(form: dict, *, reviewed: bool = False) -> bool:
    """Recognize an IR option within the actual question form before its policy.

    Mixed product/recruitment/IR menus are legitimate. A plain IR option needs
    a captured selection control plus an inquiry-category prompt; an IR word
    in a privacy policy or unrelated navigation does not establish this route.
    """
    # A PR vendor's selectable "IR活動支援" service is an offering to its
    # customers, not a category for investors' questions about that issuer.
    # An explicit issuer-IR parent link may still designate a generic form;
    # that independent binding is verified by has_form_binding below.
    labels = IR_SERVICE_OFFERING.sub("", form_labels(form))
    if IR_CONTACT.search(labels):
        return True
    choice = any(isinstance(c, dict) and
                 (c.get("tag") == "select" or c.get("type") == "radio")
                 for c in form.get("controls", []))
    category = re.search(r"(?:お?問(?:い)?合(?:わ)?せ)(?:の)?(?:種類|種別|内容|項目|分類)|分類\s*(?:必須|\*)", labels)
    category = category or reviewed and re.search(r"右の項目から\s*おひとつお選びください", labels)
    return bool(choice and category and IR_MARKER.search(labels))


def reviewed_form_ir_scope(form: dict, quotes: list[str]) -> bool:
    """Recover cited operational labels after an introductory privacy block.

    Ordinary extraction still stops at privacy text. This manual-review-only
    path needs an exact quote IN this form, an actual category selection or a
    direct instruction to use the form below. A policy's IR words, navigation,
    and directions to read financial information never designate this form.
    The caller separately requires its real reply/question controls.
    """
    text = form.get("text", "")
    if not isinstance(text, str):
        return False
    category_selection = any(
        isinstance(c, dict) and (c.get("tag") == "select" or c.get("type") == "radio")
        and (re.search(r"category|kind|type|item|kubun|shubetsu|syubetu", str(c.get("name", "")), re.I)
             or c.get("tag") == "select" and c.get("type") != "hidden" and c.get("name") == "kbn")
        for c in form.get("controls", [])
    )
    direct_use = re.compile(r"(?:IR|ＩＲ)に関するご質問(?:やご連絡)?(?:など)?にご(?:使用|利用)ください[。.]", re.I)
    for quote in quotes:
        if not isinstance(quote, str) or not quote or quote not in text or PRIVACY_START.search(quote):
            continue
        category = re.search(r"(?:お?問(?:い)?合(?:わ)?せ)(?:の)?(?:種類|種別|項目|件名)\s*(?:必須|\*|※)?[^。]{0,130}", quote)
        if (category_selection and category and IR_MARKER.search(IR_SERVICE_OFFERING.sub("", category[0]))
                and not re.search(r"ご覧|ご確認|参照|電話のみ|受付(?:け)?ません", category[0])):
            return True
        use = direct_use.search(quote)
        if not use or re.match(r"\s*(?:製品|商品|サポート|採用|営業|報道|プレス|product|support|press|recruit)", text, re.I):
            continue
        for occurrence in re.finditer(re.escape(use[0]), text):
            if re.match(r"\s*下記フォームに必要事項をご入力の上", text[occurrence.end():occurrence.end() + 120]):
                return True
    return False


def reviewed_english_ir_subject_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind a captured misspelt IR subject to its actual question selector.

    The exact public spelling is not a new global IR keyword. This reviewed
    form engine needs its full cited fields, subject select after the country
    select, reply input and details textarea, before its data-handling policy.
    Navigation, a country selector alone and investment-service offers cannot
    supply this operational subject.
    """
    text = form.get("text", "")
    block = ("Subject Select the subject of your inquiry Business Contact "
             "Investers Relation Contact Public Relation Contact Details of Your Inquiry")
    if (not isinstance(text, str) or str(form.get("method", "")).lower() != "post"
            or not re.match(r"You can contact [^.]{2,60} by filling out and sending the following form[.]", text)
            or text.count(block) != 1 or not any(q.strip() == text.strip() for q in quotes)
            or not any(block in q for q in quotes)
            or "Email Address * Please enter your email address." not in text
            or block not in re.split(r"About the Handling of Personal Information|privacy policy", text, maxsplit=1, flags=re.I)[0]
            or source.get("text", "").count(text) != 1
            or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1):
        return False
    controls = [c for c in form.get("controls", []) if isinstance(c, dict)
                and c.get("tag") in {"input", "select", "textarea"}
                and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
    selectors = [c for c in controls if c.get("tag") == "select"]
    reply = [i for i, c in enumerate(controls) if c.get("tag") == "input" and c.get("type") == "text" and c.get("name") == "q_1"]
    subject = [i for i, c in enumerate(controls) if c.get("tag") == "select" and c.get("name") == "q_7"]
    details = [i for i, c in enumerate(controls) if c.get("tag") == "textarea" and c.get("name") == "q_3"]
    action = urlsplit(str(form.get("action", "")))
    return bool(
        [c.get("name") for c in selectors] == ["q_2", "q_7"]
        and len(reply) == len(subject) == len(details) == 1 and reply[0] < subject[0] and subject[0] + 1 == details[0]
        and action.scheme == "https" and action.hostname == urlsplit(source.get("url", "")).hostname
        and action.path.endswith("/gencgi/mod/enqcsv") and action.query == "q_1+q_4+q_5" and not action.fragment
    )


def reviewed_results_question_checkbox_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Require an issuer choice and a real financial-question checkbox.

    A cited results-question instruction designates the checkbox in the same
    post form as native reply/confirmation and a question textarea. The first
    corporate choice must match the saved page title, keeping subsidiary
    destinations separate. A stock benefit, services menu, global IR link or
    privacy consent checkbox cannot designate an investor question route.
    """
    text = form.get("text", "")
    title_company = re.fullmatch(r"お問い合わせ\s*-\s*【([^【】]{2,80})】", source.get("title", ""))
    instruction = "決算についての質問時チェックしてください。"
    reply_labels = "メール ※ メール（確認） ※ お問い合せ内容 ※"
    if not title_company or not isinstance(text, str):
        return False
    company_choice = "お問い合わせ先を確認 ※ " + title_company[1]
    labels = form_labels(form)
    if (str(form.get("method", "")).lower() != "post" or not labels.startswith(company_choice + " ")
            or text.count(instruction) != 1 or instruction not in labels or reply_labels not in labels
            or not all(any(part in q for q in quotes) for part in (company_choice, instruction, reply_labels))
            or source.get("text", "").count(text) != 1
            or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
            or re.search(r"決算[^。]{0,60}(?:電話のみ|フォームでは受け付けません|受付(?:け)?ません)", text)):
        return False
    controls = [c for c in form.get("controls", []) if isinstance(c, dict)
                and c.get("tag") in {"input", "select", "textarea"}
                and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
    if (len(controls) < 5 or controls[0].get("tag") != "select" or controls[0].get("name") != "gcname"
            or controls[1].get("tag") != "input" or controls[1].get("type") != "checkbox"
            or controls[1].get("name") != "aboir" or controls[1].get("id") != "aboir"
            or sum(c.get("tag") == "select" for c in controls) != 1):
        return False
    reply = [i for i, c in enumerate(controls) if c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "email"]
    confirm = [i for i, c in enumerate(controls) if c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "kmail"]
    question = [i for i, c in enumerate(controls) if c.get("tag") == "textarea" and c.get("name") == "freeans"]
    actual_url = source.get("url") or source.get("requested_url")
    action = urljoin(str(actual_url), str(form.get("action", "")))
    return bool(
        len(reply) == len(confirm) == len(question) == 1 and 1 < reply[0] and reply[0] + 1 == confirm[0] and confirm[0] + 1 == question[0]
        and url_key(action) == url_key(urljoin(str(actual_url), "./complete.php"))
    )


def reviewed_personal_ir_email_signature(source: dict, quotes: list[str], address: str) -> bool:
    """Keep a personal sender-name instruction at its sole public IR mailbox.

    This is an input instruction for the cited IR email operation, not an
    inference from privacy terms or a general personal contact. The caller
    already verifies IR attribution and the exact claimed page URL.
    """
    text = source.get("text", "")
    instruction = ("お問い合わせに際しましては、法人のお客様は会社名及びご担当者様のお名前を、"
                   "個人の方は御氏名の記載をお願いいたします。")
    receipt = ("弊社では、株主や投資家の皆様をはじめ、弊社グループで展開する各種事業におけるお客様など、"
               "様々なステークホルダーの皆様との対話のため、メールでのお問い合わせをお受けしております。")
    mailbox = re.search(r"問い合わせ担当：[^\s]{2,40}部\s+IR・広報\s+" + re.escape(address) + r"(?=\s|$)", text)
    if (not mailbox or source.get("headings", []).count("お問い合わせに際してのお願い") != 1
            or any(text.count(part) != 1 for part in (receipt, instruction, mailbox[0]))
            or not all(any(part in q for q in quotes) for part in (receipt, instruction, mailbox[0]))
            or set(re.findall(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)) != {address}
            or source.get("forms")
            or not text.index(receipt) < text.index("お問い合わせに際してのお願い") < text.index(instruction) < mailbox.start()):
        return False
    operation = text[text.index("お問い合わせに際してのお願い"):mailbox.end()]
    return not bool(re.search(
        r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)|"
        r"機関投資家(?:のみ|限定|専用)", operation
    ))


def reviewed_financial_stock_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind a stock category only when the same page documents financial
    questions and its reply operation. A stock-admin/benefit option alone is
    insufficient; the public-information exception and response instruction
    must both be cited, with the actual same-form reply and question controls.
    """
    if not question_form(form):
        return False
    scope = ("お問い合わせ区分 ※ 商品・サービスに関するお問い合わせ 採用に関するお問い合わせ "
             "個人情報保護に関するお問い合わせ 株式に関するお問い合わせ このサイトに関するお問い合わせ その他のお問い合わせ")
    policy = ("当社に関する業績見通し、計画、方針、経営戦略といった内容等（公表しているものを除きます）"
              "につきましても、個別にお答えすることは差し控えさせていただきます。")
    response = "受付時間外・土日祝・当社休業日に送信されたお問い合わせにつきましては、翌営業日以降にご回答いたします。"
    text = form.get("text", "")
    controls = form.get("controls", [])
    stock_choices = sum(isinstance(c, dict) and c.get("tag") == "input" and c.get("type") == "radio"
                        and c.get("name") == "kubun" for c in controls)
    return bool(
        isinstance(text, str) and scope in text and stock_choices == 6
        and any(scope in q for q in quotes) and any(policy in q for q in quotes) and any(response in q for q in quotes)
        and all(part in source.get("text", "") for part in (scope, policy, response))
        and not re.search(r"株式(?:事務|手続)|株主優待|株主名簿", text)
        and not re.search(r"IR[^。]{0,20}(?:電話のみ|電話専用|フォームでは受け付けません)", source.get("text", ""), re.I)
        and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1
    )


def reviewed_public_qa_personal_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind personal questions answered publicly to the same actual IR form.

    A public-answer policy is an explicit audience, not a promise of private
    email replies. Require its cited personal-IR policy, publication statement
    and IR-question/form instruction on this QA page, followed by its sole
    actual reply/question form. General QA, navigation and privacy text cannot
    transfer an audience from another page or another form.
    """
    if (not question_form(form) or str(form.get("method", "")).lower() != "post"
            or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
            or source.get("headings", [])[:1] != ["株主・投資家Q&A"]
            or not source.get("title") or not any(source["title"] in q for q in quotes)):
        return False
    intro = "当社はIRの基本方針として、個人投資家の皆様を重視したIR活動を行ってまいります。"
    policy = re.compile(
        r"また、双方向でオープンな質問・回答となるよう、機関投資家やアナリスト及び個人投資家の皆様から"
        r"いただいた質問は回答と合わせて、\s*「株主・投資家Q&A」コーナーにて開示させていただきます[。.]"
    )
    operation = re.compile(
        r"Q\.\s*(?:IR|ＩＲ)へ質問しましたが、メールで返事がきません[。.]\s*A\.\s*"
        r"一部のご質問内容によっては、メールで回答させていただく場合がございますが、原則としてこちら"
        r"[（(]株主・投資家Q&A[）)]に回答いたします[。.]\s*質問する\s*"
        r"上記内容で解決しない場合は、下記フォームよりご質問ください[。.]", re.I
    )
    text = source.get("text", "")
    public_policy = policy.search(text)
    form_operation = operation.search(text)
    fields = form.get("text", "").strip()
    if (not public_policy or not form_operation or not fields or not any(intro in q for q in quotes)
            or not any(public_policy[0] in q for q in quotes) or not any(form_operation[0] in q for q in quotes)
            or not any(fields in q for q in quotes) or text.count(intro) != 1 or text.count(fields) != 1):
        return False
    intro_start, fields_start = text.index(intro), text.index(fields)
    segment = text[intro_start:fields_start]
    return bool(
        intro_start < public_policy.start() < form_operation.start() < fields_start
        and not PRIVACY_START.search(segment)
        and not re.search(r"個人(?:投資家|の方)(?:からの(?:質問|ご質問|お問い合わせ))?は(?:対象外|お断り|受け付けておりません)", segment)
        and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", form_labels(form), re.I)
    )


def reviewed_anchored_personal_ir_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind a personal-contact IR selector to its exact saved shareholder form.

    Runsystem offers separate store, IR and franchise forms on one page. The
    captured IR link names #inqformN; the matching post action, reply/question
    controls and shareholder radio belong to formN. A cited operational
    selector and the same form's ownership quote are also mandatory. No other
    form's fields or global IR navigation can supply this evidence.
    """
    text = form.get("text", "")
    if not isinstance(text, str) or not question_form(form):
        return False
    selector = any(isinstance(q, str) and q.startswith("個人のお客様のお問合せ ")
                   and "お問合せは以下フォームよりお問合せ下さい。" in q
                   and "入力前にお問い合わせ内容を選択" in q and " IRに関して " in q
                   for q in quotes)
    ownership = re.compile(r"株主確認[^。]{0,15}当社の株式を所有していない[。.]\s*当社の株式を所有している[。.]")
    if not selector or not any(q in text and ownership.search(q) and "株主名簿と照合" in q for q in quotes):
        return False
    source_urls = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
    for link in source.get("links", []):
        if not isinstance(link, dict) or link.get("label") != "IRに関して" or url_key(link.get("url")) not in source_urls:
            continue
        anchor = re.fullmatch(r"inqform([1-9][0-9]*)", urlsplit(link["url"]).fragment)
        if not anchor:
            continue
        prefix = "form" + anchor[1] + "_"
        names = {(c.get("tag"), c.get("type"), c.get("name")) for c in form.get("controls", []) if isinstance(c, dict)}
        if not (any(name == prefix + "mail" and tag == "input" and kind in {"text", "email"} for tag, kind, name in names)
                and any(name == prefix + "content" and tag == "textarea" for tag, _, name in names)
                and any(name == prefix + "stock" and kind == "radio" for _, kind, name in names)):
            continue
        action = r"(?:^|/)confirm_personal_" + anchor[1] + r"\.html$"
        if (str(form.get("method", "")).lower() == "post" and re.search(action, urlsplit(str(form.get("action", ""))).path)
                and sum(bool(re.search(action, urlsplit(str(f.get("action", ""))).path)) for f in source.get("forms", []) if isinstance(f, dict)) == 1):
            return True
    return False


def reviewed_named_ir_tab_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind a cited IR tab to its own named form among product/other forms.

    Tokuden's tab labels are outside the forms. Its cited operational notice
    designates separate forms, and the IR reply/question controls use ir- names
    while the other two forms use product-/other-. Require that entire saved
    structure, unique same-page post actions, and the exact IR form field quote.
    An IR menu word or another tab's controls never supplies this binding.
    The caller permits this only for a recorded review at the target URL.
    """
    text = source.get("text", "")
    instruction = ("会社情報・IR情報・製品・その他お問い合わせについては下記のメールフォームをご利用ください。"
                   "なお、お問い合わせの際には、ご用件に合ったメールフォームをご利用ください。")
    tabs = "IRに関するお問い合わせ 製品に関するお問い合わせ その他のお問い合わせ"
    labels = form.get("text", "")
    if (not isinstance(text, str) or not isinstance(labels, str) or not labels
            or source.get("headings", []).count("お問い合わせ用メールフォーム") != 1
            or not any(instruction in q for q in quotes)
            or not any(tabs in q for q in quotes)
            or not any(q.strip() == labels.strip() for q in quotes)
            or any(text.count(part) != 1 for part in (instruction, tabs, labels))
            or not text.index(instruction) < text.index(tabs) < text.index(labels)
            or not re.search(r"メールアドレス", labels)
            or not re.search(r"お問い合わせ内容", labels)
            or re.match(r"\s*(?:製品|商品|採用|product|recruit)", labels, re.I)):
        return False
    forms = source.get("forms", [])
    if len(forms) != 3 or form is not forms[0]:
        return False
    source_url = source.get("url") or source.get("requested_url")
    if url_key(source_url) is None:
        return False
    actions = []
    for candidate, prefix in zip(forms, ("ir", "product", "other")):
        if not isinstance(candidate, dict) or candidate.get("method", "").lower() != "post":
            return False
        action = candidate.get("action", "")
        if not isinstance(action, str) or not action:
            return False
        action = urljoin(source_url, action)
        if url_key(action) != url_key(source_url) or not urlsplit(action).fragment:
            return False
        actions.append(action)
        controls = [c for c in candidate.get("controls", []) if isinstance(c, dict)]
        reply = any(c.get("tag") == "input" and c.get("type") == "email"
                    and c.get("name") == prefix + "-email" for c in controls)
        question = any(c.get("tag") == "textarea" and c.get("type") != "hidden"
                       and c.get("name") == prefix + "-message" for c in controls)
        if not reply or not question:
            return False
    return len(set(actions)) == 3


def reviewed_ir_desk_reply_form(source: dict, form: dict, quotes: list[str]) -> bool:
    """Bind the sole explicit IR-desk operation to its own native CF7 form.

    A short consent notice precedes the public IR response exclusions. Read
    that exact cited operation only in its complete cited form, with its own
    native email/message and ordered action. The outside purpose selector is
    cited text; missing native selector attributes are never manufactured.
    Other forms' personal/logo choices and receipt mail confer no IR access.
    """
    policy = ("※なお、以下に該当するお問い合わせに関してましては、IR担当からの回答を差し控えておりますので何卒ご了承ください。 "
              "弊社製品に関するお問い合わせ 営業、勧誘のお問い合わせ 株価予測・株価動向に関するお問い合わせ "
              "当社がインサイダー情報等に関連する事項と判断した場合 "
              "広告・プロモーションなどのご提案や営業などIRに関するお問い合わせ以外のもの "
              "誹謗中傷など当社が社会通念上不適切な内容と判断した場合")
    fields = form.get("text", "").strip()
    forms = source.get("forms", [])
    if (len(forms) != 10 or form not in forms or not fields
            or not fields.startswith("お名前 必須 メールアドレス 必須 メールアドレスに誤りがないかご確認ください メッセージ 1000 文字以内 ")
            or not fields.endswith(" " + policy + " Δ") or policy not in quotes
            or not any(q.strip() == fields for q in quotes)
            or source.get("text", "").count(fields) != 1
            or sum(policy in f.get("text", "") for f in forms) != 1
            or str(form.get("method", "")).lower() != "post"):
        return False
    purpose = [q for q in quotes if q.startswith("お問い合わせ用件 必須 選択してください ")
               and re.search(r"(?<!\S)IRについて(?=\s|$)", q)]
    if not any(source.get("text", "").count(q) == 1
               and all(q not in f.get("text", "") for f in forms)
               and source["text"].index(q) < source["text"].index(fields) for q in purpose):
        return False
    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
    if (len(controls) < 3 or controls[0].get("tag") != "input" or controls[0].get("type") != "text" or controls[0].get("name") != "your-name"
            or controls[1].get("tag") != "input" or controls[1].get("type") != "email" or controls[1].get("name") != "your-email"
            or controls[2].get("tag") != "textarea" or controls[2].get("type") == "hidden" or controls[2].get("name") != "your-message"):
        return False
    actions = [urljoin(source.get("url", ""), f.get("action") or "") for f in forms]
    index = forms.index(form)
    action = urlsplit(actions[index])
    ordinal = re.fullmatch(r"wpcf7-f[0-9]+-o([1-9][0-9]*)", action.fragment)
    return bool(url_key(source.get("url")) and url_key(actions[index]) == url_key(source.get("url"))
                and ordinal and int(ordinal[1]) == index + 1 and len(set(actions)) == len(forms))


def public_attribute_quote(item: dict, source: dict) -> bool:
    """Exact public instructional attributes only; never hidden/input values."""
    if item.get("extraction_scope") != "form_control_attribute":
        return False
    match = FORM_ATTRIBUTE_PATH.fullmatch(str(item.get("field_path", "")))
    if not match:
        return False
    try:
        control = source["forms"][int(match[1])]["controls"][int(match[2])]
    except (KeyError, IndexError, TypeError):
        return False
    if not isinstance(control, dict) or str(control.get("type", "")).lower() in {
        "hidden", "submit", "button", "reset", "image"
    }:
        return False
    value = control.get(match[3])
    return isinstance(value, str) and value == item.get("quote") and bool(value.strip())


def reviewed_ir_form_with_separate_sales_route(source: dict, form: dict, quotes: list[dict]) -> bool:
    """A cited alternate sales link does not designate the adjacent IR form.

    The caller separately needs the actual official IR-parent link. This
    path also binds the complete sole post-form text, its IR heading, and the
    exact different sales URL, rather than dropping unrelated form prefixes.
    """
    heading = "IRに関するお問い合わせ"
    prefix = "営業・セールスに関するお問い合わせは こちら お問い合わせ内容をご入力ください"
    text = form.get("text", "")
    labels = form_labels(form)
    if (not isinstance(text, str) or not text.startswith(prefix)
            or str(form.get("method", "")).lower() != "post"
            or not question_form(form) or not ir_page_heading(source)
            or source.get("headings", []).count(heading) != 1
            or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
            or not any(heading in e["quote"] for e in quotes)
            or not any(e["quote"].strip() == text.strip() for e in quotes)
            or OTHER_CONTACT.search(labels[len(prefix):])
            or re.search(r"株主優待|株式(?:事務|手続)|IR[^。]{0,30}電話のみ", labels[len(prefix):], re.I)):
        return False
    links = [link for link in source.get("links", []) if isinstance(link, dict) and link.get("label") == "こちら"]
    if len(links) != 1:
        return False
    alternate = url_key(links[0].get("url"))
    source_url = url_key(source.get("url"))
    if (alternate is None or source_url is None or alternate == source_url
            or urlsplit(alternate).hostname != urlsplit(source_url).hostname):
        return False
    declared_sales = any(isinstance(link, dict) and link.get("label") == "営業・セールスに関するお問い合わせはこちら"
                         and url_key(link.get("url")) == alternate for link in source.get("links", []))
    cited_alternate = any(e["quote"] == prefix and url_key(e.get("source_link_url")) == alternate for e in quotes)
    return bool(declared_sales and cited_alternate)


def individual_access_supported(pairs: list[tuple[dict, dict]], *, target_url: str | None = None, reviewed: bool = False) -> bool:
    """Literal form choices and individual-entry instructions, without
    inferring access from a company field being optional or from navigation.
    """
    instruction = re.compile(
        r"(?:職種|属性)[^。]{0,100}個人投資家|個人/業務\s*個人|"
        r"個人の方は[^。]{0,80}(?:記入|入力)|"
        r"個人の場合は\s*[「『]個人[」』]とご?(?:記入|入力)|"
        r"個人投資家[^。]{0,45}(?:受付|ご利用)|"
        r"個人投資家[^。]{0,75}からのお問い合わせ(?!\s*は\s*(?:受け付けません|お断り|対象外|ご遠慮))"
    )
    choice = re.compile(
        r"(?:法人[・/／]個人|個人[・/／]法人(?:・団体)?(?:等)?|"
        r"(?:お客様)?区分|お客様について|所属).{0,180}?"
        r"(?:^|\s)個人(?:投資家|のお客様|の方)?(?:\s|$)"
    )
    explicit_audience_choice = re.compile(
        r"(?:個人又は法人|お問(?:い)?合(?:わ)?せされる方|種別\s*(?:必須|\*))[^。]{0,160}?"
        r"(?:^|\s)個人(?:投資家|のお客様|の方)?(?=\s|$)"
    )
    reviewed_customer_choice = re.compile(
        r"お客様種別\s*(?:※|必須|\*)[^。]{0,160}?"
        r"(?:^|\s)個人(?:株主のお客様|のお客様)(?=\s|$)"
    )
    reviewed_investor_prompt = re.compile(
        r"当てはまるものをひとつご選択ください[。.]\s*機関投資家\s*個人投資家(?=\s|$)"
    )
    alternate_entry = re.compile(r"会社名\s*[（(]\s*(?:または|もしくは)個人[^）)]{0,40}[）)]")
    for evidence, source in pairs:
        quote = evidence["quote"]
        if instruction.search(quote):
            return True
        for form in source.get("forms", []):
            if not isinstance(form, dict):
                continue
            text = form.get("text", "")
            for match in alternate_entry.finditer(text):
                if match[0] in quote:
                    return True
            selection = any(isinstance(c, dict) and
                            (c.get("tag") == "select" or c.get("type") == "radio")
                            for c in form.get("controls", []))
            if selection:
                for match in choice.finditer(text):
                    if match[0] in quote:
                        return True
                # These are field prompts, not an audience navigation label.
                # Bind new variants to this actual target question form; a
                # separate form or URL cannot confer individual access.
                at_target = target_url is None or target_url in {
                    url_key(source.get("url")), url_key(source.get("requested_url"))
                }
                if at_target and question_form(form):
                    for match in explicit_audience_choice.finditer(form_labels(form)):
                        if match[0] in quote:
                            return True
                # ASP.NET can wrap both a privacy navigation link and the
                # real form in one captured element. After recorded review,
                # recover only this literal audience-field quote, not arbitrary
                # "individual investor" words elsewhere in the same element.
                # "Individual shareholder" remains that limited public option;
                # it does not assert that a non-shareholder is eligible.
                if (reviewed and at_target and reviewed_question_form(form)
                        and quote in text and not PRIVACY_START.search(quote)):
                    if reviewed_customer_choice.search(quote) or reviewed_investor_prompt.search(quote):
                        return True
    return False


def ir_page_heading(source: dict) -> bool:
    """An unrelated product heading cannot transfer IR scope to its form."""
    if source.get("title") or source.get("headings"):
        headings = source.get("headings", [])
        text = " ".join([source.get("title", ""), *headings[:1]])
    else:
        text = source.get("text", "")[:160]
    match = IR_CONTACT.search(text)
    return bool(match and not OTHER_CONTACT.search(text[:match.start()]))


def identity_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"株式会社|有限会社|\(株\)|ホールディングス|holdings", "", value)
    return re.sub(r"[^\wぁ-んァ-ン一-龥]", "", value)


def associated_email(quote: str, email: str) -> bool:
    """Conservative attribution; an email following an unrelated heading fails."""
    if not isinstance(email, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return False
    local, domain = email.lower().split("@", 1)
    if local in {"example", "sample", "xxxx", "xxxxx"} or domain in {"example.com", "example.org", "example.jp"}:
        return False
    source = quote
    if email not in source:
        # Only normalize an obfuscation when its replacement instruction exists.
        instructed_symbols = [symbol for symbol in ("★", "＊") if symbol in source and re.search(
            re.escape(symbol) + r"(?:部分)?\s*を\s*@\s*に\s*(?:置き換|変更)", source
        )]
        if not instructed_symbols:
            return False
        for symbol in instructed_symbols:
            source = source.replace(symbol, "@")
    for occurrence in re.finditer(re.escape(email), source):
        prefix = source[max(0, occurrence.start() - 180):occurrence.start()]
        if re.search(r"(?:入力例|記入例|例\s*[:：]|example\s*[:：])\s*$", prefix, re.I):
            continue
        markers = list(IR_MARKER.finditer(prefix))
        if markers and not OTHER_CONTACT.search(prefix[markers[-1].end():]):
            return True
    return False


def associated_public_email(item: dict, source: dict, email: str) -> bool:
    """Bind readable text or a public mailto target to a specific IR route."""
    quote = item["quote"]
    if associated_email(quote, email):
        return True
    for link in source.get("links", []):
        if not isinstance(link, dict):
            continue
        target = link.get("url", "")
        label = link.get("label", "")
        if isinstance(target, str) and target.lower().startswith("mailto:"):
            address = target[7:].split("?", 1)[0]
            if address.lower() == email.lower() and isinstance(label, str) and label in quote and IR_CONTACT.search(label):
                return True
    # A fallback explicitly replacing a dedicated IR question form is an IR
    # channel (Synclayer). A generic product form's error email is not one.
    if ir_page_heading(source) and any(question_form(f) for f in source.get("forms", [])):
        for sentence in re.split(r"[。\n]", quote):
            if email in sentence and re.search(
                r"フォーム[^。]{0,70}(?:正常に動作しない|利用できない|使えない|送信が行えない|送信できない)", sentence
            ) and re.search(r"フォーム入力項目|入力項目を[^。]{0,30}記入|宛(?:て)?[^。]{0,30}お問い合わせ", sentence):
                return True
            # Aun Consulting explicitly assigns questions beyond the form's
            # character limit to a public email on its dedicated IR form.
            # An unrelated email elsewhere on the page cannot substitute.
            if (email in sentence and re.search(r"[0-9]{1,6}\s*文字を超える場合", sentence)
                    and re.search(r"まで連絡をお願い", sentence)
                    and any(question_form(f) and email in form_labels(f)
                            and re.search(r"お?問(?:い)?合(?:わ)?せ内容|お問い合わせ内容", form_labels(f))
                            for f in source.get("forms", []))):
                return True
    return False


def reviewed_sole_investor_email(item: dict, source: dict, email: str) -> bool:
    """Bind an exclusive investor mail instruction to its sole readable address.

    No mailto is inferred. The complete cited operational span must run from
    the investor audience to the contact caption. Explicit response exclusions
    and privacy handling remain conditions, without borrowing another purpose
    or asserting that every question receives a reply.
    """
    scope = "当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。"
    caption = "お問い合わせEmail：" + email
    text, quote = source.get("text", ""), item.get("quote", "")
    if (not isinstance(text, str) or not isinstance(quote, str)
            or text.count(scope) != 1 or text.count(caption) != 1 or text.count(email) != 1
            or source.get("forms") or not quote.startswith(scope) or not quote.endswith(caption)
            or text.count(quote) != 1):
        return False
    if (not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
            or email.split("@", 1)[0].lower() in {"example", "sample", "xxxx", "xxxxx"}
            or email.split("@", 1)[1].lower() in {"example.com", "example.org", "example.jp"}):
        return False
    visible = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    mail_links = [link.get("url", "")[7:].split("?", 1)[0]
                  for link in source.get("links", []) if isinstance(link, dict)
                  and isinstance(link.get("url"), str) and link["url"].lower().startswith("mailto:")]
    if visible != [email] or any(address != email for address in mail_links):
        return False
    conditions = quote[len(scope):-len(caption)]
    exclusion_intro = "下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。"
    privacy_intro = "お問い合わせいただいた個人情報につきましては、厳重にお取り扱いいたします。"
    if conditions.count(exclusion_intro) != 1 or conditions.count(privacy_intro) != 1:
        return False
    begin, end = conditions.index(exclusion_intro), conditions.index(privacy_intro)
    excluded = conditions[begin + len(exclusion_intro):end].strip()
    if (end <= begin or not excluded.startswith("・")
            or re.search(r"窓口|ご連絡|お送り|メールアドレス|お問い合わせEmail|mailto:|https?://|フォーム(?:へ|から|に)", excluded)):
        return False
    remaining = conditions[:begin] + conditions[end:]
    remaining = remaining.replace(privacy_intro, "")
    remaining = re.sub(r"当社の個人情報の取り扱いについては、\s*プライバシーポリシー\s*をご確認ください[。.]", "", remaining)
    return not (OTHER_CONTACT.search(remaining)
                or re.search(r"株主優待|株式(?:手続|事務)|配信(?:登録|停止)|メルマガ|入力例|記入例|例\s*[:：]|example\s*[:：]|電話のみ|メールでは受け付けません", remaining, re.I))


def reviewed_financial_stock_email(item: dict, source: dict, email: str, quotes: list[dict]) -> bool:
    """Bind a financial/stock contact section to its readable stock mailbox.

    The complete public operation and response conditions are cited, alongside
    the actual financial-contact link in the same ordered contact-link group.
    Stock administration alone, general IR navigation, public financial
    documents, examples and unrelated mailboxes cannot supply that scope.
    This does not assert individual eligibility or broaden response topics.
    """
    labels = ("決算・財務情報", "株式情報", "株式手続き", "配当金", "株主優待", "株主総会")
    prefix = " ".join(labels) + " 直接のお問い合わせは、下記までご連絡ください。 株式に関するお問い合わせ メールアドレス： "
    restriction = "※株式関連以外のお問い合わせはお送りいただきましても返答いたしかねます。"
    response = ("※お問い合わせに対する回答は平日のみ（土・日・祝日以外）となります。 "
                "また、内容によっては返信にお時間をいただく場合がございます。何卒ご了承ください。")
    quote, text = item.get("quote", ""), source.get("text", "")
    if (quote != prefix + email + " " + restriction + " " + response
            or not isinstance(text, str) or text.count(quote) != 1
            or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
            or email.split("@", 1)[0].lower() in {"example", "sample", "xxxx", "xxxxx"}
            or email.split("@", 1)[1].lower() in {"example.com", "example.org", "example.jp"}
            or re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text) != [email]):
        return False
    source_url = url_key(source.get("url"))
    if source_url is None:
        return False
    namespace = urlsplit(source_url).path.rstrip("/") + "/"
    links = [link for link in source.get("links", []) if isinstance(link, dict)]
    groups = [links[i:i+len(labels)] for i in range(len(links)-len(labels)+1)
              if tuple(link.get("label") for link in links[i:i+len(labels)]) == labels]
    if len(groups) != 1:
        return False
    group = groups[0]
    destinations = [url_key(link.get("url")) for link in group]
    if (any(dest is None or dest == source_url or urlsplit(dest).hostname != urlsplit(source_url).hostname
            or not urlsplit(dest).path.startswith(namespace) for dest in destinations)
            or len(set(destinations)) != len(labels)):
        return False
    return any(e.get("quote") == labels[0] and url_key(e.get("source_link_url")) == destinations[0]
               for e in quotes)


def reviewed_ir_consent_email_section(item: dict, source: dict, email: str) -> bool:
    """Bind a consent/fallback mail address to its complete public IR section.

    This is a bounded heading-to-next-heading assignment, not a larger email
    proximity window. Privacy, partner, general and press sections on the same
    page cannot borrow its IR scope; the actual cited mailto and final public
    fallback sentence must name the requested address.
    """
    heading = "当社IRに関するお問い合わせ"
    headings = source.get("headings", [])
    text = source.get("text", "")
    if headings.count(heading) != 1 or text.count(heading) != 1:
        return False
    index = headings.index(heading)
    if index + 1 >= len(headings) or not isinstance(headings[index + 1], str) or not headings[index + 1]:
        return False
    next_heading = headings[index + 1]
    if text.count(next_heading) != 1:
        return False
    begin, end = text.index(heading), text.index(next_heading)
    section = text[begin:end].strip()
    if (end <= begin or item.get("quote", "").strip() != section
            or not re.search(r"以下の内容についてご同意いただける方は[「『]同意します[」』]をクリックしてお問い合わせ下さい[。.]", section)):
        return False
    fallback = re.search(
        r"［\s*同意します\s*］\s*クリックでメーラーが起動します[。.]起動しない場合は\s*" + re.escape(email) +
        r"\s*に直接ご連絡ください[。.]\Z", section, re.I
    )
    links = [link for link in source.get("links", []) if isinstance(link, dict)
             and link.get("url") == item.get("source_link_url")
             and link.get("url") == "mailto:" + email and link.get("label") == "［ 同意します ］"]
    return bool(fallback and len(links) == 1
                and not re.search(r"入力例|記入例|例\s*[:：]|example\s*[:：]", section[max(0, fallback.start()-40):fallback.start()], re.I)
                and not re.search(r"IR[^。]{0,35}(?:電話のみ|メールでは受け付けません)", section, re.I))


def reviewed_ordered_mailto(item: dict, source: dict, email: str) -> bool:
    """Match a cited IR section to its public mail link in saved DOM order.

    Gakujo displays identical labels instead of email text. This limited path
    needs the sole, fully cited IR section, an explicit captured href, and equal
    counts of unique mail links and visible labels. It cannot assign all mail
    links on a contact directory to IR. The caller requires recorded review.
    """
    quote = item.get("quote", "")
    text = source.get("text", "")
    if not isinstance(quote, str) or not isinstance(text, str) or text.count(quote) != 1:
        return False
    legacy_section = (source.get("headings", []).count("IRについて") == 1
                      and re.match(r"IRについて\s*メールでのお問い合わせ\s*※メーラーが起動します[。.] *メールを送信\s*電話でのお問い合わせ", quote)
                      and re.search(r"(?:^|\s)IR担当(?:\s|$)", quote)
                      and not OTHER_CONTACT.search(quote.split("メールを送信", 1)[0]))
    investor_section = (source.get("headings", []).count("IRに関する問い合わせ先") == 1
                        and re.fullmatch(
                            r"IRに関する問い合わせ先\s+株主さま・一般投資家さまからのお問い合わせ\s+メールで問い合わせ\s+"
                            r"証券アナリスト・機関投資家さまからのお問い合わせ\s+"
                            r"[0-9]{2,4}-[0-9]{2,4}-[0-9]{3,4}\s+[（(]営業時間\s*[0-9：:～〜\s]+\s+土日祝日年末年始を除く[）)]", quote))
    if legacy_section:
        label = "メールを送信"
    elif investor_section:
        # The IR directory separates a general-investor MAIL row from its
        # institutional TELEPHONE row; it does not assign the salon/product
        # row's earlier same-label mailto or assert an individual option.
        if "@" not in email:
            return False
        local, domain = email.lower().split("@", 1)
        if local in {"example", "sample", "xxxx", "xxxxx"} or domain in {"example.com", "example.org", "example.jp"}:
            return False
        label = "メールで問い合わせ"
    else:
        return False
    mail_links = [link for link in source.get("links", []) if isinstance(link, dict)
                  and str(link.get("url", "")).lower().startswith("mailto:")]
    occurrences = list(re.finditer(re.escape(label), text))
    if (len(mail_links) < 2 or len(mail_links) != len(occurrences)
            or len({link["url"] for link in mail_links}) != len(mail_links)
            or any(link.get("label") != label for link in mail_links) or quote.count(label) != 1):
        return False
    quote_start = text.index(quote)
    inside = [i for i, occurrence in enumerate(occurrences)
              if quote_start <= occurrence.start() < quote_start + len(quote)]
    if len(inside) != 1:
        return False
    captured = mail_links[inside[0]]["url"]
    return bool(item.get("source_link_url") == captured and captured[7:].split("?", 1)[0].lower() == email.lower())


def decode_cloudflare_email(href: str) -> str | None:
    """Reproduce the documented derivation of a public protected-link address.

    No browser challenge or remote endpoint is accessed. This is only XOR of
    the captured public hex fragment, followed by strict UTF-8 decoding.
    """
    if not url_key(href):
        return None
    parsed = urlsplit(href)
    if parsed.path != "/cdn-cgi/l/email-protection" or not re.fullmatch(r"(?:[0-9A-Fa-f]{2}){2,2048}", parsed.fragment):
        return None
    raw = bytes.fromhex(parsed.fragment)
    try:
        value = bytes(byte ^ raw[0] for byte in raw[1:]).decode("utf-8").split("?", 1)[0]
    except UnicodeDecodeError:
        return None
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
        return None
    local, domain = value.lower().split("@", 1)
    if local in {"example", "sample", "xxxx", "xxxxx"} or domain in {"example.com", "example.org", "example.jp"}:
        return None
    return value


class SurveyValidator:
    def __init__(self, root: Path, universe: dict[str, dict], previous_root: Path | None = None):
        self.root = root.resolve()
        self.universe = universe
        self.previous_root = previous_root.resolve() if previous_root else None
        self.allowed_roots = [self.root] + ([self.previous_root] if self.previous_root else [])
        self.issues: list[dict] = []
        self.cache: dict[Path, dict | None] = {}

    def issue(self, code: str, kind: str, reason: str, severity: str = "error") -> None:
        self.issues.append({"security_code": code, "kind": kind, "reason": reason, "severity": severity})

    def load_snapshot(self, reference: object, code: str) -> dict | None:
        if not isinstance(reference, str) or not reference or Path(reference).is_absolute():
            self.issue(code, "snapshot_path", "Snapshot must be a nonempty relative path")
            return None
        path = (self.root / reference).resolve()
        if not any(path.is_relative_to(base) for base in self.allowed_roots):
            self.issue(code, "snapshot_path", f"Snapshot outside declared evidence roots: {reference}")
            return None
        if path not in self.cache:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(value, dict):
                    raise ValueError("Snapshot must be an object")
                self.cache[path] = value
            except (OSError, ValueError) as error:
                self.issue(code, "snapshot_unreadable", f"{reference}: {type(error).__name__}")
                self.cache[path] = None
        return self.cache[path]

    def evidence(self, record: dict) -> list[tuple[dict, dict]]:
        code = record["security_code"]
        pairs = []
        references = record.get("evidence", [])
        if not isinstance(references, list):
            self.issue(code, "evidence_type", "evidence must be an array")
            return pairs
        for item in references:
            if not isinstance(item, dict):
                self.issue(code, "evidence_type", "Evidence entry must be an object")
                continue
            source = self.load_snapshot(item.get("snapshot"), code)
            if source is None:
                continue
            valid = True
            quote = item.get("quote")
            quote_matches = public_attribute_quote(item, source) if item.get("extraction_scope") == "form_control_attribute" else (
                item.get("extraction_scope") in {None, "text"} and isinstance(quote, str) and quote in source.get("text", "")
            )
            if not isinstance(quote, str) or not quote.strip() or not quote_matches:
                self.issue(code, "quote_mismatch", f"Exact nonempty quote missing: {item.get('snapshot')}")
                valid = False
            if item.get("url") != source.get("url", source.get("requested_url")):
                self.issue(code, "evidence_url", f"Evidence URL differs from snapshot: {item.get('snapshot')}")
                valid = False
            if item.get("retrieved_at") != source.get("retrieved_at") or not aware_time(source.get("retrieved_at")):
                self.issue(code, "evidence_time", f"Evidence retrieval time differs or lacks offset: {item.get('snapshot')}")
                valid = False
            if source.get("submitted") is not False:
                self.issue(code, "submission_flag", f"Read-only submitted:false is required: {item.get('snapshot')}")
                valid = False
            if valid:
                pairs.append((item, source))
        return pairs

    @staticmethod
    def successful(source: dict) -> bool:
        status = source.get("http_status")
        return (
            isinstance(status, int) and not isinstance(status, bool) and 200 <= status < 300
            and isinstance(source.get("text"), str) and bool(source["text"].strip())
            and not source.get("error")
        )

    def derived_public_email(self, record: dict, pairs: list[tuple[dict, dict]], email: str) -> bool:
        if not manual_review_valid(record):
            return False
        derivation = record["manual_review"].get("public_email_derivation")
        if not isinstance(derivation, dict) or derivation.get("method") != "cloudflare_email_protection_public_href_xor":
            return False
        href = derivation.get("encoded_href")
        if not isinstance(href, str) or decode_cloudflare_email(href) != email or derivation.get("decoded_address") != email or not derivation.get("decode_steps"):
            return False
        for evidence, source in pairs:
            if (not self.successful(source) or evidence.get("snapshot") != derivation.get("snapshot")
                    or evidence.get("source_link_url") != href):
                continue
            protected = [link for link in source.get("links", []) if isinstance(link, dict)
                         and link.get("url") == href and isinstance(link.get("label"), str)]
            if len(protected) != 1 or not protected[0]["label"]:
                continue
            label = protected[0]["label"]
            same_label_links = [link for link in source.get("links", []) if isinstance(link, dict)
                                and link.get("label") == label
                                and isinstance(link.get("url"), str)
                                and urlsplit(link["url"]).path == "/cdn-cgi/l/email-protection"]
            occurrences = list(re.finditer(re.escape(label), source["text"]))
            if len(occurrences) != len(same_label_links):
                # Without a one-to-one captured label order, association is
                # not recoverable from the stored representation alone.
                continue
            index = next(i for i, link in enumerate(same_label_links) if link["url"] == href)
            occurrence = occurrences[index]
            citation_spans = [match for match in re.finditer(re.escape(evidence["quote"]), source["text"])
                              if match.start() <= occurrence.start() and occurrence.end() <= match.end()]
            scoped = any(not OTHER_CONTACT.search(
                evidence["quote"][:occurrence.start() - match.start()]
            ) for match in citation_spans)
            if not scoped:
                continue
            if ir_page_heading(source):
                return True
            targets = {url_key(source.get("url")), url_key(source.get("requested_url"))}
            for parent_evidence, parent in pairs:
                if not self.successful(parent):
                    continue
                for link in parent.get("links", []):
                    label = link.get("label", "")
                    if url_key(link.get("url")) in targets and label in parent_evidence["quote"] and IR_CONTACT.search(label):
                        return True
        return False

    @staticmethod
    def quoted_ir_direction(evidence: dict, source: dict, targets: set[str | None], *, scope_pairs: list[tuple[dict, dict]] | None = None) -> bool:
        """A quoted operational instruction can designate a generically named
        contact link. A navigation heading plus its Contact footer cannot.
        """
        for link in source.get("links", []):
            label = link.get("label", "")
            if not isinstance(label, str) or not label or url_key(link.get("url")) not in targets:
                continue
            if IR_CONTACT.search(label) and label in evidence["quote"]:
                return True
            if evidence.get("source_link_url") == link.get("url"):
                # A literal IR instruction points HERE, rather than the
                # generic Contact footer. The exact captured href and unique
                # "here" target are mandatory, including query parameters.
                direct_here = re.fullmatch(r"\*?(?:IR|ＩＲ)に関するお問い合わせは\s*こちら", evidence["quote"].strip(), re.I)
                if direct_here and label == "こちら":
                    here_links = [l for l in source.get("links", []) if isinstance(l, dict) and l.get("label") == "こちら"]
                    here_targets = {url_key(l.get("url")) for l in here_links}
                    if here_targets == {url_key(link.get("url"))}:
                        return True
                    # Repeated "here" anchors can still be bound by their
                    # saved DOM/text order. Require equal complete counts and
                    # a single IR quote/target; never choose every generic
                    # link, or a same-label link from another contact row.
                    text = source.get("text", "")
                    occurrences = list(re.finditer(r"(?<!\S)こちら(?=\s|$)", text))
                    quote = evidence["quote"].strip()
                    if (len(occurrences) == len(here_links) and text.count(quote) == 1
                            and sum(l.get("url") == link.get("url") for l in here_links) == 1):
                        position = text.index(quote) + quote.rindex("こちら")
                        indexes = [i for i, occurrence in enumerate(occurrences) if occurrence.start() == position]
                        if len(indexes) == 1 and here_links[indexes[0]].get("url") == evidence.get("source_link_url"):
                            return True
                # This FAQ offers the form as an explicit alternative to
                # phoning the IR contact, within the SAME quoted answer.
                # Phone-only IR directions and a different general form do
                # not establish this alternative.
                faq_form = re.fullmatch(
                    r"(?:IR|ＩＲ)に関する問い合せはどうすればできますか[?？]\s*"
                    r"当社[^。]{0,100}IR担当[^。]{0,160}お問い合せください[。.]\s*"
                    r"もしくは当社ホームページの\s*(「お問い合せ」)\s*のフォームに入力いただき送信してください[。.]",
                    evidence["quote"].strip(), re.I
                )
                if faq_form and label == faq_form[1]:
                    faq_targets = {url_key(l.get("url")) for l in source.get("links", [])
                                   if isinstance(l, dict) and l.get("label") == label}
                    if faq_targets == {url_key(link.get("url"))}:
                        return True
                # A numbered IR FAQ can directly request inquiries through
                # its uniquely captured form link. Bind the entire question
                # and answer, not the FAQ's ordinary Contact navigation. The
                # exact target must also contain one cited native post form;
                # its search form and other contact destinations are separate.
                faq_request = re.fullmatch(
                    r"Q\s+[0-9]+\s+(?:IR|ＩＲ)に関する問合せ先を教えてください[。.]\s*"
                    r"「\s*(問い合わせフォーム)\s*」よりお問い合わせを頂けますようお願いいたします[。.]",
                    evidence["quote"].strip(), re.I
                )
                if (faq_request and label == faq_request[1] and scope_pairs
                        and IR_MARKER.search(source.get("title", ""))
                        and source.get("text", "").count(evidence["quote"].strip()) == 1
                        and sum(isinstance(l, dict) and l.get("label") == label for l in source.get("links", [])) == 1):
                    for fields_evidence, fields_source in scope_pairs:
                        if (fields_source is source or not SurveyValidator.successful(fields_source)
                                or url_key(link.get("url")) not in {
                                    url_key(fields_source.get("url")), url_key(fields_source.get("requested_url"))}
                                or urlsplit(fields_source.get("url", "")).hostname != urlsplit(source.get("url", "")).hostname):
                            continue
                        forms = [f for f in fields_source.get("forms", []) if question_form(f) or reviewed_question_form(f)]
                        if len(forms) != 1:
                            continue
                        form = forms[0]
                        fields = form.get("text", "").strip()
                        controls = [c for c in form.get("controls", []) if isinstance(c, dict)
                                    and c.get("tag") in {"input", "select", "textarea"}
                                    and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
                        action = urlsplit(urljoin(fields_source.get("url", ""), str(form.get("action", ""))))
                        if (str(form.get("method", "")).lower() == "post"
                                and fields and fields_evidence["quote"].strip() == fields
                                and fields_source.get("text", "").count(fields) == 1
                                and form_labels(form).startswith("お問い合わせ内容 必須 ")
                                and "メールアドレス 必須" in form_labels(form)
                                and controls and controls[0].get("tag") == "textarea"
                                and re.fullmatch(r"aform-field-[0-9]+", str(controls[0].get("name", "")))
                                and any(c.get("tag") == "input" and c.get("type") == "email"
                                        and re.fullmatch(r"aform-field-[0-9]+", str(c.get("name", ""))) for c in controls)
                                and action.hostname == urlsplit(fields_source.get("url", "")).hostname
                                and action.path.endswith("/AForm/aform_engine.cgi") and not action.query and not action.fragment):
                            return True
                # A FAQ may display "お問い合わせ フォーム" inline while
                # the captured anchor label is "お問い合わせフォーム".
                # Normalize only that cited link phrase, inside a literal IR
                # use instruction, and require a unique captured target. A
                # common footer or directions to read IR documents do not bind.
                direction = re.search(
                    r"(?:IR|ＩＲ)に関するお問い合わせは[、,]\s*こちらの\s*"
                    r"(お問い合わせ\s*フォーム)からお願い(?:致|いた)します[。.]",
                    evidence["quote"], re.I
                )
                if direction and re.sub(r"\s+", "", label) == re.sub(r"\s+", "", direction[1]):
                    matching_targets = {url_key(l.get("url")) for l in source.get("links", []) if isinstance(l, dict)
                                        and isinstance(l.get("label"), str)
                                        and re.sub(r"\s+", "", l["label"]) == re.sub(r"\s+", "", direction[1])}
                    if matching_targets == {url_key(link.get("url"))}:
                        return True
            if IR_FORM_DIRECTION.search(evidence["quote"]) and label in evidence["quote"] and re.search(
                r"こちら|問(?:い)?合(?:わ)?せ|問い合わせ|フォーム|contact|form", label, re.I
            ):
                return True
            # A dedicated IR page can assign the contact block below a cited
            # instruction, with a separately cited mail-form link in that block.
            # Require both citations on this SAME page and no intervening
            # product/privacy/recruitment purpose; navigation alone fails.
            if scope_pairs and ir_page_heading(source):
                direction = re.search(r"メールフォーム\s*" + re.escape(label) + r"\s*ページよりお願いいたします", evidence["quote"])
                if not direction:
                    continue
                for scope_evidence, scope_source in scope_pairs:
                    if scope_source is not source:
                        continue
                    assignment = re.search(r"(?:IR|ＩＲ)に関するお問(?:い)?合(?:わ)?せ[^。]{0,35}下記までお願いいたします", scope_evidence["quote"], re.I)
                    if not assignment:
                        continue
                    text = source["text"]
                    start = text.find(assignment[0])
                    end = text.find(direction[0], start + len(assignment[0])) if start >= 0 else -1
                    if end >= 0 and not OTHER_CONTACT.search(text[start + len(assignment[0]):end]):
                        return True
        return False

    def reviewed_finite_form_witness(self, record: dict, source: dict, pairs: list[tuple[dict, dict]],
                                    index: int, method: str, action: str | None, layout: list[dict]) -> dict | None:
        """Check the complete cited native form used only by the finite branches below."""
        if (not manual_review_valid(record) or not self.successful(source) or source.get("submitted") is not False
                or record.get("contact_url") != source.get("url") or not aware_time(source.get("retrieved_at"))):
            return None
        forms = source.get("forms")
        if not isinstance(forms, list) or len(forms) <= index or not isinstance(forms[index], dict):
            return None
        form = forms[index]
        fields = form.get("text")
        controls = form.get("controls")
        if (form.get("method") != method or "action" not in form or form["action"] != action
                or not isinstance(fields, str) or not fields or source["text"].count(fields) != 1
                or not isinstance(controls, list) or any(not isinstance(c, dict) for c in controls)
                or [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls] != layout
                or any(refusal in source["text"] for refusal in (
                    "IRのお問い合わせは受け付けません", "IRに関するお問い合わせは電話のみ",
                    "個人投資家のお問い合わせはお断り", "個人のお問い合わせは受け付けません"))
                or not any(s is source and e.get("quote") == fields and e.get("url") == source.get("url")
                           and e.get("retrieved_at") == source.get("retrieved_at")
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == index
                           and ("form_index" not in e or type(e["form_index"]) is int and e["form_index"] == index)
                           for e,s in pairs)):
            return None
        return form

    def reviewed_finite_native_ir_form(self, record: dict, pairs: list[tuple[dict, dict]], seed: dict | None) -> bool | None:
        """Dispatch four complete saved reception families without changing generic form binding."""
        if not manual_review_valid(record):
            return None
        families = (
            ("お問い合わせ モリタグループは、皆様から寄せられた貴重なご意見・ご質問を", self.reviewed_ir_checkbox_after_long_policy),
            ("1 入力画面 現在表示されている画面です。 2 確認画面 現在表示されている画面です。 3 完了画面", self.reviewed_ir_subject_checkboxes),
            ("会社名 ご住所 〒 - お名前 * お役職 電話番号 - - FAX番号 - - メールアドレス * ご質問", self.reviewed_ir_japanese_named_question),
            ("会社名 例）株式会社 Orchestra Holdings 所属部署 例）営業部 お名前 例）山田 太郎 返信先メールアドレス", self.reviewed_ir_formmailer_reply_fields),
        )
        witnesses = {}
        for _, source in pairs:
            for index, form in enumerate(source.get("forms", [])):
                for prefix, handler in families:
                    if not isinstance(form, dict) or not str(form.get("text", "")).startswith(prefix):
                        continue
                    if handler == self.reviewed_ir_subject_checkboxes:
                        controls = form.get("controls", [])
                        if (not isinstance(controls, list) or len(controls) != 16
                                or any(not isinstance(c, dict) for c in controls)
                                or [c.get("name") for c in controls[:8]] != ["companyname","username","email","tel","zip","pref","addr","building"]
                                or any(c.get("tag") != "input" or c.get("type") != "checkbox" or c.get("name") != "subject[]" for c in controls[8:14])
                                or controls[2].get("type") != "email" or controls[14].get("tag") != "textarea" or controls[14].get("name") != "message"
                                or controls[15].get("name") != "agreement[]"
                                or "ご用件 当社の事業内容・サービスについて 製品や技術仕様・購入・メンテナンスなどについて IR情報・投資・総会などについて 採用情報・求人応募などについて 会社情報・事業所・環境への取り組みについて その他" not in form.get("text", "")):
                            continue
                    witnesses[(id(source), index)] = (source, handler)
        if not witnesses:
            return None
        if len(witnesses) != 1:
            return False
        source, handler = next(iter(witnesses.values()))
        return handler(record, source, pairs)

    def reviewed_ir_checkbox_after_long_policy(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The actual external issuer form has exactly two IR/other category checkboxes."""
        official = record.get("official_url", "")
        if not isinstance(official, str) or not official.startswith("https://") or not official.endswith(".com/"):
            return False
        parsed = urlsplit(official)
        if parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname:
            return False
        target = official[:-5] + "-contact.com/mhd/contacthd/"
        company = identity_key(record.get("company_name", ""))
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or len(source.get("forms", [])) != 1 or len(company) < 2
                or not source.get("title", "").endswith("｜資料請求･お問い合わせ – お問い合わせ")
                or identity_key(source["title"].split("｜",1)[0]) != company):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/mhd/contacthd/#wpcf7-f8-p16-o1", [{'tag': 'input', 'type': 'text', 'name': 'your-name'}, {'tag': 'input', 'type': 'text', 'name': 'your-namekana'}, {'tag': 'input', 'type': 'email', 'name': 'your-email'}, {'tag': 'input', 'type': 'text', 'name': 'your-company'}, {'tag': 'input', 'type': 'text', 'name': 'your-companykana'}, {'tag': 'input', 'type': 'text', 'name': 'your-busyo'}, {'tag': 'input', 'type': 'text', 'name': 'your-zip', 'id': 'zip'}, {'tag': 'select', 'name': 'your-pref', 'id': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'your-addr', 'id': 'addr'}, {'tag': 'input', 'type': 'tel', 'name': 'your-tel'}, {'tag': 'input', 'type': 'checkbox', 'name': 'your-sbt'}, {'tag': 'input', 'type': 'checkbox', 'name': 'your-sbt'}, {'tag': 'textarea', 'name': 'your-message'}, {'tag': 'input', 'type': 'submit'}])
        purpose = "必須 お問い合わせの種類 IR関連 その他のお問い合わせ 必須 お問い合わせ内容"
        if (form is None or not form["text"].endswith(purpose)
                or "必須 E-mailアドレス 任意 御社名 任意 御社名（ふりがな） 任意 部署名" not in form["text"]
                or "【お問い合わせ窓口】 " not in form["text"]
                or company not in identity_key(form["text"].split("【お問い合わせ窓口】 ",1)[1].split(" 総務部",1)[0])
                or not any(s is source and e["quote"] == purpose and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e,s in pairs)):
            return False
        for e,parent in pairs:
            if (not self.successful(parent) or parent.get("submitted") is not False
                    or parent.get("url") != official + "ir/" or parent.get("requested_url") != parent.get("url")
                    or parent.get("redirects") or not aware_time(parent.get("retrieved_at"))
                    or e["quote"] != parent.get("title") or not e["quote"].startswith("株主・投資家情報 | ")
                    or identity_key(e["quote"].split(" | ",1)[1]) != company
                    or "株主・投資家情報 HOME 株主・投資家情報 IRニュース " not in parent["text"]
                    or "IR資料室 決算短信 有価証券報告書 統合報告書" not in parent["text"]
                    or "株主・投資家情報" not in parent.get("headings", [])
                    or not any("決算説明資料" in h for h in parent.get("headings", []))):
                continue
            links = parent.get("links", [])
            if (len(links) > 2 and links[2] == {"url":target,"href":target,"label":"お問い合わせ"}
                    and any(p is parent and pe["quote"] == "お問い合わせ" and type(pe.get("source_link_index")) is int and pe["source_link_index"] == 2
                            and pe.get("source_link_url") == target and pe.get("source_link_href") == target and pe.get("source_link_label") == "お問い合わせ" for pe,p in pairs)):
                return True
        return False

    def reviewed_ir_subject_checkboxes(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Keep the six subject choices and public error text on one native question form."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/contact/"
        company = identity_key(record.get("company_name", ""))
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != "お問い合わせ | 株式会社" + record.get("company_name", "")
                or len(source.get("forms", [])) != 3):
            return False
        for search in (source["forms"][0], source["forms"][2]):
            if (search.get("method") != "get" or search.get("action") != official or search.get("text") != "製品情報を検索"
                    or search.get("controls") != [{"tag":"input","type":"text","name":"s","placeholder":"製品名・用途などで検索","id":"s"}]):
                return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 1, "post", "", [{'tag': 'input', 'type': 'text', 'name': 'companyname'}, {'tag': 'input', 'type': 'text', 'name': 'username'}, {'tag': 'input', 'type': 'email', 'name': 'email'}, {'tag': 'input', 'type': 'tel', 'name': 'tel'}, {'tag': 'input', 'type': 'text', 'name': 'zip', 'id': 'zip'}, {'tag': 'select', 'name': 'pref', 'id': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'addr', 'id': 'addr'}, {'tag': 'input', 'type': 'text', 'name': 'building'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'subject[]'}, {'tag': 'textarea', 'name': 'message'}, {'tag': 'input', 'type': 'checkbox', 'name': 'agreement[]'}])
        purpose = "ご用件 当社の事業内容・サービスについて 製品や技術仕様・購入・メンテナンスなどについて IR情報・投資・総会などについて 採用情報・求人応募などについて 会社情報・事業所・環境への取り組みについて その他"
        if (form is None or purpose + " メッセージ プライバシーポリシー " not in form["text"]
                or not form["text"].startswith("1 入力画面 現在表示されている画面です。 2 確認画面 現在表示されている画面です。 3 完了画面 現在表示されている画面です。 会社名 お名前 Eメール ")
                or not form["text"].endswith("予期しない問題が発生しました。 後でもう一度やり直すか、他の方法で管理者に連絡してください。")
                or not any(s is source and e["quote"] == purpose and type(e.get("source_form_index")) is int and e["source_form_index"] == 1 for e,s in pairs)):
            return False
        identity = "投資家の皆さまへ ㈱" + record.get("company_name", "") + " 東証スタンダード " + str(record.get("security_code", ""))
        return any(self.successful(parent) and parent.get("submitted") is False
                   and parent.get("url") == official + "ir/" and parent.get("requested_url") == parent.get("url") and not parent.get("redirects")
                   and parent.get("title") == "IR情報一覧 | 株式会社" + record.get("company_name", "")
                   and "投資家の皆さまへ" in parent.get("headings", []) and parent["text"].count(identity) == 1
                   and "有価証券報告書" in parent["text"] and "決算短信" in parent["text"]
                   and e["quote"] == identity and e.get("role") == "company_security_code_and_financial_ir"
                   and aware_time(parent.get("retrieved_at")) and len(company) >= 2 for e,parent in pairs)

    def reviewed_ir_japanese_named_question(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The explicit IR operation names the Japanese question field, not the address textarea."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/contact/ir/form/"
        company = identity_key(record.get("company_name", ""))
        operation = "ＩＲ情報についてご質問のある方は、こちらからお問い合せ下さい。"
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or len(source.get("forms", [])) != 1 or len(company) < 2
                or not source.get("title", "").startswith("入力フォーム | ")
                or identity_key(source["title"].split(" | ")[1]) != company
                or source.get("text", "").count("TOP > 各種お問い合せ > ＩＲに関するお問い合せ > 入力フォーム 入力フォーム " + operation) != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "", [{'tag': 'input', 'type': 'text', 'name': '会社名'}, {'tag': 'input', 'type': 'text', 'name': '郵便番号[data][0]'}, {'tag': 'input', 'type': 'text', 'name': '郵便番号[data][1]'}, {'tag': 'textarea', 'name': 'ご住所'}, {'tag': 'input', 'type': 'text', 'name': 'お名前'}, {'tag': 'input', 'type': 'text', 'name': 'お役職'}, {'tag': 'input', 'type': 'text', 'name': '電話番号[data][0]'}, {'tag': 'input', 'type': 'text', 'name': '電話番号[data][1]'}, {'tag': 'input', 'type': 'text', 'name': '電話番号[data][2]'}, {'tag': 'input', 'type': 'text', 'name': 'FAX番号[data][0]'}, {'tag': 'input', 'type': 'text', 'name': 'FAX番号[data][1]'}, {'tag': 'input', 'type': 'text', 'name': 'FAX番号[data][2]'}, {'tag': 'input', 'type': 'email', 'name': 'メールアドレス'}, {'tag': 'textarea', 'name': 'ご質問'}, {'tag': 'input', 'type': 'submit', 'name': 'submitConfirm'}])
        if (form is None or form["text"] != "会社名 ご住所 〒 - お名前 * お役職 電話番号 - - FAX番号 - - メールアドレス * ご質問"
                or source["text"].count("* が付いている項目は入力必須項目です。 " + form["text"] + " ※フォームより 送信できない場合は、") != 1):
            return False
        for e,parent in pairs:
            links = parent.get("links", [])
            if (not self.successful(parent) or parent.get("submitted") is not False or parent.get("url") != official + "contact/ir/"
                    or parent.get("requested_url") != parent.get("url") or parent.get("redirects")
                    or not parent.get("title", "").startswith("ＩＲに関するお問い合せ | ")
                    or identity_key(parent["title"].split(" | ")[1]) != company
                    or "ＩＲに関するお問い合せ" not in parent.get("headings", [])
                    or "IR情報 開示情報 決算短信 有価証券報告書 中期経営計画 株主総会" not in parent["text"]
                    or e["quote"] != "同意する" or type(e.get("source_link_index")) is not int or e["source_link_index"] != 30
                    or e.get("source_link_url") != target or len(links) <= 30):
                continue
            if (links[30] == {"url":target,"href":"/contact/ir/form/","label":"同意する"}
                    and any(s is parent and pe["quote"] == parent["title"] for pe,s in pairs)
                    and aware_time(parent.get("retrieved_at"))):
                return True
        return False

    def reviewed_ir_formmailer_reply_fields(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A dedicated IR input operation binds its opaque reply/confirmation and question fields."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/ir/inquiry/"
        company = identity_key(record.get("company_name", ""))
        title = source.get("title", "")
        operation = "IRに関するお問い合わせ: 入力画面 [ 1/2 ] 下記のフォームに必要事項を入力の上、「送信する」ボタンを押してください。"
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or len(source.get("forms", [])) != 1 or len(company) < 2
                or not title.startswith("IRに関するお問い合わせ｜株式会社")
                or identity_key(title.split("｜",1)[1].split("－",1)[0]) != company
                or not {"CONTACT IRに関するお問い合わせ","IRに関するお問い合わせ: 入力画面 [ 1/2 ]"}.issubset(source.get("headings", []))
                or source["text"].count(operation) != 1 or not any(s is source and e["quote"] == title for e,s in pairs)
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "https://pro.form-mailer.jp/fm/service/Forms/complete", [{'tag': 'input', 'type': 'text', 'name': 'field_2014335', 'id': ''}, {'tag': 'input', 'type': 'text', 'name': 'field_2014336', 'id': ''}, {'tag': 'input', 'type': 'text', 'name': 'field_2014337', 'id': ''}, {'tag': 'input', 'type': 'text', 'name': 'field_2014338', 'id': ''}, {'tag': 'input', 'type': 'text', 'name': 'field_2014338_mcon', 'id': ''}, {'tag': 'textarea', 'name': 'field_2014339', 'id': ''}, {'tag': 'input', 'type': 'checkbox', 'name': 'field_2014340', 'id': 'privacy1'}])
        if (form is None or not form["text"].startswith("会社名 例）株式会社 Orchestra Holdings 所属部署 例）営業部 お名前 例）山田 太郎 返信先メールアドレス ")
                or "確認のため、もう一度入力してください。 例）sample@orchestraholdings.co.jp お問い合わせ内容 個人情報の取り扱いについて" not in form["text"]
                or source["text"].count(operation + " なお、内容によっては、ご連絡までお時間がかかるものがございます。 あらかじめご了承ください。 " + form["text"]) != 1):
            return False
        for _,parent in pairs:
            links = parent.get("links", [])
            if (self.successful(parent) and parent.get("submitted") is False and parent.get("url") == official + "ir/"
                    and parent.get("requested_url") == parent.get("url") and not parent.get("redirects")
                    and str(parent.get("title", "")).startswith("IR情報｜株式会社")
                    and identity_key(parent["title"].split("｜",1)[1].split("－",1)[0]) == company
                    and "IR 株主・投資家向け情報" in parent.get("headings", [])
                    and "IRライブラリ 決算短信 決算説明資料 有価証券報告書" in parent["text"]
                    and len(links) > 30 and links[30] == {"url":target,"href":"/ir/inquiry/","label":"IRお問い合わせ"}
                    and aware_time(parent.get("retrieved_at"))):
                return True
        return False

    def reviewed_ir_personal_shareholder_checkboxes(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A seven-checkbox audience on the indexed IR form includes personal shareholders."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/ir/ir-contact/"
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != "IRに関するお問い合わせ | 株式会社" + record.get("company_name", "")
                or len(source.get("forms", [])) != 1):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", None, [{'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14660'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14661'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14662'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14663'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14664'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14665'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal1466[]', 'id': 'formElementVal14666'}, {'tag': 'textarea', 'name': 'formElementVal1467', 'id': 'formElementVal1467'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal1468Sei', 'id': 'formElementVal1468Sei'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal1468Mei', 'id': 'formElementVal1468Mei'}, {'tag': 'input', 'type': 'email', 'name': 'formElementVal1469', 'id': 'formElementVal1469'}, {'tag': 'input', 'type': 'tel', 'name': 'formElementVal1470', 'id': 'formElementVal1470'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal1471', 'id': 'formElementVal1471'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal1472', 'id': 'formElementVal1472'}, {'tag': 'input', 'type': 'checkbox', 'name': 'agreementFlg', 'id': 'agreementFlg'}])
        audience = "お客様について 必須 個人の株主様 当社株式の購入をお考えの方 機関投資家の方 リサーチ機関関係者・アナリスト 証券関係者 メディア関係者 その他"
        if (form is None or not form["text"].startswith("IRに関するお問い合わせ CONTACT 入力画面 入力内容の 確認 送信完了 " + audience + " お問い合わせ内容 必須")
                or not any(s is source and e["quote"] == audience and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e,s in pairs)
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)):
            return False
        return any(self.successful(parent) and parent.get("submitted") is False
                   and parent.get("url") == official + "ir/stock-information/" and parent.get("requested_url") == parent.get("url")
                   and parent.get("title") == "株式情報 | 株式会社" + record.get("company_name", "")
                   and "株式情報 IR INFORMATION 上場市場 東京証券取引所グロース市場 証券コード " + str(record.get("security_code", "")) + " 事業年度" in parent["text"]
                   and "株式情報" in parent.get("headings", []) and "株主総会 電子公告・決算公告 株価情報" in e["quote"]
                   and "ディスクロージャーポリシー よくあるご質問 免責事項 IRに関するお問い合わせフォーム" in e["quote"]
                   and aware_time(parent.get("retrieved_at")) for e,parent in pairs)

    def reviewed_ir_person_standing_company_entry(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The exact personal company entry belongs to the saved GET form; missing IDs remain missing."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/contact/"
        company = identity_key(record.get("company_name", ""))
        operation = "当社への製品情報・会社情報・IR情報等に関するお問い合わせを希望するお客様は、以下のフォームに必要事項をご記入の上、送信をお願いいたします。"
        personal = "個人の立場でのご質問の場合は、「個人」とご入力ください。"
        purpose = "投資家情報、広報、IR、WEBサイト等に関するお問い合わせ"
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != "お問い合わせ - " + record.get("company_name", "") + "株式会社"
                or len(source.get("forms", [])) != 2 or source["forms"][0] != {"action":"/search/","method":"get","controls":[{"tag":"input","type":"search","name":"s","placeholder":"","aria-label":"検索"}],"text":""}
                or source["text"].count(operation) != 1 or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 1, "get", None, [{'tag': 'input', 'type': 'text', 'name': 'xtitle98'}, {'tag': 'input', 'type': 'checkbox', 'name': 'xagree99'}, {'tag': 'input', 'type': 'email'}, {'tag': 'input', 'type': 'text'}, {'tag': 'input', 'type': 'text'}, {'tag': 'input', 'type': 'text'}, {'tag': 'input', 'type': 'text', 'id': 'kana'}, {'tag': 'select'}, {'tag': 'input', 'type': 'text'}, {'tag': 'input', 'type': 'tel'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'input', 'type': 'radio'}, {'tag': 'textarea'}, {'tag': 'input', 'type': 'checkbox'}])
        if (form is None or not form["text"].startswith("表題(必須)： 同意(必須)： メールアドレス 必須 0 / 140 文字 入力間違いにご注意ください。 会社名 必須 0 / 100 文字 " + personal + " 部署名 任意")
                or "▶ 会社に関するお問い合わせ " + purpose + " よくある質問 もご参照ください。 人事・採用" not in form["text"]
                or not any(s is source and e["quote"] == personal and type(e.get("source_form_index")) is int and e["source_form_index"] == 1 for e,s in pairs)
                or not any(s is source and e["quote"] == purpose and type(e.get("source_form_index")) is int and e["source_form_index"] == 1 for e,s in pairs)
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)):
            return False
        return any(self.successful(parent) and parent.get("submitted") is False and parent.get("url") == official + "ir/"
                   and parent.get("requested_url") == parent.get("url") and parent.get("title") == "IR 情報 - " + record.get("company_name", "") + "株式会社"
                   and {"最新の決算資料","IR News"}.issubset(parent.get("headings", []))
                   and "最新の決算資料 直近のイベント 一覧 " in parent["text"] and "決算発表 IR News 一覧 Information 一覧" in parent["text"]
                   and "IR 情報 IR Information トップメッセージ 事業紹介 個人投資家の皆様へ 業績・財務ハイライト IR ライブラリ 株式・株価情報" in e["quote"]
                   and aware_time(parent.get("retrieved_at")) and len(company) >= 2 for e,parent in pairs)

    def reviewed_ir_company_person_placeholder(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Bind a literal company/person placeholder to its actual control on the complete IR form."""
        official = record.get("official_url", "")
        if not url_key(official):
            return False
        parsed = urlsplit(official)
        target = "https://" + parsed.netloc + "/ja/contactus/ir"
        company = record.get("company_name", "")
        title = "IRについてのお問い合わせ | 株式会社" + company + "（SEMBA）"
        operation = "IRに関するお問い合わせフォーム 入力 確認 完了 ●は入力必須項目です。"
        redirects = source.get("redirects", [])
        if (parsed.scheme != "https" or parsed.path != "/ja" or parsed.query or parsed.fragment or parsed.netloc != parsed.hostname
                or source.get("url") != target or source.get("requested_url") != target + "/" or source.get("title") != title
                or len(source.get("forms", [])) != 1 or len(redirects) != 1 or not isinstance(redirects[0], dict)
                or redirects[0].get("requested_url") != target + "/" or redirects[0].get("url") != target + "/"
                or type(redirects[0].get("http_status")) is not int or redirects[0]["http_status"] != 301
                or redirects[0].get("redirect_target") != target or not aware_time(redirects[0].get("retrieved_at"))
                or source["text"].count("HOME お問い合わせ IRについて contact " + operation) != 1
                or not any(s is source and e["quote"] == title for e,s in pairs)
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/ja/contactus/ir#wpcf7-f52147-o1", [{'tag': 'textarea', 'name': 'your-message'}, {'tag': 'input', 'type': 'text', 'name': 'your-name'}, {'tag': 'input', 'type': 'text', 'name': 'your-kana'}, {'tag': 'input', 'type': 'email', 'name': 'your-email'}, {'tag': 'input', 'type': 'tel', 'name': 'your-tel'}, {'tag': 'input', 'type': 'text', 'name': 'your-company'}, {'tag': 'input', 'type': 'text', 'name': 'your-department'}, {'tag': 'input', 'type': 'text', 'name': 'your-position'}, {'tag': 'input', 'type': 'text', 'name': 'your-zip', 'id': 'zip'}, {'tag': 'select', 'name': 'your-pref', 'id': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'your-city', 'id': 'city'}, {'tag': 'input', 'type': 'text', 'name': 'your-address', 'id': 'address1'}, {'tag': 'input', 'type': 'text', 'name': 'your-building', 'id': 'address2'}, {'tag': 'input', 'type': 'submit'}])
        placeholder = "株式会社" + company + " ※個人の場合は「個人」"
        if (form is None or not form["text"].startswith("お問い合わせ内容 （最大2000文字） 氏名 ふりがな メールアドレス 電話番号 会社・組織名 部署名 役職名 ")
                or form["controls"][5].get("placeholder") != placeholder
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)):
            return False
        return any(s is source and e.get("extraction_scope") == "form_control_attribute"
                   and e.get("field_path") == "forms.0.controls.5.placeholder"
                   and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                   and e.get("quote") == placeholder for e,s in pairs)

    def reviewed_ir_operation_after_policy(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """This designated IR questionnaire keeps its instruction before the intervening privacy policy."""
        if not manual_review_valid(record):
            return None
        witnesses = {}
        for _, source in pairs:
            for index, form in enumerate(source.get("forms", [])):
                names = {c.get("name") for c in form.get("controls", []) if isinstance(c, dict)}
                if {"form[name]", "form[email-confirm]", "form[naiyo]"}.issubset(names):
                    witnesses[(id(source), index)] = source
        if not witnesses:
            return None
        if len(witnesses) != 1:
            return False
        (_, index), source = next(iter(witnesses.items()))
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if official is None or company != self.universe.get(record.get("security_code"), {}).get("company_name"):
            return False
        target = official + "contact/cmenu/contact1"
        if (index != 0 or source.get("url") != target or source.get("requested_url") != target
                or self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "IRについて - " + company + "株式会社"
                or source.get("headings") != [source["title"], "IRについて", "IRについて"]
                or len(source.get("forms", [])) != 1):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", target, [{'tag': 'input', 'type': 'text', 'name': 'form[name]', 'id': 'name'}, {'tag': 'input', 'type': 'text', 'name': 'form[email]', 'id': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'form[email-confirm]', 'id': 'email-confirm'}, {'tag': 'input', 'type': 'text', 'name': 'form[tel]', 'id': 'tel'}, {'tag': 'input', 'type': 'text', 'name': 'form[zip]', 'id': 'zip'}, {'tag': 'select', 'name': 'form[pref][]', 'id': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'form[address]', 'id': 'address'}, {'tag': 'textarea', 'name': 'form[naiyo]', 'id': 'naiyo'}, {'tag': 'input', 'type': 'submit', 'name': 'form[submit]', 'id': 'submit'}])
        operation = ("IRについて お問い合わせは下記のフォームから送信下さい。後日ご連絡いたします。 "
                     "回答には2～3営業日のお時間をいただく場合がございます。お急ぎの方は、お電話にてお願いいたします。 "
                     "お気軽に、お問い合わせ下さい。")
        privacy = ("【プライバシーポリシー】 当サイトは、お客様の個人情報について、お客様の承諾が無い限り第三者に開示、提供を一切いたしません。"
                   "お客様から個人情報をご提供していただき、お客様へのサービスにご利用させていただく場合があります。"
                   "その目的以外には利用いたしません。そして、ご提供いただいた個人情報を取り扱うにあたり管理責任者を置き、適切な管理を行っております。")
        if (form is None or not form["text"].startswith("未入力の必須項目があります。 お名前 (必須) 必須項目です。 Eメールアドレス (必須) Eメールアドレスを入力してください。 Eメールアドレス(確認用) (必須) Eメールアドレスが一致しません。 ")
                or not form["text"].endswith(" 市区町村番地/建物名/部屋番号 不正な入力です。 お問合せ内容 (必須) 必須項目です。 認証項目 必須項目です。")
                or not any(s is source and e["quote"] == operation for e, s in pairs)
                or source["text"].count("IRについて Home お問い合わせ 各種お問い合わせはこちらから IRについて " + operation) != 1
                or source["text"].count(operation + " 06-6482-2007 " + privacy + " " + form["text"]) != 1):
            return False
        menu = self.reviewed_late_ir_capture(record, official + "contact/cmenu", official + "contact/cmenu")
        financial = self.reviewed_late_ir_capture(record, official + "ir/ir-msg", official + "ir/ir-msg")
        if (menu is None or menu.get("redirects") or menu.get("title") != "各種お問い合わせはこちらから - " + company + "株式会社"
                or menu["text"].count("各種お問い合わせはこちらから Home お問い合わせ 各種お問い合わせはこちらから 各種お問い合わせはこちらから IRについて 半導体検査用部品 について 電子管部品 について 採用について") != 1
                or len(menu.get("links", [])) <= 70 or menu["links"][70] != {"url": target, "href": "/contact/cmenu/contact1", "label": "IRについて"}
                or not any(s is menu and e["quote"] == "IRについて" and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 70 and e.get("source_link_url") == target for e, s in pairs)
                or financial is None or financial.get("redirects")
                or financial.get("title") != "株主・投資家の皆様へ - " + company + "株式会社"
                or not {"株主・投資家の皆様へ", "社長メッセージ", "株主還元について", "業績の見通し"}.issubset(financial.get("headings", []))
                or financial["text"].count("株主・投資家の皆様へ Home 投資家情報 株主・投資家の皆様へ 社長メッセージ ") != 1
                or "株主還元について 当社は、株主の皆様に対する「安定的な利益還元」を重要な経営方針の一つとしております。" not in financial["text"]
                or "連結業績予想 （単位：百万円） 売上高 営業利益 経常利益 親会社株主に帰属する 当期純利益" not in financial["text"]):
            return False
        return True

    def reviewed_ir_enterprise_row_category(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Bind the five public enterprise/IR categories to their complete row-backed question form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if isinstance(f,dict) and any(isinstance(c,dict) and c.get("name") == "row[body][6596][]"
                                                  for c in f.get("controls", []))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified"
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)

        target = official + "form/"
        source = next(iter(witnesses.values()))
        home = self.reviewed_late_ir_capture(record, official, official)
        financial = self.reviewed_late_ir_capture(record, official + "ir/", official + "ir/")
        parent = self.reviewed_late_ir_capture(record, official + "inquiry/", official + "inquiry/")
        parent_quote = "お問い合わせ先 企業・IRに関するお問い合わせ 採用に関するお問い合わせ"
        finance = "財務ハイライト IRライブラリ 株式関連 統合報告書 IRニュース 一覧"
        if (len(witnesses) != 1 or record.get("individual_access") != "not_stated"
                or self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or len(source.get("forms", [])) != 1
                or source.get("title") != "企業・IRに関するお問い合わせ｜お問い合わせ｜" + display + "株式会社"
                or home is None or home.get("redirects") or home.get("title") != display + "株式会社-Welcome to Ichikoh website-"
                or financial is None or financial.get("redirects")
                or financial.get("title") != "株主・投資家のみなさまへ｜" + display + "株式会社"
                or finance not in financial["text"] or "決算説明会" not in financial["text"] or "決算短信" not in financial["text"]
                or not any(s is financial and e["quote"] == financial["text"] for e,s in pairs)
                or parent is None or parent.get("redirects") or parent.get("title") != "お問い合わせ｜" + display + "株式会社"
                or len(parent.get("links", [])) <= 12
                or parent["links"][12] != {"url":target + "#tel","href":"/form/#tel","label":"企業・IRに関するお問い合わせ"}
                or not any(s is parent and e["quote"] == parent_quote and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 12 and e.get("source_link_url") == target + "#tel"
                           and e.get("source_link_href") == "/form/#tel" for e,s in pairs)
                or len(source.get("links", [])) <= 13
                or source["links"][13] != {"url":target + "#mail","href":"#mail","label":"メールでお問い合わせ"}
                or not any(s is source and e["quote"] == source["text"] for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'radio', 'name': 'row[body][6596][]'}, {'tag': 'input', 'type': 'radio', 'name': 'row[body][6596][]'}, {'tag': 'input', 'type': 'radio', 'name': 'row[body][6596][]'}, {'tag': 'input', 'type': 'radio', 'name': 'row[body][6596][]'}, {'tag': 'input', 'type': 'radio', 'name': 'row[body][6596][]'}, {'tag': 'textarea', 'name': 'row[body][6597]', 'placeholder': 'お問合わせ内容は、できるだけ具体的にご記入をお願いたします。'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6598]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6599]'}, {'tag': 'select', 'name': 'row[body][6600][]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6601]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6602]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6603]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6604]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6605]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6606]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6607]'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6608]', 'id': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'row[body][6609]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'row[body][6610][]'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", '/tables/456/form_configs/341/rows',
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        fields = 'お問い合わせ項目 を選択してください お問い合わせ項目 ' + display + 'について 製品について IR情報について サイトについて その他 お問い合わせ内容 をご記入ください お問い合わせ内容 郵便番号 － （例：155-0031） － 都道府県 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 住所 会社名／組織名 所属部署名 漢字氏名 （全角入力) ふりがな （全角入力) 電話番号 半角英数（例：03-XXXX-XXXX) FAX番号 半角英数（例：03-XXXX-XXXX) Eメールアドレス 半角英数（例：sample@ichikoh.com) Eメールアドレス 入力確認 半角英数（例：sample@ichikoh.com) プライバシーポリシー「個人情報保護方針」 に同意'
        if form is None or form["controls"] != controls or form["text"] != fields:
            return False

        operation = 'メールでお問い合わせ 注意事項 1.当社から返信いたしますメールは、お問合せいただきましたお客さまに対してお答えさせていただくことを目的としています。当社の許可なくメールの一部または全体を転載、二次使用すること、ならびに当該お客さま以外に開示することは固くお断りいたします。 2.お問合せの内容によっては電話等でのお答えをさせていただく場合がございます。 3.「よくある質問」に掲載されている内容についても返信を差し上げておりません。お問い合わせの前に、よくあるご質問内容もご活用ください。 4.こちらのフォームからの営業・商談・営利目的のメール送信はお断りいたします。 「 ※ 」は必須項目です。'
        return source["text"].count(operation + " " + fields) == 1

    def reviewed_ir_financial_purpose_and_site_seal(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Keep the cited financial IR form separate from its second, nonquestion site-seal form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if isinstance(f,dict) and any(isinstance(c,dict) and c.get("id") == "other-purpose"
                                                  for c in f.get("controls", []))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified"
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)

        target = official + "ir/contact/"
        source = next(iter(witnesses.values()))
        parent = self.reviewed_late_ir_capture(record, official + "ir/", official + "ir")
        home = self.reviewed_late_ir_capture(record, official, official)
        finance = "株主・投資家向け情報 INVESTOR RELATIONS 株主・投資家の皆さまへ、決算報告やIRニュース、最新の財務情報、ESGへの 取り組み、コーポレートガバナンス、株式情報などをお届けいたします。"
        parent_quote = 'お問い合わせ CONTACT IRについてのお問い合わせは、お電話または、お問い合わせフォームにて受け付けております。 ※ お問い合わせ内容によっては、お答えできない場合もございます。 お問い合わせフォーム よくあるご質問はこちらからご覧いただけます。 FAQ 028-667-7122 受付時間 9:00～17:00（休業日：土日) 担当 株式会社' + display + 'IR担当'
        operation = 'IRに関するご質問・ご相談・お問い合わせなどは、 下記フォームからお願いいたします。 必須 がある欄は必須項目になります。'
        if (len(witnesses) != 1 or record.get("individual_access") != "not_stated"
                or self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせフォーム | IRサイト - 株式会社" + display
                or len(source.get("forms", [])) != 2 or source["forms"][1] != {'action': 'https://sitesealinfo.pubcert.jprs.jp/SiteSealReference', 'method': 'post', 'controls': [{'tag': 'input', 'type': 'image', 'name': 'Sticker'}], 'text': ''}
                or home is None or home.get("redirects") or home.get("title") != "株式会社" + display
                or parent is None or parent.get("title") != "IRサイト - 株式会社" + display
                or len(parent.get("redirects", [])) != 1
                or parent["redirects"][0].get("requested_url") != official + "ir"
                or parent["redirects"][0].get("url") != official + "ir"
                or type(parent["redirects"][0].get("http_status")) is not int or parent["redirects"][0]["http_status"] != 301
                or parent["redirects"][0].get("redirect_target") != official + "ir/"
                or finance not in parent["text"] or "決算短信" not in parent["text"] or "有価証券報告書" not in parent["text"]
                or len(parent.get("links", [])) <= 86
                or parent["links"][86] != {"url":target,"href":"contact/","label":"お問い合わせ"}
                or not any(s is parent and e["quote"] == parent_quote and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 86 and e.get("source_link_url") == target for e,s in pairs)
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'radio', 'name': 'purpose', 'required': 'required', 'id': 'purpose-1'}, {'tag': 'input', 'type': 'radio', 'name': 'purpose', 'required': 'required', 'id': 'purpose-2'}, {'tag': 'input', 'type': 'radio', 'name': 'purpose', 'required': 'required', 'id': 'purpose-3'}, {'tag': 'input', 'type': 'radio', 'name': 'purpose', 'required': 'required', 'id': 'purpose-0'}, {'tag': 'input', 'type': 'text', 'name': 'other_purpose', 'required': 'required', 'placeholder': 'その他を選択された場合ご入力ください。', 'id': 'other-purpose'}, {'tag': 'textarea', 'name': 'content', 'required': 'required', 'placeholder': 'お問い合わせ内容をご入力ください。', 'id': 'content'}, {'tag': 'input', 'type': 'text', 'name': 'company', 'placeholder': '企業名・団体名をご入力ください。', 'id': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'department', 'placeholder': '部署名をご入力ください。', 'id': 'department'}, {'tag': 'input', 'type': 'text', 'name': 'name1', 'required': 'required', 'placeholder': '佐藤', 'id': 'name1'}, {'tag': 'input', 'type': 'text', 'name': 'name2', 'required': 'required', 'placeholder': '太郎', 'id': 'name2'}, {'tag': 'input', 'type': 'text', 'name': 'kana1', 'required': 'required', 'placeholder': 'さとう', 'id': 'kana1'}, {'tag': 'input', 'type': 'text', 'name': 'kana2', 'required': 'required', 'placeholder': 'たろう', 'id': 'kana2'}, {'tag': 'input', 'type': 'text', 'name': 'tel', 'required': 'required', 'placeholder': '例） 0286677121', 'id': 'tel'}, {'tag': 'input', 'type': 'text', 'name': 'email', 'required': 'required', 'placeholder': '例） sample@sample.co.jp', 'id': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'postcode', 'placeholder': '例） 3213231', 'id': 'postcode'}, {'tag': 'input', 'type': 'text', 'name': 'address1', 'id': 'address1'}, {'tag': 'input', 'type': 'text', 'name': 'address2', 'id': 'address2'}, {'tag': 'input', 'type': 'checkbox', 'name': 'privacy', 'required': 'required', 'id': 'privacy'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", '/ir/contact/',
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        fields = 'お問い合わせ区分 必須 経営方針について 業務・財務について 株式について その他 お問い合わせ内容 必須 企業名・団体名 部署名 お名前 必須 ふりがな 必須 電話番号 必須 メールアドレス 必須 ご住所 郵便番号（数字のみ） 郵便番号をご入力後、自動で住所が入力されます。 住所（市区町村番地） 住所（建物） 個人情報の取り扱いについて（利用目的） 当社は、当社の個人情報の利用目的を以下のとおりとし、利用目的を別途通知等する場合を除き、以下に定める利用目的の範囲外で個人情報を利用することはありません。個人情報の利用は、個人情報保護法その他の法令および当社個人情報保護方針に従い必要な措置を講じ、適正に行います。 当社が取扱商品・サービスをお客さまにご提供するため 当社および当社の関係会社・協力会社からのお客さまにとって有益であると当社が考える情報を、お客さまにご紹介・ご案内するため 打ち合わせ、決済、アンケートの実施、苦情・問い合わせの対応その他お客さま等と当社との間の契約を適切に履行するため お客さまの傾向、満足度等を分析した統計データの作成等の新商品・新サービスの開発のため その他当社事業に関連する業務のため 当社は、上記に定める目的を達成するため、当社業務上必要かつ法令で認められる場合に限り、個人情報を当社の関係会社との間で共同利用させていただいたり、業務委託先その他の当社が適切と認めた第三者に対し提供させていただくことがあります。これらの場合、必要な秘密保持契約等を締結し、その他法令上必要な措置を講じます。これらの場合およびお客さまの同意がある場合を除き、個人情報を第三者に提供することはありません。 当社は、採用活動時に応募者から当社に提供された個人情報について、当社からの連絡や採用関係資料の送付、採用選考の判断等の人材採用活動のために、利用させていただきます。 個人情報の共同利用に関する事項 当社は、グループ全体で総合的なサービスをご提供するため、業務上必要かつ法令で認められる場合に限り、グループ内でお客さまの個人情報を共同利用させていただくことがあります。この場合、個人情報保護のため、当社の関係会社との間で必要な秘密保持契約等を締結し、その他法令上必要な措置を講じます。 当社の個人情報の共同利用に関する事項は以下のとおりです。 共同利用者の範囲 当社および有価証券報告書等に記載されている、当社の子会社（以下、当社グループといいます） 共同利用者の利用目的 当社グループが取り扱う商品・サービスおよび関連するサービスを当社グループ全体で総合的にご提供するため 当社グループ・協力会社からのお客さまにとって有益であると当社が考える情報を、お客さまにご紹介・ご案内するため 打ち合わせ、決済、アンケートの実施、苦情・問い合わせの対応その他お客さま等と当社との間の契約を適切に履行するため お客さまの傾向、満足度等を分析した統計データの作成等の新商品・新サービスの開発のため その他当社グループ事業に関連する業務のため 共同利用者の範囲 氏名 住所 電話番号 メールアドレス その他上記の共同利用目的のために必要な事項 個人情報の第三者提供に関する事項 当社は、業務上必要かつ法令で認められる場合に限り、当社が適切と認めた第三者に対してのみ個人情報を提供させていただくことがあります。この場合、個人情報保護のため、法令上必要な措置を講じます。当社の個人情報の第三者提供に関する事項は以下のとおりです。 お客さまのご請求による第三者への提供停止 当社は、お客さま本人に関する個人データの第三者提供の停止をお客さまが希望される場合は、本人確認のうえ、事前に本人の同意がある場合または法令に基づく場合を除き、第三者提供を停止いたします。 第三者への提供の方法 書面または電子データを交付することによって行います。 第三者に提供される個人データの項目 氏名 住所 電話番号 メールアドレス その他上記の当社個人情報の利用目的のために必要な事項 保有個人データに関する事項 当社お客さまの保有個人データに関する事項は以下のとおりです。 個人情報取扱事業者の名称：株式会社' + display + ' 保有個人データの利用目的：上記「個人情報の利用目的」のとおりです。 お客さまは、当社に対し、ご本人に関する保有個人データの利用目的の通知、開示、訂正、追加、削除、利用停止、消去、第三者提供の停止等についてのご請求や、個人情報の取り扱いいに関する苦情等のご相談を行うことができます。 お問い合わせ窓口 〒321-3231 栃木県宇都宮市清原工業団地7番地1 株式会社' + display + ' 総務人事部 電話： 028-667-7122 FAX：028-667-8808 電子メール： ir@muro.co.jp 個人情報の取り扱いに同意する 入力内容を確認する'
        if form is None or form["controls"] != controls or form["text"] != fields:
            return False

        return source["text"].count(operation + " " + fields) == 1

    def reviewed_ir_organization_personal_instruction(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The public company-name substitution belongs to this complete IR organization form."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified"
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)

        if record.get("individual_access") not in {"explicit", "explicitly_allowed"}:
            return False
        target = official + "contact/ir/"
        source = self.reviewed_late_ir_capture(record, target, target)
        home = self.reviewed_late_ir_capture(record, official, official)
        finance = "投資家の皆様向けIR情報 最新IRニュースから 資料アーカイブまで"
        operation = '株主、投資家の皆様からのお問い合わせは、 メールによるお問い合わせに限定させていただいております。 お問い合わせについては以下のフォームより承っております。 お手数ですがご入力のうえ確認画面へお進みください。'
        policy = '※お問い合わせ内容によってはお答えできない場合もございます。 下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 非公開情報に関するご質問（業績動向など） 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など） 株式市場の値動きに関するご質問（株価動向、売買手口など） 誹謗中傷に該当するメッセージ 個別のサービスに関するご質問 営業や勧誘のお問い合わせ 上記に該当するご質問以外にも、お問い合わせ内容によってはお答えできない場合、また回答にお時間をいただく場合がございますのであらかじめご了承ください。 ※当社からご回答としてお送りする内容は、株主・投資家の皆様からお寄せいただいたお問い合わせなどにお答えさせていただく目的で、皆様個人宛てにお送りするものです。その一部または全部を転載、二次利用することはご遠慮ください。その他免責事項については「 免責事項 」をご確認ください。'
        instruction = "会社名 ※必須 個人投資家の方は「個人」と入力してください"
        if (source is None or source.get("redirects") or len(source.get("forms", [])) != 1
                or source.get("title") != "IRに関するお問い合わせ | " + display + "株式会社"
                or home is None or home.get("redirects") or not home.get("title", "").endswith(" | " + display + "株式会社")
                or finance not in home["text"] or "2026年6月期 決算説明資料" not in home["text"]
                or "2026年6月期 決算短信" not in home["text"]
                or not any(s is home and e["quote"] == home["title"] for e,s in pairs)
                or len(home.get("links", [])) <= 61
                or home["links"][61] != {"url":target,"href":"/contact/ir/","label":"IRに関するお問い合わせ"}
                or not any(s is home and e["quote"] == "IRに関するお問い合わせ" and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 61 and e.get("source_link_url") == target for e,s in pairs)
                or source["text"].count(operation) != 1 or source["text"].count(policy) != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)
                or not any(s is source and e["quote"] == policy for e,s in pairs)
                or not any(s is source and e["quote"] == instruction and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 0 for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'data[organization]', 'id': 'data001'}, {'tag': 'input', 'type': 'text', 'name': 'data[url]', 'id': 'data002'}, {'tag': 'input', 'type': 'text', 'name': 'data[zip]', 'id': 'data003'}, {'tag': 'input', 'type': 'text', 'name': 'data[address]', 'id': 'data004'}, {'tag': 'input', 'type': 'text', 'name': 'data[name_last]', 'id': 'data005'}, {'tag': 'input', 'type': 'text', 'name': 'data[name_first]', 'id': 'data006'}, {'tag': 'input', 'type': 'text', 'name': 'data[tel]', 'id': 'data007'}, {'tag': 'input', 'type': 'email', 'name': 'data[email]', 'id': 'data008'}, {'tag': 'textarea', 'name': 'data[content]', 'id': 'data009'}, {'tag': 'input', 'type': 'checkbox', 'name': 'data[_agreement]', 'id': '_agreement'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", None,
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        fields = '会社名 ※必須 個人投資家の方は「個人」と入力してください 会社URL 郵便番号 Japan （半角数字ハイフンなし） 住所 氏名 ※必須 氏 名 電話番号 ※必須 （半角数字ハイフンなし） メールアドレス ※必須 （半角英数） お問い合わせ内容 ※必須 個人情報保護 ※必須 こちらでご入力いただいた個人情報は、以下の目的でのみ利用させていただきます。 お問い合わせいただいたご質問へのご回答のため 当社における連絡・情報提供等は、電話・郵便・ＦＡＸ・電子メール等の電磁的方法のいずれかの方法で行います。 お問い合わせの前に、' + display + '株式会社「 個人情報保護ポリシー 」 および「 個人情報のお取り扱いについて 」を必ずお読みいただき、内容にご同意の上、確認画面にお進みください。 上記の利用目的及び、' + display + '株式会社「個人情報保護ポリシー」「個人情報のお取り扱いについて」の内容に同意する 確認画面'
        if form is None or form["controls"] != controls or form["text"] != fields:
            return False

        return fields.startswith(instruction + " 会社URL ")

    def reviewed_ir_personal_and_institutional_routes(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Use the personal IR entry and its native reply/question fields, separate from institutional contact."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified"
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)

        if record.get("individual_access") not in {"explicit", "explicitly_allowed"}:
            return False
        target = official + "ir/contact/personal.html"
        institutional = official + "ir/contact/institution.html"
        source = self.reviewed_late_ir_capture(record, target, target)
        parent = self.reviewed_late_ir_capture(record, official + "ir/contact/", official + "ir/contact/")
        home = self.reviewed_late_ir_capture(record, official, official)
        menu = "IR情報に関するお問い合わせ IR情報に関するお問い合わせ 個人投資家の皆様 詳しくはこちら 機関投資家の皆様 詳しくはこちら"
        operation = 'IR情報に関するお問い合わせ Inquiry about IR information 個人投資家の皆様 Individual investors 以下に必要な項目を入力して「確認する」ボタンを押して下さい。 Please complete the form below and click “Continue”. 全角英数・半角カタカナはご使用にならないで下さい。 ※項目は必須項目です。必ずご記入下さい。 * Required'
        if (source is None or source.get("redirects") or len(source.get("forms", [])) != 1
                or source.get("title") != "個人投資家の皆様 | IR情報に関するお問い合わせ | IR情報 | 株式会社" + display
                or home is None or home.get("redirects") or home.get("title") != "株式会社" + display
                or not any(s is home and e["quote"] == "株式会社" + display for e,s in pairs)
                or parent is None or parent.get("redirects")
                or parent.get("title") != "IR情報に関するお問い合わせ | IR情報 | 株式会社" + display
                or parent["text"].count(menu) != 1 or len(parent.get("links", [])) <= 15
                or parent["links"][14] != {"url":target,"href":"/ir/contact/personal.html","label":"詳しくはこちら"}
                or parent["links"][15] != {"url":institutional,"href":"/ir/contact/institution.html","label":"詳しくはこちら"}
                or not any(s is parent and e["quote"] == menu and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 14 and e.get("source_link_url") == target
                           and e.get("source_link_label") == "詳しくはこちら" for e,s in pairs)
                or not any(s is source and e["quote"] == operation and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 0 and ("form_index" not in e or type(e["form_index"]) is int and e["form_index"] == 0)
                           for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'T_pno_1'}, {'tag': 'textarea', 'name': 'T_add_2'}, {'tag': 'input', 'type': 'text', 'name': 'T_tell_3'}, {'tag': 'input', 'type': 'text', 'name': 'reply'}, {'tag': 'input', 'type': 'text', 'name': 'T_shimei_4'}, {'tag': 'textarea', 'name': 'T_msg_5'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", target,
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        fields = 'ご住所 ※ Address 〒 電話番号 ※ Telephone number * e-mail ※ Email address * 氏名 ※ Full Name * お問い合わせ内容 ※ お問い合わせ内容を 詳しくお書き下さい。 Inquiry * Please provide as much information as possible 個人情報の取扱いにつきましては、必ず「 個人情報保護方針 の下段部分」をご確認ください。 Please be sure to read the lower part of our Privacy Policy to learn more about how we proceed your personal information. リセット Reset 個人情報の取扱いについて 同意して確認する Agree to the processing of your personal data and confirm'
        if form is None or form["controls"] != controls or form["text"] != fields:
            return False

        return source["text"].count(operation + " " + fields) == 1

    def reviewed_ir_public_investment_type(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Bind the public personal/buy-side/sell-side choices to their complete captured IR form."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified"
                or record.get("individual_access") not in {"explicit", "explicitly_allowed"}
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)
        target = official + "ir/contact"
        witnesses = {id(s):(e,s) for e,s in pairs
                     if type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                     and s.get("url") == target and len(s.get("forms", [])) == 1
                     and e.get("quote") == s["forms"][0].get("text")}
        if len(witnesses) != 1:
            return False
        evidence, source = next(iter(witnesses.values()))
        captures = [f for f in record.get("fetches", []) if isinstance(f,dict)
                    and f.get("snapshot") == evidence.get("snapshot") and f.get("url") == target
                    and f.get("final_url") == target and type(f.get("http_status")) is int and f["http_status"] == 200
                    and f.get("retrieved_at") == source.get("retrieved_at")]
        home = self.reviewed_late_ir_capture(record, official, official)
        faq_url = official + "ir/faq"
        faq = self.reviewed_late_ir_capture(record, faq_url, faq_url)
        identity = "証券コードは何番ですか？ " + str(record.get("security_code")) + "です。"
        if (len(captures) != 1 or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != "IRお問い合わせ | " + display + "株式会社"
                or home is None or home.get("redirects") or home.get("title") != display + "株式会社"
                or len(home.get("links", [])) <= 13
                or home["links"][13] != {"url":target,"href":"/ir/contact","label":"IRお問い合わせ"}
                or not any(s is home and e["quote"] == "IRお問い合わせ" and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 13 and e.get("source_link_url") == target for e,s in pairs)
                or faq is None or faq.get("redirects") or faq.get("title") != "よくあるご質問 | " + display + "株式会社"
                or not {"企業に関するご質問","決算に関するご質問","株式に関するご質問"}.issubset(faq.get("headings", []))
                or faq["text"].count(identity) != 1 or not any(s is faq and e["quote"] == identity for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': '00N10000002L7hc', 'id': '00N10000002L7hc'}, {'tag': 'input', 'type': 'text', 'name': '00N10000002L7hh', 'id': '00N10000002L7hh'}, {'tag': 'input', 'type': 'text', 'name': '00N10000002L7hm', 'id': '00N10000002L7hm'}, {'tag': 'input', 'type': 'text', 'name': '00N10000002L7hr', 'id': '00N10000002L7hr'}, {'tag': 'input', 'type': 'text', 'name': 'company', 'id': 'company'}, {'tag': 'input', 'type': 'text', 'name': '00N5F0000070wZD', 'id': '00N5F0000070wZD'}, {'tag': 'select', 'name': '00N5F000006ps3A', 'id': '00N5F000006ps3A'}, {'tag': 'textarea', 'type': 'text', 'name': '00N5F000006YCrt', 'id': '00N5F000006YCrt'}, {'tag': 'input', 'type': 'text', 'name': '00N5F000006ptbN', 'id': '00N5F000006ptbN'}, {'tag': 'input', 'type': 'text', 'name': 'mail_chk', 'id': 'mail_chk'}, {'tag': 'input', 'type': 'text', 'name': '00N10000002L7iu', 'id': '00N10000002L7iu'}, {'tag': 'input', 'type': 'checkbox', 'name': 'chk1', 'id': 'chk1_checkbox'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", 'https://webto.salesforce.com/servlet/servlet.WebToCase?encoding=UTF-8',
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        fields = 'お名前 （必須） 姓 名 お名前（全角カナ） （必須） セイ メイ 会社名 （任意） 部署名 （任意） 投資タイプ （必須） --未選択-- 個人投資家 バイサイド セルサイド お問い合わせ内容詳細 （必須） メールアドレス （必須） メールアドレス（確認） （必須） 電話番号（半角） （必須） 以下の「個人情報の取り扱いについて」及び当社ホームページの「 個人情報のお取り扱いについて 」(以下「当社ホームページ」)の内容を確認、同意の上、チェックボックスにチェックして送信ボタンを押してください。 個人情報の取り扱いについて (1) お預かりする個人情報につきましては、「お問い合わせへのご対応」を目的として取得しています。この目的以外に、ご回答いただいた内容や個人情報をこの目的以外に利用することはありません。 (2) 上記(1)に記載した目的のために、お預かりした個人情報を外部の業者に委託し、情報処理を行う場合があります。この場合、当該業者と契約を締結し、お預かりした個人情報を適正に管理できるようにいたします。 (3) ご自身に関する情報の利用目的の通知、開示、訂正または削除、利用の停止・消去または第三者への提供の停止のご依頼をいただいた場合には、依頼者がご本人であることを確認させていただいたうえで、法令等に基づき対応できない、又は対応が困難であると当社が判断した場合を除き、対応させていただきます。 お問い合わせ先の詳細につきましては、当社ホームページをご参照ください。 同意します 送信'
        operation = '株主・投資家の皆さまからのお問い合わせを承ります。 ・ お問い合わせにつきましては順次対応させていただいております。後日、お電話もしくはメールにてご連絡を差し上げます。 ・ お問い合わせ内容によっては、回答に数営業日かかる場合やお返事を差し上げられない場合があります。あらかじめご了承ください。 ・ ご回答内容の一部または全部を転載・二次利用することはご遠慮ください。'
        audience = "投資タイプ （必須） --未選択-- 個人投資家 バイサイド セルサイド"
        if (form is None or form["controls"] != controls or form["text"] != fields
                or source["text"].count(operation + " " + fields) != 1
                or not any(s is source and e["quote"] == "株主・投資家の皆さまからのお問い合わせを承ります。" for e,s in pairs)
                or not any(s is source and e["quote"] == audience for e,s in pairs)):
            return False
        return True

    def reviewed_ir_opaque_reply_radio_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """The cited financial IR route and radio form identify an opaque reply field by its full public labels."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if {"f1","f7","f8"}.issubset({c.get("name") for c in f.get("controls", []) if isinstance(c,dict)})
                     and len(f.get("controls", [])) == 13}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/"
        source = next(iter(witnesses.values()))
        financial = self.reviewed_late_ir_capture(record, official+"ir/", official+"ir/")
        parent = 'IRに関するお問い合わせは こちらからお願いします。 メールでのお問い合わせ'
        if (self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせ | " + company + "株式会社" or len(source.get("forms", [])) != 1
                or financial is None or financial.get("redirects") or financial.get("title") != "IR情報 | " + company + "株式会社"
                or financial["text"].count('IRライブラリー IR Library 01 Financial Results 決算短信 Financial Results 02 Securities Report 有価証券報告書 Securities Report 03 IR Materials IR資料 IR Materials 最新IR資料一括DL') != 1 or financial["text"].count(parent) != 1
                or len(financial.get("links", [])) <= 51
                or financial["links"][51] != {"url":target,"href":"/contact/","label":"メールでのお問い合わせ"}
                or not any(s is financial and e["quote"] == parent and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 51 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'radio', 'name': 'f1'}, {'tag': 'input', 'type': 'radio', 'name': 'f1'}, {'tag': 'input', 'type': 'radio', 'name': 'f1'}, {'tag': 'input', 'type': 'radio', 'name': 'f1'}, {'tag': 'input', 'type': 'radio', 'name': 'f1'}, {'tag': 'input', 'type': 'text', 'name': 'f2', 'placeholder': '野村太郎'}, {'tag': 'input', 'type': 'text', 'name': 'f3', 'placeholder': 'ノムラタロウ'}, {'tag': 'input', 'type': 'text', 'name': 'f4', 'placeholder': 'のむら産業株式会社'}, {'tag': 'input', 'type': 'text', 'name': 'f5', 'placeholder': '東京都東久留米市前沢5-32-23'}, {'tag': 'input', 'type': 'text', 'name': 'f6', 'placeholder': '01-2345-6789'}, {'tag': 'input', 'type': 'text', 'name': 'f7', 'placeholder': 'nomura@example.com'}, {'tag': 'textarea', 'name': 'f8', 'placeholder': 'お問い合わせ内容をなるべく詳しく入力してください。'}, {'tag': 'input', 'type': 'checkbox', 'name': ''}]
        controls[7]["placeholder"] = company + "株式会社"
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        operation = '※IRに関するお問い合わせは「お問い合わせフォーム」からのみ受け付けております。 お電話でのIRに関するお問い合わせはご対応しかねますので、ご了承ください。'
        if (form is None or form["controls"] != controls or form["text"] != '必要事項にご記入後、最下部の「個人情報取扱い基本方針」をご確認のうえ、送信ください。 お問い合わせ種別 必須 製品・サービスについて 資料請求 見積り依頼 IRについて その他 お名前 必須 フリガナ 必須 会社名 ご住所 TEL 必須 メールアドレス 必須 お問い合わせ内容 必須 当社の 個人情報取扱い基本方針 に同意する 入力内容を確認する'.replace('のむら産業', company)
                or source["text"].count(operation) != 1 or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        return True

    def reviewed_ir_literal_mail_substitution(self, record: dict, pairs: list[tuple[dict, dict]], emails: list) -> bool | None:
        """Only the complete dedicated IR operation and its explicit symbol instruction establish this mailbox."""
        witnesses = {id(s):s for e,s in pairs if "経営企画部IR担当 ir（※）" in e.get("quote", "")}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "ir_email_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        domain = urlsplit(official).hostname.removeprefix("www.")
        ir_root = "https://ir." + domain + "/"
        target = ir_root + "ja/contact.html"
        source = next(iter(witnesses.values()))
        stock = self.reviewed_late_ir_capture(record, ir_root+"ja/ir/stock/overview.html", ir_root+"ja/ir/stock/overview.html")
        faq = self.reviewed_late_ir_capture(record, ir_root+"ja/ir/faq.html", ir_root+"ja/ir/faq.html")
        instruction = "ir（※）" + domain + " （※）を@マークに置き換えてください。"
        operation = '「IRよくあるご質問」以外のご質問につきましては、IR関連のお問い合わせについてのみEメールにて承っています。 お客さまの氏名、ご連絡先、お問い合わせ内容をご記入のうえ、下記メールアドレス宛てにご送信くださいますよう、お願いします。 ライフネット生命保険株式会社 経営企画部IR担当 ir（※）lifenet-seimei.co.jp （※）を@マークに置き換えてください。'.replace('ライフネット生命保険', company)
        operation = operation.replace("lifenet-seimei.co.jp", domain)
        identity = "株式基本情報 証券コード " + str(record.get("security_code")) + " 上場証券取引所 東京証券取引所プライム市場"
        search = {'action': None, 'method': 'get', 'controls': [{'tag': 'input', 'type': 'text', 'name': 'kw', 'placeholder': '検索ワードを記入', 'id': 'i_search_input'}, {'tag': 'input', 'type': 'submit', 'name': 'search-btn'}], 'text': ''}
        if (emails != ["ir@" + domain] or record.get("contact_url") != target
                or self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせ | " + company + "株式会社" or source.get("forms") != [search]
                or source["text"].count(operation) != 1 or source["text"].count(instruction) != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)
                or not any(s is source and e["quote"] == instruction for e,s in pairs)
                or len(source.get("links", [])) <= 10
                or source["links"][10] != {"url":ir_root+"ja/ir/faq.html","href":"/ja/ir/faq.html","label":"IRよくあるご質問"}
                or stock is None or stock.get("redirects") or stock.get("title") != "株式情報 | 株主・株式情報 | IR情報 | " + company + "株式会社"
                or stock["text"].count(identity) != 1 or not any(s is stock and e["quote"] == identity for e,s in pairs)
                or faq is None or faq.get("redirects") or faq.get("title") != "IRよくあるご質問 | IR情報 | " + company + "株式会社"
                or faq["text"].count("会社概要・経営 決算・業績 株式 配当・株主還元 株主総会 会社概要・経営") != 1
                or any(q in source["text"] for q in ("IRのお問い合わせは受け付けません", "IRに関するお問い合わせは電話のみ",
                                                     "個人投資家のお問い合わせはお断り", "個人のお問い合わせは受け付けません"))):
            return False
        return True

    def reviewed_ir_native_customer_and_company_instruction(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The exact financial route targets the same native audience selector and personal company input instruction."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "explicitly_allowed"
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = 'https://form-jpb.japanpost.jp/regist/is?SMPFORM=ocqg-tbkfn-cd41acb5ed9c83f4dae405fbf74bf606'
        source = self.reviewed_late_ir_capture(record, target, target)
        parent_url = official + "ir/information/ir_inf_toiawase.html"
        parent = self.reviewed_late_ir_capture(record, parent_url, parent_url)
        financial_url = official + "ir/ir_index.html?ui_medium=banner&ui_source=ntop&ui_campaign=ir"
        financial = self.reviewed_late_ir_capture(record, financial_url, financial_url)
        library_url = official + "ir/financial/ir_fnc_index.html"
        library = self.reviewed_late_ir_capture(record, library_url, library_url)
        direction = 'ゆうちょ銀行のIRに関するお問い合わせは、下記の窓口で承っております。 お問い合わせフォーム（IR関連）'.replace('ゆうちょ銀行', company)
        if (source is None or source.get("redirects") or source.get("title") != "IRお問い合わせ窓口" or len(source.get("forms", [])) != 1
                or parent is None or parent.get("redirects") or parent.get("title") != "IR関連のお問い合わせ－" + company
                or parent["text"].count(direction) != 1 or len(parent.get("links", [])) <= 9
                or parent["links"][9] != {"url":target,"href":target,"label":"お問い合わせフォーム（IR関連）"}
                or not any(s is parent and e["quote"] == direction and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 9 and e.get("source_link_url") == target for e,s in pairs)
                or financial is None or financial.get("redirects") or financial.get("title") != "IR情報－" + company
                or financial["text"].count('主な最新決算・IR資料 決算短信（PDF/489KB） （PDFファイル） 決算説明資料（PDF/720KB） （PDFファイル） 決算補足資料（PDF/462KB） （PDFファイル） 投資家説明会資料（PDF/5,328KB）') != 1 or len(financial.get("links", [])) <= 64
                or financial["links"][64] != {"url":parent_url,"href":"/ir/information/ir_inf_toiawase.html","label":"IR関連のお問い合わせ"}
                or library is None or library.get("redirects") or library.get("title") != "決算・IRライブラリ－" + company
                or library["text"].count("財務資料 2027年3月期 第1四半期決算短信［日本基準］（連結）") != 1):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'ir_name'}, {'tag': 'input', 'type': 'text', 'name': 'ir_kana'}, {'tag': 'input', 'type': 'text', 'name': 'ir_mail'}, {'tag': 'input', 'type': 'text', 'name': 'ir_mail:cf'}, {'tag': 'input', 'type': 'text', 'name': 'ir_phone:a'}, {'tag': 'input', 'type': 'text', 'name': 'ir_phone:e'}, {'tag': 'input', 'type': 'text', 'name': 'ir_phone:n'}, {'tag': 'select', 'name': 'ir_customer'}, {'tag': 'input', 'type': 'text', 'name': 'ir_corp'}, {'tag': 'input', 'type': 'text', 'name': 'ir_inq_sub'}, {'tag': 'textarea', 'name': 'ir_inq_body'}, {'tag': 'input', 'type': 'checkbox', 'name': 'ir_agree'}, {'tag': 'input', 'type': 'submit', 'name': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/regist/Reg2",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        if (form is None or form["controls"] != controls or form["text"] != 'お名前 ＊ 全角文字で入力してください フリガナ ＊ 全角カタカナで入力してください メールアドレス ＊ （確認用） 半角英数字で入力してください 電話番号 ＊ - - 半角数字で入力してください お客さま種別 ＊ ----- 選択してください ----- 個人投資家 機関投資家 会社名 ＊ 個人投資家の方は「個人」と入力してください 件名 全角50文字以内で入力してください お問い合わせ内容 ＊ 全角1000文字以内で入力してください お問い合わせ注意事項への同意 ＊ 同意する 下記の「お問い合わせ注意事項」に同意いただける場合は「同意する」に チェックを付け、「確認画面へ」ボタンを押してください。'.replace('ゆうちょ銀行', company)
                or source["text"] != 'IRお問い合わせ窓口 ゆうちょ銀行トップ IRお問い合わせ窓口 この窓口はIRに関するお問い合わせを受け付ける窓口です。IRに関連しない内容は本窓口ではお受けできません。 また、問い合わせの内容によっては回答できない場合や、回答にお時間をいただく場合もございますのであらかじめご了承願います。 必要事項をご入力の上、「確認画面へ」ボタンを押してください。 お名前 ＊ 全角文字で入力してください フリガナ ＊ 全角カタカナで入力してください メールアドレス ＊ （確認用） 半角英数字で入力してください 電話番号 ＊ - - 半角数字で入力してください お客さま種別 ＊ ----- 選択してください ----- 個人投資家 機関投資家 会社名 ＊ 個人投資家の方は「個人」と入力してください 件名 全角50文字以内で入力してください お問い合わせ内容 ＊ 全角1000文字以内で入力してください お問い合わせ注意事項への同意 ＊ 同意する 下記の「お問い合わせ注意事項」に同意いただける場合は「同意する」に チェックを付け、「確認画面へ」ボタンを押してください。 お問い合わせ注意事項 ・入力いただいた個人情報やお問い合わせ内容は、お問い合わせへの回答、情報提供のためだけに使用し、第三者にお渡しすることはございません。 ・個人情報の取扱全般に関する当社の考え方をご覧になりたい方は「 個人情報のお取扱いについて 」のページをご覧ください。 ・入力いただいた電話番号や電子メールアドレス等に誤りがある場合、あるいはお問い合わせの内容によっては回答できない場合や、回答にお時間をいただく場合がございます。 ・土曜日・日曜日・年末年始ほか、当社休業日にいただいたお問い合わせについては、回答が遅くなる可能性がございます。 ・お問い合わせの内容によっては、電子メール以外の方法で回答を差し上げる場合がございます。 ・当社から返信するメールは、お問い合わせいただいた方に宛てたものです。回答の一部または全部を転載、二次利用することはご遠慮願います。 ・半角カタカナや特殊記号（ローマ数字・丸付き数字等）は使用しないでください（正常に送信されない場合があります）。 ・ブラウザの［戻る］や［更新］ボタンは使用しないでください（画面が正しく表示されない場合があります）。 ご登録される情報は、暗号化された通信(SSL)で保護され、プライバシーマークやISO27001/JIS Q 27001,ISO20000-1,ISO9001の認証を取得している 株式会社パイプドビッツ による 情報管理システム「スパイラル」 で安全に管理されます。 (C) JAPAN POST BANK'.replace('ゆうちょ銀行', company)):
            return False
        return True

    def reviewed_ir_dedicated_financial_child(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """A financial IR menu designates its dedicated child and complete native question form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if {"Email","ご質問","submitConfirm"}.issubset({c.get("name") for c in f.get("controls", []) if isinstance(c,dict)})
                     and urlsplit(str(s.get("url"))).path == "/ir/inquiry/"}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        display = unicodedata.normalize("NFKC", company)
        target = official + "ir/inquiry/"
        source = next(iter(witnesses.values()))
        financial = self.reviewed_late_ir_capture(record, official+"ir/", official+"ir/")
        home = self.reviewed_late_ir_capture(record, official, official)
        if (self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせ | " + display + "株式会社" or len(source.get("forms", [])) != 1
                or home is None or home.get("title") != display + "株式会社"
                or financial is None or financial.get("redirects") or financial.get("title") != "IR | " + display + "株式会社"
                or financial["text"].count('Investors 株主・投資家の皆様へ 最新のIRニュース IRニュース一覧 経営情報 トップメッセージ 会社概要 役員プロフィール コーポレート・ガバナンス 業績・財務情報 主要な経営指標の推移 経営成績 財政状態 キャッシュ・フローの状況 IRライブラリ 最新IR資料 決算短信 決算説明資料 有価証券報告書 株主総会関連資料 適時開示情報 その他IR資料 株式情報 株式基本情報 株主還元 株価情報 IRカレンダー 詳細はこちら FAQ 詳細はこちら ディスクロージャーポリシー 詳細はこちら 免責事項 詳細はこちら IRに関するお問い合わせ 詳細はこちら') != 1 or len(financial.get("links", [])) <= 58
                or financial["links"][58] != {"url":target,"href":"/ir/inquiry/","label":"詳細はこちら"}
                or not any(s is financial and e["quote"] == "IRに関するお問い合わせ 詳細はこちら"
                           and type(e.get("source_link_index")) is int and e["source_link_index"] == 58
                           and e.get("source_link_url") == target for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': '氏名'}, {'tag': 'input', 'type': 'text', 'name': 'ふりがな'}, {'tag': 'input', 'type': 'email', 'name': 'Email', 'placeholder': '〇〇〇ahc.co.jp'}, {'tag': 'input', 'type': 'text', 'name': '電話番号'}, {'tag': 'input', 'type': 'text', 'name': 'zip', 'placeholder': '1234567', 'id': 'zip'}, {'tag': 'input', 'type': 'text', 'name': 'addr', 'placeholder': '郵便番号入力で自動で入力されます', 'id': 'addr'}, {'tag': 'textarea', 'name': 'ご質問'}, {'tag': 'input', 'type': 'submit', 'name': 'submitConfirm'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        operation = '下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」 をクリックして下さい。'
        if (form is None or form["controls"] != controls or form["text"] != '氏名 必須 ふりがな 必須 メールアドレス 必須 電話番号 Japan 郵便番号 ご住所 ご質問・ご意見 必須'.replace('ＡＨＣグループ', company)
                or source["text"].count("ホーム IR お問い合わせ") != 1 or source["text"].count(operation) != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        return True

    def reviewed_ir_holdings_and_store_separation(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """The current holdings IR reception distinguishes its store contact before its actual form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if {"姓","名","メールアドレス","お問い合わせ","個人情報保護方針に同意する[]"}.issubset(
                         {c.get("name") for c in f.get("controls", []) if isinstance(c,dict)})
                     and urlsplit(str(s.get("url"))).path == "/contact/mail/"}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") not in {"explicit","explicitly_allowed"}
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/mail/"
        source = next(iter(witnesses.values()))
        financial = self.reviewed_late_ir_capture(record, official+"ir/index.html", official+"ir/index.html")
        stock = self.reviewed_late_ir_capture(record, official+"ir/individual/index.html", official+"ir/individual/index.html")
        identity = "証券コード ： " + str(record.get("security_code"))
        if (self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせ ｜ 株式会社" + company or len(source.get("forms", [])) != 1
                or financial is None or financial.get("redirects") or financial.get("title") != "IR情報 ｜ 株式会社" + company
                or financial["text"].count('IRニュース ニュース一覧 すべて お知らせ 適時開示 決算関連 有価証券報告書・半期報告書 経営方針 財務ハイライト IRライブラリ IRカレンダー') != 1
                or stock is None or stock.get("redirects") or stock.get("title") != "個人投資家の皆様へ ｜ IR情報 ｜ 株式会社" + company
                or stock["text"].count(identity + " 単元株数（売買の基本単位） ： 100株") != 1
                or not any(s is stock and e["quote"] == identity for e,s in pairs)
                or len(source.get("links", [])) <= 72 or source["links"][72] != {'url': 'https://www.curves.co.jp/contact/', 'href': 'https://www.curves.co.jp/contact/', 'label': 'https://www.curves.co.jp/contact/'}):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': '姓'}, {'tag': 'input', 'type': 'text', 'name': '名'}, {'tag': 'input', 'type': 'text', 'name': '会社名'}, {'tag': 'input', 'type': 'radio', 'name': '性別'}, {'tag': 'input', 'type': 'radio', 'name': '性別'}, {'tag': 'input', 'type': 'text', 'name': '郵便番号'}, {'tag': 'select', 'name': '都道府県'}, {'tag': 'input', 'type': 'text', 'name': '住所'}, {'tag': 'input', 'type': 'text', 'name': '電話番号'}, {'tag': 'input', 'type': 'text', 'name': 'メールアドレス'}, {'tag': 'textarea', 'name': 'お問い合わせ'}, {'tag': 'input', 'type': 'checkbox', 'name': '個人情報保護方針に同意する[]', 'id': 'checkbox1'}, {'tag': 'input', 'type': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "index.php",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        scope = '本お問い合わせフォームは、株式会社カーブスホールディングスに対するお問い合わせ専用となっておりますので、カーブスの店舗に関するお問い合わせをご希望の方は、こちらのアドレスからお問い合わせをお願いいたします。'.replace('カーブスホールディングス', company)
        operation = 'IRに関するお問い合わせは、下記のフォームよりお願いいたします。'
        if (form is None or form["controls"] != controls or form["text"] != 'お名前 * 姓 名 会社名 * ※ 個人の場合は「個人」とご記入ください 性別 男性 女性 郵便番号 入力例）123-4567 住所 都道府県を選択してください 都道府県 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 電話番号 メールアドレス * お問い合わせ内容 * ※ お客様の個人情報は、当社の個人情報保護方針に沿って管理し、お客様の承諾なく、業務遂行上必要のない第三者に開示・提示することはございません。 詳しくは「 個人情報保護方針 」をご覧ください。 個人情報保護方針に同意する'.replace('カーブスホールディングス', company)
                or source["text"].count(scope) != 1 or source["text"].count(operation) != 1
                or not all(any(s is source and e["quote"] == q for e,s in pairs) for q in (scope,operation))
                or not source["text"].index(scope) < source["text"].index(operation) < source["text"].index(form["text"])):
            return False
        return True

    def reviewed_ir_company_or_occupation(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Only the actual IR FAQ form offers occupation as an alternative in its mandatory company field."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") not in {"explicit","explicitly_allowed"}
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/ir"
        source = self.reviewed_late_ir_capture(record, target, target)
        financial = self.reviewed_late_ir_capture(record, official+"ir/faq", official+"ir/faq")
        operation = 'IRに関する問い合わせはどこからできますか？ 「 IRに関するお問い合わせ 」のページからお願いいたします。なお、電話でのお問い合わせは受け付けておりません。'
        identity = "証券コードは何番ですか？ 「" + str(record.get("security_code")) + "」です。"
        if (source is None or source.get("redirects") or source.get("title") != "お問い合わせ（IR）｜" + company + "株式会社"
                or len(source.get("forms", [])) != 1
                or financial is None or financial.get("redirects") or financial.get("title") != "よくあるご質問｜IR情報｜" + company + "株式会社"
                or financial["text"].count(identity) != 1 or financial["text"].count(operation) != 1
                or not any(s is financial and e["quote"] == identity for e,s in pairs)
                or len(financial.get("links", [])) <= 44
                or financial["links"][44] != {"url":target,"href":"/contact/ir","label":"IRに関するお問い合わせ"}
                or not any(s is financial and e["quote"] == operation and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 44 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'field', 'required': '', 'placeholder': '会社名または職業を入力してください', 'id': 'field'}, {'tag': 'input', 'type': 'text', 'name': 'field', 'required': '', 'placeholder': 'お名前を入力してください', 'id': 'field'}, {'tag': 'input', 'type': 'email', 'name': 'field', 'required': '', 'placeholder': 'メールアドレスを入力してください', 'id': 'field'}, {'tag': 'input', 'type': 'tel', 'name': 'field', 'placeholder': '電話番号を入力してください', 'id': 'field'}, {'tag': 'textarea', 'name': 'field', 'required': '', 'placeholder': 'お問い合わせ内容を入力してください', 'id': 'field'}, {'tag': 'input', 'type': 'checkbox', 'name': 'checkbox', 'required': '', 'id': 'checkbox'}, {'tag': 'input', 'type': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "get", None,
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        personal = '会社名または職業 必須 氏名 必須 メールアドレス 必須 電話番号 お問い合わせ内容 必須'
        if (form is None or form["controls"] != controls or form["text"] != 'Tagline お問い合わせフォーム リンクページ名 セクションの説明が入ります。 会社名または職業 必須 氏名 必須 メールアドレス 必須 電話番号 お問い合わせ内容 必須 お問い合わせにあたってのご注意事項 お問い合わせフォームは、セキュリティとしてSSL（データ暗号化技術）を使用しております。お客様からいただいたEメールアドレスが違っている場合や、システム障害等によりお返事できない場合がございます。個人情報取扱い方針につきましては、「 プライバシーポリシー 」をご覧ください。お客様からいただく個人情報は、お問い合わせ・ご質問への回答、情報提供のために使用させていただきます。 当社は、株主・投資家の皆様へお知らせすべき重要事象について、適時開示規則に従い、公平かつ適時・適切な情報開示に努めております。また、公平な情報開示体制を維持し、回答内容に差異や誤解が生じるのを防ぐため、お電話での受付は行っておらず、お問い合わせフォームでのみ対応とさせていただいております。なお、お問い合わせの内容によっては、回答にお時間をいただく場合やお答えいたしかねる場合がございます。 特に以下の項目に該当するお問い合わせにつきましては、回答を差し控えておりますのであらかじめご了承ください。 ・非公開情報に関するご質問（足元の業績動向など） ・未公表の「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など） ・株価の値動きに関するご質問 ・当社へのご意見・ご感想（個別の回答は差し控えさせていただきます） ※当社から回答した内容の一部または全部を、他媒体へ転載・二次利用することはご遠慮くださいますようお願いいたします。 プライバシーポリシー の内容に同意する 必須'.replace('フォースタートアップス', company)
                or form["text"].count(personal) != 1 or not any(s is source and e["quote"] == personal for e,s in pairs)):
            return False
        return True

    def reviewed_ir_investor_star_company(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The native investor selector includes an individual choice while the public company star remains."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") not in {"explicit","explicitly_allowed"}
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "inquiry/ir/"
        source = self.reviewed_late_ir_capture(record, target, target)
        financial = self.reviewed_late_ir_capture(record, official+"ir/", official+"ir/")
        identity = '株式上場をしている取引所と証券コードを教えてください。 2020年（令和2年）3月17日に東京証券取引所グロース市場（旧マザーズ）に上場しました。 証券コードは' + str(record.get("security_code")) + 'です。'
        parent = '株式の状況 株主メモ 株価情報 IRお問い合わせ 電子公告 免責事項'
        if (source is None or source.get("redirects") or source.get("title") != "IR情報に関するお問い合わせ | 株式会社" + company
                or len(source.get("forms", [])) != 1
                or financial is None or financial.get("redirects") or financial.get("title") != "IR情報 | 株式会社" + company
                or financial["text"].count(identity) != 1 or not any(s is financial and e["quote"] == identity for e,s in pairs)
                or financial["text"].count(parent) != 1 or len(financial.get("links", [])) <= 31
                or financial["links"][31] != {"url":target,"href":"/inquiry/ir/","label":"IRお問い合わせ"}
                or not any(s is financial and e["quote"] == parent and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 31 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'params[name1]', 'required': None, 'placeholder': '例）山田'}, {'tag': 'input', 'type': 'text', 'name': 'params[name2]', 'required': None, 'placeholder': '例）太朗'}, {'tag': 'input', 'type': 'text', 'name': 'params[kana1]', 'required': None, 'placeholder': '例）ヤマダ'}, {'tag': 'input', 'type': 'text', 'name': 'params[kana2]', 'required': None, 'placeholder': '例）タロウ'}, {'tag': 'input', 'type': 'email', 'name': 'params[email]', 'required': None, 'placeholder': '例）mail@example.com'}, {'tag': 'input', 'type': 'tel', 'name': 'params[tel]', 'required': None, 'placeholder': '例）090-0123-4567'}, {'tag': 'select', 'name': 'params[investor_type]', 'required': None, 'id': 'investorType'}, {'tag': 'input', 'type': 'text', 'name': 'params[company]'}, {'tag': 'textarea', 'name': 'params[message]', 'required': None}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/inquiry/ir",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        operation = 'IRに関するお問い合わせ ★ が付いた項目は必須項目となります。'
        personal = '投資家種別 ★ 機関投資家 個人投資家 会社名 ★ お問い合わせ内容 ★'
        if (form is None or form["controls"] != controls or form["text"] != 'お名前 ★ 姓 名 お名前（フリガナ） ★ セイ メイ メールアドレス ★ ※メールアドレスに誤りがあるとご連絡できない場合がありますので、入力にはご注意ください。 電話番号 ★ ※半角数値で入力してください。 投資家種別 ★ 機関投資家 個人投資家 会社名 ★ お問い合わせ内容 ★ 確認画面へ'.replace('リビングプラットフォーム', company)
                or source["text"].count(operation) != 1 or not any(s is source and e["quote"] == operation for e,s in pairs)
                or not any(s is source and e["quote"] == personal and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 0 for e,s in pairs)):
            return False
        return True

    def reviewed_ir_faq_repeat_contact(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Both complete financial FAQ contact answers point to the same current issuer's native question form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if {"ContactName","ContactEmail","ContactMessage","ContactContract"}.issubset(
                         {c.get("id") for c in f.get("controls", []) if isinstance(c,dict)})}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/"
        source = next(iter(witnesses.values()))
        home = self.reviewed_late_ir_capture(record, official, official)
        financial = self.reviewed_late_ir_capture(record, official+"ir/faq/", official+"ir/faq/")
        operation = '資料請求等のお問い合わせ先はどこですか？ こちら へお問い合わせください。 問合せをしたが返信がないのですが？ 失礼があればお詫び申し上げます。 大変お手数ですが、再度ご連絡いただけますようお願い申し上げます。 こちら へお問い合わせください。'
        identity = "証券コードを教えてください。 " + str(record.get("security_code")) + "です。"
        if (self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != company + "株式会社" or len(source.get("forms", [])) != 1
                or home is None or home.get("title") != company + "株式会社"
                or financial is None or financial.get("redirects") or financial.get("title") != "FAQ｜IR情報｜" + company + "株式会社"
                or financial["text"].count(identity) != 1 or not any(s is financial and e["quote"] == identity for e,s in pairs)
                or financial["text"].count(operation) != 1 or len(financial.get("links", [])) <= 48
                or any(financial["links"][i] != {"url":target,"href":"../../contact/","label":"こちら"} for i in (47,48))
                or not any(s is financial and e["quote"] == operation and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 47 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'data[Contact][name]', 'placeholder': '例）\u3000日生 花子', 'id': 'ContactName'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][name_kana]', 'placeholder': '例）\u3000にっせい はなこ', 'id': 'ContactNameKana'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][email]', 'placeholder': '例）\u3000abc-def@mail.com', 'id': 'ContactEmail'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][tel]', 'placeholder': '例）\u300009012345678', 'id': 'ContactTel'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][zip]', 'placeholder': '例）162-0064', 'id': 'ContactZip'}, {'tag': 'select', 'name': 'data[Contact][pref]', 'id': 'ContactPref'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][city]', 'placeholder': '市区町村名・番地', 'id': 'ContactCity'}, {'tag': 'input', 'type': 'text', 'name': 'data[Contact][building]', 'placeholder': 'ビル名、マンション名', 'id': 'ContactBuilding'}, {'tag': 'textarea', 'name': 'data[Contact][message]', 'placeholder': 'こちらにご記入ください', 'id': 'ContactMessage'}, {'tag': 'input', 'type': 'checkbox', 'name': 'data[Contact][contract]', 'placeholder': '', 'id': 'ContactContract'}, {'tag': 'input', 'type': 'submit', 'name': 'confirm'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/contact/",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        if form is None or form["controls"] != controls or form["text"] != 'お名前 ふりがな メールアドレス お電話番号 ご住所 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 ご質問・ご意見 個人情報の取り扱いについて ミアヘルサホールディングス株式会社（以下、「当社」という）は、お預かりした個人情報に関し、下記の通り細心の注意を払い、適切かつ安全に管理しております。 1. 個人情報の利用目的 ご入力いただいた個人情報はお問合せに対する回答の目的のみに利用し、それ以外の目的では一切利用いたしません。 ※個人情報はご本人の任意でご提供いただいておりますが、必要な項目をいただけない場合、当社のサービス等を適切な状態で提供できない場合があります。 ２．個人情報の利用・提供 当社は下記の場合を除き、ご提供いただいた個人情報を第三者に開示または提供することはありません。 ・あらかじめご本人の同意をいただいている場合 ・法的な手段で開示の要求があった場合 ・警察、司法当局等の機関から個人情報の開示を求められた場合 ・合併、分社化、営業譲渡等により個人情報の提供が必要な場合 ・人の生命、身体または財産の保護のために必要がある場合であって、ご本人の同意を得ることが困難である場合 ３．個人情報取扱いの委託 当社は、利用目的遂行のため業務の全部または一部を外部に委託する場合があります。個人情報を委託する際は、個人情報保護の水準を十分に満たしている委託先を選定し、個人情報の適正管理・機密保持を行っています。また、お客様の個人情報漏洩防止に必要な事項を契約等により取り決め、適切な管理を実施しています。 ４．個人情報の開示等の請求 当社では個人情報の開示、利用目的の通知、内容の訂正、追加または削除、利用停止、消去及び第三者への提供の停止についてご本人から申出があった場合、お客様ご本人を確認させていただいたうえで、適切に対応いたします。（※なお、開示等を行う場合、実費が発生しますので予めご了承ください。） ５．個人情報に関するお問い合わせ 【 個人情報に関する相談窓口 】 お客様の個人情報に関するお問合せにつきましては、下記窓口で受け付けております。 〒162-0064 東京都新宿区市谷仲之町3-19 ミアヘルサホールディングス株式会社 個人情報保護相談窓口 TEL：03-3341-7205 （受付時間 平日9:00～18:00） FAX：03-3341-1737 EMAIL: info-privacy@merhalsa.jp ミアヘルサホールディングス株式会社 個人情報保護管理者 上記、個人情報の取り扱いについて同意する'.replace('ミアヘルサホールディングス', company):
            return False
        return True

    def reviewed_ir_consent_two_hop_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Financial FAQ -> official consent -> the captured named external native form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if any(isinstance(c,dict) and c.get("id") == "E-MAIL" and c.get("name") == "_email" for c in f.get("controls", []))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        source = next(iter(witnesses.values()))
        target = record.get("contact_url")
        parsed = urlsplit(str(target))
        if (parsed.scheme != "https" or parsed.netloc != parsed.hostname or parsed.path != "/form/contact_form.html"
                or parsed.query or parsed.fragment or source.get("redirects")
                or self.reviewed_late_ir_capture(record, target, target) is not source
                or source.get("title") != "お問い合わせ | 株式会社" + company or len(source.get("forms", [])) != 1):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': '_お名前', 'id': 'お名前'}, {'tag': 'input', 'type': 'text', 'name': '_ふりがな', 'id': '_お名前'}, {'tag': 'input', 'type': 'text', 'name': '_email', 'id': 'E-MAIL'}, {'tag': 'textarea', 'name': '_お問い合わせ内容', 'id': '_お問い合わせ内容'}, {'tag': 'input', 'type': 'reset'}, {'tag': 'input', 'type': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", "contact_postmail.php",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        financial = self.reviewed_late_ir_capture(record, official + "ir/faq/", official + "ir/faq/")
        consent = self.reviewed_late_ir_capture(record, official + "contact/", official + "contact/")
        operation = '個人情報保護基本方針 及び 個人情報の取り扱いについて をご了解いただいた上で、 下記をクリックしてお問い合わせください。 同意してお問い合わせ'
        if (form is None or form["controls"] != controls or form["text"] != 'お名前 ふりがな E-MAIL お問い合わせ内容 ※ご記入いただくお客様の個人情報は、以下の目的のために使用させていただきます。 ・フロンティアインターナショナルからのご返答、お知らせをお送りするため ・個人を特定しない統計のための資料 ※ご記入の前には必ず「 個人情報の取り扱いについて 」をお読みいただき、内容にご同意いただいたうえで、【同意した上で送信】ボタンを押してください。'.replace('フロンティアインターナショナル', company)
                or financial is None or financial.get("redirects") or financial.get("title") != "よくあるご質問 | 株式会社" + company
                or financial["text"].count("証券コードは何番ですか？ " + str(record.get("security_code")) + "です。") != 1
                or len(financial.get("links", [])) <= 40
                or financial["links"][40] != {"url":official+"contact/","href":"/contact/","label":"Contact IR IRお問い合わせ"}
                or not any(s is financial and e["quote"] == "Contact IR IRお問い合わせ" and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 40 and e.get("source_link_url") == official+"contact/" for e,s in pairs)
                or consent is None or consent.get("redirects") or consent.get("title") != "お問い合わせ – 株式会社" + company
                or consent["text"].count(operation) != 1 or len(consent.get("links", [])) <= 36
                or consent["links"][36] != {"url":target,"href":target,"label":"同意してお問い合わせ"}
                or not any(s is consent and e["quote"] == operation and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 36 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        return True

    def reviewed_ir_group_destination_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """The full group form has a separate IR selector and the current parent destination."""
        witnesses = {(id(s),i):s for _,s in pairs for i,f in enumerate(s.get("forms", []))
                     if "KSSグループ" in f.get("text", "") and {"inquiry_type","inquiry_destination[data][]","submit_email"}.issubset(
                         {c.get("name") for c in f.get("controls", []) if isinstance(c,dict)})}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        (_,index),source = next(iter(witnesses.items()))
        target = official + "contact/"
        requested = official + "contact"
        expected_search = {'action': 'https://kyoei-ss.co.jp/search', 'method': 'get', 'controls': [{'tag': 'input', 'type': 'search', 'name': 's', 'placeholder': 'サイト内検索'}], 'text': ''}
        expected_search["action"] = "https://" + urlsplit(official).hostname.removeprefix("www.") + "/search"
        if (index != 1 or self.reviewed_late_ir_capture(record, target, requested) is not source
                or source.get("title") != "お問い合わせ – " + company + "株式会社" or len(source.get("forms", [])) != 2
                or source["forms"][0] != expected_search or len(source.get("redirects", [])) != 1):
            return False
        redirect = source["redirects"][0]
        if (redirect.get("requested_url") != requested or redirect.get("url") != requested
                or type(redirect.get("http_status")) is not int or redirect["http_status"] != 301
                or redirect.get("redirect_target") != target):
            return False
        controls = [{'tag': 'input', 'type': 'checkbox', 'name': 'agree[data][]'}, {'tag': 'select', 'name': 'inquiry_type'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': 'inquiry_destination[data][]'}, {'tag': 'input', 'type': 'text', 'name': 'company', 'placeholder': '共栄セキュリティーサービス株式会社'}, {'tag': 'input', 'type': 'text', 'name': 'name', 'placeholder': '山田\u3000太郎'}, {'tag': 'input', 'type': 'email', 'name': 'email', 'placeholder': 'example@mail.co.jp'}, {'tag': 'input', 'type': 'text', 'name': 'tel', 'placeholder': '03-0000-0000'}, {'tag': 'textarea', 'name': 'content'}, {'tag': 'input', 'type': 'text', 'name': 'submit_title'}, {'tag': 'input', 'type': 'text', 'name': 'submit_email'}]
        controls[14]["placeholder"] = company + "株式会社"
        form = self.reviewed_finite_form_witness(record, source, pairs, 1, "post", "",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        instruction = 'お問い合わせ内容 * お見積依頼・ご相談 サービスに関するお問い合わせ 採用に関するお問い合わせ IRに関するお問い合わせ その他 お問い合わせ先 * 共栄セキュリティーサービス'.replace('共栄セキュリティーサービス', company)
        destination = 'お問い合わせ先 * 共栄セキュリティーサービス KSS 道都警備 KSS管財 合建警備保障 KSS大阪 ネオ・アメニティーサービス KSS神奈川 常総警備保障 中国警備 その他 KSSグループ'.replace('共栄セキュリティーサービス', company)
        financial = self.reviewed_late_ir_capture(record, official + "ir/", official + "ir")
        if (form is None or form["controls"] != controls or form["text"] != 'はじめに 個人情報の取り扱いについて（お問い合わせ） ◾️利用目的 KSSグループ（以下当グループ）が取得した個人情報は、お問い合わせへの回答以外に使用することはございません。 ◾️第三者提供 当グループは、お預かりした個人情報を、法令の規定または司法手続きに基づく要請による場合を除き、第三者に提供することはありません。 ◾️外部委託 当グループは、お預かりした個人情報を業務管理のためクラウドサービス事業者に委託することがございます。 ◾️情報提供の任意性 当グループへの個人情報の提供は任意となっています。ただし、情報に漏れやミスがある場合、適切なお問い合わせへの回答ができない場合があります。 ◾️個人情報の開示等 個人情報の利用目的の通知、開示、訂正、追加又は削除、利用又は提供の拒否、第三者提供記録の開示については、以下問い合わせ先までご一報ください。 ただし、人事考課などの個人情報に関してはこの限りではありません。 ◾️お問い合わせ先 KSSグループ 担当：共栄セキュリティーサービス株式会社 個人情報保護管理責任者 松林 篤樹 電話 ：03-3511-7780 FAX ：03-3511-7781 \u200b上記の内容に関し、同意する場合のみご送信ください。 \u200bお問い合わせにあたっての注意事項 当社から返信いたしますメールは、お問い合わせいただきましたお客さまに対してお答えさせていただくことを目的としています。当社の許可なくメールの一部または全体を転載、二次使用すること、ならびに当該お客さま以外に開示することは固くお断りいたします。 お問い合わせの内容によっては電話等でのお答えをさせていただく場合がございます。 上記「お問い合わせ情報の取り扱いについて」に同意する お問い合わせ内容 * お見積依頼・ご相談 サービスに関するお問い合わせ 採用に関するお問い合わせ IRに関するお問い合わせ その他 お問い合わせ先 * 共栄セキュリティーサービス KSS 道都警備 KSS管財 合建警備保障 KSS大阪 ネオ・アメニティーサービス KSS神奈川 常総警備保障 中国警備 その他 KSSグループ 貴社名・ご所属 お名前 * ご連絡先メールアドレス * お電話番号 内容 * 確認する'.replace('共栄セキュリティーサービス', company)
                or not all(any(s is source and e["quote"] == q for e,s in pairs) for q in (instruction,destination))
                or financial is None or financial.get("title") != "IR – " + company + "株式会社"
                or len(financial.get("redirects", [])) != 1
                or financial["redirects"][0].get("requested_url") != official+"ir"
                or financial["redirects"][0].get("url") != official+"ir"
                or type(financial["redirects"][0].get("http_status")) is not int or financial["redirects"][0]["http_status"] != 301
                or financial["redirects"][0].get("redirect_target") != official+"ir/"
                or "株主・投資家の皆様へ " + company + "株式会社とKSSグループは、 警備事業を通じて社会の安全・安心を支える企業として、 安定的かつ持続的な成長を目指しています。" not in financial["text"]
                or len(financial.get("links", [])) <= 68 or financial["links"][68] != {"url":requested,"href":"/contact","label":"お問い合わせ"}):
            return False
        return True

    def reviewed_ir_shareholder_intent_audience(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Native personal shareholder/purchase choices do not waive the public mandatory company field."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/ir/"
        source = self.reviewed_late_ir_capture(record, target, target)
        home = self.reviewed_late_ir_capture(record, official, official)
        if (source is None or source.get("redirects") or source.get("title") != "IRについて｜株式会社" + company
                or len(source.get("forms", [])) != 1 or home is None or home.get("redirects")
                or home.get("title") != "株式会社" + company + "｜CyberBuzz, Inc." or len(home.get("links", [])) <= 117
                or home["links"][117] != {"url":target,"href":target,"label":"IR について"}):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'company-name', 'placeholder': '貴社名を入力してください', 'id': 'company-name'}, {'tag': 'input', 'type': 'text', 'name': 'your-name', 'placeholder': '氏名を入力してください', 'id': 'your-name'}, {'tag': 'input', 'type': 'tel', 'name': 'tel', 'placeholder': '電話番号（数字のみ）を入力してください', 'id': 'tel'}, {'tag': 'input', 'type': 'email', 'name': 'email', 'placeholder': 'メールアドレス（半角英数記号のみ）を入力してください', 'id': 'email'}, {'tag': 'textarea', 'name': 'message', 'id': 'message'}, {'tag': 'select', 'name': 'menu-552'}, {'tag': 'input', 'type': 'checkbox', 'name': 'privacy[]'}, {'tag': 'input', 'type': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/contact/ir/#wpcf7-f481-p497-o1",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        financial_text = 'INVESTOR RELATIONS IR情報 IR最新資料 IRニュース IRライブラリ 株式情報 CONTACT お問い合わせ ソーシャルメディアマーケティング について IR について'
        operation = 'CONTACT IRについて 下記の入力フォームよりお問い合わせをお願いいたします。'
        if (form is None or form["controls"] != controls or form["text"] != '貴社名 必須 氏名 必須 電話番号 必須 入力例：0123456789 メールアドレス 必須 入力例： [email protected] お問い合せ内容 必須 属性の選択 必須 選択してください 個人の株主様 当社株式の購入をお考えの方 機関投資家の方 リサーチ機関関係者・アナリスト 証券関係者 メディア関係者 その他 プライバシーポリシー 必須 プライバシーポリシー を確認 同意する'.replace('サイバー・バズ', company)
                or home["text"].count(financial_text) != 1 or source["text"].count(operation) != 1
                or not any(s is home and e["quote"] == financial_text and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 117 and e.get("source_link_url") == target for e,s in pairs)
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        return True

    def reviewed_ir_japanese_reply_operation(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """The public Japanese mail field and native IR radio family belong to this complete operating form."""
        witnesses = {id(s):s for _,s in pairs for f in s.get("forms", [])
                     if any(isinstance(c,dict) and c.get("id") == "service_select-1" and c.get("name") == "お問い合わせ種別" for c in f.get("controls", []))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        source = next(iter(witnesses.values()))
        target = official + "contact/"
        if (self.reviewed_late_ir_capture(record, target, target) is not source or source.get("redirects")
                or source.get("title") != "お問い合わせ | 株式会社" + company or len(source.get("forms", [])) != 1):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'お名前', 'placeholder': '日本 太郎'}, {'tag': 'input', 'type': 'text', 'name': 'メールアドレス', 'placeholder': 'sample@intimatemerger.com'}, {'tag': 'input', 'type': 'text', 'name': '会社名', 'placeholder': '株式会社インティメート・マージャー'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-1'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-2'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-3'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-4'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-5'}, {'tag': 'input', 'type': 'radio', 'name': 'お問い合わせ種別', 'id': 'service_select-6'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'input', 'type': 'checkbox', 'name': '興味のあるサービス[data][]'}, {'tag': 'textarea', 'name': 'お問い合わせ内容', 'placeholder': 'お問い合わせ内容をご記入ください'}, {'tag': 'input', 'type': 'checkbox', 'name': '個人情報保護方針[data][]'}, {'tag': 'input', 'type': 'submit', 'name': 'submitConfirm'}]
        controls[2]["placeholder"] = "株式会社" + company
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        operation = 'なお、IRに関するお問い合わせにつきましては、ご質問の内容によってはお答えできない、または回答に時間を要する場合があります。'
        financial_text = 'IR IR 株主・投資家の皆様へ MESSAGE IRライブラリー IR LIBRARY IRニュース IR NEWS 業績ハイライト HIGHLIGHT IRカレンダー IR CALENDAR 株式情報 IR INFORMATION'
        financial = self.reviewed_late_ir_capture(record, official+"ir/", official+"ir/")
        stock = self.reviewed_late_ir_capture(record, official+"ir/information/", official+"ir/information/")
        if (form is None or form["controls"] != controls or form["text"] != '株式会社インティメート・マージャーのコーポレートサイトをご利用頂きありがとうございます。 お問い合わせ頂いた内容に関して、弊社担当者より返答させて頂きます。なお、ご登録いただきました個人情報は、お問い合わせの対応、弊社のセミナー・イベントや商品・サービスに関するご案内に利用させていただく場合がございます。 また、頂いた個人情報の取り扱いの詳細につきましては、『 プライバシーポリシー 』をご確認ください。 なお、IRに関するお問い合わせにつきましては、ご質問の内容によってはお答えできない、または回答に時間を要する場合があります。 株価については、あくまでも市場の売買により決定されるものであり、またインサイダー情報防止の観点から、コメントを差し控える方針ですのでご了承ください。 お名前 必須 メールアドレス 必須 会社名 お問い合わせ種別 必須 広告配信に関して データ活用・商品開発に関して 採用に関して 広報・取材に関して IRに関して その他のお問い合わせ 興味のあるサービス Web広告の獲得単価の改善 ポストクッキーソリューション ブランディング広告の評価 データを使った商品開発 オーディエンスデータの拡充 インテントデータ活用 営業活動の効率化 アクセス解析の高度化 プライバシー保護対策 お問い合わせ内容 必須 このフォームへの特定電子メールの送信を拒否いたします。 個人情報の取り扱いについてはこちら 個人情報保護方針に同意する'.replace('インティメート・マージャー', company)
                or not any(s is source and e["quote"] == operation and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 0 for e,s in pairs)
                or financial is None or financial.get("redirects") or financial.get("title") != "IR | 株式会社" + company
                or financial["text"].count(financial_text) != 1 or not any(s is financial and e["quote"] == financial_text for e,s in pairs)
                or stock is None or stock.get("redirects") or stock.get("title") != "株式情報 | 株式会社" + company
                or stock["text"].count("証券コード " + str(record.get("security_code")) + " 事業年度 10月1日から9月末日まで") != 1):
            return False
        return True

    def reviewed_ir_personal_and_recruitment_choice(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The same corporate reception model exposes a personal attribute and a separate IR category."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/"
        source = self.reviewed_late_ir_capture(record, target, target)
        financial = self.reviewed_late_ir_capture(record, official+"ir/", official+"ir/")
        if (source is None or source.get("redirects") or source.get("title") != "お問い合わせ - 株式会社" + company + "｜就職支援・採用支援・社員教育"
                or len(source.get("forms", [])) != 1 or financial is None or financial.get("redirects")
                or financial.get("title") != "IR情報" or len(financial.get("links", [])) <= 144
                or financial["links"][144] != {"url":target,"href":target,"label":"IRお問い合わせ"}):
            return False
        controls = [{'tag': 'select', 'name': 'attribute', 'id': 'attribute'}, {'tag': 'input', 'type': 'text', 'name': 'company', 'placeholder': '例）株式会社ジェイック', 'id': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'position', 'placeholder': '例）主任', 'id': 'position'}, {'tag': 'input', 'type': 'text', 'name': 'person', 'placeholder': '例）ジェイック太郎', 'id': 'person'}, {'tag': 'input', 'type': 'email', 'name': 'mail', 'placeholder': '例）sample@co.jp', 'id': 'mail'}, {'tag': 'input', 'type': 'tel', 'name': 'tel', 'placeholder': '例）0999999999', 'id': 'tel'}, {'tag': 'select', 'name': 'category', 'id': 'category'}, {'tag': 'textarea', 'name': 'body', 'id': 'body'}]
        controls[1]["placeholder"] = "例）株式会社" + company
        controls[3]["placeholder"] = "例）" + company + "太郎"
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/contact/#wpcf7-f8358-o1",
            [{k:c[k] for k in ("tag","type","name","id","required") if k in c} for c in controls])
        financial_text = 'IRコンテンツ IR Contents 経営方針 コーポレートガバナンス 個人投資家のみなさまへ SDGsへの取り組み・環境宣言 IRライブラリー 決算短信 決算説明会資料 有価証券報告書 株主通信 その他資料 業績ハイライト 業績・財務ハイライト 株式情報 株式情報 配当の推移 株主優待情報 株主総会 株価情報 その他 IRスケジュール よくある質問 IRお問い合わせ'
        if (form is None or form["controls"] != controls or form["text"] != '属性 必須 —以下から選択してください— 企業/組織 個人/求職者 大学 報道 その他 会社名/組織名 部署・役職 お名前 必須 メールアドレス 必須 電話番号 必須 お問い合わせ種類 必須 —以下から選択してください— 【企業向け】新卒採用支援サービス 【企業向け】中途採用支援サービス 【企業向け】適性診断サービス 【企業向け】教育研修 【個人向け】新卒の就職支援サービス 【個人向け】既卒/中途の就職支援サービス Kakedas 就活AI by ジェイック 取材/寄稿依頼 IR その他 お問い合わせ内容 必須 プライバシーポリシー 当社ホームページをご覧いただきまして、誠にありがとうございます。当社は、お客様の個人情報（以下、個人情報という）の取扱いを、下記の通りとさせて頂きますので、予めご確認いただきますようお願い申し上げます。 １）個人情報の利用目的 いただきました個人情報は、お問い合わせに対するご回答のほか、以下の目的で利用する可能性があります。 職業紹介（条件に合致する求人企業の検索）を行うため。 職業紹介に関するカウンセリング、説明会、セミナー等に参加される個人を識別するため。 職業紹介に関するメルマガ等の情報を提供するため。 当社が提供するサービスの向上を目的としたご登録者のユーザプロファイルの集計とその結果を分析するため。（※この際には、集計結果の統計情報のみの利用となりますので、個人を特定のできるデータを第三者機関へ公表することは一切ございません。） 教育研修事業、人材紹介事業における商品・サービスの提供、関連するアフターサービスの提供、新商品・新サービスに関する情報のお知らせのため。 人材紹介事業における商品・サービスの提供、関連するアフターサービスの提供のため。 教育研修事業における商品・サービスの提供、関連するアフターサービスの提供、新商品・新サービスに関する情報のお知らせのため。 公開情報より当該公開情報の利用目的を確認のうえ、マーケティング活動の一環としてDM（電子メールを含む）その他情報提供の資料として利用するため。 アンケート調査等を行い、当社の各種サービスに反映するため。 アンケート調査等を行い、プレスリリースの内容に反映するため。 当社事業に関してご請求いただいた各種資料を発送するため。 ホームページの運営・会員管理業務のため。 当社の従業者管理及び採用業務のため。 当社サービスの品質向上、又はAIプログラム等を用いたツールの開発・改良のため。 ご協力いただける場合に、「お客様の声」として利用させていただくため。 利用者のインフォマティブデータを取得・分析し、最適な広告配信、当社サービスおよびウェブサイトの改善を行うため。 当社は、クッキー、広告識別子、ウェブビーコン、JavaScript等、利用者が容易に知覚できない手段を用いて、閲覧履歴、行動履歴、利用環境情報等のインフォマティブデータを取得することがあります。これらの情報は、Google・Yahoo!・Microsoft・Meta・LINE等の広告配信事業者が保有するユーザー情報と、当社が保有するメールアドレス・電話番号・cookie等を照合し、一定の条件を満たす利用者（当社サービスまたは広告関連事業者のサービスの利用者を含みます）に対する最適な広告配信や各種サービスの提案、または当社サービスおよびウェブサイトの改善のために利用します。当該第三者によって取得された情報は、それぞれのプライバシーポリシーに従って取り扱われます。 利用者は、以下の各広告事業者が提供するオプトアウト手段により、これらの情報の取得・広告配信への利用を停止することができます。 オプトアウト説明ページ Google : https://policies.google.com/technologies/ads?hl=ja LINEヤフー株式会社 : https://line.me/ja/terms/policy/ Microsoft : https://www.microsoft.com/ja-jp/servicesagreement Meta : https://www.facebook.com/privacy/policy ２）個人情報の第三者提供 個人情報は、法令に定める場合を除き、事前に本人の同意を得ることなく第三者に提供することはありません。ただし、上に記す利用目的と同様の目的で、当社のグループ会社（連結子会社）に対して提供することがあります。また、サービスを利用される際は、サービスのご利用に必要な範囲で第三者提供を行うことがあります。詳しくは下記ページをご覧ください。 https://www.jaic-g.com/privacy/privacy.php ３）個人情報の委託 他の事業者へ個人情報を委託する場合は、個人情報保護体制が整備された委託先を選定するとともに、個人情報保護に関する契約を締結し、適切な管理監督をいたします。 ４）個人情報を提供することの任意性 個人情報のご提供は任意です。ただし、必要な情報をいただけない場合は、いただいたお問い合わせへのご回答やサービスのご案内等ができない場合がありますので予めご了承ください。 ５）開示等の受付・窓口 いただいた個人情報について、開示・訂正・削除等を求められたときは、対応させていただきます。お申し出は、以下の窓口にて受付けます。 【問合せ窓口】 窓口の名称 ：個人情報問合せ窓口 個人情報保護管理者：株式会社ジェイック 経営企画部 谷中 拓生 住所：〒101-0051 東京都千代田区神田神保町1-101 神保町101ビル7F 電話：03-5282-7600 FAX：03-5282-7607 電子メール：info@jaic-g.com 送信する このサイトはreCAPTCHAによって保護されており、Googleの プライバシーポリシー と 利用規約 が適用されます。'.replace('ジェイック', company)
                or financial["text"].count(financial_text) != 1
                or not any(s is financial and e["quote"] == financial_text and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 144 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        return True

    def reviewed_ir_civil_and_stock_audience(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Personal civil occupations and nonshareholders belong to this actual IR form."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("investigation_status") != "confirmed" or record.get("verification_level") != "form_fields_verified"
                or record.get("outreach_suitability") != "candidate"):
            return False
        target = official + "contact/ir/"
        source = self.reviewed_late_ir_capture(record, target, target)
        home = self.reviewed_late_ir_capture(record, official, official)
        if (source is None or source.get("redirects") or source.get("title") != ""
                or source.get("headings") != ["お問い合わせフォーム", "IRに関するお問い合わせ", "個人情報の取り扱いについて", "個人情報の取り扱いの同意"]
                or len(source.get("forms", [])) != 1 or home is None or home.get("redirects")
                or home.get("title") != company + "株式会社" or len(home.get("links", [])) <= 52
                or home["links"][52] != {"url": target, "href": "/contact/ir/", "label": "IRに関するお問い合わせ"}
                or not any(s is home and e["quote"] == "IRに関するお問い合わせ"
                           and type(e.get("source_link_index")) is int and e["source_link_index"] == 52
                           and e.get("source_link_url") == target for e, s in pairs)):
            return False
        controls = [{'tag': 'input', 'type': 'text', 'name': 'lastname', 'placeholder': '田中'}, {'tag': 'input', 'type': 'text', 'name': 'firstname', 'placeholder': '太郎'}, {'tag': 'input', 'type': 'text', 'name': 'lastkana', 'placeholder': 'タナカ'}, {'tag': 'input', 'type': 'text', 'name': 'firstkana', 'placeholder': 'タロウ'}, {'tag': 'input', 'type': 'text', 'name': 'age', 'placeholder': '30'}, {'tag': 'input', 'type': 'radio', 'name': 'sex'}, {'tag': 'input', 'type': 'radio', 'name': 'sex'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'radio', 'name': 'job'}, {'tag': 'input', 'type': 'text', 'name': 'zip', 'placeholder': '1234567'}, {'tag': 'input', 'type': 'text', 'name': 'address', 'placeholder': '京都府亀岡市北古世町2丁目15番1号'}, {'tag': 'input', 'type': 'tel', 'name': 'tel', 'placeholder': '0120123456'}, {'tag': 'input', 'type': 'email', 'name': 'mail', 'placeholder': 'mail@nichicon.co.jp'}, {'tag': 'input', 'type': 'radio', 'name': 'stock'}, {'tag': 'input', 'type': 'radio', 'name': 'stock'}, {'tag': 'input', 'type': 'radio', 'name': 'stock'}, {'tag': 'textarea', 'name': 'text'}, {'tag': 'input', 'type': 'checkbox', 'name': 'agree'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", "./",
            [{k:c[k] for k in ("tag", "type", "name", "id", "required") if k in c} for c in controls])
        operation = 'IRに関するお問い合わせ 「投資家情報」についてのご質問やご意見をお待ちしています。 下記項目に入力し、個人情報保護方針に同意の上、確認画面にお進みください。'
        occupation = "職業 会社員 公務員（教職員を除く） 教職員 自営 主婦 学生 無職"
        stock = "現在当社の株式をお持ちですか？ 現在、株主である 株式の購入を検討している どちらでもない"
        if (form is None or form["controls"] != controls or form["text"] != '氏名 姓 名 フリガナ セイ メイ 年齢 歳 性別 男性 女性 職業 会社員 公務員（教職員を除く） 教職員 自営 主婦 学生 無職 郵便番号 ※半角７桁、ハイフンなし 住所 TEL ※半角、ハイフンなし メールアドレス 現在当社の株式をお持ちですか？ 現在、株主である 株式の購入を検討している どちらでもない お問い合わせ内容詳細 お問合せフォームからの売込・セールスはご遠慮ください。 個人情報の取り扱いについて 個人情報の取扱について同意が必要です。下記リンクより個人情報保護方針をご確認いただき、「同意する」にチェックを入れ入力内容の確認にお進みください。 個人情報保護方針 個人情報の取り扱いの同意 【個人情報の利用目的】 (1) お客様・お取引先様に関する情報 ① お客様へ製品・サービスの案内、販売、設置、提供、保守を行うため ② お客様へ各種アンケートを依頼するため ③ お客様へキャンペーン・展示会等イベントの案内を行うため ④ お客様へ各種資料・サンプルの提供を行うため ⑤ 各種問い合わせ等に対する回答および連絡を行うため ⑥ お取引先への発注および諸連絡のため ⑦ 契約の交渉、締結、義務の履行および契約上のご請求、お支払い等を行うため ⑧ 各種製品・サービス等の企画・開発のため (2) 各種研究会・各種業界団体に関する情報 ① お客様へ製品・サービスの案内、販売、設置、提供、保守を行うため ② お客様へ各種アンケートを依頼するため ③ お客様へキャンペーン・展示会等イベントの案内を行うため ④ お客様へ各種資料・サンプルの提供を行うため ⑤ 各種問い合わせ等に対する回答および連絡を行うため ⑥ お取引先への発注および諸連絡のため ⑦ 契約の交渉、締結、義務の履行および契約上のご請求、お支払い等を行うため ⑧ 各種製品・サービス等の企画・開発のため (3) 株主様に関する情報 ① 株主様への諸連絡・資料送達のため (4) 採用応募者に関する情報 ① 採用選考のため ② 問い合わせ等に対する回答および連絡を行うため (5) 当社従業員並びに家族または関係者等に関する情報 ① 当社従業員の人事・労務管理を行うため ② 当社従業員の経理・総務等の必要事務および連絡のため (6) 退職者に関する情報 ① 当社従業員の人事・労務管理を行うため ② 当社従業員の経理・総務等の必要事務および連絡のため (7) その他上記各項目に関連する業務 ① 当社従業員の人事・労務管理を行うため ② 当社従業員の経理・総務等の必要事務および連絡のため なお、個別に利用目的を開示または通知する場合には、その利用目的によるものとします。 上記の個人情報の取り扱いに同意する 確認する 入力内容リセット 製品一覧 電子デバイス 家庭用蓄電システム V2H・V2Lシステム EV・PHEV用急速充電器 公共・産業用蓄電システム スイッチング電源 機能モジュール コンデンサ応用装置 研究・医療・産業用特殊電源 電力用コンデンサ関連装置および付属機器 企業情報 企業情報トップ ニチコンについて サステナビリティ 広告宣伝 イベント ブランド 株主・投資家情報 株主・投資家情報トップ 経営方針 業績・財務状況 IRライブラリー 個人投資家の皆さまへ 株式情報 採用情報 採用情報トップ 新卒採用情報 キャリア採用情報 拠点・工場情報 お問い合わせ サイトのご利用について ソーシャルメディアポリシー 個人情報保護方針 脆弱性情報開示ポリシー サイトマップ © 2022 NICHICON CORPORATION. 当サイトでは、サイトの利便性向上のため、クッキー(Cookie)を使用しています。 サイトのクッキー(Cookie)の使用に関しては、「 個人情報保護方針 」をお読みください。 同意する'
                or source["text"].count(operation) != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)
                or not all(any(s is source and e["quote"] == q for e,s in pairs) for q in (occupation, stock))
                or any(refusal in source["text"] for refusal in ("株主様以外のお問い合わせは受け付けません", "個人からのIRお問い合わせはお断りします"))):
            return False
        return True

    def reviewed_ir_email_only_operation(self, record: dict, pairs: list[tuple[dict, dict]], emails: list) -> bool | None:
        """Attribute the published Email line within its whole email-only financial IR operation."""
        target = record.get("contact_url")
        if not isinstance(target, str) or not target.endswith("/ir/inquiry/"):
            return None
        witnesses = {id(s): s for _,s in pairs if s.get("url") == target
                     and ("Contact IR IR お問い合わせ お問い合わせ先" in s.get("text", "")
                          or s.get("title", "").startswith("お問い合わせ｜株式会社"))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or target != official + "ir/inquiry/" or record.get("verification_level") != "ir_email_verified"
                or record.get("individual_access") != "not_stated" or record.get("outreach_suitability") != "candidate"):
            return False
        source = next(iter(witnesses.values()))
        requested = official + "ir/inquiry"
        if (self.reviewed_late_ir_capture(record, target, requested) is not source
                or source.get("title") != "お問い合わせ｜株式会社" + company or source.get("forms") != []
                or "IR お問い合わせ" not in source.get("headings", []) or len(source.get("redirects", [])) != 1):
            return False
        redirect = source["redirects"][0]
        if (redirect.get("requested_url") != requested or redirect.get("url") != requested
                or type(redirect.get("http_status")) is not int or redirect["http_status"] != 301
                or redirect.get("redirect_target") != target):
            return False
        address = "ir_request@" + urlsplit(official).hostname.removeprefix("www.")
        operation = 'Contact IR IR お問い合わせ お問い合わせ先 株主・投資家の皆様からよく寄せられるご質問をまとめております。 疑問点をすばやく解決できる場合もございますので、ぜひお問い合わせ前にご覧ください。 当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。 お問い合わせいただく際のお願いとご注意 サービスに関するお問い合わせ、営業・ご取材等のご連絡は「Contact」よりご連絡をお願いいたします。 迅速な対応を心がけておりますが、内容によっては回答に時間を要する場合もございます。 お問い合わせ内容によってはお答えできない場合もございます。下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 非公開情報に関するご質問（業績動向など） 金融商品取引法 第166条にある「重要事実」に該当する可能性のあるご質問（株主還元、株価対策など） 株式市場の値動きに関するご質問（株価動向、売買手口など） 誹謗中傷に該当するメッセージ（根拠のない悪口、名誉を棄損する言葉など） 営業や勧誘のお問い合わせ（○○サービスのご案内など） お問い合わせいただいた個人情報につきましては、厳重にお取り扱いいたします。当社の個人情報の取り扱いについては、「当社における個人情報の取扱いについて」をご確認ください。 上記ご理解のほど、何卒よろしくお願いいたします。 お問い合わせEmail：ir_request@prored-p.com'.replace("ir_request@prored-p.com", address)
        line = "お問い合わせEmail：" + address
        home = self.reviewed_late_ir_capture(record, official, official)
        if (emails != [address] or source["text"].count(operation + " IR Contents ") != 1
                or not any(s is source and e["quote"] == operation for e,s in pairs)
                or not any(s is source and e["quote"] == line for e,s in pairs)
                or any(isinstance(link, dict) and str(link.get("url", "")).startswith("mailto:") for link in source.get("links", []))
                or home is None or home.get("redirects") or home.get("title") != "株式会社" + company
                or len(home.get("links", [])) <= 196
                or any(home["links"][i] != {"url": requested, "href": "/ir/inquiry", "label": "お問い合わせ"} for i in (48,95,196))
                or any(refusal in source["text"] for refusal in ("IRお問い合わせは電話のみ", "個人投資家からのお問い合わせは受け付けません",
                    "IRに関するお問い合わせは電話のみ", "個人のお問い合わせは受け付けません"))):
            return False
        return True

    def reviewed_ir_meeting_reception(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """This native form receives IR interviews/meetings; general question suitability stays unconfirmed."""
        witnesses = {(id(s),i):s for _,s in pairs for i,f in enumerate(s.get("forms", []))
                     if any(isinstance(c,dict) and c.get("name") == "radio-398" for c in f.get("controls", []))}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "unconfirmed"):
            return False
        (_, index), source = next(iter(witnesses.items()))
        target = official + "contact/"
        if (index != 0 or self.reviewed_late_ir_capture(record, target, target) is not source
                or source.get("redirects") or source.get("title") != "お問い合わせ｜and factory（アンドファクトリー）"
                or len(source.get("forms", [])) != 1):
            return False
        controls = [{'tag': 'input', 'type': 'radio', 'name': 'radio-398'}, {'tag': 'input', 'type': 'radio', 'name': 'radio-398'}, {'tag': 'input', 'type': 'radio', 'name': 'radio-398'}, {'tag': 'input', 'type': 'radio', 'name': 'radio-398'}, {'tag': 'input', 'type': 'radio', 'name': 'radio-398'}, {'tag': 'input', 'type': 'text', 'name': 'your-name', 'placeholder': '例）田中 太郎'}, {'tag': 'input', 'type': 'email', 'name': 'your-email', 'placeholder': '例）andfactory@example.com'}, {'tag': 'input', 'type': 'tel', 'name': 'tel-530', 'placeholder': '例）09012345678'}, {'tag': 'textarea', 'name': 'your-message', 'placeholder': 'こちらにお問い合わせ内容をご記入ください。'}, {'tag': 'input', 'type': 'checkbox', 'name': 'acceptance-621'}, {'tag': 'input', 'type': 'submit'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/contact/#wpcf7-f3678-p3679-o1",
            [{k:c[k] for k in ("tag", "type", "name", "id", "required") if k in c} for c in controls])
        operation = 'お問い合わせ 本窓口は、株主・投資家等の皆様からのIR取材、ミーティング、 および当社への取材やサービスに関する専用窓口です。 営業・勧誘目的のご連絡は、一切お断りしております。 株主様や投資家様からのIR関連の取材・面談や当社代表への取材等の各種お問い合わせは歓迎いたします。 ※営業目的のメールに対しては、原則として一切返信いたしませんので予めご了承ください。'
        financial_text = 'IRトップ IRニュース IRライブラリ 業績・財務情報 株式情報 IRカレンダー 経営成績 財政状態 キャッシュ・フロー 1Q 2Q 3Q 4Q 売上高 (百万円) 営業利益 (百万円) 経常利益 (百万円) 親会社株主に帰属する当期純利益 (百万円) 1株当たり当期純利益 (円) 自己資本当期純利益率 (％) 当社は2025年８月期第１四半期より連結決算に移行しております。上記では、業績の推移をご覧いただくため、2024年８月期期末までは単体の数値を記載しております。 ご利用上の注意 ・決算短信等の訂正が発表された場合、本データの記載内容は即時反映されません。 ・一部の指標については、決算短信様式変更に伴い通期のみの更新となる場合があります。'
        financial = self.reviewed_late_ir_capture(record, official + "ir/performance/", official + "ir/performance/")
        if (form is None or form["controls"] != controls or form["text"] != 'サービスについて 採用について 広報・取材について その他について IRについて 氏名 （必須） メールアドレス （必須） 電話番号 ご質問内容 （必須） 個人情報の取り扱いについて同意する こちらのフォームにてご提供いただく個人情報は、お問い合わせいただいた内容へのご回答のために利用いたします。 プライバシーポリシー にご同意いただければ、チェックボックスにチェックを入れ、送信してください。'
                or source["text"].count(operation) != 1 or not any(s is source and e["quote"] == operation for e,s in pairs)
                or financial is None or financial.get("redirects")
                or financial.get("title") != "業績・財務情報｜and factory（アンドファクトリー）"
                or financial["text"].count(financial_text) != 1
                or not any(s is financial and e["quote"] == financial_text for e,s in pairs)
                or len(financial.get("links", [])) <= 14
                or any(financial["links"][i] != {"url":target,"href":"/contact/","label":"お問い合わせ"} for i in (7,14))
                or any(refusal in source["text"] for refusal in ("IR取材・面談は受け付けません", "IRのお問い合わせは電話のみ"))):
            return False
        return True

    def reviewed_ir_inquiry_after_privacy(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """The captured form2, separate from two GET searches, has its own native IR choice."""
        witnesses = {(id(s),i):s for _,s in pairs for i,f in enumerate(s.get("forms", []))
                     if "Frontier Eyes Onlineについて" in f.get("text", "")
                     and {"organization_name","your-email_confirm","message"}.issubset(
                         {c.get("name") for c in f.get("controls", []) if isinstance(c,dict)})}
        if not witnesses:
            return None
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (len(witnesses) != 1 or not manual_review_valid(record) or official is None
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")
                or record.get("verification_level") != "form_fields_verified" or record.get("individual_access") != "not_stated"
                or record.get("outreach_suitability") != "candidate"):
            return False
        (_,index),source = next(iter(witnesses.items()))
        target = official + "contact/"
        if (index != 2 or self.reviewed_late_ir_capture(record, target, target) is not source
                or source.get("redirects") or source.get("title") != "お問い合わせ | " + company + "株式会社"
                or len(source.get("forms", [])) != 3 or source["forms"][:2] != [{'action': '/search/', 'method': 'get', 'controls': [{'tag': 'input', 'type': 'text', 'name': 'q', 'placeholder': 'ページ内検索', 'id': 'q'}], 'text': '検索'}, {'action': '/search/', 'method': 'get', 'controls': [{'tag': 'input', 'type': 'text', 'name': 'q', 'placeholder': 'ページ内検索', 'id': 'q'}], 'text': '検索'}]):
            return False
        controls = [{'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry'}, {'tag': 'input', 'type': 'text', 'name': 'your-name', 'placeholder': '例：山田太郎'}, {'tag': 'input', 'type': 'text', 'name': 'organization_name', 'placeholder': '例：フロンティア・マネジメント株式会社'}, {'tag': 'input', 'type': 'radio', 'name': 'location'}, {'tag': 'input', 'type': 'radio', 'name': 'location'}, {'tag': 'select', 'name': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'address', 'placeholder': '例：〇〇区〇〇\u30001丁目2番3号\u3000〇〇ビル'}, {'tag': 'input', 'type': 'tel', 'name': 'telephone', 'placeholder': '例：03-1234-5678'}, {'tag': 'input', 'type': 'email', 'name': 'your-email', 'placeholder': '例：abc@example.co.jp'}, {'tag': 'input', 'type': 'email', 'name': 'your-email_confirm', 'placeholder': '例：abc@example.co.jp'}, {'tag': 'textarea', 'name': 'message', 'placeholder': 'お問い合わせ、ご質問・ご意見の内容'}, {'tag': 'input', 'type': 'checkbox', 'name': 'your-agree'}, {'tag': 'input', 'type': 'submit', 'id': 'form_btn1'}]
        form = self.reviewed_finite_form_witness(record, source, pairs, 2, "post", "/contact/#wpcf7-f9-o1",
            [{k:c[k] for k in ("tag", "type", "name", "id", "required") if k in c} for c in controls])
        choice = "お問い合わせ項目 Inquiry 当社サービスについて（ご相談） IR関連について 取材について 採用について Frontier Eyes Onlineについて その他のお問い合わせ"
        financial = self.reviewed_late_ir_capture(record, official + "ir/information/", official + "ir/information/")
        if (form is None or form["controls"] != controls or form["text"] != 'フロンティア･マネジメント株式会社への各種お問い合わせを受け付けております。 当社「 個人情報保護方針 」を必ずご確認・ご同意のうえ、お問合せください。 For the inquiry to Frontier Management Inc. (FMI), please click here. Please be sure to read and agree to our " Privacy Policy " before contacting us. ※ 必須 マークがついている項目は入力必須項目です。 お問い合わせフォームからのセールス・勧誘はご遠慮ください。 Required Fields お問い合わせ項目 Inquiry 当社サービスについて（ご相談） IR関連について 取材について 採用について Frontier Eyes Onlineについて その他のお問い合わせ お名前 Name 会社・団体名 Organization name ご住所 Address 所在地 Location 国内 国外 都道府県 選択して下さい 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 Overseas 市区郡町村 番地・建物名 * If you live outside Japan, please fill in your address. 電話番号 Telephone 半角数字で入力してください E-mail 半角英数字で入力してください E-mail(確認) Confirm E-mail 半角英数字で入力してください お問い合わせ内容 Message 個人情報の取り扱いに同意する I agree to the privacy policy 入力内容の確認 Confirm'
                or not any(s is source and e["quote"] == choice and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 2 for e,s in pairs)
                or financial is None or financial.get("redirects")
                or financial.get("title") != "株式情報 | IR情報 | " + company + "株式会社"
                or financial["text"].count("証券コード " + str(record.get("security_code")) + " 事業年度 毎年1月1日から12月31日まで") != 1
                or "配当性向の目標を親会社株主に帰属する当期純利益の40%とし、" not in financial["text"]
                or len(financial.get("links", [])) <= 3
                or financial["links"][3] != {"url":target,"href":"/contact/","label":"お問い合わせ"}
                or not any(s is financial and e["quote"] == "お問い合わせ" and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 3 and e.get("source_link_url") == target for e,s in pairs)):
            return False
        return True

    def reviewed_ir_affiliation_name(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The captured corporate IR form explicitly names personal input in its affiliation label."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None or record.get("investigation_status") != "confirmed"
                or record.get("verification_level") != "form_fields_verified"
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")):
            return False
        homes = [f for f in record.get("fetches", []) if isinstance(f, dict) and f.get("url") == official]
        if len(homes) != 1 or not isinstance(homes[0].get("final_url"), str):
            return False
        origin = homes[0]["final_url"]
        parsed = urlsplit(origin)
        home = self.reviewed_late_ir_capture(record, origin, official)
        if (home is None or parsed.scheme != "https" or parsed.netloc != parsed.hostname or parsed.path != "/jp/"
                or parsed.query or parsed.fragment or home.get("title") != company + "株式会社"
                or not home["text"].startswith(company + "株式会社 ") or len(home.get("redirects", [])) != 1):
            return False
        redirect = home["redirects"][0]
        if (redirect.get("requested_url") != official or redirect.get("url") != official
                or type(redirect.get("http_status")) is not int or redirect["http_status"] != 301
                or redirect.get("redirect_target") != origin):
            return False
        target = "https://form.movabletype.net/DA1DC4EC-AAF1-11EF-A525-BC9147D9BC0D?embed=true"
        source = self.reviewed_late_ir_capture(record, target, target)
        if (source is None or source.get("redirects") or source.get("title") != "*リニューアル*お問い合わせフォーム_企業情報_日本"
                or source.get("headings") != [] or len(source.get("forms", [])) != 1):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", "/DA1DC4EC-AAF1-11EF-A525-BC9147D9BC0D/entries", [{'tag': 'select', 'name': '479a037f-c6b0-4fc3-b34d-b6d50db04895', 'id': '479a037f-c6b0-4fc3-b34d-b6d50db04895', 'required': 'required'}, {'tag': 'input', 'type': 'text', 'name': '942191b0-c492-439c-9ac7-63c56def9e8a', 'id': '942191b0-c492-439c-9ac7-63c56def9e8a', 'required': 'required'}, {'tag': 'input', 'type': 'text', 'name': 'e6fced7b-3403-4e93-9fe8-293c4d289923', 'id': 'e6fced7b-3403-4e93-9fe8-293c4d289923'}, {'tag': 'select', 'name': '8af81b5f-a0b0-4e53-bcc9-747e61ecc32a', 'id': '8af81b5f-a0b0-4e53-bcc9-747e61ecc32a'}, {'tag': 'input', 'type': 'text', 'name': '7032871a-f39c-495a-8961-f2ec3fc00d26', 'id': '7032871a-f39c-495a-8961-f2ec3fc00d26', 'required': 'required'}, {'tag': 'input', 'type': 'text', 'name': '4efa2ae3-415f-4792-8b3a-11af62cc7b7c', 'id': '4efa2ae3-415f-4792-8b3a-11af62cc7b7c', 'required': 'required'}, {'tag': 'input', 'type': 'text', 'name': '1bd9d3c3-e093-4472-ae58-b40c2292a6e2', 'id': '1bd9d3c3-e093-4472-ae58-b40c2292a6e2'}, {'tag': 'select', 'name': '4bd9ff02-3efc-4d68-a9c7-268fcf4bb3db', 'id': '4bd9ff02-3efc-4d68-a9c7-268fcf4bb3db'}, {'tag': 'input', 'type': 'text', 'name': '7e455591-057e-4376-a13a-606be86345d3', 'id': '7e455591-057e-4376-a13a-606be86345d3'}, {'tag': 'input', 'type': 'tel', 'name': '355860e5-54bf-42c8-b717-5e350f37e4cb', 'id': '355860e5-54bf-42c8-b717-5e350f37e4cb', 'required': 'required'}, {'tag': 'input', 'type': 'email', 'name': '7af3acbc-19bc-4c27-838d-d7b6169307e6', 'id': '7af3acbc-19bc-4c27-838d-d7b6169307e6', 'required': 'required'}, {'tag': 'textarea', 'name': '230b71c2-2631-4ca7-a9d3-a15ce1b049ea', 'id': '230b71c2-2631-4ca7-a9d3-a15ce1b049ea', 'required': 'required'}, {'tag': 'input', 'type': 'checkbox', 'name': '0757a8c4-9847-4a47-b376-f9bd9f860784', 'id': '0757a8c4-9847-4a47-b376-f9bd9f860784_1'}])
        affiliation = "会社名／学校名／団体名／個人名 必須 会社名／学校名／団体名／個人名を入力してください"
        choice = "お問い合わせ種別 必須 選択してください 企業情報 株主・投資家情報 新卒採用 中途採用"
        if (form is None or form["text"] != 'お問い合わせ種別 必須 選択してください 企業情報 株主・投資家情報 新卒採用 中途採用 お問い合わせ種別を選択してください 会社名／学校名／団体名／個人名 必須 会社名／学校名／団体名／個人名を入力してください 部署名 任意 部署名を入力してください 業種 任意 選択してください 交通・輸送機器 電子・電機機器 デバイス・部品 機械・精密・計測機器 通信・ネットワーク機器 家電AV アミューズメント SI・ソフトウェア 医療・ヘルスケア機器 教育関係 官公庁・公共団体 その他 業種を選択してください お名前(漢字) 必須 姓名を入力してください お名前(カナ) 必須 お名前（セイメイ）を入力してください 郵便番号 任意 郵便番号を入力してください 都道府県 任意 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 都道府県を入力してください 住所 任意 市区町村・番地・建物名を入力してください。 電話番号 必須 電話番号を入力してください メールアドレス 必須 メールアドレスを正しく入力してください お問い合わせ内容 必須 個人情報保護に関する同意について 必須 同意する お客さまからいただいた個人情報は、当社の『 グローバルプライバシーポリシー 』で定める利用目的の範囲で使用いたします。『 グローバルプライバシーポリシー 』ページをご覧いただき、記載されている内容に関して同意していただける場合は、下の［同意する］をチェックしてください。 送信内容を確認する 送信する 入力内容は暗号化されて送信されます。' or form["controls"] != [{'tag': 'select', 'name': '479a037f-c6b0-4fc3-b34d-b6d50db04895', 'required': 'required', 'id': '479a037f-c6b0-4fc3-b34d-b6d50db04895'}, {'tag': 'input', 'type': 'text', 'name': '942191b0-c492-439c-9ac7-63c56def9e8a', 'required': 'required', 'placeholder': "例）" + company + "株式会社", 'id': '942191b0-c492-439c-9ac7-63c56def9e8a'}, {'tag': 'input', 'type': 'text', 'name': 'e6fced7b-3403-4e93-9fe8-293c4d289923', 'placeholder': '例）広報部', 'id': 'e6fced7b-3403-4e93-9fe8-293c4d289923'}, {'tag': 'select', 'name': '8af81b5f-a0b0-4e53-bcc9-747e61ecc32a', 'id': '8af81b5f-a0b0-4e53-bcc9-747e61ecc32a'}, {'tag': 'input', 'type': 'text', 'name': '7032871a-f39c-495a-8961-f2ec3fc00d26', 'required': 'required', 'placeholder': '例）山田太郎', 'id': '7032871a-f39c-495a-8961-f2ec3fc00d26'}, {'tag': 'input', 'type': 'text', 'name': '4efa2ae3-415f-4792-8b3a-11af62cc7b7c', 'required': 'required', 'placeholder': '例）ヤマダタロウ', 'id': '4efa2ae3-415f-4792-8b3a-11af62cc7b7c'}, {'tag': 'input', 'type': 'text', 'name': '1bd9d3c3-e093-4472-ae58-b40c2292a6e2', 'placeholder': '例）123-4567', 'aria-label': '郵便番号', 'id': '1bd9d3c3-e093-4472-ae58-b40c2292a6e2'}, {'tag': 'select', 'name': '4bd9ff02-3efc-4d68-a9c7-268fcf4bb3db', 'id': '4bd9ff02-3efc-4d68-a9c7-268fcf4bb3db'}, {'tag': 'input', 'type': 'text', 'name': '7e455591-057e-4376-a13a-606be86345d3', 'placeholder': '例）目黒区中目黒2-9-13', 'id': '7e455591-057e-4376-a13a-606be86345d3'}, {'tag': 'input', 'type': 'tel', 'name': '355860e5-54bf-42c8-b717-5e350f37e4cb', 'required': 'required', 'placeholder': '例）03-1234-5678', 'id': '355860e5-54bf-42c8-b717-5e350f37e4cb'}, {'tag': 'input', 'type': 'email', 'name': '7af3acbc-19bc-4c27-838d-d7b6169307e6', 'required': 'required', 'placeholder': '例）xxxxx@stanley.co.jp', 'id': '7af3acbc-19bc-4c27-838d-d7b6169307e6'}, {'tag': 'textarea', 'name': '230b71c2-2631-4ca7-a9d3-a15ce1b049ea', 'required': 'required', 'placeholder': 'お問い合わせ内容を1500文字以内で入力ください。', 'id': '230b71c2-2631-4ca7-a9d3-a15ce1b049ea'}, {'tag': 'input', 'type': 'checkbox', 'name': '0757a8c4-9847-4a47-b376-f9bd9f860784', 'id': '0757a8c4-9847-4a47-b376-f9bd9f860784_1'}]
                or not any(s is source and e["quote"] == choice for e, s in pairs)
                or not any(s is source and e["quote"] == affiliation for e, s in pairs)
                or not any(s is source and e["quote"] == "お問い合わせ内容を1500文字以内で入力ください。"
                           and e.get("extraction_scope") == "form_control_attribute" and e.get("field_path") == "forms.0.controls.11.placeholder"
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and public_attribute_quote(e, source) for e, s in pairs)):
            return False
        parent_url = origin + "inquiry/corporate/"
        parent = self.reviewed_late_ir_capture(record, parent_url, parent_url)
        financial_url = origin + "ir/others/faq/"
        financial = self.reviewed_late_ir_capture(record, financial_url, financial_url)
        operation = "株主・投資家情報、採用またはその他企業活動に関するお問い合わせをご希望の場合は、下記フォームをご利用ください。"
        proposal_refusal = ("法人様や個人様による製品やアイデアのご提案は、当社独自の研究開発活動に対して制約を受けることを避け、"
                            "特許などの産業財産権に関わるトラブルや誤解を防ぐため、受け付けておりません。 営業・商談・営利目的のお問い合わせはご遠慮願います。")
        purpose = "IRに関するお問い合わせ Q19 IRに関するお問い合わせ A19 IRに関するお問合せは こちら からお願いいたします。"
        identity = "Q10 証券コードを教えて下さい。 A10 " + str(record.get("security_code")) + "です。"
        if (parent is None or parent.get("redirects") or parent.get("title") != "企業情報についてのお問い合わせ | お問い合わせ | " + company + "株式会社"
                or "企業情報についてのお問い合わせ" not in parent.get("headings", [])
                or parent["text"].count("ホーム お問い合わせ 企業情報についてのお問い合わせ 企業情報についてのお問い合わせ " + operation) != 1
                or parent["text"].count(proposal_refusal) != 1 or len(parent.get("links", [])) <= 154
                or parent["links"][154] != {"url": target, "src": target, "label": "embedded frame"}
                or not any(s is parent and e["quote"] == operation and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 154 and e.get("source_link_url") == target
                           and e.get("discovery_link_label") == "embedded frame" for e, s in pairs)
                or not any(s is parent and e["quote"] == proposal_refusal for e, s in pairs)
                or financial is None or financial.get("redirects")
                or financial.get("title") != "よくあるご質問（IR FAQ） | 株主・投資家情報 | " + company + "株式会社"
                or not {"よくあるご質問（IR FAQ）", "決算・財務について", "株式について", "IRに関するお問い合わせ"}.issubset(financial.get("headings", []))
                or "決算・財務について Q5 決算期はいつですか。 A5 3月31日です。" not in financial["text"]
                or financial["text"].count(identity) != 1 or financial["text"].count(purpose) != 1
                or not any(s is financial and e["quote"] == identity for e, s in pairs)
                or len(financial.get("links", [])) <= 167
                or financial["links"][167] != {"url": parent_url, "href": "/jp/inquiry/corporate/", "label": "こちら"}
                or not any(s is financial and e["quote"] == purpose and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 167 and e.get("source_link_url") == parent_url
                           and e.get("discovery_link_label") == "こちら" for e, s in pairs)
                or any(refusal in s["text"] for s in (source, parent, financial) for refusal in (
                    "個人のお問い合わせは受け付けません", "個人投資家のお問い合わせはお断り", "IRのお問い合わせは受け付けません",
                    "IRに関するお問い合わせは電話のみ", "個人様によるIRに関するお問い合わせは受け付けておりません。"))):
            return False
        return self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)

    def reviewed_ir_affiliation_attribute(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Only the actual affiliation/department attributes of this indexed financial IR question form."""
        official = self.reviewed_late_ir_issuer_root(record)
        company = record.get("company_name")
        if (not manual_review_valid(record) or official is None or record.get("investigation_status") != "confirmed"
                or record.get("verification_level") != "form_fields_verified"
                or company != self.universe.get(record.get("security_code"), {}).get("company_name")):
            return False
        parsed = urlsplit(official)
        target = "https://info." + parsed.hostname.removeprefix("www.") + "/form/pub/fukuda/public"
        source = self.reviewed_late_ir_capture(record, target, target)
        if (source is None or source.get("redirects") or source.get("title") != ""
                or source.get("headings") != ["一般総合お問い合わせフォ－ム", "ご注意", "個人情報の取り扱いについて"]
                or len(source.get("forms", [])) != 1):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", "/form/pub/fukuda/public", [{'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_2'}, {'tag': 'textarea', 'name': 'c_q2', 'id': 'c_q2'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_first', 'id': 'c_q3_first'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_second', 'id': 'c_q3_second'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_etc'}, {'tag': 'input', 'type': 'text', 'name': 'c_q12_etc_text', 'id': 'c_q12_etc_text'}, {'tag': 'input', 'type': 'text', 'name': 'c_q4', 'id': 'c_q4'}, {'tag': 'input', 'type': 'text', 'name': 'c_q11', 'id': 'c_q11'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q13', 'id': 'c_q13_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q13', 'id': 'c_q13_1'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_left', 'id': 'c_q5_left'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_right', 'id': 'c_q5_right'}, {'tag': 'select', 'name': 'c_q6', 'id': 'c_q6'}, {'tag': 'input', 'type': 'text', 'name': 'c_q7', 'id': 'c_q7'}, {'tag': 'input', 'type': 'text', 'name': 'c_q8', 'id': 'c_q8'}, {'tag': 'input', 'type': 'text', 'name': 'c_q8_confirm', 'id': 'c_q8_confirm'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_2'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_areacode', 'id': 'c_q10_areacode'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_citycode', 'id': 'c_q10_citycode'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_subscribercode', 'id': 'c_q10_subscribercode'}, {'tag': 'input', 'type': 'submit', 'name': 'wcf5start', 'id': 'wcf5start'}])
        instruction = "例）" + company + "株式会社（医療機関名、会社名、個人など）"
        department = "部署名の無い方は「なし」と入力してください。"
        choice = "お問い合わせ項目 ※必須 IRについて 採用について その他 内容 ※必須"
        if (form is None or form["text"] != '一般総合お問い合わせフォ－ム TOP 一般総合お問い合わせフォ－ム ご注意 1.各項目は正確にご記入ください。ご記入内容が正確でない場合や空欄の場合は、お問い合わせにご回答できない場合もございますので、あらかじめご了承ください。また、お問い合わせの内容は具体的にご記入ください。内容により回答にお時間をいただく場合がございますので、あらかじめご了承ください。 2.当社からの回答内容の一部または全体を、当社の許可無く転用、二次利用することは、著作権上認められておりませんのでご注意願います。 3.フォームのご利用にあたっては必ず こちら をご覧ください。 ※3営業日以内（弊社営業カレンダーに基づく）にご返答させていただいております。 お急ぎの場合は機器等に記載の最寄りの 営業所 へ直接お電話願います。 お問い合わせ項目 ※必須 IRについて 採用について その他 内容 ※必須 お名前（漢字） ※必須 姓 名 ご職業 ※必須 一般企業 学校・各種団体 その他 ご所属 ※必須 部署名 ※必須 住所種別 ※必須 ご自宅 勤務先 郵便番号 ※必須 - 都道府県 ※必須 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 市区町村 ※必須 メールアドレス ※必須 (確認) 電話番号種別 ※必須 ご自宅 勤務先 携帯電話 電話番号 ※必須 - - 個人情報の取り扱いについて お問い合わせいただいた内容につきましては、第三者に転売・譲渡・開示することは一切ございません。また個人情報保護法をはじめとする法令法規を遵守し、第三者への漏洩なきよう、厳重な機密管理のもとで取り扱わせていただきます。当社プライバシーポリシー（個人情報保護方針）については こちら をご覧ください。 プライバシーポリシー サイトのご利用にあたって 特定商取引法 サイトマップ Copyright © FUKUDA DENSHI All Rights Reserved' or form["controls"] != [{'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q1', 'id': 'c_q1_2'}, {'tag': 'textarea', 'name': 'c_q2', 'id': 'c_q2'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_first', 'id': 'c_q3_first'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_second', 'id': 'c_q3_second'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q12', 'id': 'c_q12_etc'}, {'tag': 'input', 'type': 'text', 'name': 'c_q12_etc_text', 'id': 'c_q12_etc_text'}, {'tag': 'input', 'type': 'text', 'name': 'c_q4', 'placeholder': instruction, 'id': 'c_q4'}, {'tag': 'input', 'type': 'text', 'name': 'c_q11', 'placeholder': '部署名の無い方は「なし」と入力してください。', 'id': 'c_q11'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q13', 'id': 'c_q13_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q13', 'id': 'c_q13_1'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_left', 'id': 'c_q5_left'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_right', 'id': 'c_q5_right'}, {'tag': 'select', 'name': 'c_q6', 'id': 'c_q6'}, {'tag': 'input', 'type': 'text', 'name': 'c_q7', 'placeholder': '例）文京区', 'id': 'c_q7'}, {'tag': 'input', 'type': 'text', 'name': 'c_q8', 'id': 'c_q8'}, {'tag': 'input', 'type': 'text', 'name': 'c_q8_confirm', 'id': 'c_q8_confirm'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_0'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_1'}, {'tag': 'input', 'type': 'radio', 'name': 'c_q9', 'id': 'c_q9_2'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_areacode', 'id': 'c_q10_areacode'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_citycode', 'id': 'c_q10_citycode'}, {'tag': 'input', 'type': 'tel', 'name': 'c_q10_subscribercode', 'id': 'c_q10_subscribercode'}, {'tag': 'input', 'type': 'submit', 'name': 'wcf5start', 'id': 'wcf5start'}]
                or source["text"] != form["text"]
                or not any(s is source and e["quote"] == choice and type(e.get("source_form_index")) is int
                           and e["source_form_index"] == 0 and type(e.get("form_index")) is int and e["form_index"] == 0 for e, s in pairs)
                or not all(any(s is source and e["quote"] == text and e.get("extraction_scope") == "form_control_attribute"
                               and e.get("field_path") == path and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                               and type(e.get("form_index")) is int and e["form_index"] == 0 and public_attribute_quote(e, source)
                               for e, s in pairs) for text, path in ((instruction, "forms.0.controls.10.placeholder"), (department, "forms.0.controls.11.placeholder")))):
            return False
        parent_url = official + "info/inquiry.html"
        parent = self.reviewed_late_ir_capture(record, parent_url, parent_url)
        financial_url = official + "ir/faq.html"
        financial = self.reviewed_late_ir_capture(record, financial_url, financial_url)
        route = "一般総合お問い合わせ （採用・IR含むその他）"
        identity = "Q " + company + "の証券コードは？ A 当社の証券コードは「" + str(record.get("security_code")) + "」で、所属業種は「電気機器」です。"
        context = "よくあるご質問 TOP IR情報 よくあるご質問 沿革 決算・財務 株式"
        if (parent is None or parent.get("redirects") or parent.get("title") != "お問い合わせ | " + company
                or "フォームでのお問い合わせ" not in parent.get("headings", [])
                or parent["text"].count("一般・療養者の皆さま " + route + " 在宅療養で機器をご使用中の方") != 1
                or len(parent.get("links", [])) <= 92 or parent["links"][92] != {"url": target, "href": target, "label": route}
                or not any(s is parent and e["quote"] == route and type(e.get("source_link_index")) is int
                           and e["source_link_index"] == 92 and e.get("source_link_url") == target and e.get("source_link_label") == route for e, s in pairs)
                or financial is None or financial.get("redirects") or financial.get("title") != "よくあるご質問 | " + company
                or financial.get("headings") != ["よくあるご質問", "沿革", "決算・財務", "株式"]
                or financial["text"].count(context) != 1 or financial["text"].count(identity) != 1
                or "決算・財務 Q 会社の決算期を教えてください A 決算期は毎年3月31日です。中間決算期は9月30日です。" not in financial["text"]
                or not any(s is financial and e["quote"] == identity for e, s in pairs)
                or not any(s is financial and e["quote"] == context for e, s in pairs)
                or any(refusal in s["text"] for s in (source, parent, financial) for refusal in (
                    "個人のお問い合わせは受け付けません", "個人投資家のお問い合わせはお断り", "IRのお問い合わせは受け付けません", "IRに関するお問い合わせは電話のみ"))):
            return False
        return self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)

    def reviewed_ir_region_company_placeholder(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Only the company input's public individual instruction; region behavior stays unverified."""
        if (not manual_review_valid(record) or record.get("investigation_status") != "provisional"
                or record.get("verification_level") != "form_fields_verified" or record.get("identity_status") != "unverified"
                or record.get("identity_matches") != []):
            return False
        official = self.reviewed_late_ir_issuer_root(record)
        if (official is None or record.get("company_name") != self.universe.get(record.get("security_code"), {}).get("company_name")):
            return False
        target = official + "en/contact/"
        source = self.reviewed_late_ir_capture(record, target, target)
        if (source is None or source.get("redirects") or source.get("title") != "Contact | ADVANTEST CORPORATION"
                or source.get("headings") != ["Contact"] or len(source.get("forms", [])) != 2
                or source["forms"][0] != {"action": "/en/search/", "method": "get", "text": "Search",
                                          "controls": [{"tag": "input", "type": "text", "name": "q", "placeholder": "Search Keywords"}]}
                or any(s is not source and e.get("extraction_scope") == "form_control_attribute"
                       and e.get("quote") == 'If you are an individual investor, please enter "Individual."' for e, s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 1, "post", "./", [{'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region1'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region2'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region3'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region4'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region5'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region6'}, {'tag': 'input', 'type': 'radio', 'name': 'data[ContactEn][region]', 'id': 'region7'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry1'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry2'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry3'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry4'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry5'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry6'}, {'tag': 'select', 'name': 'data[ContactEn][category]', 'id': 'cInquiry7'}, {'tag': 'input', 'type': 'text', 'name': 'data[ContactEn][fname]', 'id': 'firstname'}, {'tag': 'input', 'type': 'text', 'name': 'data[ContactEn][lname]', 'id': 'lastname'}, {'tag': 'textarea', 'name': 'data[ContactEn][address]', 'id': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'data[ContactEn][email]', 'id': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'data[ContactEn][company]', 'id': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'data[ContactEn][subject]', 'id': 'subject'}, {'tag': 'textarea', 'name': 'data[ContactEn][message]', 'id': 'message'}])
        instruction = 'If you are an individual investor, please enter "Individual."'
        operation = "Contact Please fill out the form below to submit a question or comment. * is mandatory."
        if (form is None or form["text"] != 'Region * Americas Europe Singapore China Taiwan South Asia South Korea Please select a region. Category * Please select... General inquiries Field service Information security Intellectual property Investor relations Podcast Sales: Test systems Sales: Advanced test interface solutions Sales: Advantest cloud solutions Sales: Device certification Test Automation Software (MLT) for 4G, IoT and 5G Sales: High-performance conductive elastomer interconnect solutions Sales: Socket and thermal control units Sales: System level test Sales: Certified Pre-Owned system System engineering Training Advantest Innovation Center Webmaster Please select... General enquires & comments ATE Product Information security Intellectual property Measurement instruments Power semiconductor test equipment Press Service & support Training Webmaster Please select... General inquiries Field service engineering Information security Intellectual property Investors information Training Webmaster Please select... General inquiries HR Information security Intellectual property Training Webmaster Please select... General inquiries Information security Intellectual property Please select... General inquiries Sales Information security Intellectual property Please select... General inquiries Field service Information security Intellectual property Manufacturing Purchasing R&D Sales System engineering memory System engineering T2000 System engineering V93000 Training Please select a category. First Name * Please enter a value for the "First Name" field. Last Name * Please enter a value for the "Last Name" field. Mailing Address Email * Please enter a value for the "Email" field. Company * Please enter a value for the "Company" field. Subject * Please enter a value for the "Subject" field. Message * confirm'
                or form["controls"][18].get("placeholder") != instruction
                or any("value" in c for c in form["controls"][:7])
                or any(refusal in source["text"] for refusal in (
                    "Individual investor inquiries are not accepted.", "Investor relations inquiries are accepted by telephone only.",
                    "Individual investors must use the Japan region."))
                or not any(s is source and e["quote"] == instruction and e.get("extraction_scope") == "form_control_attribute"
                           and e.get("field_path") == "forms.1.controls.18.placeholder"
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == 1
                           and public_attribute_quote(e, source) for e, s in pairs)
                or not any(s is source and e["quote"] == operation for e, s in pairs)
                or source["text"].count(operation + " " + form["text"]) != 1
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form,
                                             official_host=urlsplit(official).hostname)):
            return False
        parent_url = official + "en/investors/shares-and-corporate-bonds/share-information/"
        financial = self.reviewed_late_ir_capture(record, parent_url, parent_url)
        identity = "Stock Exchange Listings Tokyo Stock Exchange, Prime Market (Securities Code: " + str(record.get("security_code")) + ")"
        return (financial is not None and not financial.get("redirects")
                and financial.get("title") == "Share Information｜Shares and Corporate Bonds｜ADVANTEST CORPORATION"
                and {"Share Information", "Ownership Information", "Administrative Procedures Regarding Shares"}.issubset(financial.get("headings", []))
                and financial["text"].count(identity) == 1
                and "Fiscal Year April 1 through March 31 Ordinary General Meeting of Shareholders" in financial["text"]
                and any(s is financial and e["quote"] == identity for e, s in pairs)
                and len(financial.get("links", [])) > 223
                and financial["links"][223] == {"url": target, "href": "/en/contact/", "label": "Contact"}
                and any(s is financial and e["quote"] == "Contact" and type(e.get("source_link_index")) is int
                        and e["source_link_index"] == 223 and e.get("source_link_url") == target for e, s in pairs))

    def reviewed_captured_ir_parent(self, record: dict, pairs: list[tuple[dict, dict]], url: str,
                                    requested: str, title: str, headings: set[str], primary: str,
                                    index: int, href: str, target: str, label: str,
                                    quote: str, *, redirected: bool = False) -> dict | None:
        """The seven saved families use their own financial primary and exact captured link."""
        parent = self.reviewed_late_ir_capture(record, url, requested)
        if (parent is None or parent.get("title") != title or not headings.issubset(parent.get("headings", []))
                or parent["text"].count(primary) != 1):
            return None
        redirects = parent.get("redirects", [])
        if redirected:
            if (not isinstance(redirects, list) or len(redirects) != 1
                    or {k: redirects[0].get(k) for k in ("requested_url", "url", "http_status", "redirect_target")}
                       != {"requested_url": requested, "url": requested, "http_status": 301, "redirect_target": url}):
                return None
        elif redirects:
            return None
        links = parent.get("links", [])
        if (not isinstance(links, list) or len(links) <= index
                or links[index] != {"url": target, "href": href, "label": label}
                or not any(s is parent and e["quote"] == quote
                           and type(e.get("source_link_index")) is int and e["source_link_index"] == index
                           and e.get("source_link_url") == target
                           and e.get("source_link_label", e.get("discovery_link_label")) == label
                           and ("source_link_href" not in e or e["source_link_href"] == href)
                           for e, s in pairs)):
            return None
        return parent

    def reviewed_captured_ir_reception(self, record: dict, pairs: list[tuple[dict, dict]]) -> tuple | None:
        """Complete native families, their local purposes and financial routes remain separate.

        The company-instruction and bilingual-audience families add personal
        evidence only. The English family has one saved TSE-code witness;
        it neither rewrites the historical identity state nor invents an alias.
        """
        if not manual_review_valid(record):
            return None
        families = (("company", {"sales_office", "inquiry_category", "zip1", "zip2"}),
                    ("consent", {"last_name_kana", "product[]", "service[]"}),
                    ("english", {"region", "fname", "msg"}),
                    ("stock_attribute", {"氏名", "フリガナ", "ご相談内容", "submitConfirm"}),
                    ("department", {"job_name", "job_post", "facsimile", "mail:cf"}),
                    ("bilingual", {"category", "occupation", "address1", "address2"}),
                    ("faq_numeric", {"formElementVal70", "formElementVal71Sei", "formElementVal71Mei"}))
        witnesses = {}
        for _, source in pairs:
            for index, form in enumerate(source.get("forms", [])):
                if not isinstance(form, dict):
                    continue
                names = {c.get("name") for c in form.get("controls", []) if isinstance(c, dict)}
                for family, signature in families:
                    if signature.issubset(names):
                        witnesses[(id(source), index)] = (family, source)
        if not witnesses:
            return None
        if len(witnesses) != 1:
            return ("ambiguous", False, False, False)
        (_, observed_index), (family, source) = next(iter(witnesses.items()))
        failed = (family, False, False, False)
        official = record.get("official_url")
        parsed = urlsplit(str(official))
        if (not isinstance(official, str) or parsed.scheme != "https" or parsed.netloc != parsed.hostname
                or parsed.query or parsed.fragment or parsed.path != ("/jp/" if family == "company" else "/")
                or len(identity_key(record.get("company_name", ""))) < 2):
            return failed
        company = record["company_name"]
        if company != self.universe.get(record.get("security_code"), {}).get("company_name"):
            return failed
        personal = False
        identity = False
        index = 1 if family == "department" else 0
        method, action = "post", None
        layout = []
        if family == "company":
            target = official + "inquiry/inquiry.html"
            title = "お問い合わせ | TOCOSR | " + company + "株式会社"
            required_headings = {"お問い合わせ"}
            action = "confirm.html"
            layout = [{'tag': 'input', 'type': 'radio', 'name': 'inquiry_category'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry_category'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry_category'}, {'tag': 'input', 'type': 'radio', 'name': 'inquiry_category'}, {'tag': 'select', 'name': 'sales_office'}, {'tag': 'textarea', 'name': 'contents'}, {'tag': 'input', 'type': 'text', 'name': 'last_name'}, {'tag': 'input', 'type': 'text', 'name': 'first_name'}, {'tag': 'input', 'type': 'text', 'name': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'zip1'}, {'tag': 'input', 'type': 'text', 'name': 'zip2'}, {'tag': 'select', 'name': 'prefecture'}, {'tag': 'input', 'type': 'text', 'name': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'tel1'}, {'tag': 'input', 'type': 'text', 'name': 'tel2'}, {'tag': 'input', 'type': 'text', 'name': 'tel3'}, {'tag': 'input', 'type': 'checkbox', 'name': 'agree'}]
        elif family == "consent":
            target = official + "contact/contact.php"
            title = "お問い合わせ | " + company
            required_headings = {"株式会社" + company, "お問い合わせ"}
            method, action = "POST", "confirm.php"
            layout = [{'tag': 'input', 'type': 'checkbox', 'name': 'privacy', 'id': 'privacy', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'last_name', 'id': 'last_name', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'first_name', 'id': 'first_name', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'last_name_kana', 'id': 'last_name_kana', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'first_name_kana', 'id': 'first_name_kana', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'company', 'required': None}, {'tag': 'select', 'name': 'industry', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'zip', 'required': None}, {'tag': 'input', 'type': 'text', 'name': 'address', 'required': None}, {'tag': 'input', 'type': 'tel', 'name': 'phone', 'required': None}, {'tag': 'input', 'type': 'email', 'name': 'email', 'required': None}, {'tag': 'select', 'name': 'inquiry', 'id': 'inquiry', 'required': None}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'duosim5g'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'uesimbox'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'fh'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'evolver'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'traffic'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'linktropy'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'wicheck'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'callbox'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'rls'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'eeneo'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'qp'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'pureinsight'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'ethernet'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'ctcu_ethernet'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'endace'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'griffin'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'ptp'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'falcon'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'c2m'}, {'tag': 'input', 'type': 'checkbox', 'name': 'product[]', 'id': 'other'}, {'tag': 'input', 'type': 'checkbox', 'name': 'service[]', 'id': 'test_service'}, {'tag': 'input', 'type': 'checkbox', 'name': 'service[]', 'id': 'contract_development'}, {'tag': 'input', 'type': 'checkbox', 'name': 'service[]', 'id': 'onecert'}, {'tag': 'textarea', 'name': 'body', 'id': 'body', 'required': None}]
        elif family == "english":
            target = official + "contact/index.php?type=Investor%20Relations"
            title = "Contact Us - SUMIDA CORPORATION"
            required_headings = {"Contact Us"}
            action = "index.php"
            layout = [{'tag': 'select', 'name': 'type', 'id': 'type'}, {'tag': 'select', 'name': 'region', 'id': 'region'}, {'tag': 'input', 'type': 'text', 'name': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'fname'}, {'tag': 'input', 'type': 'text', 'name': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'phone'}, {'tag': 'input', 'type': 'text', 'name': 'subject'}, {'tag': 'textarea', 'name': 'msg'}, {'tag': 'input', 'type': 'submit', 'name': 'send'}]
        elif family == "stock_attribute":
            target = official + "contact/"
            title = "お問い合わせ | " + company + "株式会社"
            required_headings = {"お問い合わせ"}
            action = ""
            layout = [{'tag': 'input', 'type': 'text', 'name': '氏名'}, {'tag': 'input', 'type': 'text', 'name': 'フリガナ'}, {'tag': 'textarea', 'name': 'ご相談内容'}, {'tag': 'input', 'type': 'text', 'name': '会社名'}, {'tag': 'input', 'type': 'email', 'name': 'メールアドレス'}, {'tag': 'input', 'type': 'submit', 'name': 'submitConfirm'}]
        elif family == "department":
            target = "https://reg31.smp.ne.jp/regist/is?SMPFORM=lhqd-ogpdl-dc81a9ee352bb5f3e0194239a6ffc00a"
            title = company + "株式会社｜お問い合わせ：その他のお問い合わせ"
            required_headings = {"その他のお問い合わせ"}
            action = "/regist/Reg2"
            layout = [{'tag': 'input', 'type': 'text', 'name': 'name', 'id': 'name'}, {'tag': 'input', 'type': 'text', 'name': 'nameKana', 'id': 'kana'}, {'tag': 'input', 'type': 'text', 'name': 'job_name', 'id': 'job_name'}, {'tag': 'input', 'type': 'text', 'name': 'job_post', 'id': 'job_post'}, {'tag': 'input', 'type': 'text', 'name': 'zipCode', 'id': 'txtZipcode1'}, {'tag': 'input', 'type': 'text', 'name': 'address', 'id': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'tel_', 'id': 'tel'}, {'tag': 'input', 'type': 'text', 'name': 'facsimile', 'id': 'fax'}, {'tag': 'input', 'type': 'text', 'name': 'mail', 'id': 'mail'}, {'tag': 'input', 'type': 'text', 'name': 'mail:cf', 'id': 'mail_conf'}, {'tag': 'textarea', 'name': 'inquiry', 'id': 'inquiry'}, {'tag': 'input', 'type': 'image', 'name': 'submit'}]
        elif family == "bilingual":
            ir_origin = "https://ir." + parsed.hostname.removeprefix("www.") + "/"
            target = ir_origin + "inquiry01/"
            title = "IRお問い合わせ | " + company
            required_headings = {"IRお問い合わせ", "入力", "確認", "完了"}
            action = "/sites/default/php/inquiry.php"
            layout = [{'tag': 'input', 'type': 'text', 'name': 'name'}, {'tag': 'input', 'type': 'radio', 'name': 'category', 'id': 'category_1'}, {'tag': 'input', 'type': 'radio', 'name': 'category', 'id': 'category_2'}, {'tag': 'input', 'type': 'radio', 'name': 'category', 'id': 'category_3'}, {'tag': 'input', 'type': 'radio', 'name': 'category', 'id': 'category_4'}, {'tag': 'input', 'type': 'text', 'name': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'email2'}, {'tag': 'input', 'type': 'text', 'name': 'tel'}, {'tag': 'input', 'type': 'text', 'name': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'occupation'}, {'tag': 'input', 'type': 'text', 'name': 'zip'}, {'tag': 'input', 'type': 'text', 'name': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'address1'}, {'tag': 'input', 'type': 'text', 'name': 'address2'}, {'tag': 'input', 'type': 'text', 'name': 'fax'}, {'tag': 'input', 'type': 'text', 'name': 'subject'}, {'tag': 'textarea', 'name': 'message', 'id': ''}]
        else:
            target = official + "contact.html"
            title = "お問い合わせ │ " + company
            required_headings = {"お問い合わせ"}
            layout = [{'tag': 'input', 'type': 'text', 'name': 'formElementVal70', 'id': 'formElementVal70'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal71Sei', 'id': 'formElementVal71Sei'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal71Mei', 'id': 'formElementVal71Mei'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal72', 'id': 'formElementVal72'}, {'tag': 'input', 'type': 'text', 'name': 'formElementVal73', 'id': 'formElementVal73'}, {'tag': 'textarea', 'name': 'formElementVal74', 'id': 'formElementVal74'}, {'tag': 'input', 'type': 'checkbox', 'name': 'formElementVal75[]', 'id': 'formElementVal750'}, {'tag': 'input', 'type': 'submit'}]
        requested = (official + "contact/index.php?type=Investor Relations" if family == "english"
                     else official + "contact" if family == "stock_attribute" else target)
        if (observed_index != index or source.get("url") != target or source.get("requested_url") != requested
                or self.reviewed_late_ir_capture(record, target, requested) is not source
                or source.get("title") != title or not required_headings.issubset(source.get("headings", []))
                or len(source.get("forms", [])) != (2 if family == "department" else 1)):
            return failed
        if family == "stock_attribute":
            redirects = source.get("redirects", [])
            if (len(redirects) != 1
                    or {k: redirects[0].get(k) for k in ("requested_url", "url", "http_status", "redirect_target")}
                       != {"requested_url": requested, "url": requested, "http_status": 301, "redirect_target": target}):
                return failed
        elif source.get("redirects"):
            return failed
        form = self.reviewed_finite_form_witness(record, source, pairs, index, method, action, layout)
        if form is None:
            return failed
        text, controls = form["text"], form["controls"]
        local_quotes = [e["quote"] for e, s in pairs if s is source]
        if family == "company":
            purpose = "お問い合わせ項目 必須 製品・販売 IR 採用 その他"
            instruction = "貴社名 必須 （個人の場合には「個人」と入力してください）"
            if (not text.startswith(purpose + " 営業所名 必須 ") or purpose not in local_quotes
                    or "E-mail（半角英数字） 必須" not in text
                    or instruction + " TEL（半角数字で市外局番から） 必須" not in text
                    or not any(s is source and e["quote"] == instruction
                               and ("source_form_index" not in e or type(e["source_form_index"]) is int and e["source_form_index"] == 0)
                               and ("form_index" not in e or type(e["form_index"]) is int and e["form_index"] == 0) for e, s in pairs)
                    or any("value" in c for c in controls[:4])):
                return failed
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "ir/index.html", official + "ir/index.html",
                "IR情報 | TOCOSR | " + company + "株式会社", {"IRニュース IR news", "株式情報", "決算短信", "有価証券報告書"},
                "お問い合わせ はこちら IRニュース IR news ", 57, "../inquiry/inquiry.html", target, "お問い合わせ はこちら", "お問い合わせ はこちら")
            if parent is None or "決算短信〔日本基準〕（連結）" not in parent["text"].split("お問い合わせ はこちら IRニュース IR news ")[1]:
                return failed
            personal = True
        elif family == "consent":
            purpose = ("* お問い合わせ種別 - 選択してください - 製品について サービスについて 製品説明・デモの依頼 見積り依頼 "
                       "サポートについて 会社・ＩＲについて 採用について 商品紹介 人材紹介 協業について その他")
            if (not text.startswith("* 私は プライバシーポリシー に同意します。 * お名前 * フリガナ * 会社名 * 業種 ")
                    or purpose not in text or purpose not in local_quotes
                    or controls[10].get("aria-label") != "メールアドレス" or controls[11].get("aria-label") != "お問い合わせ種別"
                    or not text.endswith(" お問い合わせ内容 確認する")):
                return failed
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "ir/", official + "ir/",
                "株主・投資家情報 | " + company, {"IRニュース", "IRカレンダー"},
                "TOP 株主・投資家情報 ", 67, "/contact/contact.php", target, "お問い合わせ", "お問い合わせ")
            if (parent is None or "第36期 決算発表" not in parent["text"].split("TOP 株主・投資家情報 ")[1]
                    or "財務情報 業績ハイライト 決算短信 プレゼンテーション 有価証券報告書・四半期報告書" not in parent["text"]):
                return failed
        elif family == "english":
            purpose = ("Select Enquiry Type * Please choose Products (e.g. sales quotation, product information) "
                       "Procurement(e.g. enquiry from supplier) Investor Relations Careers Sustainability")
            operation = "Contact Us Thank you for your interest in SUMIDA. To get in touch please complete the following form to send us your enquiry."
            if (text != purpose + " Your Region * Company/Group Name Name * Address E-Mail * Telephone Number Subject * Enquiry *"
                    or operation not in local_quotes or source["text"].count(operation) != 1):
                return failed
            primary = ("Welcome to the Investor Relations section of our website. Please click on reports to view our performance related information.")
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "investor-relations/", official + "investor-relations/",
                "Investor Relations - Performance Information - SUMIDA CORPORATION", {"Stock Price", "Performance Information"},
                primary, 76, "/contact/index.php?type=Investor%20Relations", target, "Investor Relations",
                "Contact Products Procurement Investor Relations Careers Sustainability")
            home = self.reviewed_late_ir_capture(record, official, official)
            witness = "Briefing Session for Individual Investors Sumida Corporation | TSE Code " + str(record.get("security_code")) + " Jun 11, 2024"
            if (parent is None or "Latest Performance Results 2nd Quarter Fiscal Year 2026" not in parent["text"]
                    or primary not in [e["quote"] for e, s in pairs if s is parent]
                    or home is None or home.get("redirects") or home.get("title") != "SUMIDA CORPORATION"
                    or home["text"].count(witness) != 1
                    or "Sumida Corporation | TSE Code " + str(record.get("security_code")) + " Jun 11, 2024" not in home.get("headings", [])
                    or not any(s is home and e["quote"] == "SUMIDA CORPORATION" for e, s in pairs)):
                return failed
            identity = True
        elif family == "stock_attribute":
            purpose = "メディア取材、業務に関するご質問、株式に関するご質問などご自由にご記入ください。"
            operation = "下記お問い合わせフォームの必須項目を入力いただき、プライバシーポリシーをお読みの上、 「確認画面へ」ボタンを押して確認画面へお進みください"
            if (text != "ご担当者様お名前 ご相談内容 会社名 メールアドレス 送信前に 個人情報保護方針 をお読みください 確認画面へ 上記内容で送信する"
                    or controls[2].get("placeholder") != purpose or operation not in local_quotes
                    or source["text"].count(operation + " 1 入力画面 2 内容確認 3 送信完了 " + text) != 1
                    or not any(s is source and e["quote"] == purpose and e.get("extraction_scope") == "form_control_attribute"
                               and e.get("field_path") == "forms.0.controls.2.placeholder"
                               and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                               and public_attribute_quote(e, source) for e, s in pairs)):
                return failed
            financial = "財務ハイライト 決算短信 有価証券報告書・ 四半期報告書 招集通知 公告 IRカレンダー 株式情報 株主優待制度 配当情報"
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "forinvestors/", official + "forinvestors",
                "投資家の皆さまへ | " + company + "株式会社", {"投資家の皆さまへ", "IR ニュース"},
                "ホーム 投資家の皆さまへ for INVESTORS 投資家の皆さまへ " + financial, 20, official + "contact", official + "contact",
                "CONTACT お問い合わせ", "CONTACT お問い合わせ", redirected=True)
            if parent is None or financial not in [e["quote"] for e, s in pairs if s is parent]:
                return failed
        elif family == "department":
            financial = "最新の財務・業績関連情報、株価・株式情報、IR資料など、投資家様向け情報を掲載しています。"
            company_instruction = "勤務先名 ※ 例）" + company + "株式会社 ＊ 個人のお客様は「個人」とご記入ください。"
            desk = "問い合わせ部署：ＩＲ広報部 TEL:042-359-7830 FAX:042-359-7447"
            search = source["forms"][0]
            if (search != {"method": "get", "action": "http://" + parsed.netloc + "/search/index.html", "text": "",
                           "controls": [{"tag": "input", "type": "text", "name": "q"}, {"tag": "input", "type": "submit"}]}
                    or not text.startswith("お名前（漢字） ※ 例）理音 太郎 お名前（フリガナ） ※ 例）リオン タロウ " + company_instruction + " 所属 ")
                    or not text.endswith(" メールアドレス ※ （半角で入力してください） メールアドレス（確認） ※ （半角で入力してください） お問い合わせ内容 ※ （最大全角で1000文字）")
                    or desk not in local_quotes or source["text"].count(text + " " + desk) != 1
                    or not any(s is source and e["quote"] == company_instruction
                               and type(e.get("source_form_index")) is int and e["source_form_index"] == 1 for e, s in pairs)):
                return failed
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "ir/", official + "ir/",
                company + "株式会社｜IR・投資家情報", {"IR・投資家情報", "決算・適時開示", "IRライブラリ", "株式情報"},
                "IR・投資家情報 " + financial + " ホーム IR・投資家情報", 92, target, target,
                "WEBからのお問い合わせ", "IRに関するお問い合わせ WEBからのお問い合わせ")
            department = self.reviewed_captured_ir_parent(record, pairs, official + "inquiry/", official + "inquiry/",
                company + "株式会社｜お問い合わせ", {"その他お問い合わせ"},
                "その他お問い合わせ 上記以外のお問い合わせ、IR関連、ホームページ等 企画部 IR広報課", 79, target, target,
                "お問い合わせフォーム", "その他お問い合わせ 上記以外のお問い合わせ、IR関連、ホームページ等 企画部 IR広報課 TEL： 042-359-7830 FAX： 042-359-7447 お問い合わせフォーム")
            if parent is None or department is None or financial not in [e["quote"] for e, s in pairs if s is parent]:
                return failed
            personal = True
        elif family == "bilingual":
            audience = ("カテゴリー Category 個人投資家(Individual investor) 機関投資家(Institutional investor) アナリスト(Analyst) その他 (Other)")
            operation = "当社株主、投資家の皆様からのお問い合わせはメールによるお問い合わせに限定させていただいております。"
            if (not text.startswith("お名前 Name " + audience + " メールアドレス Email Address メールアドレス（確認） Re-enter Email Address ")
                    or not text.endswith(" ご用件タイトル Subject ご用件 Message 確認画面へ Proceed to Confirmation")
                    or any("value" in c for c in controls[1:5])
                    or not any(s is source and e["quote"] == audience and type(e.get("source_form_index")) is int
                               and e["source_form_index"] == 0 and type(e.get("form_index")) is int and e["form_index"] == 0 for e, s in pairs)):
                return failed
            parent = self.reviewed_captured_ir_parent(record, pairs, ir_origin + "inquiry/", ir_origin + "inquiry/",
                title, {"IRお問い合わせ", "ご注意事項", "株式について", "IRライブラリー"}, operation,
                70, "/inquiry01/", target,
                "同意してお問い合わせフォームへ進む Agree and Proceed to the Inquiry Form 同意してお問い合わせへ進む Agree and Proceed",
                "同意してお問い合わせフォームへ進む Agree and Proceed to the Inquiry Form 同意してお問い合わせへ進む Agree and Proceed")
            if parent is None or not any(s is parent and e["quote"].startswith(operation) for e, s in pairs):
                return failed
            personal = True
        else:
            operation = "IRの問合せ先はどちらですか 「 問い合わせフォーム 」よりお問い合わせ下さい。"
            if (not text.startswith("入力画面 入力内容の確認 送信完了 お問い合わせ 御社名 お名前 【必須】 姓 名 メールアドレス 【必須】 電話番号 お問い合わせ内容 【必須】 ")
                    or "個人情報の取扱規定 【必須】 個人情報の取扱規定に同意する" not in text):
                return failed
            parent = self.reviewed_captured_ir_parent(record, pairs, official + "ir/question.html", official + "ir/question.html",
                "よくあるご質問 │ " + company, {"よくあるご質問"},
                "HOME IR情報 よくあるご質問 よくあるご質問 " + operation, 32, "/contact.html", target, "問い合わせフォーム", operation)
            landing = self.reviewed_late_ir_capture(record, official + "ir.html", official + "ir.html")
            if (parent is None or "株主総会はいつですか 定時株主総会は例年1月下旬に開催しております。 決算期はいつですか 決算期末は10月です。" not in parent["text"]
                    or not any(s is parent and e["quote"] == "「株式会社" + company + "」へ商号変更いたしました。" for e, s in pairs)
                    or landing is None or landing.get("redirects") or landing.get("title") != "IR情報 │ " + company
                    or not {"IR情報", "IRニュース", "財務ハイライト", "株式情報"}.issubset(landing.get("headings", []))
                    or landing["text"].count("HOME IR情報 IR情報 投資家の皆様へ Investor Relations IRニュース IR News") != 1
                    or len(landing.get("links", [])) <= 40
                    or landing["links"][38] != {"url": official + "ir/question.html", "href": "/ir/question.html", "label": "よくあるご質問 Question"}
                    or landing["links"][40] != {"url": target, "href": "/contact.html", "label": "お問い合わせはこちら"}):
                return failed
        return (family, True, personal, identity)

    def reviewed_captured_ir_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        witness = self.reviewed_captured_ir_reception(record, pairs)
        return witness[1] if witness is not None and witness[0] not in {"company", "bilingual"} else None

    def reviewed_captured_ir_individual(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        witness = self.reviewed_captured_ir_reception(record, pairs)
        return bool(witness is not None and witness[1] and witness[2])

    def reviewed_captured_tse_identity(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        if record.get("identity_status") != "unverified" or record.get("identity_matches") != []:
            return False
        witness = self.reviewed_captured_ir_reception(record, pairs)
        return bool(witness is not None and witness[0] == "english" and witness[1] and witness[3])

    def reviewed_ir_six_category_opaque_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Bind this six-category questionnaire's opaque reply field and financial parent.

        The printed dot is not a required attribute. The capture supplies no
        radio values, so the complete native group and public choices are
        checked together without assigning a value to an individual radio.
        """
        if not manual_review_valid(record):
            return None
        witnesses = {}
        for _, source in pairs:
            for index, form in enumerate(source.get("forms", [])):
                if not isinstance(form, dict):
                    continue
                names = {c.get("name") for c in form.get("controls", []) if isinstance(c, dict)}
                if {"f000062563", "f000051038", "f000000576"}.issubset(names):
                    witnesses[(id(source), index)] = source
        if not witnesses:
            return None
        if len(witnesses) != 1:
            return False
        (_, index), source = next(iter(witnesses.items()))
        official = self.reviewed_late_ir_issuer_root(record)
        if official is None:
            return False
        target = official + "contact/"
        title = "お問い合わせ | Axell"
        issuer = "copyright(c) AXELL CORPORATION / 株式会社" + record.get("company_name", "")
        if (index != 0 or source.get("url") != target or source.get("requested_url") != target
                or self.reviewed_late_ir_capture(record, target, target) is not source
                or source.get("redirects") or source.get("title") != title
                or source.get("headings") != ["", "Contact お問い合わせ"]
                or len(source.get("forms", [])) != 1
                or not any(s is source and e["quote"] == issuer for e, s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "https://reg18.smp.ne.jp/regist/Reg2", [
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "input", "type": "radio", "name": "f000062563"},
            {"tag": "textarea", "name": "f000051038"},
            {"tag": "input", "type": "text", "name": "f000006140"},
            {"tag": "input", "type": "text", "name": "f000006129"},
            {"tag": "input", "type": "text", "name": "f000000581:a"},
            {"tag": "input", "type": "text", "name": "f000000581:t"},
            {"tag": "select", "name": "f000000582"},
            {"tag": "input", "type": "text", "name": "f000000583"},
            {"tag": "input", "type": "text", "name": "f000006141:a"},
            {"tag": "input", "type": "text", "name": "f000006141:e"},
            {"tag": "input", "type": "text", "name": "f000006141:n"},
            {"tag": "input", "type": "text", "name": "f000000576"},
            {"tag": "input", "type": "image"},
        ])
        category = "●お問い合わせ項目 製品について IR関係について 採用について 個人情報保護法関係 TechBlogについて その他"
        operation = ("お問い合わせ内容及び連絡先をご記入の上、送信ボタンをクリックしてください。 "
                     "ご利用のメールソフトにメールが自動で作成されますので、そのまま送信してください。")
        if (form is None or not form["text"].startswith(category + " ●お問い合わせ内容 ●お名前 ●会社名・部署 ●郵便番号 - ●住所 -- 都道府県 -- ")
                or not form["text"].endswith(" ●電話番号 - - ●メールアドレス")
                or not any(s is source and e["quote"] == category
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and ("form_index" not in e or type(e["form_index"]) is int and e["form_index"] == 0)
                           for e, s in pairs)
                or not any(s is source and e["quote"].startswith(operation)
                           and source["text"].count("Tags Contact お問い合わせ " + e["quote"] + " " + form["text"]) == 1
                           for e, s in pairs)):
            return False
        parent = self.reviewed_late_ir_capture(record, official + "ir/", official + "ir/")
        if (parent is None or parent.get("redirects") or parent.get("title") != "投資家情報 | Axell"
                or not {"IR 投資家情報", "IRニュース", "最新の決算情報 IRデータ一括ダウンロード"}.issubset(parent.get("headings", []))
                or not any(s is parent and e["quote"] == parent["title"] for e, s in pairs)):
            return False
        primary = parent["text"].split("Tags TOP > 投資家情報 IR 投資家情報 CEO Message ")
        if (len(primary) != 2 or "IRニュース 最新の決算情報 IRデータ一括ダウンロード " not in primary[1]
                or "決算短信〔日本基準〕（連結）" not in primary[1]
                or "IR資料室 - 決算短信/その他開示資料 - 株主通信 - 動画・音声配信 業績・財務データ - 業績ハイライト - 財政状況 - キャッシュ・フローの状況 - 配当状況 IRスケジュール 株式・株主情報 - 株式情報 - 株主総会 - 定款・株式取扱規則 News Business " not in primary[1]):
            return False
        links = parent.get("links", [])
        return (isinstance(links, list) and len(links) > 144
                and links[74] == {"url": target, "href": "/contact/", "label": "Contact お問い合わせ"}
                and links[144] == {"url": target, "href": "/contact/", "label": "Contact"})

    def reviewed_late_ir_issuer_root(self, record: dict) -> str | None:
        """The late reception families keep the captured official HTTPS issuer origin."""
        official = record.get("official_url")
        if not isinstance(official, str) or not url_key(official):
            return None
        parsed = urlsplit(official)
        if (parsed.scheme != "https" or parsed.path != "/" or parsed.query or parsed.fragment
                or parsed.netloc != parsed.hostname or len(identity_key(record.get("company_name", ""))) < 2):
            return None
        return official

    def reviewed_late_ir_capture(self, record: dict, url: str, requested: str) -> dict | None:
        """Read an already captured route from this issuer's SHA-guarded record references.

        The IR-window draft cites the child title, operation and complete form.
        Its separately saved financial/department routes are structural proof,
        not invented standalone quotations or permission to use arbitrary files.
        """
        matches = []
        for fetch in record.get("fetches", []):
            if (not isinstance(fetch, dict) or fetch.get("url") != requested or fetch.get("final_url") != url
                    or type(fetch.get("http_status")) is not int or fetch["http_status"] != 200
                    or not isinstance(fetch.get("snapshot"), str)
                    or not fetch["snapshot"].startswith("evidence/" + str(record.get("security_code")) + "/")):
                continue
            source = self.load_snapshot(fetch["snapshot"], record["security_code"])
            if (source is not None and self.successful(source) and source.get("submitted") is False
                    and source.get("url") == url and source.get("requested_url") == requested
                    and fetch.get("retrieved_at") == source.get("retrieved_at") and aware_time(source.get("retrieved_at"))):
                matches.append(source)
        return matches[0] if len(matches) == 1 else None

    def reviewed_ir_form_followed_by_exclusive_scope(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Only this complete question form is immediately followed by the exclusive IR assignment."""
        official = self.reviewed_late_ir_issuer_root(record)
        if official is None:
            return False
        target = official + "ir/inquiry2021"
        company = record.get("company_name", "")
        title = "お問い合わせ | 株式会社" + company + " 企業サイト | CONVANO"
        assignment = "こちらのお問い合わせフォームは、IRに関するお問い合わせ専用です。"
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != title or len(source.get("forms", [])) != 3
                or not any(s is source and e["quote"] == title for e,s in pairs)
                or not any(s is source and e["quote"] == assignment for e,s in pairs)):
            return False
        for index, ident in ((0,"js--search-input"),(1,"js--search-input--drawer")):
            search = source["forms"][index]
            if (search.get("method") != "get" or search.get("action") != official or search.get("text") != ""
                    or search.get("controls") != [{"tag":"input","type":"search","name":"s","placeholder":"検索","id":ident}]):
                return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 2, "post", "/ir/inquiry2021#wpcf7-f4708-o2", [{'tag': 'input', 'type': 'text', 'name': 'your-name'}, {'tag': 'input', 'type': 'text', 'name': 'your-kana'}, {'tag': 'input', 'type': 'text', 'name': 'your-company'}, {'tag': 'input', 'type': 'text', 'name': 'your-department'}, {'tag': 'input', 'type': 'text', 'name': 'your-position'}, {'tag': 'input', 'type': 'email', 'name': 'your-email'}, {'tag': 'input', 'type': 'tel', 'name': 'your-tel'}, {'tag': 'input', 'type': 'text', 'name': 'your-zip'}, {'tag': 'textarea', 'name': 'your-address'}, {'tag': 'textarea', 'name': 'your-message'}, {'tag': 'input', 'type': 'checkbox', 'name': 'acceptance'}, {'tag': 'input', 'type': 'submit'}])
        if (form is None or not form["text"].startswith("* の付いたものは必須事項です。 お名前 * （全角漢字：姓と名の間にスペース） ")
                or "ご住所 （全角） お問い合わせ内容 * プライバシーポリシー に同意します リセット" not in form["text"]
                or source["text"].count(form["text"] + " " + assignment) != 1):
            return False
        issuer = "株式会社" + company + " 証券コード：" + str(record.get("security_code")) + "｜東証グロース市場"
        for e,parent in pairs:
            links = parent.get("links", [])
            if (self.successful(parent) and parent.get("submitted") is False and parent.get("url") == official[:-1] + "/ir"
                    and parent.get("requested_url") == parent.get("url") and not parent.get("redirects")
                    and parent.get("title") == "IR情報 | 株式会社" + company + " 企業サイト | CONVANO"
                    and {"IR情報","業績・財務情報","IRライブラリ","株式情報"}.issubset(parent.get("headings", []))
                    and any(p is parent and pe["quote"] == issuer for pe,p in pairs)
                    and e["quote"] == "お問い合わせ" and type(e.get("source_link_index")) is int and e["source_link_index"] == 71
                    and e.get("source_link_url") == target and e.get("discovery_link_label") == "お問い合わせ"
                    and len(links) > 71 and links[71] == {"url":target,"href":target,"label":"お問い合わせ"}
                    and aware_time(parent.get("retrieved_at"))):
                return True
        return False

    def reviewed_ir_window_native_question(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Bind the cited IR-window questionnaire and its separately captured financial routes."""
        official = self.reviewed_late_ir_issuer_root(record)
        if official is None:
            return False
        target = official + "contact/ir/"
        company = record.get("company_name", "")
        title = "IR窓口 | 株式会社" + company
        operation = "お問い合わせ IR窓口 プライバシーポリシー に同意の上、お問い合わせフォームにご入力くださいますようお願いいたします。"
        delay = "お問い合わせの内容によっては、返信に時間がかかる場合や、回答を差し控えさせていただく場合もございます。 あらかじめご了承ください。"
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != title or source.get("headings") != ["IR窓口"] or len(source.get("forms", [])) != 1
                or not any(s is source and e["quote"] == title for e,s in pairs)
                or not any(s is source and e["quote"] == operation for e,s in pairs)):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/contact/ir/#wpcf7-f4019-o1", [{'tag': 'input', 'type': 'text', 'name': 'your-company'}, {'tag': 'input', 'type': 'text', 'name': 'your-department'}, {'tag': 'input', 'type': 'text', 'name': 'your-name'}, {'tag': 'input', 'type': 'text', 'name': 'your-kana'}, {'tag': 'input', 'type': 'email', 'name': 'your-email'}, {'tag': 'input', 'type': 'text', 'name': 'tel-1'}, {'tag': 'input', 'type': 'text', 'name': 'tel-2'}, {'tag': 'input', 'type': 'text', 'name': 'tel-3'}, {'tag': 'textarea', 'name': 'your-message'}, {'tag': 'input', 'type': 'checkbox', 'id': 'js_check'}, {'tag': 'input', 'type': 'submit'}])
        if (form is None or form["text"] != "会社名 部署名 お名前 フリガナ メールアドレス 電話番号 － － お問い合わせ内容 プライバシーポリシー に同意いただける場合は「同意する」にチェックを入れてください。 同意する 編集する 確認画面へ"
                or source["text"].count(operation + " " + delay + " " + form["text"]) != 1):
            return False
        financial = self.reviewed_late_ir_capture(record, official + "ir/stock_information/", official + "ir/stock_information/")
        department = self.reviewed_late_ir_capture(record, official + "contact/", official + "contact")
        if financial is None or department is None:
            return False
        redirects = department.get("redirects", [])
        if (financial.get("title") != "株式情報・株主総会 | 株式会社" + company or financial.get("redirects")
                or not {"株式情報","株主還元","株価","株主総会","IRに関するお問い合わせ"}.issubset(financial.get("headings", []))
                or "株式の状況、株主メモを" not in financial["text"] or "株主総会 招集ご通知、決議ご通知を" not in financial["text"]
                or "IRに関するお問い合わせ IR窓口はこちら" not in financial["text"]
                or len(financial.get("links", [])) <= 53 or financial["links"][53] != {"url":target,"href":target,"label":"IR窓口はこちら"}
                or department.get("title") != "お問い合わせ | 株式会社" + company
                or not {"お客様窓口","IR窓口","採用窓口","報道関係者・その他の窓口","GHG Inventory窓口"}.issubset(department.get("headings", []))
                or "メールで問い合わせ IR窓口 045-476-5711 メールで問い合わせ 採用窓口" not in department["text"]
                or len(department.get("links", [])) <= 75
                or department["links"][39] != {"url":target,"href":"./ir/","label":"メールで問い合わせ"}
                or department["links"][75] != {"url":target,"href":target,"label":"IR窓口"}
                or len(redirects) != 1 or redirects[0].get("requested_url") != official + "contact"
                or redirects[0].get("url") != official + "contact" or type(redirects[0].get("http_status")) is not int
                or redirects[0]["http_status"] != 301 or redirects[0].get("redirect_target") != official + "contact/"
                or not aware_time(redirects[0].get("retrieved_at"))):
            return False
        return True

    def reviewed_ir_cform_opaque_reply(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The complete financial IR CForm labels its opaque text reply and textarea explicitly."""
        official = self.reviewed_late_ir_issuer_root(record)
        if official != "https://www.epson.jp/" or identity_key(record.get("company_name", "")) != "セイコーエプソン":
            return False
        target = "https://cform.epson.jp/form5/pub/e040/3009009007012109727"
        title = "IR（投資家情報）に関するお問い合わせ"
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or source.get("title") != title or len(source.get("forms", [])) != 1):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "POST", "/form5/pub/e040/3009009007012109727", [{'tag': 'input', 'type': 'text', 'name': 'c_q1', 'id': 'c_q1'}, {'tag': 'input', 'type': 'text', 'name': 'c_q1_confirm', 'id': 'c_q1_confirm'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_first', 'id': 'c_q3_first'}, {'tag': 'input', 'type': 'text', 'name': 'c_q3_second', 'id': 'c_q3_second'}, {'tag': 'input', 'type': 'text', 'name': 'c_q4_first', 'id': 'c_q4_first'}, {'tag': 'input', 'type': 'text', 'name': 'c_q4_second', 'id': 'c_q4_second'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_left', 'id': 'c_q5_left'}, {'tag': 'input', 'type': 'text', 'name': 'c_q5_right', 'id': 'c_q5_right'}, {'tag': 'input', 'type': 'submit', 'name': 'searchAddr_c_q5', 'id': 'searchAddr_c_q5'}, {'tag': 'select', 'name': 'c_q6', 'id': 'c_q6'}, {'tag': 'input', 'type': 'text', 'name': 'c_q7', 'id': 'c_q7'}, {'tag': 'input', 'type': 'text', 'name': 'c_q8', 'id': 'c_q8'}, {'tag': 'input', 'type': 'text', 'name': 'c_q10', 'id': 'c_q10'}, {'tag': 'input', 'type': 'text', 'name': 'c_q9', 'id': 'c_q9'}, {'tag': 'input', 'type': 'text', 'name': 'c_q14_areacode', 'id': 'c_q14_areacode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q14_citycode', 'id': 'c_q14_citycode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q14_subscribercode', 'id': 'c_q14_subscribercode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q15_areacode', 'id': 'c_q15_areacode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q15_citycode', 'id': 'c_q15_citycode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q15_subscribercode', 'id': 'c_q15_subscribercode'}, {'tag': 'input', 'type': 'text', 'name': 'c_q11', 'id': 'c_q11'}, {'tag': 'textarea', 'name': 'c_q16', 'id': 'c_q16'}, {'tag': 'input', 'type': 'submit', 'name': 'wcf5start', 'id': 'wcf5start'}])
        reply = "1. Eメールアドレス [半角英数字] [必須] ※確認用のため再入力をお願いします。"
        question = "13. お問い合わせ内容を記載ください。 （最大全角1000文字） [必須]"
        company = "12. 会社名・団体名 [全角] ※法人の方は会社名のご入力をお願いします。"
        if (form is None or not form["text"].startswith(title + " 注意事項 製品に関するお問い合わせにつきましては、 お問い合わせページ をご確認いただき、各製品窓口へお問い合わせください。 ")
                or "1.お客様に関する情報 " + reply + " 2. お名前 [全角] [必須]" not in form["text"]
                or company + " 2.ご相談・お問い合わせ内容 " + question not in form["text"]
                or not all(any(s is source and e["quote"] == text and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e,s in pairs) for text in (reply,question,company))
                or not form["text"].endswith("上記、「注意事項」に記載の内容をご確認いただき、同意のうえ送信してください。 送信するには、ブラウザのcookie設定を有効にしてください。")):
            return False
        for e,parent in pairs:
            links = parent.get("links", [])
            if (self.successful(parent) and parent.get("submitted") is False and parent.get("url") == official + "contact/"
                    and parent.get("requested_url") == parent.get("url") and not parent.get("redirects")
                    and parent.get("title") == "お問い合わせ｜エプソン" and "各サイトに関するお問い合わせ" in parent.get("headings", [])
                    and e["quote"] == "IR（投資家情報）について" and type(e.get("source_link_index")) is int and e["source_link_index"] == 31
                    and e.get("source_link_url") == target and len(links) > 31
                    and links[31] == {"url":target,"href":target,"label":"IR（投資家情報）について 新規ウィンドウで開く"}
                    and aware_time(parent.get("retrieved_at"))
                    and any(self.successful(root) and root.get("submitted") is False and root.get("url") == official
                            and root.get("requested_url") == official and identity["quote"] == "エプソン ホームページ" for identity,root in pairs)):
                return True
        return False

    def reviewed_ir_personal_and_corporate_name_fields(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """The company/department corporate labels and shared personal-name label belong to this IR form."""
        official = self.reviewed_late_ir_issuer_root(record)
        if official is None:
            return False
        target = "https://reg31.smp.ne.jp/regist/is?SMPFORM=nish-lereth-ec923ba2f68d7c2e5142015105491bd1&type=4"
        company = identity_key(record.get("company_name", ""))
        personal = "御社名（法人様） 部署名（法人様） お名前（個人様・法人様）"
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or len(source.get("forms", [])) != 1 or company not in identity_key(source.get("title", ""))):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/regist/Reg2", [{'tag': 'select', 'name': 'type'}, {'tag': 'input', 'type': 'text', 'name': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'department'}, {'tag': 'input', 'type': 'text', 'name': 'name'}, {'tag': 'input', 'type': 'text', 'name': 'zipCode'}, {'tag': 'select', 'name': 'pref'}, {'tag': 'input', 'type': 'text', 'name': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'address2'}, {'tag': 'input', 'type': 'text', 'name': 'phone'}, {'tag': 'input', 'type': 'email', 'name': 'email'}, {'tag': 'textarea', 'name': 'inquiry'}, {'tag': 'input', 'type': 'checkbox', 'name': 'doui', 'id': 'agree'}])
        purpose = "お問い合わせ種別 - お問い合わせ内容を選択してください - ゴミ全般に関するお問い合わせ 採用に関するお問い合わせ 請求書に関するお問い合わせ IRに関するお問い合わせ その他のお問い合わせ"
        if (form is None or not form["text"].startswith(purpose + " " + personal + " 住所 〒 都道府県")
                or not any(s is source and e["quote"] == personal for e,s in pairs)
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)):
            return False
        return any(self.successful(parent) and parent.get("submitted") is False and parent.get("url") == official + "ir/"
                   and parent.get("requested_url") == parent.get("url") and not parent.get("redirects")
                   and company in identity_key(parent.get("title", ""))
                   and {"IRニュース","IRライブラリー","株式について"}.issubset(parent.get("headings", []))
                   and e["quote"] == "IRに関する お問い合わせ" and type(e.get("source_link_index")) is int and e["source_link_index"] == 17
                   and e.get("source_link_url") == target and e.get("discovery_link_label") == "IRに関する お問い合わせ"
                   and len(parent.get("links", [])) > 17 and parent["links"][17] == {"url":target,"href":target,"label":"IRに関する お問い合わせ"}
                   and aware_time(parent.get("retrieved_at")) for e,parent in pairs)

    def reviewed_ir_affiliation_including_individual(self, record: dict, source: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """An affiliation field expressly includes individuals on the same financial IR questionnaire."""
        official = self.reviewed_late_ir_issuer_root(record)
        if official is None:
            return False
        target = "https://reg18.smp.ne.jp/regist/is?SMPFORM=neri-relfm-55d39a824dde54a6f9b5923e64dab558&typesm=3"
        company = identity_key(record.get("company_name", ""))
        personal = "所属企業・団体名・個人 必須 例 : " + record.get("company_name", "") + "株式会社"
        if (source.get("url") != target or source.get("requested_url") != target or source.get("redirects")
                or len(source.get("forms", [])) != 1 or identity_key(source.get("title", "").split(" | ")[-1]) != company):
            return False
        form = self.reviewed_finite_form_witness(record, source, pairs, 0, "post", "/regist/Reg2", [{'tag': 'input', 'type': 'radio', 'name': 'typesm', 'id': 'typesm_01'}, {'tag': 'input', 'type': 'radio', 'name': 'typesm', 'id': 'typesm_03'}, {'tag': 'input', 'type': 'text', 'name': 'name'}, {'tag': 'input', 'type': 'text', 'name': 'furigana'}, {'tag': 'input', 'type': 'text', 'name': 'company'}, {'tag': 'input', 'type': 'text', 'name': 'department'}, {'tag': 'input', 'type': 'text', 'name': 'hpUrl'}, {'tag': 'input', 'type': 'text', 'name': 'zipCode'}, {'tag': 'input', 'type': 'text', 'name': 'address'}, {'tag': 'input', 'type': 'text', 'name': 'phoneNum'}, {'tag': 'input', 'type': 'text', 'name': 'fax_Num'}, {'tag': 'input', 'type': 'text', 'name': 'email'}, {'tag': 'input', 'type': 'text', 'name': 'email:cf'}, {'tag': 'textarea', 'name': 'inquiry'}, {'tag': 'input', 'type': 'checkbox', 'name': 'doui', 'id': 'agree_01'}])
        if (form is None or not form["text"].startswith("お問い合わせの内容 必須 採用情報について 投資家情報、サステナビリティ、その他について お名前 必須 ")
                or personal + " 部署名" not in form["text"]
                or not any(s is source and e["quote"] == personal and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e,s in pairs)
                or not self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(target), target_form=form)):
            return False
        faq = False
        department = False
        for e,parent in pairs:
            if (not self.successful(parent) or parent.get("submitted") is not False or parent.get("requested_url") != parent.get("url")
                    or parent.get("redirects") or not aware_time(parent.get("retrieved_at"))):
                continue
            links = parent.get("links", [])
            if (parent.get("url") == official + "ir/faq.html" and company in identity_key(parent.get("title", ""))
                    and {"決算・財務に関する質問","株式に関する質問","その他の質問"}.issubset(parent.get("headings", []))
                    and "Q 証券コードは何ですか？ A " + str(record.get("security_code")) + "です。" in e["quote"]
                    and e["quote"].endswith("その他の質問 Q 意見、問い合わせの窓口はどこにありますか？ A こちら までお問い合わせください。")
                    and type(e.get("source_link_index")) is int and e["source_link_index"] == 57 and len(links) > 57
                    and links[57] == {"url":target,"href":target,"label":"こちら"}
                    and e.get("source_link_url") == e.get("source_link_href") == target and e.get("source_link_label") == "こちら"):
                faq = True
            if (parent.get("url") == official + "inquiry/" and e["quote"] == "経営管理本部 企画・広報グループ 投資家情報・サステナビリティ・その他について お問い合わせ"
                    and type(e.get("source_link_index")) is int and e["source_link_index"] == 62 and len(links) > 62
                    and links[62] == {"url":target,"href":target,"label":"お問い合わせ"}
                    and e.get("source_link_url") == e.get("source_link_href") == target and e.get("source_link_label") == "お問い合わせ"):
                department = True
        return faq and department

    def reviewed_late_native_ir_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool | None:
        """Dispatch only three actual late IR reception families; generic form binding stays intact."""
        if not manual_review_valid(record):
            return None
        handlers = {}
        for _,source in pairs:
            for index,form in enumerate(source.get("forms", [])):
                if not isinstance(form, dict):
                    continue
                text = form.get("text", "")
                names = {c.get("name") for c in form.get("controls", []) if isinstance(c, dict)}
                handler = None
                if (text.startswith("* の付いたものは必須事項です。 お名前 * （全角漢字：姓と名の間にスペース） ")
                        and {"your-address","your-message","your-email"}.issubset(names)):
                    handler = self.reviewed_ir_form_followed_by_exclusive_scope
                elif (str(source.get("title", "")).startswith("IR窓口 | ") and {"your-message","your-email","tel-1"}.issubset(names)):
                    handler = self.reviewed_ir_window_native_question
                elif source.get("title") == "IR（投資家情報）に関するお問い合わせ" and {"c_q1","c_q1_confirm","c_q16"}.issubset(names):
                    handler = self.reviewed_ir_cform_opaque_reply
                if handler is not None:
                    handlers[(id(source),index)] = (source,handler)
        if not handlers:
            return None
        if len(handlers) != 1:
            return False
        source,handler = next(iter(handlers.values()))
        return handler(record,source,pairs)

    def reviewed_late_ir_individual(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Two personal-label variants require the complete, already-bound financial IR form."""
        sources = {id(source):source for _,source in pairs}
        return any(self.reviewed_ir_personal_and_corporate_name_fields(record,source,pairs)
                   or self.reviewed_ir_affiliation_including_individual(record,source,pairs) for source in sources.values())

    def reviewed_finite_ir_individual(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Personal eligibility is separate from question-form attribution."""
        sources = {id(source):source for _,source in pairs}
        return any(self.reviewed_ir_personal_shareholder_checkboxes(record, source, pairs)
                   or self.reviewed_ir_person_standing_company_entry(record, source, pairs)
                   or self.reviewed_ir_company_person_placeholder(record, source, pairs)
                   for source in sources.values())


    def reviewed_representative_ir_email_reference(self, record: dict, evidence: dict, source: dict,
                                                   pairs: list[tuple[dict, dict]], email: str) -> bool:
        """Resolve one cited IR instruction's explicit representative-mail reference.

        The complete reception block names recruitment and overseas mailboxes
        separately. Its IR/earnings instruction points to the representative
        mailbox below them; ordinary proximity, navigation and product forms
        cannot supply this attribution.
        """
        official_url = record.get("official_url")
        if not url_key(official_url) or not isinstance(email, str):
            return False
        official = urlsplit(official_url)
        if (official.scheme != "https" or official.path != "/" or official.query or official.fragment
                or not official.hostname or official.netloc != official.hostname):
            return False
        domain = official.hostname.removeprefix("www.")
        target = official_url + "inquiry"
        if (email != "soumu@" + domain or not self.successful(source)
                or record.get("contact_url") != target or source.get("url") != target
                or source.get("requested_url") != target or source.get("submitted") is not False
                or source.get("redirects") or source.get("forms") != [] or source.get("title") != "お問い合わせ"):
            return False
        block = (
            "IR情報等・お手続きに関するお問い合わせ IR情報全般・決算に関するご質問 "
            "代表電話または代表メールにてご相談ください。 "
            "株式手続き（住所変更・名義変更・配当金等） "
            "お取引の証券会社、または三井住友信託銀行へご相談ください。 "
            "採用に関するお問い合わせ 電話： （088）845－5511 メール： saiyou@" + domain + " "
            "海外からのお問い合わせ TEL： +81-88-845-5511 FAX： +81-88-845-5211 E-mail： kaigai@" + domain + " "
            "その他 代表電話： （088）845－5511 代表FAX： （088）845－5211 代表メール： " + email
        )
        label = "代表メール： " + email
        text = source["text"]
        if (evidence.get("role") != "ir_email_reference" or evidence.get("quote") != block
                or evidence.get("url") != target or evidence.get("retrieved_at") != source.get("retrieved_at")
                or not aware_time(source.get("retrieved_at")) or text.count(block) != 1
                or text.count("製品のご相談 フォームよりご相談ください。 " + block + " 本社所在地：") != 1
                or text.count(email) != 1 or text.count("代表メール：") != 1
                or evidence.get("source_link_url") != "mailto:" + email
                or evidence.get("discovery_link_label") != label
                or type(evidence.get("source_link_index")) is not int or evidence["source_link_index"] != 16):
            return False
        links = source.get("links")
        company = record.get("company_name")
        if not isinstance(links, list) or len(links) <= 16 or not isinstance(company, str) or not company:
            return False
        logo = {"url": official_url, "href": "/", "label": company + "のロゴ"}
        if links[0] != logo:
            return False
        public_mail = [(12, "saiyou@" + domain, "メール： "),
                       (14, "kaigai@" + domain, "E-mail： "), (16, email, "代表メール： ")]
        if [i for i, link in enumerate(links) if isinstance(link, dict)
            and isinstance(link.get("url"), str) and link["url"].lower().startswith("mailto:")] != [12, 14, 16]:
            return False
        for index, address, prefix in public_mail:
            if links[index] != {"url": "mailto:" + address, "href": "mailto:" + address, "label": prefix + address}:
                return False
        code = record.get("security_code")
        if not isinstance(code, str) or not code:
            return False
        identity = "証券コード " + code
        for issuer_evidence, issuer_source in pairs:
            if (issuer_evidence.get("role") != "issuer_identity" or issuer_evidence.get("quote") != identity
                    or not self.successful(issuer_source) or issuer_source.get("submitted") is not False
                    or issuer_source.get("url") != official_url + "ir/stockinformation"
                    or issuer_source.get("requested_url") != issuer_source.get("url")
                    or issuer_source.get("redirects") or issuer_source.get("forms") != []
                    or issuer_source.get("title") != "IR情報 - 株式・株主情報"
                    or issuer_evidence.get("url") != issuer_source.get("url")
                    or issuer_evidence.get("retrieved_at") != issuer_source.get("retrieved_at")
                    or not aware_time(issuer_source.get("retrieved_at"))):
                continue
            body = issuer_source["text"]
            stock = "株式の状況 発行可能株式総数 "
            returns = "株主還元・配当方針 当社は、株主の皆様に対する利益還元"
            procedure = "株式事務手続き 事業年度 "
            code_row = "株主名簿管理人 三井住友信託銀行株式会社 " + identity
            issuer_links = issuer_source.get("links")
            if (body.count(identity) == 1 and all(body.count(part) == 1 for part in (stock, returns, procedure, code_row))
                    and body.index(stock) < body.index(returns) < body.index(procedure) < body.index(code_row)
                    and isinstance(issuer_links, list) and len(issuer_links) > 5 and issuer_links[0] == logo
                    and issuer_links[5] == {"url": target, "href": "/inquiry", "label": "お問い合わせ"}):
                return True
        return False


    def reviewed_public_email(self, record: dict, pairs: list[tuple[dict, dict]], email: str) -> bool:
        """Verify an explicitly assigned cross-page or policy-scoped IR mail
        route after recorded manual review. General email presence is insufficient.
        """
        if not manual_review_valid(record) or not isinstance(email, str):
            return False
        for evidence, source in pairs:
            if not self.successful(source):
                continue
            if self.reviewed_representative_ir_email_reference(record, evidence, source, pairs, email):
                return True
            quote = evidence["quote"]
            mail_links = [link for link in source.get("links", []) if isinstance(link, dict)
                          and str(link.get("url", "")).lower().startswith("mailto:")
                          and str(link["url"])[7:].split("?", 1)[0].lower() == email.lower()]
            # A business-hours label inside this fully cited IR reception
            # block is not a sales purpose. Recover only the exact external
            # issuer-bound IR form, public address and captured mailto.
            official_url = record.get("official_url")
            official_host = urlsplit(official_url).hostname if url_key(official_url) else None
            ir_heading = "IRに関するご質問（株主・投資家の方）"
            reception = (ir_heading + " Contact一覧ページへ Contact一覧ページへ "
                         "下記フォームより必要事項をご記入・ご選択の上、 お問い合わせください。 "
                         "担当より改めてご連絡させていただきます。 営業時間 平日 E-mail : " + email)
            if (official_host and email == "ir@" + official_host.removeprefix("www.")
                    and record.get("contact_url") == source.get("url") and quote == reception
                    and source.get("text", "").count(reception) == 1
                    and evidence.get("source_link_url") == "mailto:" + email
                    and len(mail_links) == 1 and mail_links[0].get("href") == "mailto:" + email and mail_links[0].get("label") == email
                    and any(self.reviewed_external_ir_attribute_form(source, form, pairs, official_host)
                            and source.get("text", "").count(reception + " 1 Input 2 Complete 「 ※ 」は必須項目です。 " + form.get("text", "")) == 1
                            for form in source.get("forms", []))):
                return True
            # Some issuers insert visible spaces immediately around @ while
            # preserving the actual mailto. Do not rewrite the original quote
            # or infer arbitrary obfuscations. Require one exact captured
            # public label, the explicitly cited matching mailto and the full
            # same-URL IR assignment sentence; generic Mail aliases add no
            # purpose and never authorize a different address.
            if (url_key(record.get("contact_url")) in {url_key(source.get("url")), url_key(source.get("requested_url"))}
                    and "@" in email):
                local, domain = email.rsplit("@", 1)
                if (local.lower() in {"example", "sample", "xxxx", "xxxxx"}
                        or domain.lower() in {"example.com", "example.org", "example.jp"}):
                    continue
                visible_address = re.compile(re.escape(local) + r"\s*@\s*" + re.escape(domain), re.I)
                for link in mail_links:
                    label = link.get("label", "")
                    if (not isinstance(label, str) or not visible_address.fullmatch(label)
                            or label == email or label not in quote or evidence.get("source_link_url") != link.get("url")):
                        continue
                    assignment = re.fullmatch(
                        r"(?:IR|ＩＲ)情報に関するお問い合わせは(?P<office>[^。]{0,80})" + re.escape(label) +
                        r"\s*までご連絡ください[。.]", quote.strip(), re.I
                    )
                    if (assignment and not OTHER_CONTACT.search(assignment["office"])
                            and not re.search(r"入力例|記入例|例\s*[:：]|example\s*[:：]", assignment["office"], re.I)
                            and sum(l.get("label") == label and l.get("url") == link.get("url") for l in mail_links) == 1):
                        return True
            if len(mail_links) == 1 and evidence.get("source_link_url") == mail_links[0].get("url"):
                # A public mail anchor's decorative leading # is absent from
                # the visible page text. Retain the original quote; only the
                # reviewed, explicitly cited exact mailto and exact IR body
                # label can remove this ONE decoration. General/privacy mail
                # labels and an IR word elsewhere remain insufficient.
                decorated = re.fullmatch(r"#\s+(.+)", str(mail_links[0].get("label", "")))
                if (decorated and quote.strip() == decorated[1]
                        and source["text"].count(decorated[1]) == 1
                        and IR_CONTACT.search(decorated[1]) and not OTHER_CONTACT.search(decorated[1])):
                    return True
            address_cited = email in quote or any(isinstance(link.get("label"), str)
                                                 and link["label"] and link["label"] in quote for link in mail_links)
            if not address_cited:
                continue
            if (url_key(record.get("contact_url")) is not None
                    and url_key(record.get("contact_url")) in {url_key(source.get("url")), url_key(source.get("requested_url"))}
                    and (reviewed_ir_consent_email_section(evidence, source, email)
                         or reviewed_sole_investor_email(evidence, source, email)
                         or reviewed_financial_stock_email(evidence, source, email, [e for e, s in pairs if s is source]))):
                return True
            # A corporate contact can explicitly serve IR alongside press,
            # recruitment and privacy inquiries. This is a shared IR route,
            # not a privacy mailbox inferred from an unrelated IR menu. Keep
            # the consecutive purpose and fallback instructions in one quote
            # at the claimed URL; a navigation word or a different mailbox
            # cannot supply this exact assignment.
            corporate_fallback = re.search(
                r"の(?P<topics>(?:広報|IR|ＩＲ|採用|個人情報)(?:[・、]\s*(?:広報|IR|ＩＲ|採用|個人情報))*)"
                r"等?に関するお問い合わせは下記よりご連絡ください[。.]\s*"
                r"フォームからのご連絡が難しい場合は[、,]\s*" + re.escape(email) +
                r"までお問い合わせ内容をお送りください[。.]", quote, re.I
            )
            safe_address = (re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
                            and email.split("@", 1)[0].lower() not in {"example", "sample", "xxxx", "xxxxx"}
                            and email.split("@", 1)[1].lower() not in {"example.com", "example.org", "example.jp"})
            if (corporate_fallback and safe_address
                    and any(topic.upper() in {"IR", "ＩＲ"} for topic in re.split(r"[・、]\s*", corporate_fallback["topics"]))
                    and url_key(record.get("contact_url")) is not None
                    and url_key(record.get("contact_url")) in {url_key(source.get("url")), url_key(source.get("requested_url"))}
                    and not re.search(r"入力例|記入例|例\s*[:：]|example\s*[:：]", quote[max(0, corporate_fallback.start() - 100):corporate_fallback.start()], re.I)):
                return True
            if reviewed_ordered_mailto(evidence, source, email):
                return True
            targets = {url_key(source.get("url")), url_key(source.get("requested_url"))}
            explicit_parent = any(self.successful(parent) and self.quoted_ir_direction(parent_evidence, parent, targets)
                                  for parent_evidence, parent in pairs)
            if explicit_parent and not OTHER_CONTACT.search(quote):
                return True
            # GNI publishes IR answers instead of sending individual replies.
            # Its sole public mailto contact belongs to the SAME quoted policy
            # page. A policy from another page cannot confer this attribution.
            all_mail_links = [link for link in source.get("links", []) if isinstance(link, dict)
                              and str(link.get("url", "")).lower().startswith("mailto:")]
            same_page_policy = any(s is source and NO_REPLY.search(e["quote"]) and IR_MARKER.search(e["quote"])
                                   for e, s in pairs)
            if same_page_policy and mail_links and len(all_mail_links) == 1 and not OTHER_CONTACT.search(quote):
                return True
            # Pietro's IR inquiry page assigns the contact block below its
            # introductory instruction. Require that instruction to be cited,
            # the actual sole mailto target, and no different contact purpose
            # between the assignment and address. IR navigation alone fails.
            if (IR_MARKER.search(source.get("title", "")) and mail_links and len(all_mail_links) == 1
                    and email in quote and not OTHER_CONTACT.search(quote)):
                for scope_evidence, scope_source in pairs:
                    if scope_source is not source:
                        continue
                    assignment = re.search(r"(?:当社の)?(?:IR|ＩＲ)に関するお問い合わせはこちらからお願いいたします", scope_evidence["quote"], re.I)
                    if assignment:
                        text = source["text"]
                        start = text.find(assignment[0])
                        end = text.find(email, start + len(assignment[0]))
                        if start >= 0 and end >= 0 and not OTHER_CONTACT.search(text[start + len(assignment[0]):end]):
                            return True
            # House Foods explicitly calls the adjacent address the dedicated
            # earnings-announcement inquiry mailbox. The financial words in
            # another heading, or a phone-only notice, confer no attribution.
            for occurrence in re.finditer(re.escape(email), quote):
                prefix = quote[max(0, occurrence.start() - 35):occurrence.start()]
                if re.search(r"(?:入力例|記入例|例\s*[:：]|example\s*[:：])\s*$", prefix, re.I):
                    continue
                if re.match(r"\s*[※＊*]?\s*決算発表に関わる業績についてのお問い合わせ専用メールアドレスです", quote[occurrence.end():]):
                    return True
            # A captured sentence assigns IR inquiries to the contact block
            # below it. An explicit instruction that recruitment uses another
            # page is an exclusion, not the purpose of the following address.
            direction = re.search(r"(?:IR|ＩＲ)[^。]{0,100}お問い合わせ[^。]{0,90}以下[^。]{0,60}ご連絡先[^。]{0,60}お願", quote, re.I)
            if direction and email in quote:
                context = quote[direction.end():quote.index(email)]
                context = re.sub(r"なお、採用に関するお問い合わせは、\s*採用情報のページ\s*をご覧ください。", "", context)
                if not OTHER_CONTACT.search(context):
                    return True
        return False

    def reviewed_individual_email_access(self, record: dict, pairs: list[tuple[dict, dict]], *, email_supported: bool) -> bool:
        """Bind a personal-IR directory row to its exact public mailto.

        The saved purpose heading, immediately following department heading,
        and readable email must form the entire cited row at the claimed URL.
        Another row's institutional/partner address cannot inherit the personal
        audience. This recorded-review path requires existing IR attribution;
        an ordinary contact email or a search form never supplies it.
        """
        target = url_key(record.get("contact_url"))
        emails = record.get("public_ir_emails", [])
        if (not manual_review_valid(record) or not email_supported or target is None
                or "email" not in record.get("channels", []) or not emails):
            return False
        allowed_topics = {"事業全般", "個人情報", "株主総会"}
        personal_topic = re.compile(r"(?:IR|ＩＲ)関連[（(]\s*個人投資家\s*[）)]\Z", re.I)
        matched = set()
        for evidence, source in pairs:
            if (not self.successful(source)
                    or target not in {url_key(source.get("url")), url_key(source.get("requested_url"))}):
                continue
            if (len(emails) == 1 and reviewed_personal_ir_email_signature(
                source, [e["quote"] for e, s in pairs if s is source], emails[0]
            )):
                return True
            headings = source.get("headings", [])
            for i, heading in enumerate(headings[:-1]):
                if not isinstance(heading, str):
                    continue
                topics = [topic.strip() for topic in re.split(r"[、,]", heading)]
                if (not any(personal_topic.fullmatch(topic) for topic in topics)
                        or not all(topic in allowed_topics or personal_topic.fullmatch(topic) for topic in topics)):
                    continue
                department = headings[i + 1]
                if (not isinstance(department, str) or not department.strip()
                        or not re.search(r"(?:部|室|担当)$", department)):
                    continue
                for address in emails:
                    if not isinstance(address, str):
                        continue
                    row = heading + " " + department + " " + address
                    if evidence["quote"].strip() != row or source.get("text", "").count(row) != 1:
                        continue
                    href = evidence.get("source_link_url")
                    if not isinstance(href, str) or not href.lower().startswith("mailto:") or href[7:].split("?", 1)[0] != address:
                        continue
                    exact_links = [link for link in source.get("links", []) if isinstance(link, dict)
                                   and link.get("url") == href and link.get("label") == address]
                    if len(exact_links) == 1:
                        matched.add(address)
        return bool(matched) and matched == set(emails)

    def reviewed_individual_form_access(self, record: dict, pairs: list[tuple[dict, dict]], seed: dict | None) -> bool:
        """Tie a reviewed individual audience to the claimed, actual IR form.

        A title on a different page, an uncited audience, or a generic footer
        link cannot give the selected contact form individual access.
        """
        if not manual_review_valid(record):
            return False
        if self.reviewed_ir_organization_personal_instruction(record, pairs):
            return True
        if self.reviewed_ir_personal_and_institutional_routes(record, pairs):
            return True
        if self.reviewed_ir_public_investment_type(record, pairs):
            return True
        if self.reviewed_ir_native_customer_and_company_instruction(record, pairs):
            return True
        if self.reviewed_ir_company_or_occupation(record, pairs) or self.reviewed_ir_investor_star_company(record, pairs):
            return True
        if self.reviewed_ir_shareholder_intent_audience(record, pairs) or self.reviewed_ir_personal_and_recruitment_choice(record, pairs):
            return True
        if self.reviewed_ir_civil_and_stock_audience(record, pairs):
            return True
        if self.reviewed_ir_affiliation_name(record, pairs) or self.reviewed_ir_affiliation_attribute(record, pairs):
            return True
        if self.reviewed_ir_region_company_placeholder(record, pairs):
            return True
        if self.reviewed_captured_ir_individual(record, pairs):
            return True
        if self.reviewed_finite_ir_individual(record, pairs):
            return True
        if self.reviewed_late_ir_individual(record, pairs):
            return True
        finite_official = seed.get("official_url") if isinstance(seed, dict) else record.get("official_url")
        if any(record.get("contact_url") == source.get("url") and self.successful(source)
               and any(self.reviewed_ir_opaque_fields_after_policy(source, form, pairs, urlsplit(str(finite_official)).hostname)
                       for form in source.get("forms", [])) for _, source in pairs):
            return True
        target = url_key(record.get("contact_url"))
        if target is None or not self.has_form_binding(pairs, None, reviewed=True, target_url=target):
            return False
        official_url = seed.get("official_url") if isinstance(seed, dict) else record.get("official_url")
        official_host = urlsplit(official_url).hostname if url_key(official_url) else None
        personal_title = re.compile(r"[（(]\s*個人(?:のお客様|投資家|の方)\s*[）)]|個人(?:のお客様|投資家|の方)(?:専用|向け)")
        audience = r"(?:機関投資家[、,・\s]+)?個人投資家(?:[、,・\s]+(?:機関投資家|報道機関|アナリスト))*の皆(?:様|さま)"
        for evidence, source in pairs:
            if not self.successful(source):
                continue
            quote = evidence["quote"]
            if target in {url_key(source.get("url")), url_key(source.get("requested_url"))}:
                local_quotes = [e["quote"] for e, s in pairs if s is source]
                if any(quote.strip() == form.get("text", "").strip()
                       and self.reviewed_external_ir_attribute_form(source, form, pairs, official_host)
                       for form in source.get("forms", [])):
                    return True
                if any(reviewed_anchored_personal_ir_form(source, form, local_quotes) for form in source.get("forms", [])):
                    return True
                # These literal company/personal prompts use two native
                # audience radios in the same complete cited IR form. Keep
                # this separate from the generic audience_radios regex: navigation,
                # product choices, optional company fields and other forms
                # cannot establish the selected IR form's eligibility.
                for form in source.get("forms", []):
                    fields = form.get("text", "").strip()
                    labels = form_labels(form)
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    if (urlsplit(source.get("url", "")).hostname != official_host
                            or str(form.get("method", "")).lower() != "post" or not question_form(form)
                            or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
                            or not fields or not any(e["quote"].strip() == fields and e.get("form_index", source["forms"].index(form)) == source["forms"].index(form)
                                                     for e, s in pairs if s is source)
                            or source.get("text", "").count(fields) != 1
                            or re.search(r"個人(?:の方|のお客様)?(?:からの)?(?:お問い合わせ)?は(?:受け付けません|お断り|対象外|ご遠慮)", fields)
                            or not self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        continue
                    # A shareholder/non-holder audience belongs to this
                    # native investor selector in the complete indexed IR
                    # post form, not to a shareholder link or optional firm.
                    investor_choice = "投資家区分 必須 投資家区分を選択してください 当社株主様 当社株主以外の個人投資家様 その他"
                    if (quote == investor_choice and investor_choice in labels
                            and not re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", fields)
                            and fields.startswith("お問い合わせ内容 必須 お客様情報 会社名 部署名 お名前 必須 ")
                            and ir_page_heading(source) and source.get("headings", []).count("IRに関するお問い合わせ") == 1
                            and "IRに関するお問い合わせ" in local_quotes
                            and any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int
                                    and e["source_form_index"] == source["forms"].index(form) for e, s in pairs if s is source)
                            and [c.get("name") for c in controls] == ["note", "company", "department", "name", "phone", "email", "email_confirm", "investor", "anotherinvestor"]
                            and controls[0].get("tag") == "textarea" and controls[0].get("type") != "hidden" and "required" in controls[0]
                            and all(c.get("tag") == "input" and c.get("type") == "text" for c in controls[1:7])
                            and all("required" in c for c in controls[3:8])
                            and controls[7].get("tag") == "select" and controls[7].get("type") != "hidden"
                            and controls[8].get("tag") == "input" and controls[8].get("type") == "text"
                            and urljoin(source.get("url", ""), form.get("action") or "") == source.get("url")):
                        return True
                    # The public company/organization/person field can
                    # explicitly include a person. Bind it to this mixed IR
                    # selector's native company input and full indexed form;
                    # the neighbouring required department remains required.
                    personal_company = "会社名／団体名／個人 必須 部署名 必須 お名前 必須"
                    mixed_ir_purpose = ("お問い合わせ項目 必須 選択してください。 耐火物・レンガ ニューセラミックス "
                                        "窯・機械・プラント設備 各種原料販売、受託加工 IR・採用・技術・その他")
                    reply_intro = "以下のフォームに必要事項をご入力の上、ご送信ください。担当部署よりご返信させていただきます。"
                    if (quote == personal_company and personal_company in labels
                            and fields.startswith(reply_intro + " " + mixed_ir_purpose + " " + personal_company + " ")
                            and any(e["quote"] == mixed_ir_purpose for e, s in pairs if s is source)
                            and any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int
                                    and e["source_form_index"] == source["forms"].index(form) for e, s in pairs if s is source)
                            and len(controls) >= 12
                            and controls[0].get("tag") == "select" and controls[0].get("type") != "hidden" and controls[0].get("name") == "your-select"
                            and all(c.get("tag") == "input" and c.get("type") == "text" and c.get("name") == name
                                    for c, name in zip(controls[1:3], ("your-company", "your-part")))
                            and controls[7].get("tag") == "input" and controls[7].get("type") == "email" and controls[7].get("name") == "your-mail"
                            and controls[11].get("tag") == "textarea" and controls[11].get("type") != "hidden" and controls[11].get("name") == "your-message"
                            and url_key(urljoin(source.get("url", ""), form.get("action") or "")) == url_key(source.get("url"))):
                        return True
                    # This asterisk-marked attribute family has its own
                    # native selector and field order, distinct from the older
                    # TRIGGER_TYPE engine. Cite the exact financial IR parent
                    # link, whole indexed form and public individual option.
                    attribution = "属性 ＊ 選択してください 金融機関 証券会社 事業法人 メディア 個人 その他"
                    attribution_names = ["Attribution", "Company", "Name", "Furigana", "Email", "Tel", "Description", "Privacy"]
                    if (fields.startswith(attribution + " 会社名・団体名等 ") and attribution in labels and quote == attribution
                            and source.get("title") == "IRに関するお問い合わせ" and source.get("headings", []).count("IRに関するお問い合わせ") == 1
                            and [c.get("name") for c in controls] == attribution_names
                            and controls[0].get("tag") == "select" and controls[0].get("type") != "hidden" and controls[0].get("id") == "Attribution" and "required" in controls[0]
                            and controls[4].get("tag") == "input" and controls[4].get("type") == "email" and "required" in controls[4]
                            and controls[6].get("tag") == "textarea" and controls[6].get("type") != "hidden" and "required" in controls[6]
                            and any(e["quote"].strip() == fields and type(e.get("form_index")) is int and e.get("form_index") == source["forms"].index(form) for e, s in pairs if s is source)
                            and url_key(urljoin(source.get("url", ""), form.get("action") or "")) == url_key(source.get("url"))
                            and any(self.successful(parent) and parent is not source and IR_MARKER.search(parent.get("title", ""))
                                    and urlsplit(parent.get("url", "")).hostname == official_host and pe["quote"] == "IRに関するお問い合わせ"
                                    and pe.get("source_link_url") == source.get("url")
                                    and any(link.get("label") == pe["quote"] and link.get("url") == pe["source_link_url"]
                                            and pe.get("source_link_index") == i for i, link in enumerate(parent.get("links", [])))
                                    for pe, parent in pairs)):
                        return True
                    # A dedicated IR audience group is distinct from the
                    # same form's general customer and recruitment groups.
                    # Require its literal field quote, native group/order,
                    # complete indexed form citation and actual IR fields.
                    ir_choice = "お客様種別 投資家・アナリスト 個人投資家"
                    ir_category = ("お問い合わせ ゴルフシャフトの問い合わせはこちらから 製品に関する問い合わせ "
                                   "IRに関する問い合わせ コンプライアンスに関する問い合わせ その他の問い合わせ 採用に関する問い合わせ")
                    if (ir_choice in quote and ir_choice in labels and fields.startswith(ir_category + " ")
                            and any(e["quote"] == ir_choice for e, s in pairs if s is source)
                            and any(e["quote"].strip() == fields and e.get("source_form_index") == source["forms"].index(form) for e, s in pairs if s is source)
                            and len(controls) > 10
                            and all(c.get("tag") == "input" and c.get("type") == "radio" and c.get("name") == "inquiry-details" for c in controls[:5])
                            and sum(c.get("name") == "inquiry-details" for c in controls) == 5
                            and all(c.get("tag") == "input" and c.get("type") == "radio" and c.get("name") == "customer-type-ir" for c in controls[9:11])
                            and sum(c.get("name") == "customer-type-ir" for c in controls) == 2
                            and any(c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "your-email" for c in controls)
                            and any(c.get("tag") == "textarea" and c.get("type") != "hidden" and c.get("name") == "your-content" for c in controls)
                            and url_key(urljoin(source.get("url", ""), form.get("action") or "")) == url_key(source.get("url"))
                            and not re.search(r"個人投資家(?:の方)?(?:からの)?(?:お問い合わせ)?は(?:受け付けません|お断り|対象外|ご遠慮)", fields)):
                        return True
                    group_choice = "企業／団体・個人 ＊ 企業／団体 個人"
                    legal_choice = "法人 / 個人 法人のお客様 個人のお客様"
                    audience_radios = [c for c in controls if c.get("name") in {"way1", "legal_entity_or_individual"}]
                    if (len(audience_radios) != 2 or any(c.get("tag") != "input" or c.get("type") != "radio" for c in audience_radios)
                            or controls.index(audience_radios[1]) != controls.index(audience_radios[0]) + 1):
                        continue
                    group = (group_choice in quote and group_choice in labels
                             and [c.get("name") for c in audience_radios] == ["way1", "way1"]
                             and [c.get("id") for c in audience_radios] == ["ownClassCompanyTrue", "ownClassCompanyFalse"]
                             and controls[4:6] == audience_radios
                             and all(c.get("tag") == "input" and c.get("type") == "radio" and c.get("name") == "way2" for c in controls[:4])
                             and any(c.get("tag") == "input" and c.get("type") == "text" and c.get("name") == "mail_address"
                                     and i + 1 < len(controls) and controls[i+1].get("tag") == "textarea" and controls[i+1].get("name") == "content"
                                     for i, c in enumerate(controls))
                             and form_ir_scope(form, reviewed=True)
                             and sum(c.get("tag") == "input" and c.get("type") == "radio" and c.get("name") == "way2" for c in controls) == 4
                             and any(c.get("tag") == "input" and c.get("type") == "text" and c.get("name") == "mail_address" for c in controls)
                             and any(c.get("tag") == "textarea" and c.get("type") != "hidden" and c.get("name") == "content" for c in controls))
                    legal = (legal_choice in quote and legal_choice in labels
                             and [c.get("name") for c in audience_radios] == ["legal_entity_or_individual"] * 2
                             and [c.get("id") for c in audience_radios] == ["edit-legal-entity-or-individual-", "edit-legal-entity-or-individual---2"]
                             and controls[4:6] == audience_radios
                             and controls[0].get("tag") == "textarea" and controls[0].get("name") == "your_comment"
                             and controls[3].get("tag") == "input" and controls[3].get("type") == "email" and controls[3].get("name") == "email"
                             and fields.startswith("IRに関するお問い合わせ 現在 入力 確認 完了 ") and ir_page_heading(source)
                             and any(c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "email" for c in controls)
                             and any(c.get("tag") == "textarea" and c.get("type") != "hidden" and c.get("name") == "your_comment" for c in controls))
                    if group or legal:
                        return True
                # A public company-input placeholder may explicitly tell
                # individual investors what to enter. Do not turn arbitrary
                # "write" wording into eligibility: bind this literal saved
                # attribute to its actual company input, the complete cited
                # post form and the same already verified IR question form.
                if self.reviewed_ir_customer_person_company_input(record, evidence, source, pairs, official_host):
                    return True
                if self.reviewed_ir_person_none_company_input(record, evidence, source, pairs, official_host):
                    return True
                if self.reviewed_ir_company_record_person_entry(record, evidence, source, pairs, official_host):
                    return True
                if self.reviewed_person_or_corporation_ir_radios(record, evidence, source, pairs, official_host):
                    return True
                if self.reviewed_personal_company_label_ir_form(record, evidence, source, pairs, official_host):
                    return True
                if record.get("contact_url") == source.get("url") and self.reviewed_ir_quoted_company_person_entry(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_sf_ir_personal_radios(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_native_ir_occupation(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_ir_trigger_personal_selector(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_numeric_ir_audience_iframe(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_bilingual_ir_investor_selector(evidence, source, pairs, official_host):
                    return True
                if self.reviewed_ir_company_person_name_placeholder(evidence, source, pairs, official_host):
                    return True
                # This required company placeholder expressly tells a person
                # what to enter in the same native, indexed mixed-IR form.
                # The company example alone, other forms and product/recruit
                # groups cannot confer personal financial-IR eligibility.
                if (quote == "例）カナレ電気株式会社（個人の方は個人）"
                        and evidence.get("field_path") == "forms.2.controls.11.placeholder"
                        and type(evidence.get("source_form_index")) is int and evidence["source_form_index"] == 2
                        and public_attribute_quote(evidence, source) and len(source.get("forms", [])) == 3
                        and urlsplit(source.get("url", "")).hostname == official_host):
                    form = source["forms"][2]; fields = form.get("text", "").strip()
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    purpose = ("件名： 必須 ご選択ください 会社情報・企業活動・IRに関するお問い合わせ 製品に関するお問い合わせ "
                               "海外製品、海外の営業に関するお問い合わせ 高パワー用光ファイバ関連製品 採用に関するお問い合わせ")
                    if (str(form.get("method", "")).lower() == "post" and form.get("action") == "check.php"
                            and fields.startswith(purpose + " 題名： 必須 質問グループ： 購入検討相談 ")
                            and "法人名/団体/学校： 必須 お名前： 必須 住所： TEL： Eメール： 必須 内容： 必須 メールを書く前に、ご確認ください。" in fields
                            and fields.endswith("環境依存文字をご使用すると、正確に情報が届かない場合がございます。")
                            and source.get("text", "").count(fields) == 1 and form_ir_scope(form, reviewed=True) and question_form(form)
                            and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source["forms"]) == 1
                            and any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 2
                                    for e, s in pairs if s is source)
                            and [c.get("name") for c in controls] == ["contact_type", "title"] + ["division"] * 9 + ["company", "name", "address", "tel", "email", "comment", None]
                            and controls[0].get("tag") == "select" and controls[0].get("type") != "hidden" and "required" in controls[0]
                            and controls[11].get("tag") == "input" and controls[11].get("type") == "text" and "required" in controls[11]
                            and all(c.get("tag") == "input" and c.get("type") == "radio" for c in controls[2:11])
                            and controls[15].get("tag") == "input" and controls[15].get("type") == "email" and "required" in controls[15]
                            and controls[16].get("tag") == "textarea" and controls[16].get("type") != "hidden" and "required" in controls[16]
                            and not re.search(r"個人(?:の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", fields)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True

                attribute_path = FORM_ATTRIBUTE_PATH.fullmatch(str(evidence.get("field_path", "")))
                if (quote == "個人投資家の方は個人投資家と記載ください。"
                        and attribute_path and attribute_path[3] == "placeholder"
                        and public_attribute_quote(evidence, source)):
                    form = source["forms"][int(attribute_path[1])]
                    control = form["controls"][int(attribute_path[2])]
                    if (control.get("tag") == "input" and control.get("type") == "text"
                            and re.fullmatch(r"com_name|company(?:[_-]?name)?", str(control.get("name", "")), re.I)
                            and str(form.get("method", "")).lower() == "post"
                            and question_form(form)
                            and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1
                            and any(c.get("tag") == "input" and c.get("type") == "email"
                                    for c in form.get("controls", []) if isinstance(c, dict))
                            and any(q.strip() == form.get("text", "").strip() for q in local_quotes)
                            and re.search(r"会社(?:・団体・学校)?名等?\s+必須", form.get("text", ""))
                            and not re.search(r"個人投資家(?:の方)?(?:からの)?(?:お問い合わせ)?は(?:受け付けません|お断り|対象外|ご遠慮)", form.get("text", ""))
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", form.get("text", ""), re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # An industry selector can explicitly classify the inquirer
                # as an individual investor. Require this literal saved field
                # block BEFORE privacy text, the actual named selector and
                # reply/question fields in one unambiguous question form, and
                # independently bound financial-IR purpose for THAT form.
                investor_options = re.compile(
                    r"業種\s+選択\s+個人投資家\s+機関投資家\s+アナリスト\s+その他(?=\s|$)"
                )
                actual_forms = [f for f in source.get("forms", []) if reviewed_question_form(f)]
                results_entry = "会社名・団体名（個人の場合は個人とご記入下さい） ※"
                for form in actual_forms:
                    if (results_entry in quote and results_entry in form_labels(form)
                            and any(c.get("tag") == "input" and c.get("type") == "text" and c.get("name") == "org_name"
                                    for c in form.get("controls", []) if isinstance(c, dict))
                            and not re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", ""))
                            and reviewed_results_question_checkbox_form(source, form, local_quotes)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # The company-information block can expressly waive those
                # additional fields for individuals. This is a stated input
                # rule, not an inference from optional company information.
                # Require the literal cited instruction at that block's start
                # and its native company/department controls in the same post
                # form as a cited IR/CSR purpose selector and reply/question
                # fields. Another form's instruction cannot confer access.
                waiver = "法人の場合は以下の情報も入力してください。個人の方の入力は不要です。"
                for form in actual_forms:
                    labels = form_labels(form)
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)
                                and c.get("tag") in {"input", "select", "textarea"}
                                and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
                    company_block = (len(controls) >= 2
                                     and controls[0].get("tag") == "input" and controls[0].get("type") == "text"
                                     and re.fullmatch(r"company[_-]?name", str(controls[0].get("name", "")), re.I)
                                     and controls[1].get("tag") == "input" and controls[1].get("type") == "text"
                                     and re.fullmatch(r"department[_-]?name", str(controls[1].get("name", "")), re.I))
                    purpose = re.search(r"用件\s+＊\s+選択してください[^。]{0,400}?\sIR/CSR関連について(?=\s|$)", labels)
                    purpose_control = any(c.get("tag") == "select" and c.get("name") == "matter" for c in controls)
                    if (len(actual_forms) == 1 and quote == waiver and company_block and purpose_control
                            and labels.startswith("会社情報 " + waiver + " 会社名 ")
                            and purpose and any(purpose[0] in q for q in local_quotes)
                            and any(c.get("tag") == "textarea" and QUESTION_FIELD.search(str(c.get("name", ""))) for c in controls)
                            and str(form.get("method", "")).lower() == "post" and question_form(form)
                            and not re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", ""))
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                for form in actual_forms:
                    if (reviewed_public_qa_personal_form(source, form, local_quotes)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                for form in actual_forms:
                    labels = form_labels(form)
                    choice = investor_options.search(labels)
                    named_selector = any(isinstance(c, dict) and c.get("tag") == "select"
                                         and c.get("type") != "hidden"
                                         and re.fullmatch(r"industry|industry_type|gyoshu|業種", str(c.get("name", "")), re.I)
                                         for c in form.get("controls", []))
                    if (len(actual_forms) != 1 or not choice or choice[0] not in quote or not named_selector
                            or re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)):
                        continue
                    explicit_parent = any(
                        self.successful(parent) and any(
                            isinstance(link, dict) and url_key(link.get("url")) == target
                            and isinstance(link.get("label"), str) and link["label"] in pe["quote"]
                            and IR_CONTACT.search(link["label"])
                            and re.search(r"(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])|investor relations", link["label"], re.I)
                            for link in parent.get("links", []))
                        for pe, parent in pairs if parent is not source
                    )
                    dedicated_heading = ir_page_heading(source) and any(
                        h and h in q and IR_CONTACT.search(h) for h in
                        [source.get("title", ""), *source.get("headings", [])[:1]] for q in local_quotes
                    )
                    if (explicit_parent or dedicated_heading) and self.has_form_binding(
                        pairs, None, reviewed=True, target_url=target, target_form=form
                    ):
                        return True
                # A literal "individual" option in an attribute selector is
                # different from a privacy/nav reference to a person. Bind
                # the complete cited public block to the first and only
                # visible native selector and reply/question fields of this
                # same independently verified IR post form.
                attribute_options = re.compile(
                    r"属性\s+必須\s+選択してください\s+金融機関\s+証券会社\s+事業法人\s+メディア\s+個人\s+その他(?=\s|$)"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    option = attribute_options.match(labels.strip())
                    visible = [c for c in form.get("controls", []) if isinstance(c, dict)
                               and c.get("tag") in {"input", "select", "textarea"}
                               and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
                    selectors = [c for c in visible if c.get("tag") == "select"]
                    if (len(actual_forms) != 1 or not option or option[0] not in quote
                            or str(form.get("method", "")).lower() != "post"
                            or len(selectors) != 1 or not visible or visible[0] is not selectors[0]
                            or selectors[0].get("id") != selectors[0].get("name")
                            or not re.fullmatch(r"TRIGGER_TYPE_[0-9]+", str(selectors[0].get("name", "")))
                            or not any(c.get("tag") == "input" and c.get("type") == "email"
                                       and c.get("name") == "MAIL" for c in visible)
                            or not any(c.get("tag") == "textarea" and c.get("name") == "CONTACT_BODY" for c in visible)
                            or not any(q.strip() == form.get("text", "").strip() for q in local_quotes)
                            or not re.search(r"お問い合わせ内容\s+必須", labels)
                            or re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", ""))):
                        continue
                    declared_ir = ir_page_heading(source) and any(
                        h and h in q and IR_CONTACT.search(h) for h in
                        [source.get("title", ""), *source.get("headings", [])[:1]] for q in local_quotes
                    )
                    explicit_parent = any(
                        self.successful(parent) and self.quoted_ir_direction(pe, parent, {target})
                        for pe, parent in pairs if parent is not source
                    )
                    if (declared_ir or explicit_parent) and self.has_form_binding(
                        pairs, None, reviewed=True, target_url=target, target_form=form
                    ):
                        return True
                # Literal company-field instructions for a general person
                # or an individual investor must belong to the already bound
                # IR question form. Neither an employment-input instruction
                # nor an unrelated privacy/example paragraph can supply it.
                plain_personal_entry = re.compile(
                    r"会社名[（(]団体名[）)]\s*※個人の場合は個人と入力してください[。.]"
                )
                investment_personal_entry = re.compile(
                    r"貴社名/所属\s+必須\s+【投資】個人投資家の方は、\s*『個人投資家』と記入してください[。.]"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    plain = plain_personal_entry.search(labels)
                    investing = investment_personal_entry.search(labels)
                    company_input = any(c.get("tag") == "input" and c.get("type") == "text"
                                        and ((c.get("name") == "会社名（学校名）" and c.get("id") == "corp")
                                             or c.get("name") == "your-company") for c in controls)
                    investing_category = (any(c.get("tag") == "input" and c.get("type") == "radio"
                                               and c.get("name") == "your-type" for c in controls)
                                          and "投資に関するお問い合わせ" in labels
                                          and any("投資に関するお問い合わせ" in q and q in labels for q in local_quotes))
                    if (len(actual_forms) == 1 and company_input
                            and ((plain and plain[0] in quote) or (investing and investing[0] in quote and investing_category))
                            and str(form.get("method", "")).lower() == "post" and question_form(form)
                            and any(c.get("tag") == "input" and c.get("type") == "email" for c in controls)
                            and any(c.get("tag") == "textarea" and c.get("type") != "hidden"
                                    and QUESTION_FIELD.search(str(c.get("name", ""))) for c in controls)
                            and not re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", ""))
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # An instruction to enter "individual" in the company field
                # is explicit eligibility. Bind this quoted public label to
                # its actual company input and the same verified IR question
                # form; an optional/mandatory company field alone says less.
                personal_company_entry = re.compile(
                    r"(?:企業名|会社名)\s*[（(]\s*個人の方は[、,]\s*[「『]個人[」』]とご?記載ください[）)]"
                )
                customer_company_entry = re.compile(
                    r"(?:必須\s+)?会社名\s+"
                    r"(?:(?!会社名フリガナ|必須\s|任意\s|部署名|メール|個人情報|プライバシー).){0,200}?"
                    r"※\s*個人のお客様は[「『]個人[」』]とご入力ください[。.]"
                )
                organization_company_entry = re.compile(
                    r"会社名・団体名\s+必須\s+※[「『]個人のお客様は[「『]個人[」』]とご入力ください[。.]"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    primary_instruction = personal_company_entry.search(labels)
                    organization_instruction = organization_company_entry.search(labels)
                    instruction = primary_instruction or customer_company_entry.search(labels) or organization_instruction
                    company_input = any(
                        isinstance(c, dict) and c.get("tag") == "input"
                        and str(c.get("type", "text")).lower() == "text"
                        and re.fullmatch(r"company(?:[_-]?name)?|corporate[_-]?name|企業名|会社名", str(c.get("name", "")), re.I)
                        for c in form.get("controls", [])
                    )
                    if (len(actual_forms) == 1 and instruction and instruction[0] in quote and company_input
                            and (not organization_instruction or question_form(form) and any(
                                isinstance(c, dict) and c.get("tag") == "input" and c.get("type") == "email"
                                for c in form.get("controls", [])))
                            and (primary_instruction or str(form.get("method", "")).lower() == "post")
                            and (primary_instruction or not re.search(r"個人(?:投資家|の方|のお客様)[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", "")))
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # The public "standing" prompt can identify an individual
                # investor even when its actual radio name is opaque. Its
                # three options, one unambiguous three-radio group and the
                # reply/question fields must be in this verified IR form.
                standing_options = re.compile(
                    r"あなたのお立場を教えてください[。.]\s+個人投資家\s+プロフェッショナル\s+その他(?=\s|$)"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    choice = standing_options.search(labels)
                    groups = Counter(str(c.get("name")) for c in form.get("controls", [])
                                     if isinstance(c, dict) and c.get("tag") == "input" and c.get("type") == "radio"
                                     and re.fullmatch(r"position|standing|investor[_-]?type|inquiry_[0-9]+", str(c.get("name", "")), re.I))
                    declared_ir = ir_page_heading(source) and any(
                        h and h in q and IR_CONTACT.search(h) for h in
                        [source.get("title", ""), *source.get("headings", [])[:1]] for q in local_quotes
                    )
                    explicit_parent = any(
                        self.successful(parent) and self.quoted_ir_direction(pe, parent, {target})
                        for pe, parent in pairs if parent is not source
                    )
                    if (len(actual_forms) == 1 and choice and choice[0] in quote
                            and len([name for name, count in groups.items() if count == 3]) == 1
                            and (declared_ir or explicit_parent)
                            and str(form.get("method", "")).lower() == "post"
                            and not re.search(r"個人(?:投資家|の方|のお客様)[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", form.get("text", ""))
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # Profession is a checkbox group on some IR forms, rather
                # than a radio/select customer category. The four actual job
                # controls and the four literal public options must belong to
                # the same verified question form, before the privacy policy.
                profession_options = re.compile(r"ご?職業\s+個人投資家\s+機関投資家\s+証券会社\s+その他(?=\s|$)")
                personal_refusal = re.compile(r"個人(?:投資家|の方|のお客様)[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)")
                for form in actual_forms:
                    labels = form_labels(form)
                    choice = profession_options.search(labels)
                    ir_category = re.search(r"お問い合わせの(?:種類|項目|種別)\s*(?:必須)?[^。]{0,120}(?:IR|ＩＲ)情報に関して(?=\s|$)", labels, re.I)
                    inquiry_selector = any(
                        isinstance(c, dict) and c.get("tag") == "select"
                        and re.fullmatch(r"category|syurui|kind|inquiry[_-]?type", str(c.get("name", "")), re.I)
                        for c in form.get("controls", [])
                    )
                    job_groups = Counter(str(c.get("name")) for c in form.get("controls", [])
                                         if isinstance(c, dict) and c.get("tag") == "input"
                                         and str(c.get("type", "")).lower() == "checkbox"
                                         and re.fullmatch(r"(?:job|occupation|profession)\[\]", str(c.get("name", "")), re.I))
                    if (len(actual_forms) == 1 and choice and choice[0] in quote and list(job_groups.values()) == [4]
                            and inquiry_selector and ir_category and any(ir_category[0] in q for q in local_quotes)
                            and not personal_refusal.search(labels) and not personal_refusal.search(quote)
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # Literal personal/corporate options and personal company
                # field exceptions require the same verified IR question
                # form. Consent controls, navigation, and an optional company
                # field alone confer no access.
                checkbox_audience = re.compile(
                    r"個人・法人\s+個人投資家\s+機関投資家\s+証券会社\s+その他法人(?=\s|$)"
                )
                company_exception = re.compile(
                    r"貴社名\s+任意\s+正式名を入力[（(]個人投資家以外の方は必須[）)]\s+"
                    r"部署\s+任意\s+正式名を入力[（(]個人投資家以外の方は必須[）)]"
                )
                personal_customer_options = re.compile(
                    r"どちらかを選択してください\s+必須\s+個人のお客様\s+法人のお客様(?=\s|$)"
                )
                personal_none_entry = re.compile(
                    r"必須\s+貴社名・部署名\s*[（(]個人で依頼のお客様は[「『]なし[」』]とご記入ください[）)]"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    if (len(actual_forms) != 1 or str(form.get("method", "")).lower() != "post"
                            or personal_refusal.search(form.get("text", ""))
                            or re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)):
                        continue
                    declared_ir = ir_page_heading(source) and any(
                        h and h in q and IR_CONTACT.search(h) for h in
                        [source.get("title", ""), *source.get("headings", [])] for q in local_quotes
                    )
                    explicit_parent = any(
                        self.successful(parent) and self.quoted_ir_direction(pe, parent, {target})
                        for pe, parent in pairs if parent is not source
                    )
                    category_control = any(
                        isinstance(c, dict) and (c.get("tag") == "select" or c.get("type") == "radio")
                        and c.get("type") != "hidden"
                        and re.search(r"category|kind|inquiry|type|お?問(?:い)?合(?:わ)?せ(?:種類|種別|内容|項目)", str(c.get("name", "")), re.I)
                        for c in form.get("controls", [])
                    )
                    cited_category = category_control and form_ir_scope(form, reviewed=True) and any(
                        q and q in labels and re.search(r"(?<![A-Za-z0-9])(?:IR|ＩＲ)(?![A-Za-z0-9])", IR_SERVICE_OFFERING.sub("", q), re.I)
                        for q in local_quotes
                    )
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    reply_input = any(c.get("tag") == "input" and c.get("type") == "email" for c in controls)
                    if not (reply_input and (declared_ir or explicit_parent or cited_category)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        continue
                    choice = checkbox_audience.search(labels)
                    audience_groups = Counter(str(c.get("name")) for c in controls
                                              if c.get("tag") == "input" and c.get("type") == "checkbox"
                                              and re.fullmatch(r"(?:ir|investor)[_-]?type\[data\]\[\]", str(c.get("name", "")), re.I))
                    exception = company_exception.search(labels)
                    company_department = any(
                        c.get("tag") == "input" and c.get("type") == "text"
                        and re.fullmatch(r"company(?:[_-]?name)?", str(c.get("name", "")), re.I)
                        and i + 1 < len(controls) and controls[i+1].get("tag") == "input"
                        and controls[i+1].get("type") == "text"
                        and re.fullmatch(r"department|dept|mail_author", str(controls[i+1].get("name", "")), re.I)
                        for i, c in enumerate(controls)
                    )
                    customer_options = personal_customer_options.search(labels)
                    personal_radios = sum(c.get("tag") == "input" and c.get("type") == "radio"
                                          and c.get("name") == "f_kojin_or_hojin" for c in controls)
                    none_entry = personal_none_entry.search(labels)
                    company_department_field = any(c.get("tag") == "input" and c.get("type") == "text"
                                                   and c.get("name") == "貴社名・部署名" for c in controls)
                    if ((choice and choice[0] in quote and list(audience_groups.values()) == [4])
                            or (exception and exception[0] in quote and company_department)
                            or (customer_options and customer_options[0] in quote and personal_radios == 2)
                            or (none_entry and none_entry[0] in quote and company_department_field and cited_category)):
                        return True
                # A private-consultation customer option can be written
                # without whitespace before its explanation. Require that
                # literal field and two native customer radios in the SAME
                # IR-category post form, with a full public form citation.
                # Multiple tabs/forms cannot transfer these choices to a
                # recruitment form or a different question form.
                private_customer_choice = re.compile(
                    r"区分\s+必須\s+個人[（(]プライベート[/／]個人でのご相談[）)]\s+"
                    r"事業者[（(]法人[、,]個人事業主[、,]団体等[）)](?=\s|$)"
                )
                ir_stock_category = re.compile(
                    r"問い合わせ種別\s+必須\s+選択してください[^。]{0,200}?\sIR・株式関連(?=\s|$)"
                )
                for form in actual_forms:
                    labels = form_labels(form)
                    choice = private_customer_choice.search(labels)
                    category = ir_stock_category.search(labels)
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    customer_radios = sum(c.get("tag") == "input" and c.get("type") == "radio"
                                          and c.get("name") == "customer_type" for c in controls)
                    category_selector = any(c.get("tag") == "select" and c.get("type") != "hidden"
                                            and c.get("name") == "type" for c in controls)
                    reply_field = any(c.get("tag") == "input" and c.get("type") == "email"
                                      and c.get("name") == "email" for c in controls)
                    question_field = any(c.get("tag") == "textarea" and c.get("type") != "hidden"
                                         and c.get("name") == "message" for c in controls)
                    if (choice and choice[0] in quote and category
                            and any(category[0] in q for q in local_quotes)
                            and any(q.strip() == form.get("text", "").strip() for q in local_quotes)
                            and category_selector and customer_radios == 2 and reply_field and question_field
                            and str(form.get("method", "")).lower() == "post"
                            and not personal_refusal.search(form.get("text", ""))
                            and not re.match(r"\s*(?:製品|商品|採用|サポート|product|support|recruit)", labels, re.I)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # Literal personal/company alternatives are public FIELD
                # labels, not an inference from whether company is required.
                # Recover this cited field after an introductory privacy
                # notice only when its actual organization input or pair of
                # officecheck radios belongs to this verified IR form.
                for form in actual_forms:
                    text = form.get("text", "")
                    if (len(actual_forms) != 1 or quote not in text or PRIVACY_START.search(quote)
                            or personal_refusal.search(text)):
                        continue
                    controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                    organization = re.search(r"個人・企業・団体・学校名\s*必須(?=\s|$)", quote)
                    organization_input = any(c.get("tag") == "input" and c.get("type") == "text"
                                             and c.get("name") == "organization" for c in controls)
                    office_choice = re.search(r"会社名/団体名\s*※\s*法人\s+個人\s+所属・役職等(?=\s|$)", quote)
                    office_radios = sum(c.get("tag") == "input" and c.get("type") == "radio"
                                        and c.get("name") == "officecheck" for c in controls)
                    office_input = any(c.get("tag") == "input" and c.get("type") == "text"
                                       and c.get("name") == "office" for c in controls)
                    stock_label_end = text.find("株式に関するお問い合わせ") + len("株式に関するお問い合わせ")
                    quoted_label_start = text.find(quote)
                    stock_personal_field = (office_choice and reviewed_financial_stock_form(source, form, local_quotes)
                                            and stock_label_end >= len("株式に関するお問い合わせ")
                                            and quoted_label_start > stock_label_end
                                            and not PRIVACY_START.search(text[stock_label_end:quoted_label_start]))
                    if quote not in form_labels(form) and not stock_personal_field:
                        continue
                    affiliation = re.fullmatch(
                        r"所属等についてご記入ください\s*[（(]会社、学校、団体、個人等[）)]\s*※", quote.strip()
                    )
                    # A numeric affiliation field follows the paired numeric
                    # email and confirmation inputs on the captured form.
                    # Require this actual control order and public field
                    # label; an unrelated numeric input or a privacy example
                    # cannot serve as the personal-entry instruction.
                    affiliation_input = any(
                        i >= 2 and c.get("tag") == "input" and c.get("type") == "text"
                        and re.fullmatch(r"f[0-9]{6,}", str(c.get("name", "")))
                        and c.get("id") == c.get("name")
                        and all(x.get("tag") == "input" and x.get("type") == "text" for x in controls[i-2:i])
                        and re.fullmatch(r"f[0-9]{6,}", str(controls[i-2].get("name", "")))
                        and controls[i-1].get("name") == controls[i-2].get("name") + ":cf"
                        for i, c in enumerate(controls)
                    )
                    affiliation_labels = re.search(
                        r"メールアドレス\s*※\s*メールアドレス[（(]確認用[）)]\s*※\s*" + re.escape(quote.strip()),
                        form_labels(form)
                    ) if affiliation else None
                    customer_choice = re.fullmatch(
                        r"お客さま種別\s*\[必須\]\s*法人・団体のお客さま\s+個人のお客さま", quote.strip()
                    )
                    customer_radios = sum(c.get("tag") == "input" and c.get("type") == "radio"
                                          and c.get("name") == "user-type" for c in controls)
                    if ((organization and organization_input or office_choice and office_radios == 2 and office_input
                         or affiliation and affiliation_labels and affiliation_input
                         or customer_choice and customer_radios == 2 and quote.strip() in form_labels(form))
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                # General individuals are a separate stated option from
                # individual shareholders. This actual occupation select at
                # the cited IR page must contain BOTH literal options; a
                # shareholder-only menu never asserts non-holder eligibility.
                for form in actual_forms:
                    labels = form_labels(form)
                    personal_options = re.search(
                        r"職業\s+必須\s+選択してください\s+個人株主\s+一般個人(?=\s|$)", labels
                    )
                    occupation_select = any(
                        isinstance(c, dict) and c.get("tag") == "select" and c.get("type") != "hidden"
                        and any(str(c.get(field, "")) == "occupation" for field in ("name", "id"))
                        for c in form.get("controls", [])
                    )
                    cited_title = source.get("title") and any(source["title"] in q for q in local_quotes)
                    if (len(actual_forms) == 1 and personal_options and personal_options[0] in quote
                            and occupation_select and ir_page_heading(source) and cited_title
                            and not re.search(r"一般個人(?:の方)?[^。]{0,30}(?:対象外|お断り|受け付けません)", labels)
                            and self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                        return True
                headings = [source.get("title", ""), *source.get("headings", [])[:1]]
                if any(isinstance(h, str) and h and h in quote and
                       IR_CONTACT.search(h) and personal_title.search(h) for h in headings):
                    return True
            # An official contact directory quotes its audience immediately
            # above the cited IR-purpose link to this exact URL, query included.
            if url_key(evidence.get("source_link_url")) != target or not official_host:
                continue
            parent_host = urlsplit(source.get("url", source.get("requested_url", ""))).hostname
            base_host = official_host.removeprefix("www.")
            if not parent_host or not (parent_host.removeprefix("www.") == base_host or parent_host.endswith("." + base_host)):
                continue
            for link in source.get("links", []):
                label = link.get("label", "")
                if (url_key(link.get("url")) != target or not isinstance(label, str) or not label
                        or not (IR_CONTACT.search(label) or IR_MARKER.search(label) and "ご質問" in label)):
                    continue
                if re.search(audience + r"\s*" + re.escape(label), quote):
                    return True
        return False

    def reviewed_issuer_investment_category(self, pairs: list[tuple[dict, dict]], source: dict, form: dict) -> bool:
        """Bind a literal investment-information option to issuer investment.

        The word "investment" or an IR footer alone is insufficient. Require
        the complete cited pre-policy form block, native category/reply/question
        controls, and a captured link from a separately cited issuer-IR page
        that explicitly addresses investing in this company.
        """
        menu = ("お問い合わせ項目 必須 選択してください サービスに関する問い合わせ "
                "投資情報に関するお問い合わせ 取材のお申し込み アライアンス等のご相談 その他（貴社サービス等のご紹介）")
        fields = "お問い合わせ内容 必須 お名前 必須 フリガナ 必須 会社名 必須 メールアドレス 必須 電話番号 必須 業種 必須"
        labels = form_labels(form).strip()
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        visible = [c for c in controls if c.get("tag") in {"input", "select", "textarea"}
                   and str(c.get("type", "")).lower() not in {"hidden", "submit", "button"}]
        quotes = [e["quote"] for e, saved in pairs if saved is source]
        forbidden = re.compile(r"(?:IR|ＩＲ|投資情報)(?:に関する|の)?(?:お問い合わせ|ご質問)(?:は|については)[^。]{0,25}"
                               r"(?:電話のみ|フォームでは受け付けません|フォームの対象外)", re.I)
        if (str(form.get("method", "")).lower() != "post" or not question_form(form)
                or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
                or menu + " " + fields not in labels or not any(q.strip() == labels for q in quotes)
                or not visible or visible[0].get("tag") != "select"
                or visible[0].get("name") != "inquiry-category" or visible[0].get("id") != "inquiry-category"
                or sum(c.get("tag") == "select" and c.get("name") == "inquiry-category" for c in visible) != 1
                or not any(c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "email" for c in visible)
                or not any(c.get("tag") == "textarea" and c.get("name") == "inquiry-content" for c in visible)
                or forbidden.search(source.get("text", ""))
                or re.match(r"\s*(?:製品|商品|採用|営業|IR活動支援|金融商品|投資商品)", labels)):
            return False
        targets = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
        scope = "弊社への投資をご検討いただいている方へ、 弊社の概要を知っていただくための映像・資料をご用意いたしました。ぜひご覧ください。"
        for _, parent in pairs:
            if parent is source or not self.successful(parent):
                continue
            parent_quotes = [e for e, saved in pairs if saved is parent]
            headings = [h for h in parent.get("headings", []) if isinstance(h, str) and h.strip()]
            if (not IR_MARKER.search(parent.get("title", "")) or not headings or headings[0] != "IR"
                    or not {"株式情報", "業績ハイライト"}.issubset(headings)
                    or not any(e["quote"].strip() == parent.get("title", "") for e in parent_quotes)
                    or not any(e["quote"] == scope for e in parent_quotes)
                    or forbidden.search(parent.get("text", ""))
                    or urlsplit(parent.get("url", "")).hostname != urlsplit(source.get("url", "")).hostname):
                continue
            for link in parent.get("links", []):
                if (isinstance(link, dict) and link.get("label") in {"CONTACT", "CONTACT お問い合わせ"}
                        and url_key(link.get("url")) in targets
                        and any(e["quote"] == link["label"] and e.get("source_link_url") == link.get("url") for e in parent_quotes)):
                    return True
        return False

    def reviewed_ir_consent_form(self, pairs: list[tuple[dict, dict]], source: dict, form: dict) -> bool:
        """Verify two captured official IR links through a complete consent page.

        The generic company/business form must route service questions to a
        different cited link. A generic Contact footer, consent on another
        path, uncited conditions or fields split between forms is insufficient.
        """
        text = form.get("text", "").strip()
        prefix = "お問い合わせ件名 ※ 会社・事業について その他 サービスに関するお問い合わせはこちら お問い合わせ内容 ※"
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local_evidence = [e for e, s in pairs if s is source]
        if (not text.startswith(prefix) or str(form.get("method", "")).lower() != "post"
                or not question_form(form)
                or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
                or not any(e["quote"].strip() == text for e in local_evidence)
                or sum(c.get("tag") == "input" and c.get("type") == "radio" and c.get("name") == "subject" for c in controls) != 2
                or not all(any(c.get("tag") == "input" and c.get("type") in {"text", "email"}
                               and c.get("name") == name for c in controls) for name in ("mail", "mail_conf"))
                or not any(c.get("tag") == "textarea" and c.get("name") == "body" and c.get("type") != "hidden" for c in controls)
                or not re.search(r"メールアドレス ※[^。]{0,35}メールアドレス[（(]確認用[）)] ※", text)):
            return False
        targets = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
        service_label = "サービスに関するお問い合わせはこちら"
        service_links = [link for link in source.get("links", []) if isinstance(link, dict) and link.get("label") == service_label]
        if (len(service_links) != 1 or url_key(service_links[0].get("url")) in targets
                or url_key(service_links[0].get("url")) is None
                or not any(e["quote"] == service_label and e.get("source_link_url") == service_links[0].get("url") for e in local_evidence)):
            return False
        consent_label = "上記に同意してフォームに進む"
        ir_deflection = re.compile(
            r"(?:IR|ＩＲ)(?:に関する|の)?(?:お問い合わせ|ご質問)(?:は|については)[^。]{0,25}"
            r"(?:電話のみ|フォームでは受け付けません|フォームの対象外)", re.I
        )
        for ce, consent in pairs:
            if (consent is source or not self.successful(consent)
                    or ce["quote"].strip() != consent.get("text", "").strip()
                    or consent.get("headings", []).count("お問い合わせに当たってのご注意事項") != 1
                    or consent.get("text", "").count(consent_label) != 1
                    or ir_deflection.search(consent.get("text", ""))
                    or re.search(r"(?:株式(?:事務|手続き?)|株主優待)(?:の)?(?:専用フォーム|のみのフォーム)", consent.get("text", ""))
                    or any(question_form(f) or reviewed_question_form(f) for f in consent.get("forms", []))):
                continue
            links = [link for link in consent.get("links", []) if isinstance(link, dict) and link.get("label") == consent_label]
            if (len(links) != 1 or ce.get("source_link_url") != links[0].get("url")
                    or url_key(links[0].get("url")) not in targets):
                continue
            consent_urls = {url_key(consent.get("url")), url_key(consent.get("requested_url"))} - {None}
            consent_url, destination = url_key(consent.get("url")), url_key(links[0].get("url"))
            if (consent_url is None or destination is None or consent_url == destination
                    or urlsplit(consent_url).hostname != urlsplit(destination).hostname
                    or not urlsplit(destination).path.startswith(urlsplit(consent_url).path.rstrip("/") + "/")):
                continue
            for pe, parent in pairs:
                if (parent is source or parent is consent or not self.successful(parent)
                        or not IR_MARKER.search(parent.get("title", ""))
                        or ir_deflection.search(parent.get("text", ""))
                        or urlsplit(parent.get("url", "")).hostname != urlsplit(consent_url).hostname):
                    continue
                for link in parent.get("links", []):
                    label = link.get("label", "")
                    if (isinstance(label, str) and IR_CONTACT.search(label) and IR_MARKER.search(label)
                            and not OTHER_CONTACT.search(label) and not IR_SERVICE_OFFERING.search(label)
                            and not re.search(r"株主優待|株式(?:事務|手続)|配信(?:登録|停止)|メルマガ", label)
                            and label in pe["quote"] and pe.get("source_link_url") == link.get("url")
                            and url_key(link.get("url")) in consent_urls
                            and sum(isinstance(l, dict) and l.get("label") == label for l in parent.get("links", [])) == 1):
                        return True
        return False

    def reviewed_parenthesized_ir_question_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A backwards IR title needs its actual question form and directory row.

        The title, explicit invitation and complete fields must be cited on
        the same page. Repeated directory links are bound by saved text/link
        order, keeping the neighbouring sales form a separate destination.
        """
        title = source.get("title", "")
        heading = re.match(r"お問い合わせフォーム[（(](?:IR|ＩＲ)[）)]", title, re.I)
        local = [e for e, s in pairs if s is source]
        intro = "IR情報 ご意見・ご質問などございましたらお気軽にお問い合わせください。"
        fields = form.get("text", "").strip()
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        urls = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
        if (not heading or heading[0] not in source.get("headings", [])
                or not any(e["quote"] == title for e in local) or not any(e["quote"] == intro for e in local)
                or source.get("text", "").count(intro) != 1
                or not fields or not any(e["quote"].strip() == fields for e in local)
                or str(form.get("method", "")).lower() != "post"
                or url_key(urljoin(source.get("url", ""), form.get("action") or "")) not in urls
                or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
                or not any(c.get("tag") == "input" and c.get("type") == "email" for c in controls)
                or not any(c.get("tag") == "textarea" and c.get("type") != "hidden"
                           and QUESTION_FIELD.search(str(c.get("name", ""))) for c in controls)
                or re.match(r"\s*(?:製品|商品|採用|営業|サポート|product|support|recruit)", fields, re.I)):
            return False
        label = "お問い合わせフォームはこちら"
        for evidence, parent in pairs:
            quote = evidence["quote"]
            if (parent is source or not self.successful(parent) or parent.get("headings", []).count("IR情報") != 1
                    or not re.fullmatch(r"IR情報\s+経営企画本部\s+広報室\s+[0-9]{2,4}-[0-9]{2,4}-[0-9]{3,4}\s+" + label, quote)
                    or parent.get("text", "").count(quote) != 1
                    or urlsplit(parent.get("url", "")).hostname != urlsplit(source.get("url", "")).hostname):
                continue
            links = [link for link in parent.get("links", []) if isinstance(link, dict) and link.get("label") == label]
            occurrences = list(re.finditer(re.escape(label), parent["text"]))
            if (not links or len(links) != len(occurrences) or len({link.get("url") for link in links}) != len(links)):
                continue
            position = parent["text"].index(quote) + quote.rindex(label)
            indexes = [i for i, match in enumerate(occurrences) if match.start() == position]
            if (len(indexes) == 1 and evidence.get("source_link_url") == links[indexes[0]].get("url")
                    and url_key(evidence.get("source_link_url")) in urls):
                return True
        return False

    def reviewed_financial_material_question_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Bind financial-IR materials AND a message to an actual reply form.

        A navigation link or a product brochure alone is insufficient. The
        cited main IR preface is immediately followed by the complete post
        form, whose reply, three financial-material choices and message are
        captured in native control order, with a matching official IR parent.
        """
        preface = ("投資家情報ＩＲ TOP 株主の皆様へ コーポレートガバナンス プレスリリース "
                   "財務情報 IRカレンダー 株価情報 株主情報 FAQ お問い合わせ・資料請求 ※印は必須入力項目です。")
        fields = form.get("text", "").strip()
        local = [e for e, s in pairs if s is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        source_url = url_key(source.get("url"))
        action = url_key(urljoin(source.get("url", ""), form.get("action") or ""))
        if (not source_url or not str(source.get("title", "")).startswith("お問い合わせ・資料請求")
                or not fields or not any(e["quote"].strip() == fields for e in local)
                or not any(e["quote"] == preface for e in local)
                or source.get("text", "").count(preface) != 1 or source.get("text", "").count(fields) != 1
                or preface + " " + fields not in source.get("text", "")
                or str(form.get("method", "")).lower() != "post"
                or not action or urlsplit(action).hostname != urlsplit(source_url).hostname
                or urlsplit(action).path != urlsplit(source_url).path.rstrip("/") + "/index.html"
                or urlsplit(action).query or urlsplit(action).fragment
                or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) != 1
                or not re.search(r"E-mail\s*※\s*[（(]半角[）)]\s+送付を希望される資料\s+"
                                 r"事業報告書\s+会社案内パンフレット\s+会社説明会資料\s+メッセージ(?=\s|$)", form_labels(form), re.I)):
            return False
        sequence = False
        for i, control in enumerate(controls[:-4]):
            group = controls[i+1:i+4]
            message = controls[i+4]
            if (control.get("tag") == "input" and control.get("type") == "text"
                    and re.fullmatch(r"vl[0-9]+", str(control.get("name", ""))) and control.get("id") == control.get("name")
                    and all(c.get("tag") == "input" and c.get("type") == "checkbox"
                            and re.fullmatch(r"vl[0-9]+\[\]", str(c.get("name", ""))) for c in group)
                    and len({c.get("name") for c in group}) == 1 and len({c.get("id") for c in group}) == 3
                    and all(re.fullmatch(re.escape(group[0]["name"][:-2]) + r"_[0-9]+", str(c.get("id", ""))) for c in group)
                    and message.get("tag") == "textarea" and message.get("type") != "hidden"
                    and re.fullmatch(r"vl[0-9]+", str(message.get("name", ""))) and message.get("id") == message.get("name")):
                sequence = True
                break
        if not sequence:
            return False
        for evidence, parent in pairs:
            if (parent is source or not self.successful(parent)
                    or not str(parent.get("title", "")).startswith("投資家情報ＩＲ")
                    or urlsplit(parent.get("url", "")).hostname != urlsplit(source_url).hostname
                    or "投資家情報ＩＲ" not in evidence["quote"] or "財務情報" not in evidence["quote"]):
                continue
            links = [link for link in parent.get("links", []) if isinstance(link, dict)
                     and link.get("label") == "・資料請求/お問い合わせ" and url_key(link.get("url")) == source_url]
            if (len(links) == 1 and links[0]["label"] in evidence["quote"]
                    and evidence.get("source_link_url") == links[0].get("url")):
                return True
        return False

    def reviewed_ir_email_receipt_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A captured GET form can receive IR questions without proving POST.

        Bind the literal fair-disclosure/email operation immediately before
        its complete native form and the same issuer's cited financial-IR
        contact section. A phone policy and a generic footer cannot do this.
        """
        fields = form.get("text", "").strip()
        local = [e for e, s in pairs if s is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        target = url_key(source.get("url"))
        if (not target or str(form.get("method", "")).lower() != "get"
                or url_key(urljoin(source["url"], form.get("action") or "")) != target
                or len(source.get("forms", [])) != 1 or not question_form(form)
                or not fields.startswith("会社名 必須 お名前 必須 メールアドレス 必須 お電話番号 お問い合わせ内容 ")
                or not any(e["quote"].strip() == fields for e in local)
                or source.get("text", "").count(fields) != 1
                or not any(c.get("tag") == "input" and c.get("type") == "email" and c.get("name") == "mail_address" for c in controls)
                or not any(c.get("tag") == "textarea" and c.get("type") != "hidden" and c.get("name") == "contents" for c in controls)):
            return False
        operation = ("各種お問い合わせ 以下のフォームに必要事項をご記入いただき、お問い合わせください。 "
                     "数日中に当社担当からご連絡いたします。 "
                     "なお、当社では、正確かつ公平な情報開示を行うため、IRに関するご質問の受付、"
                     "回答はすべて電子メールで行うこととしています。ご理解とご協力をいただきますようお願いいたします。")
        if not any(e["quote"].startswith(operation) and source.get("text", "").count(e["quote"].strip() + " " + fields) == 1 for e in local):
            return False
        for evidence, parent in pairs:
            section = evidence["quote"].strip()
            if (parent is source or not self.successful(parent)
                    or not str(parent.get("title", "")).startswith("よくあるご質問｜IR情報｜")
                    or parent.get("headings", []).count("IRに関するお問い合わせ") != 1
                    or urlsplit(parent.get("url", "")).hostname != urlsplit(target).hostname
                    or parent.get("title", "").rsplit("｜", 1)[-1] != source.get("title", "").rsplit("｜", 1)[-1]
                    or not section.startswith("IRに関するお問い合わせ Inquiries about IRS ")
                    or not section.endswith(" お問い合わせ") or parent.get("text", "").count(section) != 1
                    or evidence.get("source_link_url") != source.get("url")):
                continue
            links = [l for l in parent.get("links", []) if isinstance(l, dict) and l.get("label") == "お問い合わせ"]
            if links and {l.get("url") for l in links} == {evidence["source_link_url"]}:
                return True
        return False

    def reviewed_aspnet_ir_department_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Recover the cited actual department fields inside an outer form.

        Privacy/navigation text precedes these fields in ASP.NET captures.
        Require the whole form plus the native ten-radio department block,
        adjacent opaque reply/confirmation/question controls and an exact
        IR-parent href to the saved requested URL; never normalize queries.
        """
        fields = form.get("text", "").strip()
        local = [e for e, s in pairs if s is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        target = url_key(source.get("url"))
        requested = url_key(source.get("requested_url"))
        request_query = re.fullmatch(r"frmid=([0-9]+)&to=IR・広報に関するお問い合わせ", urlsplit(requested or "").query)
        action = urlsplit(urljoin(source.get("url", ""), form.get("action") or ""))
        # This exact independently saved action spelling is a separate
        # witness, not normalization of the parent or claimed contact query.
        encoded_route = "IR%e3%83%bb%e5%ba%83%e5%a0%b1%e3%81%ab%e9%96%a2%e3%81%99%e3%82%8b%e3%81%8a%e5%95%8f%e3%81%84%e5%90%88%e3%82%8f%e3%81%9b"
        if (not target or not request_query or len(source.get("forms", [])) != 1
                or urlsplit(requested).hostname != urlsplit(target).hostname
                or str(form.get("method", "")).lower() != "post"
                or not fields or not any(e["quote"].strip() == fields for e in local)
                or source.get("text", "").count(fields) != 1
                or not str(source.get("title", "")).startswith("お問い合わせフォーム｜お問い合わせ｜")
                or action.hostname != urlsplit(target).hostname or action.path != urlsplit(target).path
                or action.query != "frmid=" + request_query[1] + "&to=" + encoded_route or action.fragment):
            return False
        category_prefix = "お問い合わせ先 ※ 企業活動全般関連 IR・広報関連 株式関連 "
        reply_suffix = re.compile(r"メールアドレス（半角英数字） ※ 例）[^\s]+ "
                                  r"メールアドレス（確認用） ※ 同じメールアドレスを入力してください お問い合わせ内容 ※\Z")
        sections = [e["quote"].strip() for e in local if e["quote"].strip().startswith(category_prefix)
                    and reply_suffix.search(e["quote"].strip()) and fields.count(e["quote"].strip()) == 1]
        if not sections or not any(section + " 個人情報保護方針" in fields for section in sections):
            return False
        subject = [c for c in controls if str(c.get("name", "")).endswith("$fldValue$rblSubjectRadioButtonList")]
        if (len(subject) != 10 or len({c.get("name") for c in subject}) != 1
                or any(c.get("tag") != "input" or c.get("type") != "radio"
                       or not str(c.get("id", "")).endswith("_rblSubjectRadioButtonList_0_" + str(i) + "_0") for i, c in enumerate(subject))):
            return False
        active = [c for c in controls if c.get("tag") in {"input", "select", "textarea"}
                  and c.get("type") not in {"hidden", "submit", "button", "search", "checkbox", "reset"}]
        if len(active) < 13 or active[:10] != subject:
            return False
        reply, confirmation, question = active[-3:]
        native_name = re.compile(r"(.+\$ViewMailForm\$grdMain\$PageID[0-9]+\$repCategory\$ctl[0-9]+\$repField\$)ItemID([0-9]+)\$fldValue\$(txtSingleTextBox|txtMultilineTextBox)\Z")
        matches = [native_name.fullmatch(str(c.get("name", ""))) for c in (reply, confirmation, question)]
        positions = [re.search(r"_(txtSingleTextBox|txtMultilineTextBox)_([0-9]+)\Z", str(c.get("id", ""))) for c in (reply, confirmation, question)]
        if (not all(matches) or not all(positions) or len({m[1] for m in matches}) != 1 or len({m[2] for m in matches}) != 3
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in (reply, confirmation))
                or question.get("tag") != "textarea" or question.get("type") == "hidden"
                or [m[3] for m in matches] != ["txtSingleTextBox", "txtSingleTextBox", "txtMultilineTextBox"]
                or [m[1] for m in positions] != ["txtSingleTextBox", "txtSingleTextBox", "txtMultilineTextBox"]
                or [int(m[2]) for m in positions] != list(range(int(positions[0][2]), int(positions[0][2]) + 3))
                or not str(subject[0]["name"]).startswith(matches[0][1])):
            return False
        for evidence, parent in pairs:
            section = evidence["quote"].strip()
            if (parent is source or not self.successful(parent)
                    or not str(parent.get("title", "")).startswith("IRに関するお問い合わせ｜株主・投資家の皆さまへ｜")
                    or parent.get("title", "").rsplit("｜", 1)[-1] != source.get("title", "").rsplit("｜", 1)[-1]
                    or urlsplit(parent.get("url", "")).hostname != urlsplit(target).hostname
                    or not section.startswith("IRに関するお問い合わせ PRINT 当社グループへのご意見・ご質問、資料のご請求はこちらからお願いいたします。")
                    or "IR・広報に関するお問い合わせ （" not in section or not section.endswith(" お問い合わせ")
                    or parent.get("text", "").count(section) != 1 or evidence.get("source_link_url") != source.get("requested_url")):
                continue
            links = [l for l in parent.get("links", []) if isinstance(l, dict) and l.get("label") == "お問い合わせ" and l.get("url") == evidence["source_link_url"]]
            if len(links) == 1:
                return True
        return False

    def reviewed_monthly_ir_faq_no_reply(self, record: dict, pairs: list[tuple[dict, dict]], seed: dict | None) -> bool:
        """The complete monthly public FAQ policy belongs to this IR form.

        A topic exclusion, delay, default/exception rule, other page or a
        refusal cited without the actual IR fields cannot establish it.
        """
        if not manual_review_valid(record):
            return False
        policy = '個別回答は行っておりません。 いただいたご質問は毎月集約し、「よくあるご質問」としてIRページ上に順次公開してまいります。'
        preface = ('IR情報 下記フォームに必要事項を入力のうえ送信ボタンをクリックして下さい。 '
                   '【お問い合わせについて】 お電話でのお問い合わせは受け付けておりませんので、あらかじめご了承ください。 ')
        target = url_key(record.get('contact_url'))
        official = seed.get('official_url') if isinstance(seed, dict) else record.get('official_url')
        host = urlsplit(official).hostname if url_key(official) else None
        for evidence, source in pairs:
            if (not self.successful(source) or evidence['quote'] != policy
                    or target not in {url_key(source.get('url')), url_key(source.get('requested_url'))}
                    or urlsplit(source.get('url', '')).hostname != host
                    or not any(e['quote'] == 'IR inquiry IRお問い合わせ' for e, s in pairs if s is source)
                    or source.get('text', '').count(preface + policy + ' 【ご回答できない内容について】') != 1):
                continue
            for form in source.get('forms', []):
                fields = form.get('text', '').strip()
                controls = [c for c in form.get('controls', []) if isinstance(c, dict)]
                local = [e for e, s in pairs if s is source]
                if (str(form.get('method', '')).lower() != 'post' or not reviewed_question_form(form)
                        or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get('forms', [])) != 1
                        or not fields.startswith('氏名 [必須] メールアドレス [必須] 会社名 お問い合わせ内容 [必須] ')
                        or not any(e['quote'].strip() == fields and type(e.get('form_index')) is int and e.get('form_index') == source['forms'].index(form) for e in local)
                        or source.get('text', '').count(fields) != 1 or len(controls) < 4
                        or controls[1].get('tag') != 'input' or controls[1].get('type') != 'text'
                        or controls[1].get('name') != 'entry.2049253258' or controls[1].get('placeholder') != 'メールアドレス'
                        or controls[3].get('tag') != 'textarea' or controls[3].get('type') == 'hidden'
                        or controls[3].get('name') != 'entry.830297578'
                        or urlsplit(str(form.get('action', ''))).hostname != 'docs.google.com'
                        or not re.fullmatch(r'/forms/u/[0-9]+/d/e/[A-Za-z0-9_-]+/formResponse', urlsplit(str(form.get('action', ''))).path)
                        or urlsplit(str(form.get('action', ''))).query or urlsplit(str(form.get('action', ''))).fragment
                        or not self.has_form_binding(pairs, None, reviewed=True, target_url=target, target_form=form)):
                    continue
                body = source['text']
                start, end = body.index(preface), body.index(fields)
                if (start >= end or re.search(r'(?:ただし|なお|但し|例外として)[^。]{0,100}(?:個別|メール)[^。]{0,60}(?:回答|返信)', body[start:end])):
                    continue
                return True
        return False

    def reviewed_ir_customer_person_company_input(self, record: dict, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The personal company entry belongs to this cited IR/publicity radio form."""
        fields = 'お問い合わせは、下記のフォームから必要項目をご入力頂き、確認ボタンをクリックして下さい。 お問い合わせの際にご入力頂いた情報は弊社の プライバシーポリシー に基づき、適切に取り扱い、保護することに努めます。 なお、ご質問によっては、お返事にお時間頂く場合、また、お答え出来かねる場合がありますので、あらかじめご了承ください。 お問い合わせフォーム 「 * 」は入力必須項目です。 お問い合わせの種類 * ガス/LNG分野関係 石油/石油化学/非鉄金属分野関係 電力/再生可能エネルギー/蓄電分野関係 脱炭素/エネルギートランジション分野関係 ライフサイエンス/医薬品/先端素材分野関係 ライフサイエンス/医薬/バイオ分野関係 技術関係 O&M-Xソリューション/ChAS事業関係 調達関係へのご提案 国内建設工事関係 海外建設工事関係 株主の皆様 CSR関係 IR・広報関係 水素サプライチェーン事業関係 件名 * お問い合わせの内容 * お名前 * 貴社名（法人名・団体名・学校名） * 個人のお客様は「個人」とご記入ください 業種 * 選択してください 金融機関 行政・自治体・政府 企業 各種団体 マスコミ・メディア 株主・投資家 学生・学校関係者 その他 HPのURL(会社の場合) 部署 住所／国 電話番号 * 市外局番より - ハイフンつなぎで入力して下さい E-mail * お問合せを頂く前に、下記の「個人情報の取り扱いについて」をお読み頂き、 ご同意いただける場合は「同意する」ボタンをクリックして、入力確認画面へ進んでください。 個人情報の取り扱いについて 1.個人情報の利用目的 当社では、ご提供いただいた個人情報を、個人情報の保護に関する法律、ならびに当社の個人情報保護方針に基づき、以下の用途で使用いたします。 製品、サービスや事業のお問い合わせ、一般の問い合わせ等 お問い合わせに対するご返事、事業遂行上のご連絡、資料等の送付のため 製品やサービスに関するお知らせのため ご提供いただいている製品やサービスの確認のため 採用に関するお問い合わせ等 お問い合わせに対するご返事、資料送付のため 採用事務手続きに関するご本人様への連絡のため 採用に関する統計用データとして 2.個人情報の第三者への提供制限 当社は個人情報を適切に管理し、下記に該当する場合を除いて、いかなる第三者にも提供や開示又は預託することはありません。 提供や開示について、あらかじめご本人様の同意が得られている場合 当社が委託した業務以外に個人情報を利用することが無いように、業務委託先に対して、あらかじめ契約を結んでいる場合 法令等により提供や開示を要請された場合 3. 個人情報のお問い合わせ先 個人情報に関する開示・訂正・削除及び個人情報の取扱いに関する苦情については、上記「CSR関係」にご連絡ください。 同意する 同意しない'
        selection = 'お問い合わせの種類 * ガス/LNG分野関係 石油/石油化学/非鉄金属分野関係 電力/再生可能エネルギー/蓄電分野関係 脱炭素/エネルギートランジション分野関係 ライフサイエンス/医薬品/先端素材分野関係 ライフサイエンス/医薬/バイオ分野関係 技術関係 O&M-Xソリューション/ChAS事業関係 調達関係へのご提案 国内建設工事関係 海外建設工事関係 株主の皆様 CSR関係 IR・広報関係 水素サプライチェーン事業関係'
        person = "貴社名（法人名・団体名・学校名） * 個人のお客様は「個人」とご記入ください"
        url = source.get("url", ""); parsed = urlsplit(url); title = source.get("title", ""); forms = source.get("forms", [])
        prefix = "お問い合わせ | "; suffix = " - プラント・エンジニアリング"
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/jp/contact/index.php" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or record.get("contact_url") != url or source.get("submitted") is not False
                or not title.startswith(prefix) or not title.endswith(suffix)
                or identity_key(title[len(prefix):-len(suffix)]) != identity_key(record.get("company_name", ""))
                or source.get("headings") != ["お問い合わせ", "お問い合わせフォーム", "個人情報の取り扱いについて"]
                or len(forms) != 2 or str(forms[0].get("method", "")).lower() != "get" or forms[0].get("action") != "/cgi-bin/jp/search/index.cgi" or forms[0].get("text") != ""
                or forms[0].get("controls") != [{"tag": "input", "type": "text", "name": "query", "placeholder": "キーワードを入力してください"}]
                or evidence["quote"] != fields or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 1
                or type(evidence.get("form_index", 1)) is not int or evidence.get("form_index", 1) != 1):
            return False
        form = forms[1]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]; body = source.get("text", "")
        local = [e["quote"] for e, s in pairs if s is source]
        names = ["syurui"] * 15 + ["title01", "note", "namae", "posit", "sector", "website", "post", "add", "tel", "email", "doui", "doui", "submit"]
        ids = ["syurui1", "syurui2", "syurui9", "syurui17", "syurui18", "syurui19", "syurui3", "syurui11", "syurui4", "syurui10", "syurui5", "syurui6", "syurui7", "syurui8", "syurui16"]
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != "index.php" or form.get("text") != fields or body.count(fields) != 1
                or not all(q in local for q in (title, selection, person)) or fields.count(selection) != 1 or fields.count(person) != 1
                or not any("株価情報 株式情報 配当情報 アナリストカバレッジ 電子公告" in q and "IRに関するお問い合わせ" in q for q in local)
                or [c.get("name") for c in controls] != names or [c.get("id") for c in controls[:15]] != ids or any("required" in c for c in controls)
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[:15])
                or controls[16].get("tag") != "textarea" or controls[16].get("type") == "hidden"
                or controls[19].get("tag") != "select" or controls[19].get("type") == "hidden"
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (15, 17, 18, 20, 21, 22, 23, 24))
                or identity_key(str(controls[18].get("placeholder", "")).removeprefix("例：")) != identity_key(record.get("company_name", ""))
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[25:27])
                or [c.get("id") for c in controls[25:27]] != ["doui1", "doui2"] or controls[27].get("tag") != "input" or controls[27].get("type") != "submit"
                or re.search(r"個人(?:のお客様|の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", body[:body.index(fields) + len(fields)])):
            return False
        links = source.get("links", [])
        return bool(len(links) > 195 and links[195] == {"url": url, "href": "/jp/contact/index.php", "label": "IRに関するお問い合わせ"}
                    and self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(url), target_form=form, official_host=official_host))

    def reviewed_ir_person_none_company_input(self, record: dict, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The literal 'none' instruction names the actual company/school input."""
        fields = 'お問い合わせ内容を選択* お問い合わせ内容を選択 * 取材依頼 IR 採用 その他 お問い合わせ内容を記入* ※よろしければ、お問い合わせの目的もご記入ください。内容検討時の参考にさせていただきます。 ※「㈱」や「①②③」などの機種依存文字を使用しないようお願いします お名前* ふりがな* 会社名・学校名 ※「㈱」などの機種依存文字を使用しないようお願いします。 ※個人の場合は「なし」とご記入ください。 部署名 役職 郵便番号* 住所 * 都道府県を選択 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 住所 番地 建物名・部屋番号 電話番号* メールアドレス* 確認用メールアドレス* 個人情報の取り扱いについて 株式会社タダノ（以下弊社といいます）は以下の原則に基づき個人情報を取り扱いします。 個人情報の利用目的 弊社は提供いただいたお客様の個人情報を、以下の目的にのみ利用するものとします。 (1) 弊社製品の販売、修理・点検等のサービスのご提供および原材料等の調達。 (2) アンケート調査の実施、ならびにアンケートに基づく商品・サービスおよび販売企画上の統計資料等の作成。 (3) ご請求いただいた商品やサービス、各種資料のご提供。 (4) お問い合わせへの回答、景品等の発送。 (5) 弊社および弊社に関連した商品・サービス・イベント開催・アンケート実施等の案内。 (6) その他、上記各業務に伴う業務、弊社が個人から同意を得た業務の実施。 個人情報取り扱いの適法性 個人情報取り扱いの法的根拠はご本人による同意です。 第三者への提供 弊社はその子会社や取引先に個人情報を提供することがあります。その場合、当該個人情報が提供先において適切に取り扱われるようにします。 個人情報の保管期間 弊社は、個人情報収集後から利用目的達成までの間、収集した個人情報を保管します。利用目的達成後は保管する個人情報を速やかに削除します。 個人情報をご提供いただけなかった場合 個人情報をご提供いただけなかった場合、お問い合わせ等に回答できない可能性があります。 ご本人の権利への対応 弊社は、ご本人からの個人情報の取り扱いに関する要求について、法令に従い適切に対応します。 プライバシーポリシー 個人情報の取り扱いについてのより詳細な情報は、 プライバシーポリシー をご覧ください。 連絡先 個人情報の取り扱いについてのお問い合わせは webmaster@tadano.com までメールでご連絡ください。 個人情報の取り扱いを読み、これに同意します。 * *必須 必須項目あと 0 件です 内容を確認する'
        selection = "お問い合わせ内容を選択* お問い合わせ内容を選択 * 取材依頼 IR 採用 その他"
        person = "※個人の場合は「なし」とご記入ください。"
        url = source.get("url", ""); parsed = urlsplit(url); forms = source.get("forms", []); body = source.get("text", "")
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/ja/contact/" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or record.get("contact_url") != url or source.get("submitted") is not False
                or source.get("title") != "contact - Tadano Corporate Website" or len(forms) != 1
                or evidence["quote"] != fields or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 0
                or type(evidence.get("form_index", 0)) is not int or evidence.get("form_index", 0) != 0):
            return False
        form = forms[0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local = [e for e, s in pairs if s is source]
        names = ["inquirytype", "inquiry-message", "name", "name-pronunciation", "company-or-school-name", "department", "position", "zip", "in_prefecture", "in_address", "in_address2", "in_address3", "tel", "email", "confirm_email", "in_privacy", "submit_contact_form"]
        required = {0, 1, 2, 3, 7, 8, 9, 10, 12, 13, 14, 15}
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != "#contact-form-container" or form.get("text") != fields or body.count(fields) != 1
                or not all(any(e["quote"] == q and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e in local) for q in (selection, person))
                or [c.get("name") for c in controls] != names or {i for i, c in enumerate(controls) if "required" in c} != required
                or any(controls[i].get("required") is not None for i in required)
                or any(controls[i].get("tag") != "select" or controls[i].get("type") == "hidden" for i in (0, 8)) or controls[0].get("id") != "inquirytype"
                or controls[1].get("tag") != "textarea" or controls[1].get("type") == "hidden"
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (2, 3, 4, 5, 6, 7, 9, 10, 11))
                or controls[12].get("tag") != "input" or controls[12].get("type") != "tel"
                or any(c.get("tag") != "input" or c.get("type") != "email" for c in controls[13:15])
                or controls[15].get("tag") != "input" or controls[15].get("type") != "checkbox" or controls[16].get("tag") != "input" or controls[16].get("type") != "submit"
                or re.search(r"個人(?:の場合|の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", body[:body.index(fields) + len(fields)])):
            return False
        issuer = "株式会社タダノ コーポレート情報サイト - Tadano Corporate Website"
        if identity_key(record.get("company_name", "")) != identity_key("タダノ") or not any(
                self.successful(s) and s.get("url") == "https://" + official_host + "/ja/" and s.get("requested_url") == "https://" + official_host + "/"
                and len(s.get("redirects", [])) == 1 and s["redirects"][0].get("requested_url") == s["requested_url"]
                and s["redirects"][0].get("url") == s["requested_url"] and s["redirects"][0].get("http_status") == 302
                and s["redirects"][0].get("redirect_target") == s["url"] and aware_time(s["redirects"][0].get("retrieved_at"))
                and e["quote"] == s.get("title") == issuer for e, s in pairs):
            return False
        for _, parent in pairs:
            if (parent is source or not self.successful(parent) or parent.get("url") != "https://" + official_host + "/ja/ir/" or parent.get("requested_url") != parent.get("url")
                    or parent.get("title") != "IR情報 - Tadano Corporate Website" or "財務情報" not in parent.get("headings", []) or "株式に関する情報" not in parent.get("headings", [])
                    or not any("資本コスト・株価を意識した経営" in e["quote"] and "IR 社長メッセージ 中期経営計画 決算短信・決算説明資料 有価証券報告書" in e["quote"] for e, s in pairs if s is parent)):
                continue
            links = parent.get("links", [])
            if len(links) > 13 and links[13] == {"url": url, "href": url, "label": "お問い合わせ お問い合わせ"}:
                return self.has_form_binding(pairs, None, reviewed=True, target_url=url_key(url), target_form=form, official_host=official_host)
        return False

    def reviewed_financial_stock_investor_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The stock page's cited investor radios bind this actual question form."""
        fields = '当社の 個人情報保護方針 に同意の上、お問合せください。 必須 同意する お問い合わせの種類をお選びください。 必須 投資家向け情報 その他 お問い合わせ内容 必須 ■お客様情報 メールアドレス 必須 会社名 必須 部署名 役職名 お名前（姓） 必須 お名前（名） 必須 〒 必須 住所自動代入 都道府県 必須 市区郡 必須 住所（市区郡以降） 必須 電話番号 必須 FAX番号 お客様情報をブラウザに保存する 確認画面をスキップする 入力内容を確認'
        title = "株式基本情報｜株式関連情報｜投資家情報｜日工株式会社"
        selection = "お問い合わせの種類をお選びください。 必須 投資家向け情報 その他 お問い合わせ内容 必須"
        url = source.get("url", ""); parsed = urlsplit(url); body = source.get("text", ""); local = [e for e, s in pairs if s is source]
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/ir/stockinfo/information.html" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or source.get("title") != title or source.get("headings", []).count("株式基本情報") != 1
                or source.get("headings", []).count("お問い合わせ内容について") != 1 or source.get("submitted") is not False
                or len(source.get("forms", [])) != 1 or source["forms"][0] is not form or str(form.get("method", "")).lower() != "post" or form.get("action") != ""
                or form.get("text") != fields or body.count(fields) != 1 or body.count("証券コード 6306") != 1
                or not all(any(e["quote"] == q for e in local) for q in (title, selection, "証券コード 6306"))
                or not any(e["quote"] == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e in local)):
            return False
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["form-agree", "inquiry-kind-ir", "inquiry-kind-ir", "inquiry-free-text", "c-email", "c-company", "c-department", "c-job-title", "c-last-name", "c-first-name", "c-post-code", "c-prefecture", "c-city", "c-address", "c-phone-number", "c-fax-number", "mrc_save_custinfo", "confirm_skip"]
        return bool([c.get("name") for c in controls] == names
                    and controls[0].get("tag") == "input" and controls[0].get("type") == "checkbox"
                    and all(c.get("tag") == "input" and c.get("type") == "radio" for c in controls[1:3])
                    and controls[3].get("tag") == "textarea" and controls[3].get("type") != "hidden"
                    and controls[4].get("tag") == "input" and controls[4].get("type") == "email"
                    and all(c.get("tag") == "input" and c.get("type") == "text" for c in controls[5:16])
                    and all(c.get("tag") == "input" and c.get("type") == "checkbox" for c in controls[16:18]))

    def reviewed_ir_opaque_fields_after_policy(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Use the real fields after the complete policy and the captured IR route."""
        fields = '同意する 同意しない ※は必須項目です。 お問い合わせ先※ 事業を選択してください 新素材加工機器事業（ワイヤーソー） 半導体機器・ディスプレイ機器 繊維機器 研削機 医療機器 美容機器 新規事業 IR・その他お問い合わせ 所属企業・団体名※ 部署名 ※個人やフリーランスの方は、「個人」とご記入ください 氏 名※ メールアドレス※ 住 所※ ▼都道府県を選択 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 お問い合わせ内容※'
        prefix = "Home »お問い合わせ お問い合わせ 個人情報について ご利用いただく前に、必ず「プライバシーポリシー（個人情報の取り扱いについて）」の内容をお読みのうえ、ご同意願います。ご同意いただける場合のみご利用いただけます。 "
        primary = "IR情報 決算短信・有価証券報告書 フィナンシャル・ハイライト 電子公告 株主総会情報 株主通信 その他開示情報 沈黙期間について"
        url = source.get("url", ""); parsed = urlsplit(url); requested = "https://" + str(official_host) + "/inquiry-form/index.html"
        text = form.get("text", ""); body = source.get("text", ""); local = [e for e, s in pairs if s is source]
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/inquiry-form-new/" or parsed.query or parsed.fragment
                or source.get("requested_url") != requested or source.get("submitted") is not False
                or not source.get("title", "").startswith("お問い合わせ｜") or source.get("headings", []).count("お問い合わせ") != 1
                or len(source.get("forms", [])) != 1 or source["forms"][0] is not form or str(form.get("method", "")).lower() != "post" or form.get("action") != "confirm.php"
                or not text.startswith(prefix) or not text.endswith(fields) or text.count(fields) != 1 or body.count(text) != 1
                or not any(e["quote"] == text and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e in local)
                or not any(e["quote"] == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 for e in local)):
            return False
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["text1", "text1", "text2", "text3", "text4", "text5", "text6", "text7", "text9", "text8"]
        if ([c.get("name") for c in controls] != names or [c.get("id") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[:2])
                or any(controls[i].get("tag") != "select" or controls[i].get("type") == "hidden" for i in (2, 7))
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (3, 4, 5, 6, 8))
                or controls[9].get("tag") != "textarea" or controls[9].get("type") == "hidden"):
            return False
        redirects = source.get("redirects", [])
        if (len(redirects) != 1 or redirects[0].get("requested_url") != requested or redirects[0].get("url") != requested
                or redirects[0].get("http_status") != 302 or redirects[0].get("redirect_target") != url or not aware_time(redirects[0].get("retrieved_at"))):
            return False
        issuer = source["title"].removeprefix("お問い合わせ｜")
        for pe, parent in pairs:
            pp = urlsplit(parent.get("url", ""))
            if (parent is source or not self.successful(parent) or pp.scheme != "http" or pp.hostname != official_host or pp.path != "/ir/index.html" or pp.query or pp.fragment
                    or parent.get("requested_url") != parent.get("url") or parent.get("title") != "IR情報｜" + issuer
                    or parent.get("headings") != [issuer, "IR情報"] or source.get("headings") != [issuer, "お問い合わせ"]
                    or pe["quote"] != "お問い合わせ" or pe.get("source_link_url") != requested or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 2
                    or "Home » IR情報 " + primary not in parent.get("text", "")
                    or not any(e["quote"] == primary for e, s in pairs if s is parent)):
                continue
            links = parent.get("links", [])
            if len(links) > 2 and links[2] == {"url": requested, "href": requested, "label": "お問い合わせ"}:
                return True
        return False

    def reviewed_ir_company_record_person_entry(self, record: dict, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Bind the literal personal company instruction to this dedicated IR form."""
        fields = '企業名（個人の方は「個人」とご記載ください） 例：株式会社ABC 部署名 例：経営企画部 役職名 例：部長 お名前 例：田中太郎 フリガナ 例：タナカタロウ メールアドレス 例：name@company.com 携帯電話／電話番号 例：08012345678 郵便番号 例：1230000 ご住所 例：福岡市博多区博多駅中央街 お問い合わせ内容 お問い合わせ内容を具体的にご記入ください。 個人情報の取扱いについて 個人情報取扱いの注意事項については こちら をご確認ください 個人情報の取扱いについて同意しました 送信等の不具合があった場合は、大変お手数ですが、下記までお問い合わせください Mail： ' + "contact@" + str(official_host).removeprefix("www.")
        operation = "当社株主、投資家の皆様からのお問い合わせは、メールによるお問い合わせに限定させていただいております。 下記IRに関するお問い合わせフォームに必要事項をご入力いただき、「送信する」ボタンを押してください。"
        url = source.get("url", ""); parsed = urlsplit(url); title = source.get("title", ""); forms = source.get("forms", [])
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/ir/contact/" or parsed.query or parsed.fragment
                or record.get("contact_url") != url or source.get("requested_url") != url or not title.startswith("IRお問い合わせ | ")
                or identity_key(title.removeprefix("IRお問い合わせ | ")) != identity_key(record.get("company_name", ""))
                or "当社株主・投資家の皆さまへ" not in source.get("headings", []) or len(forms) != 1
                or evidence["quote"] != fields or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 0
                or type(evidence.get("form_index", 0)) is not int or evidence.get("form_index", 0) != 0):
            return False
        form = forms[0]; body = source.get("text", ""); local = [e["quote"] for e, s in pairs if s is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["your-company", "your-position", "your-job", "your-name", "your-kana", "your-email", "your-tel", "your-zipcode", "your-address", "your-message", "checkbox-consent[]", None]
        if (str(form.get("method", "")).lower() != "post" or not re.fullmatch(r"/ir/contact/#wpcf7-f[0-9]+-p[0-9]+-o1", form.get("action", ""))
                or form.get("text") != fields or body.count(fields) != 1 or operation not in local or body.count(operation) != 1 or body.index(operation) >= body.index(fields)
                or [c.get("name") for c in controls] != names or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:5])
                or controls[5].get("tag") != "input" or controls[5].get("type") != "email" or controls[6].get("type") != "tel" or controls[7].get("type") != "number"
                or controls[8].get("tag") != "input" or controls[8].get("type") != "text" or controls[9].get("tag") != "textarea" or controls[9].get("type") == "hidden"
                or controls[10].get("tag") != "input" or controls[10].get("type") != "checkbox" or controls[11].get("tag") != "input" or controls[11].get("type") != "submit"
                or re.search(r"個人(?:の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", body[body.index(operation):body.index(fields) + len(fields)])):
            return False
        for pe, parent in pairs:
            pp = urlsplit(parent.get("url", "")); primary = "IRライブラリー 最新IR資料 決算短信 有価証券報告書 決算説明会資料"
            if (parent is source or not self.successful(parent) or pp.scheme != "https" or pp.hostname != official_host or pp.path != "/ir/" or pp.query or pp.fragment
                    or parent.get("requested_url") != parent.get("url") or parent.get("title") != "IR情報 | " + title.removeprefix("IRお問い合わせ | ")
                    or "IRコンテンツ" not in parent.get("headings", []) or pe["quote"] != "IRお問い合わせ" or pe.get("source_link_url") != url
                    or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 92
                    or not any(primary in e["quote"] and parent.get("text", "").count(e["quote"]) == 1 for e, s in pairs if s is parent)):
                continue
            links = parent.get("links", [])
            if len(links) > 92 and links[92] == {"url": url, "href": url, "label": "IRお問い合わせ"}:
                return True
        return False


    def reviewed_redirected_ir_opaque_reply_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The saved IR iframe redirect binds the opaque E-mail/question pair."""
        fields = '会社名 個人の方は 個人 とご記入ください。 会社名（読み） 所属 役職名 住所 都道府県/地域 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 海外 市区町村 町名・番地 Address Two ビル名等をご記入ください 電話番号 名 お名前 Eメール お問い合わせ内容 Privacy - Terms Comments 個人情報及び保有個人データの利用目的 当社は、事業を円滑に行うために個人情報を取得することがありますが、当社 個人情報保護方針 ならびに プライバシーポリシー に基づき厳正に管理いたします。 お問い合わせ内容によっては、ご入力いただいた個人情報を当社グループ会社で共同利用させていただく場合がございます。なおこの場合でも、当社 個人情報保護方針 ならびに プライバシーポリシー に基づき厳正に管理いたします。'
        url = source.get("url", ""); parsed = urlsplit(url); requested = source.get("requested_url", "")
        account = re.fullmatch(r"/l/([0-9]+)/[0-9]{4}-[0-9]{2}-[0-9]{2}/[A-Za-z0-9]+", parsed.path)
        if (not official_host or parsed.scheme != "https" or parsed.hostname != "kona." + official_host.removeprefix("www.")
                or not account or parsed.query or parsed.fragment or requested != "https://" + parsed.hostname + "/inquiry_jp_ir"
                or source.get("title") != "" or source.get("headings") != [] or source.get("submitted") is not False
                or len(source.get("forms", [])) != 1 or source["forms"][0] is not form
                or str(form.get("method", "")).lower() != "post" or form.get("action") != url or form.get("text") != fields
                or source.get("text", "").count(fields) != 1
                or not any(e["quote"] == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, s in pairs if s is source)):
            return False
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = [account[1] + "_" + str(n) + "pi_" + account[1] + "_" + str(n) for n in range(32377, 32404, 2)]
        names += ["pi_extra_field", None]
        if ([c.get("name") for c in controls] != names or [c.get("id") for c in controls[:-1]] != names[:-1]
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (*range(5), *range(6, 13), 14))
                or controls[5].get("tag") != "select" or controls[5].get("type") == "hidden"
                or controls[13].get("tag") != "textarea" or controls[13].get("type") == "hidden"
                or controls[15].get("tag") != "input" or controls[15].get("type") != "submit"):
            return False
        redirects = source.get("redirects", [])
        if (len(redirects) != 1 or redirects[0].get("requested_url") != requested or redirects[0].get("url") != requested
                or redirects[0].get("http_status") != 302 or redirects[0].get("redirect_target") != url
                or not aware_time(redirects[0].get("retrieved_at"))):
            return False
        instruction = "IR・業績に関するお問い合わせはこちらからお願いいたします。"
        for pe, parent in pairs:
            pp = urlsplit(parent.get("url", "")); title = parent.get("title", "")
            if (parent is source or not self.successful(parent) or pp.scheme != "https" or pp.hostname != official_host
                    or pp.path != "/jp/contact/ir.html" or pp.query or pp.fragment or parent.get("requested_url") != parent.get("url")
                    or not title.startswith("IR・業績関連 | ") or parent.get("headings", []).count("IR・業績関連") != 1
                    or pe["quote"] != instruction or pe.get("source_link_url") != requested):
                continue
            links = parent.get("links", [])
            if (len(links) <= 102 or links[102] != {"url": requested, "src": requested, "label": "embedded frame"}
                    or sum(link.get("src") == requested for link in links if isinstance(link, dict)) != 1):
                continue
            issuer = title.removeprefix("IR・業績関連 | ")
            if any(self.successful(identity) and urlsplit(identity.get("url", "")).hostname == official_host
                   and ie["quote"] == identity.get("title") == issuer for ie, identity in pairs):
                return True
        return False

    def reviewed_company_ir_checkboxes_after_consent(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Actual company IR checkboxes follow consent in this indexed AForm."""
        fields = 'プライバシーポリシーの同意 必須 私は上記のプライバシーポリシー及びご利用にあたってに同意します。 お問い合わせ種別 必須 選択してください 軸受（ベアリング）製品について 免震・制震製品について 採用について 会社について お問い合わせ製品 必須 建築用製品 橋梁用製品 お問い合わせ内容 必須 見積・お打ち合わせ希望 カタログ希望 製品について 価格について 納期について その他 お問い合わせ内容 必須 お打ち合わせ希望 カタログ希望 検討依頼 その他 お問い合わせ内容 必須 会社情報 IR その他 お問い合わせ内容 必須 新卒採用 キャリア採用 OB/OG訪問 工場見学 その他 内容詳細 必須 内容詳細 必須 納期のご希望などがございましたらこちらにご記入ください。 内容詳細 必須 内容詳細 必須 ご希望のカタログ 総合カタログ プレス・樹脂金型カタログ 添付ファイル ※10MB まで お名前 必須 フリガナ 必須 会社名･団体名 部署名 大学名 学部・学科名 Japan 郵便番号 必須 都道府県 必須 選択してください 日本国外（Outside Japan） 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 広島県 岡山県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 住所 必須 Japan 郵便番号 入力例:123-4567 都道府県 選択してください 北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県 日本国外（Outside Japan） 住所 電話番号 必須 メールアドレス 必須 確認のためもう一度入力してください お客様の業種 選択してください 自動車 二輪車 産業用車両 航空機・船舶 鉄道 エネルギー インフラ 半導体 ロボット 工作機械 成形機・金型部品 電子機器 ポンプ・コンプレッサー 食品・包装 医療・健康機器 その他 業務内容 選択してください 設計・開発 研究 資材・購買 生産技術（設備） 営業・企画 その他 お客様からご提供いただく個人情報は、今後のお問い合わせ対応、カタログデータダウンロード、CADデータダウンロード、販売促進に利用させていただくことがあります'
        intro = ("当社に関するお問い合わせを受け付けております。 下記よりお気軽にお問い合わせください。 なお、お問い合わせの内容によってはご回答に多少お時間をいただく場合がございますので、ご了承願います。 "
                 "お客様宛に当社からの返事（お問合せの回答）は下記にご入力いただいたE-mail宛（お客様個人宛）にお送りします。 当社からの返事（お問合せの回答）の全部又はその一部を、本問い合わせ以外の目的で利用することはご遠慮ください。 "
                 "また返信用のメールアドレスにおきましても、お客様ご自身以外の関係者や外部への展開はご遠慮ください。")
        url = source.get("url", ""); parsed = urlsplit(url); forms = source.get("forms", [])
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/contact/index.php" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or source.get("submitted") is not False or len(forms) != 3 or forms[2] is not form
                or source.get("headings", []).count("お問い合わせ") != 1 or not source.get("title", "").startswith("お問い合わせ - ")
                or any(str(f.get("method", "")).lower() != "get" or f.get("action") != "/search/" or question_form(f) for f in forms[:2])
                or str(form.get("method", "")).lower() != "post" or form.get("action") != "/mt/plugins/AForm/aform_engine.cgi"
                or form.get("text") != fields or source.get("text", "").count(fields) != 1
                or not any(e["quote"] == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 2
                           and type(e.get("form_index", 2)) is int and e.get("form_index", 2) == 2 for e, s in pairs if s is source)
                or not any(e["quote"] == "お問い合わせ内容 必須 会社情報 IR その他" for e, s in pairs if s is source)
                or not any(e["quote"] == intro for e, s in pairs if s is source)):
            return False
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["aform-field-1-1", "aform-field-2", "aform-field-209", "aform-field-209"]
        names += ["aform-field-" + str(n) + "-" + str(i) for n, count in ((3, 6), (4, 4), (5, 3), (6, 5)) for i in range(1, count + 1)]
        names += ["aform-field-7", "aform-field-87", "aform-field-88", "aform-field-8", "aform-field-26-1", "aform-field-26-2", "aform-field-89", None]
        names += ["aform-field-" + str(i) for i in range(9, 23)] + ["aform-field-22-confirm", "aform-field-23", "aform-field-24", "Submit"]
        if ([c.get("name") for c in controls] != names
                or controls[0].get("tag") != "input" or controls[0].get("type") != "checkbox" or controls[0].get("id") != "parts-1-1"
                or controls[1].get("tag") != "select" or controls[1].get("type") == "hidden" or controls[1].get("id") != "parts-4" or "required" not in controls[1]
                or any(c.get("tag") != "input" or c.get("type") != "checkbox" or c.get("id") != "parts-6-" + str(i)
                       for i, c in enumerate(controls[14:17], 1))
                or [c.get("id") for c in controls[22:26]] != ["parts-8", "parts-29", "parts-28", "parts-9"]
                or any(c.get("tag") != "textarea" or c.get("type") == "hidden" or "required" not in c for c in controls[22:26])
                or any(c.get("tag") != "input" or c.get("type") != "email" or "required" not in c for c in controls[43:45])
                or [c.get("id") for c in controls[43:45]] != ["parts-23", "parts-23-confirm"]
                or controls[47].get("tag") != "input" or controls[47].get("type") != "submit"):
            return False
        issuer = source["title"].removeprefix("お問い合わせ - ")
        return any(self.successful(identity) and identity is not source and urlsplit(identity.get("url", "")).hostname == official_host
                   and ie["quote"] == identity.get("title") == issuer for ie, identity in pairs)

    def reviewed_person_or_corporation_ir_radios(self, record: dict, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Separate the personal/corporate audience from share-holding radios."""
        fields = 'お問い合わせ内容 [必須] 当社の株を保有していますか [必須] 保有している 保有していない 個人 or 法人 [必須] 個人 法人 会社名 お名前 [必須] ふりがな 電話番号 [必須] E-mail [必須] 郵便番号 [必須] ※郵便番号を入力すると、市区町村まで自動反映されます。 住所 差し支えなければ番地、建物名までご入力ください。 お問い合わせのきっかけを教えてください（複数回答可） Web検索 当社配布資料（カタログ・リーフレットなど） 新聞・業界誌・専門誌 YouTube Linkedin X（旧：Twitter） Facebook 展示会・イベント メールマガジン テレビCM 知人・取引先からの紹介 以前から知っていた その他'
        operation = "株式・IR情報に関するお問い合わせフォーム IRに関するご質問をお問い合わせフォームにて受け付けております。下記のフォームに必要事項をご記入のうえ「送信」ボタンを押してください。"
        url = source.get("url", ""); parsed = urlsplit(url); forms = source.get("forms", []); title = source.get("title", "")
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/ja/contact/inquiry/" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or record.get("contact_url") != url or not title.startswith("IRお問い合わせ窓口 – ")
                or len(title.split(" – ")) != 3 or identity_key(title.split(" – ")[1]) != identity_key(record.get("company_name", ""))
                or source.get("headings", []).count("株式・IR情報に関するお問い合わせフォーム") != 1 or len(forms) != 2
                or str(forms[0].get("method", "")).lower() != "get" or question_form(forms[0]) or evidence["quote"] != fields
                or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 1
                or type(evidence.get("form_index", 1)) is not int or evidence.get("form_index", 1) != 1):
            return False
        form = forms[1]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["your-message", "course", "course", "radio-answer", "radio-answer", "company-name", "your-name", "your-name-cana", "your-phonenumber", "your-email", "zip", "pref", "addr1", "addr2"]
        names += ["checkbox-732[]"] * 13 + ["text-239", None, None, None]
        body = source.get("text", ""); local = [e["quote"] for e, s in pairs if s is source]
        if (str(form.get("method", "")).lower() != "post" or not re.fullmatch(r"/ja/contact/inquiry/#wpcf7-f[0-9]+-p[0-9]+-o1", form.get("action", ""))
                or form.get("text") != fields or body.count(fields) != 1 or title not in local or operation not in local or body.count(operation) != 1
                or body.index(operation) >= body.index(fields) or [c.get("name") for c in controls] != names
                or controls[0].get("tag") != "textarea" or controls[0].get("type") == "hidden"
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[1:5])
                or controls[5].get("tag") != "input" or controls[5].get("type") != "text"
                or controls[9].get("tag") != "input" or controls[9].get("type") != "email"
                or re.search(r"個人(?:の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", body[body.index(operation):body.index(fields) + len(fields)])):
            return False
        return True

    def reviewed_personal_company_label_ir_form(self, record: dict, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The company/organization/person label names this native IR input."""
        fields = 'お名前 ふりがな 会社・団体名・個人 部署 郵便番号（半角数字） ご住所 番地・ビル・マンション名 電話番号 メールアドレス メールアドレス確認 ご質問・お問い合わせ 個人情報のお取り扱いに関する規約はこちらをクリックしてください。 確認画面へ'
        intro = "IRに関するお問い合わせは以下のフォーマットにてご連絡ください。"
        url = source.get("url", ""); parsed = urlsplit(url); title = source.get("title", ""); prefix = "IRのお問い合わせ（株主様、投資家様用）｜お問い合わせ｜"
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/contact/ir/" or parsed.query or parsed.fragment
                or source.get("requested_url") != "https://" + official_host + "/contact-ir/" or record.get("contact_url") != url or not title.startswith(prefix)
                or identity_key(title.removeprefix(prefix)) != identity_key(record.get("company_name", ""))
                or source.get("headings", []).count("IRのお問い合わせ（株主様、投資家様用）") != 1 or len(source.get("forms", [])) != 1
                or evidence["quote"] != fields or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 0
                or type(evidence.get("form_index", 0)) is not int or evidence.get("form_index", 0) != 0):
            return False
        redirects = source.get("redirects", []); requested = source["requested_url"]
        if (len(redirects) != 1 or redirects[0].get("requested_url") != requested or redirects[0].get("url") != requested
                or redirects[0].get("http_status") != 301 or redirects[0].get("redirect_target") != url
                or not aware_time(redirects[0].get("retrieved_at"))):
            return False
        form = source["forms"][0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["お名前", "ふりがな", "会社・団体名・個人", "部署", "郵便番号", "ご住所", "番地・ビル・マンション名", "電話番号", "メールアドレス", "メールアドレス確認", "ご質問・お問い合わせ"]
        body = source.get("text", ""); local = [e["quote"] for e, s in pairs if s is source]
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != url + "submit/" or form.get("text") != fields
                or body.count(fields) != 1 or title not in local or not any(q.startswith(intro) for q in local) or body.count(intro) != 1
                or body.index(intro) >= body.index(fields) or [c.get("name") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:7])
                or controls[7].get("tag") != "input" or controls[7].get("type") != "tel"
                or any(c.get("tag") != "input" or c.get("type") != "email" for c in controls[8:10])
                or controls[10].get("tag") != "textarea" or controls[10].get("type") == "hidden"
                or re.search(r"個人(?:の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", body[body.index(intro):body.index(fields) + len(fields)])):
            return False
        return True

    def reviewed_financial_faq_native_id_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """An explicit financial FAQ operation binds the saved unnamed JS form."""
        fields = 'お問い合わせ内容をお選びください 採用（新卒） その他の採用 テクノセンタ その他 【必須】 「お問い合わせ内容」は選択願います。 お問い合わせ内容 【必須】 全角1,000文字以内でご入力ください。 「お問い合わせ内容」は入力必須項目ですので、必ずご記入願います。 お名前 【必須】 「お名前」は入力必須項目ですので、必ずご記入願います。 メールアドレス 【必須】 「メールアドレス」は入力必須項目ですので、必ずご記入願います。 「E-mailアドレス」は正しくご記入願います。 会社・団体・学校名 【必須】 個人の方は“個人”とご入力ください。 「会社・団体・学校名」は入力必須項目ですので、必ずご記入願います。 所属部署名 役職 郵便番号／住所 郵便番号 都道府県 【必須】 「都道府県」は入力必須項目ですので、必ずご記入願います。 ご住所 電話番号 電話番号を入力頂いた場合は、必要に応じて担当部門より連絡させていただくことがございます。ご了承のうえでご入力ください。 ホームページURL お問い合わせにあたっての注意事項 ●お問い合わせいただいた内容すべてには回答できない場合があるので予めご了承願います。 ●セールスや誹謗中傷、アンケート、各種調査、寄付などのご依頼、当社グループとは直接関係のない内容に関するお問い合わせ・ご意見・ご要望の場合には個別の回答を差し上げておりません。 ●お問い合わせの内容によっては、ご回答に日数・時間を要する場合がございます。 ●お客さまからご提供いただいた情報は、お問い合わせに対し適切な回答をするために、当社のグループ会社へ開示することがありますので、予めご了承ください。また、グループ会社から回答させていただく場合があります。 ●本ページでは、クッキー（Cookie）を使用しています。クッキーとは、ウェブページを利用したときに、入力した情報などをお客さまがお使いのコンピュータに一時的に保存させる仕組みです。クッキーの詳細については、当社「 ご利用上の注意 」をご確認ください。 ●公正な研究活動に関するお問い合わせ窓口はこのフォームになります。 個人情報の取り扱いについて ●ご入力いただきました個人情報は当社採用業務にのみ利用させていただき、他の第三者には一切、提供いたしません。 ●ご入力いただきましたお客さまの個人情報は、当社「個人情報保護への取り組み」に基づいて厳重に管理いたします。 ●このページのお問い合わせフォームは個人情報保護のため、SSL(Secure Socket Layer)暗号化通信に対応しています。 ●お客さまへの回答内容を一部または全部の転載、二次利用することは ご遠慮ください。 > 個人情報保護への取り組み 上記事項に同意いただける方は、チェックボックスにチェックを入れ、「入力内容を確認する」をクリックしてください。 同意する 認証して下さい。 入力内容を確認する'
        route = "わからないことがあった場合、どこに問い合わせればいいですか。 お問い合わせからお問い合わせいただけます。 お問い合わせ"
        url = source.get("url", ""); parsed = urlsplit(url); forms = source.get("forms", []); body = source.get("text", "")
        if (not official_host or parsed.scheme != "https" or parsed.hostname != official_host or parsed.path != "/ja/inquiry" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or source.get("submitted") is not False or len(forms) != 2 or forms[1] is not form
                or forms[0].get("method") != "GET" or forms[0].get("action") != "/ja/search" or question_form(forms[0])
                or form.get("method") != "" or form.get("action") != "" or form.get("text") != fields or body.count(fields) != 1
                or not any(e["quote"] == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 1
                           and type(e.get("form_index", 1)) is int and e.get("form_index", 1) == 1 for e, s in pairs if s is source)
                or not any(e["quote"] == source.get("title") for e, s in pairs if s is source)):
            return False
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        ids = ["contactus_type", "contactus_text", "contactus_name", "contactus_mail", "contactus_comp", "contactus_dept", "contactus_pos", "contactus_pin", "contactus_con", "contactus_add", "contactus_tel", "contactus_url", "contactus_agree"]
        if ([c.get("id") for c in controls] != ids or any(c.get("name") != "" for c in controls)
                or controls[0].get("tag") != "select" or controls[0].get("type") == "hidden"
                or controls[1].get("tag") != "textarea" or controls[1].get("type") == "hidden"
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[2:12])
                or controls[12].get("tag") != "input" or controls[12].get("type") != "checkbox"):
            return False
        for pe, parent in pairs:
            pp = urlsplit(parent.get("url", "")); title = parent.get("title", ""); prefix = "よくあるご質問｜株主・投資家情報｜"
            if (parent is source or not self.successful(parent) or pp.scheme != "https" or pp.hostname != official_host or pp.path != "/ja/ir/faq" or pp.query or pp.fragment
                    or parent.get("requested_url") != parent.get("url") or not title.startswith(prefix)
                    or source.get("title") != "お問い合わせ｜" + title.removeprefix(prefix)
                    or "決算・財務関連" not in parent.get("headings", []) or "株式" not in parent.get("headings", [])
                    or pe["quote"] != route or pe.get("source_link_url") != url or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 42):
                continue
            links = parent.get("links", []); local = [e["quote"] for e, s in pairs if s is parent]
            if (len(links) <= 42 or links[42] != {"url": url, "href": url, "label": "お問い合わせ"} or title not in local
                    or not any(q.endswith(route) and "決算・財務関連" in q and "配当方針について教えてください。" in q
                               and "株式の投資単位は何株ですか。" in q and parent.get("text", "").count(q) == 1 for q in local)):
                continue
            return True
        return False

    def reviewed_ir_quoted_company_person_entry(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Bind the curly-quoted personal company entry to this complete IR form."""
        instruction = "個人で問い合わせの際は、法人名に“個人”とご入力ください。"
        url = source.get("url", ""); parsed = urlsplit(url); title = source.get("title", "")
        prefix = "株式・IRに関するお問い合せ｜"
        if (not official_host or evidence["quote"] != instruction or parsed.hostname != official_host or parsed.query or parsed.fragment
                or parsed.scheme != "https" or parsed.path != "/contact_ir/"
                or source.get("requested_url") != url or not title.startswith(prefix) or len(source.get("forms", [])) != 1
                or source.get("headings", []).count("CONTACT 株式・IRに関するお問い合せ") != 1):
            return False
        issuer = title.removeprefix(prefix); form = source["forms"][0]; fields = form.get("text", "").strip()
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]; local = [e["quote"] for e, p in pairs if p is source]
        ending = ("文面に「http://」「https://」「www」を含めることはできません。 株主様平等の原則に則り、お問い合わせ内容によっては個別にお応えしかねる場合もありますので "
                  "予めご了承を戴きたくお願い申し上げます。 改姓、住所変更、配当金受取口座の指定、単元未満株式の買取・買増等に関しましては、 "
                  "株主名簿管理人である三井住友信託銀行にご連絡をお願いいたします。 株式情報｜IR情報｜" + issuer + " (" + official_host.removeprefix("www.") + ") 入力が終わりましたら『確認』ボタンを押してください。")
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != "/contact_ir/" or not question_form(form)
                or not fields.startswith("お名前 ※ (全角) ふりがな ※ (全角) 法人名 ※ (全角) " + instruction + " Eメールアドレス ※ (半角) Eメールアドレス(確認用) ※ (半角) ")
                or not fields.endswith(ending) or "市区町村番地 (全角) お問い合わせ内容を お書きください。 ※ " not in fields
                or title not in local or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["fullname", "kana", "company", "mail", "mail2", "tel", "fax", "zipcode1", "zipcode2", "pref", "address", "content", "submit", "reset"]
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (0, 1, 2, 5, 6, 7, 8, 10))
                or any(c.get("tag") != "input" or c.get("type") != "email" for c in controls[3:5])
                or controls[9].get("tag") != "select" or controls[9].get("type") == "hidden"
                or controls[11].get("tag") != "textarea" or controls[11].get("type") == "hidden"
                or controls[12].get("tag") != "input" or controls[12].get("type") != "submit"
                or controls[13].get("tag") != "input" or controls[13].get("type") != "reset"
                or any("required" not in controls[i] for i in (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11))
                or re.search(r"個人(?:の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", fields)):
            return False
        for pe, parent in pairs:
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or urlsplit(parent.get("url", "")).scheme != "https" or urlsplit(parent.get("url", "")).path != "/contact/"
                    or urlsplit(parent.get("url", "")).query or urlsplit(parent.get("url", "")).fragment
                    or parent.get("requested_url") != parent.get("url") or parent.get("title") != "お問い合わせ｜" + issuer
                    or pe["quote"] != "株式・IRに関するお問い合せ" or pe.get("source_link_url") != url or pe.get("source_link_href") != "../contact_ir/"
                    or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 75):
                continue
            links = parent.get("links", [])
            if (len(links) <= 75 or not isinstance(links[75], dict) or links[75].get("label") != pe["quote"]
                    or links[75].get("url") != url or links[75].get("href") != pe["source_link_href"]):
                continue
            if any(financial is not source and financial is not parent and self.successful(financial)
                   and urlsplit(financial.get("url", "")).hostname == official_host and financial.get("requested_url") == financial.get("url")
                   and urlsplit(financial.get("url", "")).scheme == "https" and urlsplit(financial.get("url", "")).path == "/ir/"
                   and not urlsplit(financial.get("url", "")).query and not urlsplit(financial.get("url", "")).fragment
                   and fe["quote"] == financial.get("title") == "IR情報｜" + issuer and "IR INFORMATION IR情報" in financial.get("headings", [])
                   and "IR INFORMATION IR情報 HOME IR情報 IR ニュース VIEW MORE IR カレンダー" in financial.get("text", "")
                   and "決算発表" in financial.get("text", "") and "定時株主総会" in financial.get("text", "")
                   and any(link.get("url") == parent.get("url") and link.get("href") == "/contact/" and link.get("label") == "お問い合わせ"
                           for link in financial.get("links", []) if isinstance(link, dict)) for fe, financial in pairs):
                return True
        return False

    def reviewed_numeric_ir_audience_iframe(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The first opaque selector's investor choices belong to this IR iframe."""
        fields = ("種別 個人投資家 アナリスト・機関投資家 報道機関 その他 社名 部署名 役職名 名前 お名前（名） "
                  "メールアドレス 電話番号 お問い合わせ内容 プライバシーポリシー について同意する 同意する Comments 送信")
        instruction = ("IRお問い合わせフォーム 必要事項をご入力の上、「送信」ボタンを押してください。 ※ 必須マークの項目は必ずご入力または選択してください。 "
                       "※ 送信いただく前に「 プライバシーポリシー 新規ウィンドウを開きます 」をご一読いただき、ご同意の上送信してください。")
        url = source.get("url", ""); parsed = urlsplit(url)
        account = re.fullmatch(r"/l/([0-9]+)/[0-9]{4}-[0-9]{2}-[0-9]{2}/[A-Za-z0-9]+", parsed.path)
        if (not official_host or parsed.hostname != "go." + official_host.removeprefix("www.") or not account or parsed.query or parsed.fragment
                or source.get("requested_url") != url or evidence["quote"].strip() != fields
                or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 0
                or type(evidence.get("form_index", 0)) is not int or evidence.get("form_index", 0) != 0
                or len(source.get("forms", [])) != 1 or source.get("text", "").count(fields) != 1):
            return False
        form = source["forms"][0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        keys = ["411123", "411096", "411099", "411102", "411105", "411108", "411111", "411114", "411117", "411120"]
        names = [account[1] + "_" + key + "pi_" + account[1] + "_" + key for key in keys]
        names[-1] += "_3919341"; names.append("pi_extra_field")
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != url or not reviewed_question_form(form)
                or form.get("text", "").strip() != fields or [c.get("name") for c in controls] != names
                or [c.get("id") for c in controls] != names
                or controls[0].get("tag") != "select" or controls[0].get("type") == "hidden"
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[1:8])
                or controls[8].get("tag") != "textarea" or controls[8].get("type") == "hidden"
                or controls[9].get("tag") != "input" or controls[9].get("type") != "checkbox"
                or controls[10].get("tag") != "input" or controls[10].get("type") != "text"):
            return False
        for pe, parent in pairs:
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or parent.get("requested_url") != parent.get("url") or pe["quote"] != instruction or pe.get("source_link_url") != url
                    or not parent.get("title", "").startswith("IRお問い合わせフォーム | ")
                    or parent.get("headings", []).count("IRお問い合わせフォーム") != 1 or parent.get("text", "").count(instruction) != 1
                    or not any(e["quote"] == parent["title"] for e, p in pairs if p is parent)):
                continue
            if sum(link.get("url") == url and link.get("src") == url and link.get("label") == "embedded frame"
                   for link in parent.get("links", []) if isinstance(link, dict)) == 1:
                return True
        return False

    def reviewed_ir_trigger_personal_selector(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The usage-origin prompt classifies the same explicit IR question form."""
        choice = "ご利用のきっかけ —以下から選択してください— 機関 個人 報道・取材 その他"
        intro = "こちらのページではIRに関するお問い合わせ・ご質問を、お問い合わせフォームにより受け付けております。"
        fields = (intro + " なお、こちらのフォームからの営業・商談・営利⽬的の送信はお断りいたします。 ※必須項⽬は全てご記⼊ください。 "
                  "お名前 必須 役職 部署名 会社名 郵便番号 必須 住所自動入力 （郵便番号を半⾓数字でご記⼊ください） 住所 必須 都道府県 住所 ビル名 "
                  "メールアドレス 必須 電話番号 （半⾓数字） FAX （半⾓数字） " + choice + " ご質問内容 必須 個人情報の取扱いについて の内容に同意する 送信する Δ")
        url = source.get("url", ""); parsed = urlsplit(url)
        if (not official_host or evidence["quote"] != choice or parsed.hostname != official_host or parsed.query or parsed.fragment
                or source.get("requested_url") != url or len(source.get("forms", [])) != 1
                or not source.get("title", "").startswith("IRについてのお問い合わせ - ")
                or "CONTACT IRについてのお問い合わせ" not in source.get("headings", [])):
            return False
        form = source["forms"][0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local = [e["quote"] for e, p in pairs if p is source]; action = urlsplit(urljoin(url, form.get("action") or ""))
        if (str(form.get("method", "")).lower() != "post" or not question_form(form) or form.get("text", "").strip() != fields
                or action._replace(fragment="").geturl() != url or not re.fullmatch(r"wpcf7-f[0-9]+-p[0-9]+-o1", action.fragment)
                or source.get("text", "").count(fields) != 1 or source["title"] not in local or intro not in local
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["c_name", "c_position", "c_department", "c_company", "c_postal", "c_prefecture", "c_address", "c_address_2", "c_email", "c_tel", "c_fax", "c_trigger", "c_message", "policy", "_wpcf7_ak_hp_textarea"]
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:8] + controls[10:11])
                or controls[8].get("tag") != "input" or controls[8].get("type") != "email"
                or controls[9].get("tag") != "input" or controls[9].get("type") != "tel"
                or controls[11].get("tag") != "select" or controls[11].get("type") == "hidden"
                or controls[12].get("tag") != "textarea" or controls[12].get("type") == "hidden"
                or controls[13].get("tag") != "input" or controls[13].get("type") != "checkbox"
                or controls[14].get("tag") != "textarea" or controls[14].get("type") == "hidden"):
            return False
        for pe, parent in pairs:
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or pe["quote"] != "IRについてのお問い合わせ" or pe.get("source_link_url") != url
                    or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 36):
                continue
            links = parent.get("links", [])
            if len(links) > 36 and isinstance(links[36], dict) and links[36].get("label") == pe["quote"] and links[36].get("url") == url and links[36].get("href") == url:
                return True
        return False

    def reviewed_native_category_financial_primary(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """This native IR category agrees with the same issuer's financial releases."""
        fields = ("カテゴリー ※ コレットチャック・ガイドブッシュ等に関するお問い合わせ 刃物（製作・再研磨）に関するお問い合わせ "
                  "自動旋盤用カムに関するお問い合わせ 請求に関するお問い合わせ IR関連 その他 送信する")
        primary = ("IR情報 IR情報 IR情報トップ 日付 タイプ イベント ダウンロード 2026.10.08 お知らせ 自己株式の処分に関する取締役会決議公告 "
                   "2026.09.28 報告書 第36期 有価証券報告書 2026.09.28 その他 第36期 コーポレート・ガバナンス報告書 "
                   "2026.09.03 株主総会 第36期定時株主総会招集ご通知 2026.09.03 株主総会 第36期定時株主総会その他の電子提供措置事項（交付書面省略事項） "
                   "2026.08.31 決算 2026年6月期 決算説明会要旨 2026.08.25 決算 2026年6月期 決算説明会資料 2026.08.10 短信 2026年6月期 決算短信〔日本基準〕（非連結）")
        url = source.get("url", ""); parsed = urlsplit(url); forms = source.get("forms", [])
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local = [e["quote"] for e, p in pairs if p is source]
        if (not official_host or parsed.hostname != official_host or parsed.query or parsed.fragment or source.get("requested_url") != url
                or len(forms) != 2 or forms[0] is not form or forms[1].get("method") != "get" or forms[1].get("controls") != []
                or str(form.get("method", "")).lower() != "post" or form.get("action") != "submit.php" or not question_form(form)
                or form.get("text", "").strip() != fields or source.get("text", "").count(fields) != 1 or "お客様情報入力 ※ 「必須」 項目は必ずご入力ください。" not in local
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or not any(e["quote"] == "会社名 ※" and e.get("field_path") == "forms.0.controls.0.placeholder"
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 and public_attribute_quote(e, source) for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["company_name", "name", "phone", "fax", "email", "category", "message"]
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != kind for i, kind in ((0, "text"), (1, "text"), (2, "tel"), (3, "tel"), (4, "email")))
                or controls[5].get("tag") != "select" or controls[5].get("type") == "hidden"
                or controls[6].get("tag") != "textarea" or controls[6].get("type") == "hidden"
                or any("required" not in controls[i] for i in (0, 1, 2, 4, 5, 6))
                or controls[4].get("placeholder") != "メールアドレス ※" or controls[6].get("placeholder") != "お問い合わせ内容 ※"
                or re.search(r"(?:IR|投資家)[^。]{0,35}(?:電話のみ|フォームでは受け付けません|対象外)", source.get("text", ""), re.I)):
            return False
        identities = {q for q in local if re.fullmatch(r"証券コード: [0-9A-Z]{4} 株式会社.{2,60}", q)}
        return any(parent is not source and self.successful(parent) and urlsplit(parent.get("url", "")).hostname == official_host
                   and parent.get("requested_url") == parent.get("url") and parent.get("title") == source.get("title")
                   and pe["quote"] == primary and parent.get("text", "").count(primary) == 1
                   and any(e["quote"] in identities for e, p in pairs if p is parent)
                   for pe, parent in pairs)

    def reviewed_native_ir_occupation(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """These occupation choices belong to the native shareholder/IR category."""
        choice = "ご職業 個人投資家 機関投資家 アナリスト その他"
        fields = ("お名前 フリガナ お電話番号 E-mail お問い合わせ種類 株主様・ IRに関すること 広報・マーケティングに関すること "
                  "ＩＴ・セキュリティに関すること 採用に関すること その他 " + choice + " 本文： 記入内容に問題がなければ「確認する」ボタンを押してください。 確認する")
        url = source.get("url", ""); parsed = urlsplit(url)
        if (not official_host or evidence["quote"] != choice or parsed.hostname != official_host or parsed.query or parsed.fragment
                or source.get("requested_url") != url or len(source.get("forms", [])) != 1 or "お問い合わせフォーム" not in source.get("headings", [])):
            return False
        form = source["forms"][0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != url + "MODE=CONFIRM#inquiry1" or not question_form(form)
                or form.get("text", "").strip() != fields or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["name", "ext_01", "ext_02", "from_mail", "from_mail2", "inquiry_category_id", "ext_05", "ext_04"]
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:5])
                or controls[3].get("placeholder") != "※メールアドレス（半角英数字）" or controls[4].get("placeholder") != "※メールアドレス（確認用）"
                or any(c.get("tag") != "select" or c.get("type") == "hidden" for c in controls[5:7])
                or controls[7].get("tag") != "textarea" or controls[7].get("type") == "hidden"):
            return False
        return any(self.successful(parent) and urlsplit(parent.get("url", "")).hostname == official_host
                   and re.fullmatch(r"株式会社.{2,60}", e["quote"]) and source.get("title") == "お問い合わせ｜" + e["quote"]
                   and e["quote"] in source.get("headings", []) for e, parent in pairs)

    def reviewed_sf_ir_personal_radios(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The optional company instruction agrees with native IR audience radios."""
        choice = "任意 該当する項目をご選択ください 株主（当社株式をお持ちの方） 個人投資家 機関投資家 アナリスト・プレス その他"
        heading = "CONTACT - IR IR・株式に関するお問い合わせ 弊社株主、投資家の皆様からの お問い合わせはこちらよりお願いします"
        fields = ("必須 お名前 任意 会社名 必須 メールアドレス 任意 電話番号 " + choice + " 必須 お問い合わせ内容の詳細 お問い合わせ内容をご入力ください "
                  "プライバシーポリシーへの同意 同意する お問い合わせには、 個人情報の取扱いについて への同意が必要です。 全てに同意の上、 入力内容を確認 修正する")
        directive = "Q.IR関連のお問い合わせ先を教えてください。 A. お問い合せフォーム にて受け付けております。"
        url = source.get("url", ""); parsed = urlsplit(url)
        if (not official_host or evidence["quote"] != choice or parsed.hostname != official_host or parsed.query or parsed.fragment
                or source.get("requested_url") != url or len(source.get("forms", [])) != 1 or source.get("headings", []).count("CONTACT - IR") != 1):
            return False
        form = source["forms"][0]; controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local = [e["quote"] for e, p in pairs if p is source]
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != "submit.php" or not question_form(form)
                or form.get("text", "").strip() != fields or source.get("text", "").count(fields) != 1 or heading not in local
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or not any(e["quote"] == "個人の方は空欄のままで結構です" and e.get("field_path") == "forms.0.controls.1.placeholder"
                           and type(e.get("source_form_index")) is int and e["source_form_index"] == 0 and public_attribute_quote(e, source) for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["sf_Name__c", "sf_KaishaMei__c", "sf_Email__c", "sf_Tel__c"] + ["sf_ContakutUsRadio__c"] * 5 + ["sf_OtoiawaseNiyou__c", "sf_KojinJouhou__c", "sf_save2"]
                or any(c.get("tag") != "input" or c.get("type") != "text" or c.get("id") != c.get("name") for c in controls[:4])
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[4:9])
                or controls[9].get("tag") != "textarea" or controls[9].get("type") == "hidden" or controls[9].get("id") != controls[9].get("name")
                or controls[10].get("tag") != "input" or controls[10].get("type") != "checkbox" or controls[10].get("id") != controls[10].get("name")
                or controls[11].get("tag") != "input" or controls[11].get("type") != "submit" or controls[11].get("id") != "sf_save"):
            return False
        return any(parent is not source and self.successful(parent) and urlsplit(parent.get("url", "")).hostname == official_host
                   and parent.get("title") == "IR | " + source.get("title", "").removeprefix("CONTACT | ")
                   and all(h in parent.get("headings", []) for h in ("FAQ よくあるご質問", "Q.証券コードを教えてください。", "Q.決算発表はいつですか？", "Q.IR関連のお問い合わせ先を教えてください。"))
                   and pe["quote"] == directive and pe.get("source_link_url") == url
                   and sum(link.get("label") == "お問い合せフォーム" and link.get("url") == url and link.get("href") == url
                           for link in parent.get("links", []) if isinstance(link, dict)) == 1 for pe, parent in pairs)

    def reviewed_ir_company_person_name_placeholder(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """This IR form's public company placeholder gives personal name entry."""
        url = source.get("url", ""); parsed = urlsplit(url)
        title = source.get("title", "")
        if (not official_host or evidence["quote"] != "個人のお客様におかれましては、氏名をご入力ください。"
                or evidence.get("field_path") != "forms.0.controls.0.placeholder"
                or type(evidence.get("source_form_index")) is not int or evidence["source_form_index"] != 0
                or type(evidence.get("form_index", 0)) is not int or evidence.get("form_index", 0) != 0
                or not public_attribute_quote(evidence, source)
                or not re.fullmatch(r"reg[0-9]+[.]smp[.]ne[.]jp", parsed.hostname or "")
                or parsed.path != "/regist/is" or not re.fullmatch(r"SMPFORM=[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", parsed.query) or parsed.fragment
                or source.get("requested_url") != url or len(source.get("forms", [])) != 1
                or not title.startswith("IRに関するお問い合わせ｜お問い合わせ｜")
                or source.get("headings", []).count("IRに関する お問い合わせ") != 1):
            return False
        form = source["forms"][0]; fields = form.get("text", "").strip()
        local = [e["quote"] for e, p in pairs if p is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["company", "name", "nameKana", "department", "post", "zipCode:a", "zipCode:t", "address", "phone", "email", "email:cf", "inquiry", "which", "which", "doui"]
        if (str(form.get("method", "")).lower() != "post" or form.get("action") != "/regist/Reg2" or not question_form(form)
                or not fields.startswith("企業・団体名 必須 ご担当者名 必須 ご担当者名（フリガナ） 部署名 役職 郵便番号 必須 ")
                or not fields.endswith("個人情報の取扱いについて同意する 入力内容を確認する")
                or "メールアドレス 必須 メールアドレス（確認） 必須 お問い合わせ内容 必須 ※1,000文字以内 ご希望の連絡方法 必須" not in fields
                or title not in local or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:9])
                or any(c.get("tag") != "input" or c.get("type") != "email" for c in controls[9:11])
                or controls[11].get("tag") != "textarea" or controls[11].get("type") == "hidden"
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[12:14])
                or [c.get("id") for c in controls[12:14]] != ["contact-tel", "contact-mail"]
                or controls[14].get("tag") != "input" or controls[14].get("type") != "checkbox"
                or re.search(r"個人(?:のお客様|の方|投資家)?[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", fields)):
            return False
        return any(parent is not source and self.successful(parent) and urlsplit(parent.get("url", "")).hostname == official_host
                   and parent.get("title") == "お問い合わせ｜" + title.split("｜お問い合わせ｜", 1)[1]
                   and pe["quote"] == "IRに関するお問い合わせ" and pe.get("source_link_url") == url
                   and sum(link.get("label") == pe["quote"] and link.get("url") == url and link.get("href") == url
                           for link in parent.get("links", []) if isinstance(link, dict)) == 1 for pe, parent in pairs)

    def reviewed_native_issuer_investment_radios(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The separate native investment category agrees with the issuer's IR."""
        purpose = ("お問い合わせ種類 必須 一般的なお問い合わせ 投資に関するお問い合わせ 採用に関するお問い合わせ 舶用製品に関するお問い合わせ "
                   "舶用製品のアフターサービスに関するお問合せ 鋳造品・機械加工品・開発品に関するお問い合わせ ネフロンシステムに関するお問い合わせ")
        scope = "社長メッセージ 株主・投資家の皆様におかれましては日頃より事業活動にご理解、ご支援を賜り厚く御礼申し上げます。"
        fields = form.get("text", "").strip(); local = [e["quote"] for e, p in pairs if p is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        url = source.get("url", ""); parsed = urlsplit(url); title = source.get("title", "")
        names = ["type"] * 7 + ["題名", "会社名", "部署名", "お名前"]
        names += [kind + "[data][" + str(i) + "]" for kind in ("電話番号", "FAX番号") for i in range(3)]
        names += ["メールアドレス", "メールアドレス確認", "ご質問内容", "送信確認[data][]", "submitConfirm"]
        forbidden = re.compile(r"(?:投資|IR)(?:に関する)?(?:お問い合わせ|ご質問)[^。]{0,35}(?:電話のみ|フォームでは受け付けません|対象外)", re.I)
        if (not official_host or parsed.hostname != official_host or parsed.query or parsed.fragment or source.get("requested_url") != url
                or not title.endswith(" | お問い合わせ") or source.get("forms") != [form]
                or str(form.get("method", "")).lower() != "post" or form.get("action") != "" or not question_form(form)
                or fields != purpose + " 題名 必須 会社名 部署名 お名前 必須 電話番号 - - FAX番号 - - メールアドレス 必須 メールアドレス確認 必須 ご質問内容 送信確認 必須 ※入力内容を確認したらチェックを入れてください。 送信する"
                or purpose not in local or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index", 0)) is int and e.get("source_form_index", 0) == 0
                           and type(e.get("form_index", 0)) is int and e.get("form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[:7])
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[7:19])
                or controls[19].get("tag") != "textarea" or controls[19].get("type") == "hidden"
                or controls[20].get("tag") != "input" or controls[20].get("type") != "checkbox"
                or controls[21].get("tag") != "input" or controls[21].get("type") != "submit" or forbidden.search(source.get("text", ""))):
            return False
        for evidence, parent in pairs:
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or parent.get("title") != title.removesuffix(" | お問い合わせ") + " | 社長メッセージ"
                    or "IR情報 社長メッセージ IR information" not in parent.get("headings", [])
                    or evidence["quote"] != scope or parent.get("text", "").count(scope) != 1
                    or not any(pe["quote"] == parent["title"] for pe, p in pairs if p is parent)
                    or forbidden.search(parent.get("text", ""))):
                continue
            if any(pe["quote"] == "お問い合わせ" and pe.get("source_link_url") == url
                   and any(link.get("label") == pe["quote"] and link.get("url") == url and link.get("href") == url
                           for link in parent.get("links", []) if isinstance(link, dict)) for pe, p in pairs if p is parent):
                return True
        return False

    def reviewed_bilingual_ir_investor_selector(self, evidence: dict, source: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Bind these literal bilingual investor choices to the native IR form."""
        choice = "区分 必須 Category 個人投資家（Individual investor) 機関投資家（Institutional investor） アナリスト（Analyst） その他（Other）"
        policy = ("お問い合わせの内容などにより、お返事に日時を頂戴する場合がございます。 また以下項目についてはご回答しかねますので、ご了解いただけますようお願い申し上げます。 "
                  "開示されていない未公表情報に関するお問い合わせ 金融商品取引法第166条に定める「重要事実」に該当する可能性のあるお問い合わせ "
                  "株式市場における株価動向や値動き等に関するお問い合わせ IR活動以外（営業・勧誘等）に関するお問い合わせ")
        url = source.get("url", ""); parsed = urlsplit(url)
        if (not official_host or evidence["quote"] != choice or parsed.hostname != official_host or parsed.query or parsed.fragment
                or source.get("requested_url") != url or len(source.get("forms", [])) != 1
                or not source.get("title", "").startswith("IR活動についてのお問い合わせ | ")
                or source.get("headings", []).count("IR活動についてのお問い合わせ") != 1):
            return False
        form = source["forms"][0]; fields = form.get("text", "").strip()
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        local = [e["quote"] for e, p in pairs if p is source]
        action = urlsplit(urljoin(url, form.get("action") or ""))
        if (str(form.get("method", "")).lower() != "post" or not question_form(form)
                or action._replace(fragment="").geturl() != url or not re.fullmatch(r"wpcf7-f[0-9]+-o2", action.fragment)
                or not fields.startswith(policy + " お名前（姓） 必須 Last Name お名前（名） 必須 First Name " + choice + " ")
                or "会社・団体名 Company Name 部署名 Department メールアドレス 必須 Email Address お問い合わせ内容 必須 Inquiry Details 当社個人情報保護方針" not in fields
                or not fields.endswith("* Information regarding the handling of personal information is provided in this website’s Privacy Policy .")
                or source.get("text", "").count(fields) != 1 or source["title"] not in local or policy not in local
                or not any(e["quote"].strip() == fields and type(e.get("form_index")) is int and e["form_index"] == 0
                           and type(e.get("source_form_index", 0)) is int and e.get("source_form_index", 0) == 0 for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != ["last-name", "first-name", "category", "company", "dept", "email", "message", None]
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:2] + controls[3:5])
                or controls[2].get("tag") != "select" or controls[2].get("type") == "hidden"
                or controls[5].get("tag") != "input" or controls[5].get("type") != "email"
                or controls[6].get("tag") != "textarea" or controls[6].get("type") == "hidden"
                or controls[7].get("tag") != "input" or controls[7].get("type") != "submit"
                or re.search(r"個人投資家[^。]{0,35}(?:対象外|お断り|受け付けません|ご遠慮)", fields)):
            return False
        for pe, parent in pairs:
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or parent.get("title") != "投資家情報" or "IR 投資家情報" not in parent.get("headings", [])
                    or "株主・投資家の皆様へ" not in parent.get("headings", [])
                    or pe["quote"] != "IR問い合わせフォーム" or pe.get("source_link_url") != url
                    or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 87):
                continue
            links = parent.get("links", [])
            if len(links) > 87 and isinstance(links[87], dict) and links[87].get("label") == pe["quote"] and links[87].get("href") == url and links[87].get("url") == url:
                return True
        return False

    def reviewed_financial_faq_external_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """An unpublished-question instruction in a financial FAQ names this form."""
        operation = ("その他の質問 掲載されていないお問い合わせは、どちらにすればよいでしょうか？ "
                     "このホームページ内の お問い合わせ のページからご連絡ください。")
        breadcrumb = "TOP > 株主・投資家情報 > よくあるご質問"
        prefix = ("氏名 ※ フリガナ ※ 会社・団体など組織名 ※ フリガナ ※ 所属部署名 郵便番号 ※ 住所 ※ "
                  "電話番号 ※ FAX番号 E-mailアドレス ※ お問い合わせ ※ ")
        instruction = ("ご意見・ご質問などがございましたら、 個人情報の取り扱いに関する事項 をご確認の上、メールフォームにご記入していただき、 "
                       "確認画面ボタンを押してお送りください。 ※ は必須項目です。 間違って記入された場合はご連絡できないことがあります。 "
                       "お問い合わせの内容によってはご回答できかねる場合や、営業時間外や休業日にはご回答に時間を要する場合がございますので、予めご了承下さい。 "
                       "（研究活動における不正行為に関するご相談・告発も、こちらで受け付けます。）")
        url = source.get("url", ""); parsed = urlsplit(url)
        fields = form.get("text", "").strip(); local = [e["quote"] for e, p in pairs if p is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["name", "namefurigana", "soshiki", "soshikifurigana", "shozoku", "zip", "address", "tel", "fax", "email", "comment", None, None]
        if (not official_host or not re.fullmatch(r"secure[0-9]+[.]red[.]shared-server[.]net", parsed.hostname or "")
                or parsed.path != "/" + official_host + "/FormMail/otoiawase/FormMail.html" or parsed.query or parsed.fragment
                or source.get("requested_url") != url or source.get("forms") != [form]
                or str(form.get("method", "")).lower() != "post" or form.get("action") != "/" + official_host + "/freecgi/FormMail/index.cgi"
                or not question_form(form) or not fields.startswith(prefix + "送信していただく前に個人情報の取り扱いに関する下記の事項をご確認ください。 ")
                or not fields.endswith("必要事項をご記入いただき、「確認」ボタンを押してください。")
                or source.get("text", "").count(fields) != 1 or instruction not in local
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index", 0)) is int and e.get("source_form_index", 0) == 0
                           for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[:10])
                or controls[10].get("tag") != "textarea" or controls[10].get("type") == "hidden"
                or controls[11].get("tag") != "input" or controls[11].get("type") != "reset"
                or controls[12].get("tag") != "input" or controls[12].get("type") != "submit"):
            return False
        for evidence, parent in pairs:
            links = parent.get("links", [])
            if (parent is source or not self.successful(parent) or urlsplit(parent.get("url", "")).hostname != official_host
                    or not parent.get("title", "").startswith("よくあるご質問｜")
                    or not {"財務・業績に関する質問", "株式に関する質問", "その他の質問"}.issubset(parent.get("headings", []))
                    or evidence["quote"] != operation or evidence.get("source_link_url") != url
                    or type(evidence.get("source_link_index", 9)) is not int or evidence.get("source_link_index", 9) != 9
                    or parent.get("text", "").count(operation) != 1 or len(links) <= 9
                    or not any(pe["quote"] == parent["title"] + " " + breadcrumb for pe, p in pairs if p is parent)):
                continue
            if (links[9].get("label") == "お問い合わせ" and links[9].get("url") == url and links[9].get("href") == url
                    and sum(link.get("url") == url and link.get("href") == url for link in links if isinstance(link, dict)) == 1):
                return True
        return False

    def reviewed_privacy_intro_ir_checkbox_iframe(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The full native checkbox form and raw financial-IR iframe chain agree."""
        intro = ("下記の必要事項にご記入いただき、当社の 個人情報のお取り扱いについて（「個人情報保護宣言」） にご同意の上、送信をお願いいたします。"
                 "折り返し、当社よりご回答申し上げます。 セールスを目的としたお問い合わせについては、回答できないこともございます。 "
                 "あらかじめご了承ください。 *がついている項目は必須項目となります。")
        personal = "貴社名 ※個人の場合は『個人』とご入力ください"
        purpose = "お問い合わせ種別 商品・サービスについて 採用について IRについて その他 お問い合わせ内容"
        policy = ("個人情報のお取り扱いについて 同意する 個人情報のお取り扱いについて（「個人情報保護宣言」）に同意いただける場合は上記チェックボックスにチェックの上、"
                  "フォーム送信してください。なお、お問い合わせの内容によっては、返信に時間がかかる場合や、お答えできない場合があることをご了承ください。 Comments")
        url = source.get("url", ""); parsed = urlsplit(url)
        account = re.fullmatch(r"/l/([0-9]+)/[0-9]{4}-[0-9]{2}-[0-9]{2}/[A-Za-z0-9]+", parsed.path)
        fields = form.get("text", "").strip(); local = [e["quote"] for e, p in pairs if p is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        if (not official_host or parsed.hostname != "contact." + official_host.removeprefix("www.") or not account or parsed.query or parsed.fragment
                or source.get("requested_url") != url or source.get("forms") != [form]
                or str(form.get("method", "")).lower() != "post" or form.get("action") != url
                or not fields.startswith(intro + " 姓 名 メールアドレス 電話番号 ※ハイフンなし " + personal + " 所属部署名 郵便番号 住所：都道府県 ")
                or not fields.endswith("市区町村 住所（その他） " + purpose + " " + policy)
                or source.get("text", "").count(fields) != 1 or personal not in local
                or not any(e["quote"].strip() == fields and type(e.get("form_index")) is int and e["form_index"] == 0
                           and type(e.get("source_form_index", 0)) is int and e.get("source_form_index", 0) == 0
                           for e, p in pairs if p is source)):
            return False
        native = lambda field: account[1] + "_" + field + "pi_" + account[1] + "_" + field
        names = [native(field) for field in ("32129", "32132", "32135", "32138", "32141", "32144", "32147", "32150", "32153", "32156")]
        names += [native("32159") + "_" + choice for choice in ("80753", "80756", "80759", "80762")]
        names += [native("32162"), native("32168") + "_80810", "pi_extra_field", None]
        if ([c.get("name") for c in controls] != names
                or any(c.get("id") != name for c, name in zip(controls[:17], names))
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (*range(7), 8, 9, 16))
                or controls[7].get("tag") != "select" or controls[7].get("type") == "hidden"
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "checkbox" for i in (10, 11, 12, 13, 15))
                or controls[14].get("tag") != "textarea" or controls[14].get("type") == "hidden"
                or controls[17].get("tag") != "input" or controls[17].get("type") != "submit"):
            return False
        for evidence, contact in pairs:
            links = contact.get("links", [])
            if (contact is source or not self.successful(contact) or urlsplit(contact.get("url", "")).hostname != official_host
                    or evidence["quote"] != "お問い合わせ" or evidence.get("source_link_url") != url
                    or type(evidence.get("source_link_index")) is not int or evidence["source_link_index"] != 29 or len(links) <= 29
                    or links[29].get("label") != "embedded frame" or links[29].get("url") != url or links[29].get("src") != url):
                continue
            for pe, parent in pairs:
                parent_links = parent.get("links", [])
                if (parent is source or parent is contact or not self.successful(parent)
                        or urlsplit(parent.get("url", "")).hostname != official_host or not IR_MARKER.search(parent.get("title", ""))
                        or not {"Investor Relations IR情報", "IRニュース"}.issubset(parent.get("headings", []))
                        or "ご質問・お問い合わせ FAQ/Contact よくあるご質問 IRお問い合わせ 株式基本情報 Stock Information" not in parent.get("text", "")
                        or pe["quote"] != "IRお問い合わせ" or pe.get("source_link_url") != contact.get("requested_url")
                        or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 37 or len(parent_links) <= 37):
                    continue
                if (parent_links[37].get("label") == "IRお問い合わせ" and parent_links[37].get("href") == "/contact/"
                        and parent_links[37].get("url") == contact.get("requested_url")
                        and urljoin(parent.get("url", ""), parent_links[37]["href"]) == contact.get("requested_url")):
                    return True
        return False

    def reviewed_opaque_mail_iframe_ir_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """The public Mail prefix, native fields and captured IR iframe chain agree."""
        purpose = ("メール お問い合わせ内容 経理シンギュラリティに関して 製品に関して 決算、開示、IR関連 "
                   "採用人材に関して 報道プレス発表に関して その他")
        fields = form.get("text", "").strip()
        url = source.get("url", "")
        parsed = urlsplit(url)
        account = re.fullmatch(r"/l/([0-9]+)/[0-9]{4}-[0-9]{2}-[0-9]{2}/[A-Za-z0-9]+", parsed.path)
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        if (not official_host or parsed.hostname != "go." + official_host.removeprefix("www.") or not account
                or parsed.query or parsed.fragment or source.get("requested_url") != url or source.get("forms") != [form]
                or str(form.get("method", "")).lower() != "post" or form.get("action") != url
                or not fields.startswith(purpose + " 会社名 部署区分 経営企画・事業企画 ")
                or not fields.endswith("役職 姓 名 電話番号 ご質問・ご相談 Privacy - Terms Comments")
                or source.get("text", "").count(fields) != 1
                or not any(e["quote"] == purpose for e, p in pairs if p is source)
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index")) is int and e["source_form_index"] == 0
                           for e, p in pairs if p is source)):
            return False
        names = [account[1] + "_" + field + "pi_" + account[1] + "_" + field
                 for field in ("87501", "87485", "87487", "198942", "240232", "87493", "240235", "87495", "87497", "87499", "213908")]
        if ([c.get("name") for c in controls] != names + ["pi_extra_field", None]
                or any(c.get("id") != name for c, name in zip(controls[:11], names))
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (0, 2, 4, 6, 7, 8, 9, 11))
                or any(controls[i].get("tag") != "select" or controls[i].get("type") == "hidden" for i in (1, 3, 5))
                or controls[10].get("tag") != "textarea" or controls[10].get("type") == "hidden"
                or controls[11].get("id") != "pi_extra_field" or controls[12].get("tag") != "input" or controls[12].get("type") != "submit"):
            return False
        instruction = ("お問い合わせ サービスに関する詳細や料金プランのご相談、取材・メディア掲載など、気軽にお問い合わせください。 "
                       "個人情報保護方針 をご覧頂き、ご登録いただいた情報の取り扱いについて ご確認、ご同意のうえ、フォームをご送信ください。")
        for evidence, contact in pairs:
            links = contact.get("links", [])
            if (contact is source or not self.successful(contact) or urlsplit(contact.get("url", "")).hostname != official_host
                    or evidence["quote"] != instruction or evidence.get("source_link_url") != url
                    or type(evidence.get("source_link_index")) is not int or evidence["source_link_index"] != 76 or len(links) <= 76
                    or links[76].get("label") != "embedded frame" or links[76].get("url") != url or links[76].get("src") != url
                    or contact.get("text", "").count(instruction) != 1):
                continue
            for pe, parent in pairs:
                parent_links = parent.get("links", [])
                if (parent is contact or parent is source or not self.successful(parent)
                        or urlsplit(parent.get("url", "")).hostname != official_host or not IR_MARKER.search(parent.get("title", ""))
                        or not {"経営情報", "IRライブラリー", "株式について", "その他IR関連リンク"}.issubset(parent.get("headings", []))
                        or pe["quote"] != "IRお問い合わせ" or pe.get("source_link_url") != contact.get("requested_url")
                        or type(pe.get("source_link_index")) is not int or pe["source_link_index"] != 94 or len(parent_links) <= 94):
                    continue
                if (parent_links[94].get("label") == "IRお問い合わせ" and parent_links[94].get("url") == contact.get("requested_url")
                        and parent_links[94].get("href") == contact.get("requested_url")):
                    return True
        return False

    def reviewed_opaque_ir_radios_after_policy(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Read this fully cited form's operational fields after its intact policy."""
        notice = ("お問い合わせフォームでは、営業・広告宣伝目的など特定電子メールに該当しうるご連絡は固くお断りしております。 "
                  "本フォームに、サービス提案やイベント・セミナー案内を送信されませんよう、ご注意ください。")
        policy = ("【個人情報の取り扱いについて】 ・お問い合わせフォームにご記入いただいた方のお名前・電話番号・メールアドレス等の個人情報は、"
                  "お問い合わせへのご回答、情報提供のために使用いたします。 ・利用目的の範囲内で、ご記入いただいた個人情報を当社グループ会社が使用する場合がございます。 "
                  "・当社の個人情報の取り扱いについては「個人情報保護方針」にて定めております。詳しくは こちら をご確認ください。")
        purpose = "お問い合わせの種類 IR（投資家情報）に関するお問い合わせ 広報関連のお問い合わせ 資料請求 責任ある鉱物調達に関するお問い合わせ その他"
        reply = "お名前 ふりがな 貴社名 メールアドレス 確認のため、再度メールアドレスを入力してください。 電話番号 - -"
        question = "お問い合わせ または資料請求内容 宣誓 入力した内容は、サービスの営業・提案やイベント・セミナーの案内ではありません。"
        fields = form.get("text", "").strip(); local = [e["quote"] for e, p in pairs if p is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        url = source.get("url", ""); parsed = urlsplit(url)
        names = ["f000029473"] * 5 + ["f000029474", "f000029475", "f000029476", "f000029477", "f000029477:cf", "f000029478:a", "f000029478:e", "f000029478:n", "f000029480", "f000029481", "f000029482", "f000029483", "f000029484", "f004479061", "submit", "reset"]
        if (not official_host or not re.fullmatch(r"reg[0-9]+[.]smp[.]ne[.]jp", parsed.hostname or "")
                or parsed.path != "/regist/is" or not re.fullmatch(r"SMPFORM=[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", parsed.query) or parsed.fragment
                or source.get("requested_url") != url or source.get("forms") != [form] or str(form.get("method", "")).lower() != "post" or form.get("action") != "/regist/Reg2"
                or not fields.startswith(notice + " " + policy + " " + purpose + " " + reply + " 郵便番号 ") or not fields.endswith(question)
                or not all(q in local for q in (purpose, reply, question)) or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields and type(e.get("source_form_index", 0)) is int and e.get("source_form_index", 0) == 0
                           for e, p in pairs if p is source)
                or [c.get("name") for c in controls] != names
                or any(c.get("tag") != "input" or c.get("type") != "radio" for c in controls[:5])
                or [c.get("id") for c in controls[:5]] != ["RadioSample2", "RadioSample9", "RadioSample3", "RadioSample10", "RadioSample4"]
                or any(c.get("tag") != "input" or c.get("type") != "text" for c in controls[5:14] + controls[15:17])
                or controls[14].get("tag") != "select" or controls[14].get("type") == "hidden" or controls[17].get("tag") != "textarea" or controls[17].get("type") == "hidden"
                or controls[18].get("tag") != "input" or controls[18].get("type") != "radio"
                or controls[19].get("tag") != "input" or controls[19].get("type") != "submit" or controls[20].get("tag") != "input" or controls[20].get("type") != "reset"):
            return False
        instruction = ("「よくあるご質問」で解決しないIR関連のお問い合わせ、または、報道機関の方からの広報関連のお問い合わせは、"
                       "お問い合わせフォームよりご連絡ください。お急ぎの場合は以下電話でもお受けしております。")
        return any(parent is not source and self.successful(parent) and urlsplit(parent.get("url", "")).hostname == official_host
                   and ir_page_heading(parent) and evidence["quote"] == instruction and evidence.get("source_link_url") == url
                   and parent.get("text", "").count(instruction) == 1
                   and sum(l.get("url") == url and l.get("href") == url and l.get("label") == "お問い合わせフォーム"
                           for l in parent.get("links", []) if isinstance(l, dict)) == 1 for evidence, parent in pairs)

    def reviewed_class_investor_purpose_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A privacy inquiry option is part of this actual nine-radio purpose.

        The complete cited fields and native order delimit the final policy;
        neither a privacy paragraph nor IR navigation supplies the purpose.
        """
        purpose = ("お問い合わせ分野を選択してください 必須 製品・技術 特殊鋼鋼材／特殊合金 精密加工 熱処理加工 "
                   "機器製品 その他 調査・分析／研究開発 株主・投資家情報 採用情報 総合窓口／個人情報保護／その他のお問い合わせ")
        personal = "会社団体名 必須 ※個人の方は個人と入力してください"
        end = ("市区町村・番地 必須 お電話番号 必須 メールアドレス 必須 件名 必須 ご質問内容 必須 "
               "当社の 個人情報保護方針 に同意の上 お問い合わせください。 個人情報保護方針に同意する 入力内容を確認する")
        fields = form.get("text", "").strip()
        local = [e["quote"] for e, s in pairs if s is source]
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        names = ["class"] * 9 + ["company", "department", "url", "name", "kana", "zip", "pref", "address", "tel", "email", "title", "comment", "consent[]"]
        return bool(source.get("forms") == [form] and str(form.get("method", "")).lower() == "post" and question_form(form)
                    and fields.startswith(purpose + " " + personal + " 部署名 ホームページURL お名前 必須 ") and fields.endswith(end)
                    and fields in local and purpose in local and personal in local and source.get("text", "").count(fields) == 1
                    and [c.get("name") for c in controls] == names
                    and all(c.get("tag") == "input" and c.get("type") == "radio" for c in controls[:9])
                    and all(c.get("tag") == "input" and c.get("type") == "text" for c in controls[9:15] + controls[16:20])
                    and controls[15].get("tag") == "select" and controls[15].get("type") != "hidden"
                    and controls[20].get("tag") == "textarea" and controls[20].get("type") != "hidden"
                    and controls[21].get("tag") == "input" and controls[21].get("type") == "checkbox"
                    and form.get("action") == "#form"
                    and not re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", fields)
                    and not re.search(r"(?:株主・投資家情報|IR)[^。]{0,40}(?:電話のみ|フォームでは受け付けません|対象外)", source.get("text", ""), re.I))

    def reviewed_external_ir_attribute_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]], official_host: str | None) -> bool:
        """Tie this external IR audience engine to the issuer's exact link.

        Its literal asterisk caption, full form and native reply controls are
        inseparable from the captured financial-IR route, including query.
        """
        heading = "IRに関するご質問（株主・投資家の方）"
        choice = "種別 ※ 選択してください 個人投資家 機関投資家 法人 その他"
        fields = form.get("text", "").strip()
        controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
        url = source.get("url", "")
        parsed = urlsplit(url)
        if (not official_host or not re.fullmatch(r"reg[0-9]+[.]smp[.]ne[.]jp", parsed.hostname or "")
                or parsed.path != "/regist/is" or not re.fullmatch(r"SMPFORM=[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+", parsed.query)
                or source.get("requested_url") != url or source.get("forms") != [form]
                or source.get("headings", []).count(heading) != 1 or str(form.get("method", "")).lower() != "post"
                or form.get("action") != "/regist/Reg2" or not question_form(form)
                or not fields.startswith("1 Input 2 Complete " + choice + " 会社名 お名前 ※ メールアドレス ※ お問い合わせの概要をご記入ください。 ※ ")
                or choice not in form_labels(form) or source.get("text", "").count(fields) != 1
                or not any(e["quote"].strip() == fields for e, s in pairs if s is source)
                or [c.get("name") for c in controls] != ["attribute", "conpany", "name", "email", "email:cf", "comment2", "knowReason1", "knowReason2", "privacy", "submit"]
                or any(controls[i].get("tag") != "select" or controls[i].get("type") == "hidden" for i in (0, 6))
                or any(controls[i].get("tag") != "input" or controls[i].get("type") != "text" for i in (1, 2, 3, 4, 7))
                or controls[5].get("tag") != "textarea" or controls[5].get("type") == "hidden"
                or controls[8].get("tag") != "input" or controls[8].get("type") != "checkbox"
                or controls[9].get("tag") != "input" or controls[9].get("type") != "submit"
                or re.search(r"個人(?:投資家|の方|のお客様)?[^。]{0,35}(?:対象外|お断り|ご遠慮|受け付けません)", fields)):
            return False
        parent_label = heading + " " + heading
        return any(self.successful(parent) and parent is not source
                   and urlsplit(parent.get("url", "")).hostname == official_host
                   and evidence["quote"] == parent_label and evidence.get("source_link_url") == url
                   and parent.get("text", "").count(parent_label) == 1
                   and sum(link.get("url") == url and link.get("href") == url and link.get("label") == parent_label
                           for link in parent.get("links", []) if isinstance(link, dict)) == 1
                   for evidence, parent in pairs)

    def reviewed_sort_ir_purpose_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Bind this literal business/IR purpose block to its native radios."""
        purpose = ('ご用件 ※必須 お掃除ロボット事業について AI高速カメラ事業について ペロブスカイト事業について '
                   '石英クリニック事業について Lark(DX/IT化)事業について FPD基板加工事業について IR情報に関して 採用に関して その他')
        fields = form.get('text', '').strip()
        local = [e['quote'] for e, s in pairs if s is source]
        controls = [c for c in form.get('controls', []) if isinstance(c, dict)]
        return bool(str(form.get('method', '')).lower() == 'post' and question_form(form)
                    and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get('forms', [])) == 1
                    and fields.startswith(purpose + ' 企業名 お名前 ※必須 ') and purpose in form_labels(form)
                    and fields in local and purpose in local and source.get('text', '').count(fields) == 1
                    and len(controls) > 9 and all(c.get('tag') == 'input' and c.get('type') == 'radio' and c.get('name') == 'sort' for c in controls[:9])
                    and sum(c.get('name') == 'sort' for c in controls) == 9
                    and any(c.get('tag') == 'input' and c.get('type') == 'email' and c.get('name') == 'e-mail' for c in controls)
                    and any(c.get('tag') == 'textarea' and c.get('type') != 'hidden' and c.get('name') == 'message' for c in controls)
                    and url_key(urljoin(source.get('url', ''), form.get('action') or '')) == url_key(source.get('url'))
                    and re.fullmatch(r'wpcf7-f[0-9]+-p[0-9]+-o1', urlsplit(str(form.get('action', ''))).fragment)
                    and not re.search(r'(?:IR|ＩＲ)(?:情報)?[^。]{0,40}(?:電話のみ|フォームでは受け付けません|対象外)', source.get('text', ''), re.I))

    def reviewed_financial_ir_breadcrumb_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A dedicated IR child, breadcrumb and full native fields bind together.

        The separate general Contact href and business/recruitment form must
        not acquire the financial IR parent's scope.
        """
        fields = form.get('text', '').strip()
        local = [e['quote'] for e, s in pairs if s is source]
        controls = [c for c in form.get('controls', []) if isinstance(c, dict)]
        url = source.get('url', '')
        expected_names = ['氏名', 'ふりがな', 'メールアドレス', 'メールアドレス再入力', '電話番号[data][0]',
                          '電話番号[data][1]', '電話番号[data][2]', '郵便番号[data][0]', '郵便番号[data][1]', '住所', 'ご質問・ご意見', 'submitConfirm']
        if (str(form.get('method', '')).lower() != 'post' or not question_form(form)
                or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get('forms', [])) != 1
                or not fields.startswith('下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」 をクリックして下さい。 ')
                or not fields.endswith('住所 ご質問・ご意見 ※') or fields not in local
                or 'HOME IR お問い合わせ' not in local or source.get('text', '').count('HOME IR お問い合わせ') != 1
                or source.get('text', '').count(fields) != 1 or [c.get('name') for c in controls] != expected_names
                or any(c.get('tag') != 'input' or c.get('type') != 'email' for c in controls[2:4])
                or controls[10].get('tag') != 'textarea' or controls[10].get('type') == 'hidden'
                or url_key(urljoin(url, form.get('action') or '')) != url_key(url)
                or re.search(r'IR[^。]{0,40}(?:電話のみ|フォームでは受け付けません|対象外)', source.get('text', ''), re.I)):
            return False
        route = 'その他IR情報 IRカレンダー FAQ ディスクロージャーポリシー 免責事項 お問い合わせ 電子公告'
        for evidence, parent in pairs:
            if (parent is source or not self.successful(parent) or evidence['quote'] != route
                    or evidence.get('source_link_url') != url or parent.get('text', '').count(route) != 1
                    or urlsplit(parent.get('url', '')).hostname != urlsplit(url).hostname
                    or not re.match(r'IR\s*[|｜]', parent.get('title', ''))
                    or not {'IR', '経営情報', 'IRライブラリ', '株式情報', 'その他IR情報'}.issubset(parent.get('headings', []))
                    or urlsplit(url).path != urlsplit(parent.get('url', '')).path.rstrip('/') + '/inquiry/'):
                continue
            target_links = [l for l in parent.get('links', []) if isinstance(l, dict) and l.get('url') == url and l.get('label') == 'お問い合わせ']
            general = urljoin(parent.get('url', ''), '/contact/')
            if (len(target_links) == 1 and target_links[0].get('href') == urlsplit(url).path
                    and any(l.get('url') == general and l.get('label') == 'お問い合わせ' for l in parent.get('links', []) if isinstance(l, dict))):
                return True
        return False

    def reviewed_financial_ir_reply_operation_form(self, source: dict, form: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """A complete IR-desk answer policy precedes this actual IR post form.

        Recipient-only reuse conditions describe replies, not individual
        eligibility; its excluded topics are not a blanket no-reply policy.
        """
        policy = ('お問い合わせ内容によってはお答えできない場合もございます。 '
                  '下記に該当するご質問は、IRからの回答を差し控えておりますので、あらかじめご了承ください。 '
                  '非公開情報に関するご質問 株式市場の値動きに関するご質問 営業や勧誘のお問い合わせ 誹謗中傷に該当するメッセージ '
                  'また、当社からご回答としてお送りするEメールは、株主・投資家の皆様からお寄せいただいたお問い合わせなどにお答えさせていただく目的で、皆様個人宛てにお送りするものです。 '
                  'その一部または全部を転載、二次利用することはご遠慮ください。その他免責事項については「 免責事項 」をご確認ください。 上記ご理解のほど、何卒よろしくお願いいたします。')
        fields = 'お名前 所属（会社名） メールアドレス 電話番号 お問合せ内容 プライバシーポリシー に同意する。'
        local = [e['quote'] for e, s in pairs if s is source]
        controls = [c for c in form.get('controls', []) if isinstance(c, dict)]
        names = ['ir_contact[name]', 'ir_contact[company]', 'ir_contact[email]', 'ir_contact[tel]', 'ir_contact[contents]', 'ir_contact[privacy_check]', 'commit']
        return bool(str(form.get('method', '')).lower() == 'post' and question_form(form)
                    and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get('forms', [])) == 1
                    and form.get('text', '').strip() == fields and fields in local and policy in local
                    and source.get('text', '').count(policy + ' ※は必須項目です。 ' + fields) == 1
                    and [c.get('name') for c in controls] == names
                    and all(c.get('tag') == 'input' and c.get('type') == 'text' for c in controls[:4])
                    and controls[4].get('tag') == 'textarea' and controls[4].get('type') != 'hidden'
                    and controls[5].get('tag') == 'input' and controls[5].get('type') == 'checkbox'
                    and url_key(urljoin(source.get('url', ''), form.get('action') or '')) == url_key(source.get('url', '') + '_confirm'))

    def has_form_binding(self, pairs: list[tuple[dict, dict]], previous: dict | None, *, reviewed: bool = False, target_url: str | None = None, target_form: dict | None = None, official_host: str | None = None) -> bool:
        # Legacy classification was manually checked. It still needs matching
        # IR quotes and actual controls; link-only legacy records never qualify.
        legacy_fields = isinstance(previous, dict) and previous.get("verification_level") == "page_and_fields_verified"
        ir_sources = [(e, s) for e, s in pairs if self.successful(s) and
                      (IR_CONTACT.search(e["quote"]) or legacy_fields and
                       (ir_page_heading(s) or previous.get("route_type") == "ir_category_form" and IR_MARKER.search(e["quote"])))]
        for _, source in pairs:
            if not self.successful(source):
                continue
            source_urls = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
            if target_url is not None and target_url not in source_urls:
                # A claimed official landing page can contain the question
                # form as a captured iframe. Bind the exact saved iframe URL,
                # query included; an ordinary footer/link on another page
                # cannot confer the landing page's channel on this form.
                embedded_at_target = any(
                    self.successful(parent) and target_url in {
                        url_key(parent.get("url")), url_key(parent.get("requested_url"))
                    } and any(link.get("label") == "embedded frame" and url_key(link.get("url")) in source_urls
                              for link in parent.get("links", []))
                    for _, parent in pairs
                )
                if not embedded_at_target:
                    continue
            for form in source.get("forms", []):
                if target_form is not None and form is not target_form:
                    continue
                finite_next_form = None
                if form.get("text", "").startswith("当社の 個人情報保護方針 に同意の上、お問合せください。 必須 同意する お問い合わせの種類をお選びください。 "):
                    finite_next_form = self.reviewed_financial_stock_investor_form
                elif form.get("text", "").startswith("Home »お問い合わせ お問い合わせ 個人情報について ご利用いただく前に、必ず「プライバシーポリシー（個人情報の取り扱いについて）」"):
                    finite_next_form = self.reviewed_ir_opaque_fields_after_policy
                if finite_next_form is not None:
                    if reviewed and finite_next_form(source, form, pairs, official_host):
                        return True
                    continue
                finite_form = None
                if form.get("text", "").startswith("会社名 個人の方は 個人 とご記入ください。 会社名（読み） 所属 役職名 住所 都道府県/地域 "):
                    finite_form = self.reviewed_redirected_ir_opaque_reply_form
                elif form.get("text", "").startswith("プライバシーポリシーの同意 必須 私は上記のプライバシーポリシー及びご利用にあたってに同意します。 "):
                    finite_form = self.reviewed_company_ir_checkboxes_after_consent
                elif form.get("text", "").startswith("お問い合わせ内容をお選びください 採用（新卒） その他の採用 テクノセンタ その他 【必須】 "):
                    finite_form = self.reviewed_financial_faq_native_id_form
                if finite_form is not None:
                    if reviewed and finite_form(source, form, pairs, official_host):
                        return True
                    continue
                # These exact opaque engines expose neither a generic mail
                # name nor ordinary labels before privacy. Their native form,
                # indexed full quote and captured issuer route must all agree.
                opaque = None
                if form.get("text", "").startswith("メール お問い合わせ内容 経理シンギュラリティに関して "):
                    opaque = self.reviewed_opaque_mail_iframe_ir_form
                elif form.get("text", "").startswith("お問い合わせフォームでは、営業・広告宣伝目的など特定電子メールに該当しうるご連絡は固くお断りしております。 "):
                    opaque = self.reviewed_opaque_ir_radios_after_policy
                elif form.get("text", "").startswith("下記の必要事項にご記入いただき、当社の 個人情報のお取り扱いについて（「個人情報保護宣言」） "):
                    opaque = self.reviewed_privacy_intro_ir_checkbox_iframe
                if opaque is not None:
                    if reviewed and opaque(source, form, pairs, official_host):
                        return True
                    continue
                if form.get("text", "").startswith("カテゴリー ※ コレットチャック・ガイドブッシュ等に関するお問い合わせ "):
                    if reviewed and self.reviewed_native_category_financial_primary(source, form, pairs, official_host):
                        return True
                    continue
                if form.get("text", "").startswith("お問い合わせ種類 必須 一般的なお問い合わせ 投資に関するお問い合わせ "):
                    if reviewed and self.reviewed_native_issuer_investment_radios(source, form, pairs, official_host):
                        return True
                    continue
                if form.get("text", "").startswith("氏名 ※ フリガナ ※ 会社・団体など組織名 ※ "):
                    if reviewed and self.reviewed_financial_faq_external_form(source, form, pairs, official_host):
                        return True
                    continue
                if not (question_form(form) or reviewed and reviewed_question_form(form) or legacy_fields and legacy_question_form(form, source)):
                    continue
                labels = form_labels(form)
                local_quotes = [e["quote"] for e, s in pairs if s is source]
                # These public form engines expose an operational subject or
                # financial-question checkbox. Once that structure is saved,
                # an IR navigation/support word must not fall through to a
                # general keyword shortcut after the explicit proof fails.
                if (re.match(r"You can contact [^.]{2,60} by filling out and sending the following form[.]", form.get("text", ""))
                        and urlsplit(str(form.get("action", ""))).path.endswith("/gencgi/mod/enqcsv")):
                    if reviewed and reviewed_english_ir_subject_form(source, form, local_quotes):
                        return True
                    continue
                if (form.get("text", "").startswith("お問い合わせ先を確認 ※ ")
                        and any(c.get("tag") == "select" and c.get("name") == "gcname"
                                for c in form.get("controls", []) if isinstance(c, dict))):
                    if reviewed and reviewed_results_question_checkbox_form(source, form, local_quotes):
                        return True
                    continue
                if reviewed and (self.reviewed_parenthesized_ir_question_form(source, form, pairs)
                                 or self.reviewed_financial_material_question_form(source, form, pairs)):
                    return True
                if reviewed and reviewed_financial_stock_form(source, form, local_quotes):
                    return True
                # This explicit sales-referral preface routes sales away
                # from the claimed IR form. Do not let an IR navigation word
                # or a phone-only notice in its body bypass the separate-link
                # and complete-form evidence required by this reviewed path.
                if reviewed and form.get("text", "").startswith(
                    "営業・セールスに関するお問い合わせは こちら お問い合わせ内容をご入力ください"
                ):
                    if (reviewed_ir_form_with_separate_sales_route(
                        source, form, [e for e, s in pairs if s is source]
                    ) and any(self.successful(parent) and self.quoted_ir_direction(pe, parent, source_urls)
                              for pe, parent in pairs if parent is not source)):
                        return True
                    continue
                if reviewed and self.reviewed_ir_email_receipt_form(source, form, pairs):
                    return True
                # An outer ASP.NET department form needs its actual body,
                # native controls and parent target. Its IR navigation cannot
                # replace missing or reordered department/question evidence.
                if (form.get("text", "").startswith("本文へ お問い合わせ アクセシビリティ LANGUAGE JP EN HOME ")
                        and any(str(c.get("name", "")).endswith("$fldValue$rblSubjectRadioButtonList")
                                for c in form.get("controls", []) if isinstance(c, dict))):
                    if reviewed and self.reviewed_aspnet_ir_department_form(source, form, pairs):
                        return True
                    continue
                # In this captured multi-form engine the literal IR desk
                # operation designates only its own form. An IR word in the
                # page title/selector cannot promote the other native forms.
                if (re.fullmatch(r"wpcf7-f[0-9]+-o[1-9][0-9]*", urlsplit(str(form.get("action", ""))).fragment)
                        and "※なお、以下に該当するお問い合わせに関してましては、IR担当からの回答を差し控えておりますので" in source.get("text", "")):
                    if reviewed and reviewed_ir_desk_reply_form(source, form, local_quotes):
                        return True
                    continue
                # Saved native engine families need their complete operational
                # evidence. Neither an IR title nor a neighbouring form/link
                # can substitute after that family's explicit proof fails.
                controls = [c for c in form.get("controls", []) if isinstance(c, dict)]
                family = None
                if form.get("text", "").startswith("お問い合わせ分野を選択してください 必須 製品・技術 特殊鋼鋼材／特殊合金 "):
                    family = self.reviewed_class_investor_purpose_form
                elif form.get("text", "").startswith("ご用件 ※必須 ") and any(c.get("name") == "sort" for c in controls):
                    family = self.reviewed_sort_ir_purpose_form
                elif form.get("text", "").startswith("下記のお問い合わせフォームに必要事項を入力のうえ下の「入力内容のご確認」") and any(c.get("name") == "メールアドレス再入力" for c in controls):
                    family = self.reviewed_financial_ir_breadcrumb_form
                elif form.get("text", "").startswith("お名前 所属（会社名） メールアドレス ") and any(c.get("name") == "ir_contact[email]" for c in controls):
                    family = self.reviewed_financial_ir_reply_operation_form
                if family is not None:
                    if reviewed and official_host and urlsplit(source.get("url", "")).hostname == official_host and family(source, form, pairs):
                        return True
                    continue
                if form_ir_scope(form, reviewed=reviewed) or reviewed and reviewed_form_ir_scope(form, local_quotes):
                    return True
                if reviewed and reviewed_anchored_personal_ir_form(source, form, local_quotes):
                    return True
                if reviewed and reviewed_named_ir_tab_form(source, form, local_quotes):
                    return True
                # Reject an explicitly unrelated form heading. Privacy/use
                # instructions after name/email fields do not change the
                # audience of a dedicated IR form (Trial Holdings).
                if not legacy_fields and re.match(r"\s*(?:製品|商品|サポート|採用|営業|報道|プレス|product|support|press|recruit)", labels, re.I):
                    continue
                local_ir = [(e, s) for e, s in ir_sources if s is source]
                dedicated_form_quote = any(re.search(r"(?:IR|ＩＲ)[^。]{0,90}専用フォーム", e["quote"], re.I) for e, _ in local_ir)
                if reviewed and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1:
                    # Explicit body sections can designate the sole form even
                    # when the site's first heading concerns stock procedures.
                    # Cite its complete actual field text as a second witness;
                    # ordinary IR navigation or an adjacent phone never does.
                    field_text = form.get("text", "").strip()
                    cited_fields = (field_text and any(field_text in q for q in local_quotes)
                                    and str(form.get("method", "")).lower() == "post")
                    for e, _ in local_ir:
                        if not cited_fields:
                            continue
                        shareholder_section = re.fullmatch(
                            r"株主様および機関投資家様[（(]IR面談[）)]お問い合わせ[（(]メール[）)]\s*"
                            r"下記に必要事項をご記入の上お問い合わせください[。.]", e["quote"].strip(), re.I
                        )
                        if shareholder_section and e["quote"].strip() + " " + field_text in source.get("text", ""):
                            dedicated_form_quote = True
                        issuer_form = re.search(
                            r"[^\s。]{2,70}の(?:IR|ＩＲ)に関するご質問は[、,]\s*"
                            r"下記の問い合わせフォームにてお問い合わせ下さい[。.]", e["quote"], re.I
                        )
                        if (issuer_form and source.get("headings", []).count("IRに関するお問い合わせ") == 1
                                and source.get("text", "").count(issuer_form[0]) == 1
                                and source.get("text", "").count(field_text) == 1
                                and source["text"].index(issuer_form[0]) < source["text"].index(field_text)):
                            dedicated_form_quote = True
                        spelling_variant = re.search(
                            r"[^\s。]{2,70}の(?:IR|ＩＲ)に関するお問い?(?:合(?:わ)?せ|あわせ)(?:など)?ございましたら[、,]\s*"
                            r"以下のフォームでお問い?(?:合(?:わ)?せ|あわせ)ください[。.]", e["quote"], re.I
                        )
                        # An issuer's literal IR assignment may use kana in
                        # "お問いあわせ". Bind that operation to the sole
                        # post form's entire quoted actual field text. A
                        # shareholder title, phone-only FAQ, document referral
                        # or IR word in navigation cannot substitute for it.
                        if (spelling_variant and question_form(form)
                                and source.get("text", "").count(spelling_variant[0]) == 1
                                and source.get("text", "").count(field_text) == 1
                                and source["text"].index(spelling_variant[0]) < source["text"].index(field_text)
                                and not re.search(r"製品|商品|採用|株主優待|株式(?:事務|手続)|product|recruit", field_text, re.I)):
                            dedicated_form_quote = True
                    # An explicit IR-consultation operation can name the
                    # form "here" without a dedicated page title. Its cited
                    # operation must end with the actual IR-only exclusion
                    # immediately BEFORE the sole complete cited post form.
                    # A navigation item, phone FAQ or unrelated adjacent form
                    # cannot replace that contiguous public assignment.
                    consultation_scope = "IRに関するお問い合わせ、ご相談はこちらから承っております。"
                    ir_only_exclusion = "・IR以外のお問い合わせ"
                    for e, _ in local_ir:
                        operation = e["quote"].strip()
                        # The literal financial-law citation concerns an
                        # excluded market-sensitive topic, not a product
                        # contact. Preserve its original public quotation.
                        operational_topics = operation[len(consultation_scope):].replace(
                            "金融商品取引法第166条「重要事実」", ""
                        )
                        if (cited_fields and question_form(form)
                                and any(q.strip() == field_text for q in local_quotes)
                                and operation.startswith(consultation_scope) and operation.endswith(ir_only_exclusion)
                                and source.get("text", "").count(consultation_scope) == 1
                                and source.get("text", "").count(operation + " " + field_text) == 1
                                and any(c.get("tag") == "input" and c.get("type") == "email"
                                        for c in form.get("controls", []) if isinstance(c, dict))
                                and not OTHER_CONTACT.search(operational_topics)
                                and not re.search(r"電話のみ|フォームでは受け付けません|株式(?:事務|手続)|株主優待|入力例", operation)):
                            dedicated_form_quote = True
                if reviewed and any(re.search(r"当社株主[、,]\s*投資家の皆様からのお問い合わせは[、,]\s*以下のフォームよりお願いいたします", e["quote"]) for e, _ in local_ir):
                    # This cited instruction names the form BELOW it on the
                    # same page; multiple actual question forms are ambiguous.
                    dedicated_form_quote = dedicated_form_quote or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1
                if reviewed and any(re.search(
                    r"(?:IR|ＩＲ)情報に関するお問い合わせは下記[「『]お問い合わせフォーム[」』]に内容をご記入の上[、,]\s*送信してください[。.]",
                    e["quote"], re.I
                ) for e, _ in local_ir):
                    # Tear's operational instruction precedes its sole form;
                    # the generic page title alone supplies no IR purpose.
                    dedicated_form_quote = dedicated_form_quote or sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1
                if reviewed and any(re.search(
                    r"(?:株式[・、]\s*)?(?:IR|ＩＲ)情報に関する(?:ご相談・ご依頼・)?お問い合わせは[、,]\s*"
                    r"以下のフォームに必要事項を入力し送信してください[。.]", e["quote"], re.I
                ) for e, _ in local_ir):
                    # An explicit financial-IR submit instruction designates
                    # the sole same-page question form. Its captured public
                    # field text must also be cited; a phone/benefit/product
                    # form or another page cannot borrow the instruction.
                    unrelated = re.search(r"製品|商品|採用|株主優待|株式(?:事務|手続)|product|recruit", labels, re.I)
                    dedicated_form_quote = dedicated_form_quote or bool(
                        not unrelated and labels.strip() and any(labels.strip() in q for q in local_quotes)
                        and str(form.get("method", "")).lower() == "post"
                        and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1
                    )
                if reviewed and source.get("headings", []).count("IRお問合せ") == 1:
                    # Cotta's single question form immediately follows this
                    # cited standalone IR notice. Require its exact field-text
                    # prefix in the quote, not an IR word in the site's menu.
                    notice = re.compile(r"IRお問合せ\s*本フォーム(?:に)?よるお問合せにあたっては[、,]\s*必ず\s*個人情報保護方針\s*に同意のうえ[、,]\s*お問合せください[。.]")
                    exact_notice = any((match := notice.search(e["quote"])) and e["quote"][match.end():].strip() == labels.strip()
                                       for e, _ in local_ir)
                    dedicated_form_quote = dedicated_form_quote or bool(exact_notice and labels.strip() and sum(
                        bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])
                    ) == 1)
                if local_ir and (legacy_fields or ir_page_heading(source) or dedicated_form_quote):
                    return True
                if reviewed and self.reviewed_ir_consent_form(pairs, source, form):
                    return True
                if reviewed and self.reviewed_issuer_investment_category(pairs, source, form):
                    return True
                # A saved explicit IR-contact link can bind a target with a
                # generic title (Manabi Aid). An ordinary footer Contact link
                # on an IR page cannot transfer IR scope by itself.
                for parent_evidence, ir_source in pairs:
                    if not self.successful(ir_source):
                        continue
                    for link in ir_source.get("links", []):
                        target = url_key(link.get("url"))
                        label = link.get("label", "")
                        if target not in {url_key(source.get("url")), url_key(source.get("requested_url"))}:
                            continue
                        if IR_CONTACT.search(label):
                            return True
                        if reviewed and self.quoted_ir_direction(parent_evidence, ir_source, {url_key(source.get("url")), url_key(source.get("requested_url"))}, scope_pairs=pairs):
                            return True
                        # Unitika's dedicated policy accepts IR only through
                        # the linked general form. That form reciprocally cites
                        # this policy immediately before its input instruction.
                        # Require BOTH operational quotes and exact captured
                        # links; a generic IR footer or an FAQ deflection fails.
                        if (reviewed and ir_page_heading(ir_source)
                                and url_key(parent_evidence.get("source_link_url")) == target
                                and re.search(r"(?:IR|ＩＲ)に関するお問(?:い)?合(?:わ)?せは[「『]お問(?:い)?合(?:わ)?せフォーム[」』]のみで受け付けております[。.]", parent_evidence["quote"], re.I)
                                and sum(bool(question_form(f) or reviewed_question_form(f)) for f in source.get("forms", [])) == 1):
                            reciprocal = re.compile(r"(?:IR|ＩＲ)に関するお問(?:い)?合(?:わ)?せは\s*こちら\s*をご確認のうえお問(?:い)?合(?:わ)?せください\s*以下のお問(?:い)?合(?:わ)?せの内容を入力してください[。.]", re.I)
                            policy_targets = {url_key(ir_source.get("url")), url_key(ir_source.get("requested_url"))} - {None}
                            if (any(reciprocal.search(e["quote"]) for e, _ in local_ir)
                                    and any(url_key(backlink.get("url")) in policy_targets and backlink.get("label") == "こちら"
                                            for backlink in source.get("links", []))):
                                return True
                        if ir_page_heading(ir_source) and any(s is ir_source for _, s in ir_sources) and (
                            label == "embedded frame" or "フォーム" in label or re.search(r"\bform\b", label, re.I)
                        ):
                            return True
                if legacy_fields and ir_sources:
                    return True
        return False

    def actual_official_get(self, record: dict, seed: dict | None) -> bool:
        fetches = record.get("fetches", [])
        if not isinstance(fetches, list):
            self.issue(record["security_code"], "fetches_type", "fetches must be an array")
            return False
        official_url = seed.get("official_url") if isinstance(seed, dict) else record.get("official_url")
        official_host = urlsplit(official_url).hostname if url_key(official_url) else None
        found = False
        for fetch in fetches:
            reference = fetch.get("snapshot") if isinstance(fetch, dict) else fetch
            source = self.load_snapshot(reference, record["security_code"])
            if source is None:
                continue
            if source.get("error") in {"robots_disallowed", "robots_access_denied_stopped", "robots_unreachable_stopped", "host_access_denied_stopped", "environment_circuit_breaker_open"}:
                # These capture wrappers did not perform a content-page GET.
                continue
            if source.get("submitted") is not False or not aware_time(source.get("retrieved_at")):
                self.issue(record["security_code"], "fetch_metadata", "Fetch lacks submitted:false or offset retrieval time")
                continue
            if source.get("method", "GET").upper() != "GET":
                self.issue(record["security_code"], "fetch_method", "Only GET fetch evidence is valid in this survey")
                continue
            requested = source.get("requested_url", source.get("url"))
            if not url_key(requested):
                self.issue(record["security_code"], "fetch_url", "Fetch lacks valid requested_url")
                continue
            host = urlsplit(requested).hostname
            if official_host and host and host.removeprefix("www.") == official_host.removeprefix("www."):
                found = True
        return found

    def previous_record(self, record: dict) -> dict | None:
        value = record.get("previous_record")
        code = record["security_code"]
        if isinstance(value, str):
            artifact = self.load_snapshot(value, code)
            rows = artifact.get("companies", []) if isinstance(artifact, dict) else []
            matches = [row for row in rows if isinstance(row, dict) and row.get("security_code") == code]
            if len(matches) != 1:
                self.issue(code, "previous_company", "Previous directory must contain exactly one matching company")
                return None
            value = matches[0]
        if value is not None and (not isinstance(value, dict) or value.get("security_code") != code):
            self.issue(code, "previous_company", "Previous evidence must belong to the same security code")
            return None
        if isinstance(value, dict) and record.get("original_verification_level") not in {None, value.get("verification_level")}:
            self.issue(code, "previous_level", "original_verification_level differs from saved previous evidence")
        return value

    def reviewed_phone_limited_ir_form(self, record: dict, pairs: list[tuple[dict, dict]]) -> bool:
        """Validate an explicitly restricted telephone-alternative IR route.

        This only supplies an eligibility basis. A captured consent link is
        still provisional until its actual reply/question fields are saved.
        Ordinary phone instructions and a policy's generic "only" do not
        establish restricted access to an IR question form.
        """
        target = url_key(record.get("contact_url"))
        if not manual_review_valid(record) or target is None:
            return False
        policy = "IRに関するお問い合わせは原則お電話で承ります。お電話が困難な方のみお問い合わせフォームより承ります。"
        consent_label = "上記に同意してフォームに進む"
        for evidence, source in pairs:
            if (not self.successful(source) or evidence["quote"] != policy
                    or source.get("text", "").count(policy) != 1
                    or source.get("text", "").count(consent_label) != 1
                    or not {"お問い合わせフォームからのお問い合わせ", "お問い合わせに当たってのご注意事項"}.issubset(source.get("headings", []))
                    or source["text"].index(policy) >= source["text"].index(consent_label)):
                continue
            urls = {url_key(source.get("url")), url_key(source.get("requested_url"))} - {None}
            source_url = url_key(source.get("url"))
            if (source_url is None or target in urls
                    or urlsplit(source_url).hostname != urlsplit(target).hostname
                    or not urlsplit(target).path.startswith(urlsplit(source_url).path.rstrip("/") + "/")):
                continue
            links = [link for link in source.get("links", []) if isinstance(link, dict)
                     and link.get("label") == consent_label and url_key(link.get("url")) == target]
            if (len(links) != 1 or not any(saved is source and e["quote"] == consent_label
                                        and e.get("source_link_url") == links[0].get("url") for e, saved in pairs)):
                continue
            for pe, parent in pairs:
                if (parent is source or not self.successful(parent) or not IR_MARKER.search(parent.get("title", ""))
                        or not IR_CONTACT.search(pe["quote"]) or "IR専用電話" not in pe["quote"]
                        or "聴覚障がい等の方は" not in pe["quote"] or "をご利用ください" not in pe["quote"]
                        or urlsplit(parent.get("url", "")).hostname != urlsplit(source_url).hostname):
                    continue
                if any(isinstance(link, dict) and link.get("label") == "お問い合わせ"
                       and url_key(link.get("url")) in urls and pe.get("source_link_url") == link.get("url")
                       and link["label"] in pe["quote"] for link in parent.get("links", [])):
                    return True
        return False

    def identity(self, record: dict, previous: dict | None) -> None:
        if previous is not None:
            if record.get("identity_status") not in {None, "previous_verified", "name_or_security_code_observed"}:
                self.issue(record["security_code"], "identity_status", "Prior evidence must retain an observed/prior identity state")
            return
        if record.get("investigation_status") != "confirmed":
            return
        code = record["security_code"]
        if record.get("identity_status") != "name_or_security_code_observed":
            self.issue(code, "identity_unverified", "New confirmed records require an observed company name or security code")
            return
        expected = identity_key(self.universe.get(code, {}).get("company_name") or record.get("company_name", ""))
        supported = False
        for witness in record.get("identity_matches", []):
            if not isinstance(witness, dict):
                continue
            source = self.load_snapshot(witness.get("snapshot"), code)
            if source is None or not self.successful(source):
                continue
            text = source.get("text", "")
            name_observed = len(expected) >= 2 and expected in identity_key(text)
            code_observed = re.search(r"(?:証券コード|銘柄コード|security code|stock code)[\s:：]*" + re.escape(code) + r"(?![0-9A-Z])", text, re.I)
            # A quoted code in an explicit statement about THIS company's
            # Tokyo listing is public identity evidence. Keep balanced literal
            # brackets and the closing predicate; an arbitrary quoted number,
            # other company's listing or longer code is not this declaration.
            quoted_listing = re.search(
                r"当社は東京証券取引所に上場しており、証券コードは「" + re.escape(code) + r"」です。", text
            )
            if name_observed or code_observed or quoted_listing:
                supported = True
        if not supported:
            self.issue(code, "identity_basis", "Identity state lacks matching saved name/code evidence")

    def validate_record(self, record: dict, seed: dict | None = None) -> dict:
        before = len(self.issues)
        code = record.get("security_code")
        if not isinstance(code, str) or not CODE.fullmatch(code):
            self.issue(str(code), "security_code", "security_code must be a four-character alphanumeric string")
            return {"security_code": str(code), "terminal": False, "official_get_attempted": False, "channel_verified": False}
        if code not in self.universe:
            self.issue(code, "outside_universe", "Record is not in the declared domestic ordinary equity universe")
        elif MARKET_ALIASES.get(record.get("market"), record.get("market")) != self.universe[code]["market"]:
            self.issue(code, "market_mismatch", "Record market differs from universe")
        status = record.get("investigation_status")
        level = record.get("verification_level")
        if status not in STATUSES:
            self.issue(code, "investigation_status", "Unknown investigation status")
        if level not in LEVELS:
            self.issue(code, "verification_level", "Unknown verification level")
        for field in ("attempted_at", "completed_at"):
            if not aware_time(record.get(field)):
                self.issue(code, "record_time", f"{field} must have an ISO 8601 timezone offset")
        if aware_time(record.get("attempted_at")) and aware_time(record.get("completed_at")):
            if datetime.fromisoformat(record["completed_at"].replace("Z", "+00:00")) < datetime.fromisoformat(record["attempted_at"].replace("Z", "+00:00")):
                self.issue(code, "record_time", "completed_at predates attempted_at")
        pairs = self.evidence(record)
        previous = self.previous_record(record)
        self.identity(record, previous)
        if self.reviewed_captured_tse_identity(record, pairs):
            self.issues[before:] = [i for i in self.issues[before:] if i["kind"] != "identity_unverified"]
        if level == "previous_verified" and previous is None:
            self.issue(code, "previous_missing", "previous_verified requires previous_record")
        email_supported = False
        emails = record.get("public_ir_emails", [])
        if not isinstance(emails, list):
            self.issue(code, "emails_type", "public_ir_emails must be an array")
            emails = []
        if emails:
            legacy_email = isinstance(previous, dict) and previous.get("verification_level") == "page_and_email_verified"
            email_supported = all(any(self.successful(s) and
                                      (associated_public_email(e, s, address) or legacy_email and address in e["quote"] and associated_email(s["text"], address))
                                      for e, s in pairs) or self.derived_public_email(record, pairs, address)
                                  or self.reviewed_public_email(record, pairs, address) for address in emails)
            if (operation_email_supported := self.reviewed_ir_email_only_operation(record, pairs, emails)) is not None:
                email_supported = operation_email_supported
            if (literal_mail_supported := self.reviewed_ir_literal_mail_substitution(record, pairs, emails)) is not None:
                email_supported = literal_mail_supported
            if not email_supported:
                self.issue(code, "email_unattributed", "An address lacks exact public IR attribution; examples/general emails do not qualify")
        # The prior manually verified schema stores an official entry URL
        # separately from its form snapshot URL. Preserve that fixed baseline
        # only at the original contact URL; new contact claims must bind their
        # own target, directly or through an exact captured iframe.
        contact_target = url_key(record.get("contact_url"))
        inherited_form = (isinstance(previous, dict) and previous.get("verification_level") == "page_and_fields_verified"
                          and contact_target is not None and contact_target == url_key(previous.get("contact_url")))
        official_url = seed.get("official_url") if isinstance(seed, dict) else record.get("official_url")
        official_host = urlsplit(official_url).hostname if url_key(official_url) else None
        form_supported = self.has_form_binding(pairs, previous, reviewed=manual_review_valid(record), target_url=None if inherited_form else contact_target, official_host=official_host)
        if (finite_form_supported := self.reviewed_finite_native_ir_form(record, pairs, seed)) is not None:
            form_supported = finite_form_supported
        if (late_form_supported := self.reviewed_late_native_ir_form(record, pairs)) is not None:
            form_supported = late_form_supported
        if (six_category_form_supported := self.reviewed_ir_six_category_opaque_form(record, pairs)) is not None:
            form_supported = six_category_form_supported
        if (captured_form_supported := self.reviewed_captured_ir_form(record, pairs)) is not None:
            form_supported = captured_form_supported
        if (policy_operation_form_supported := self.reviewed_ir_operation_after_policy(record, pairs)) is not None:
            form_supported = policy_operation_form_supported
        if (meeting_form_supported := self.reviewed_ir_meeting_reception(record, pairs)) is not None:
            form_supported = meeting_form_supported
        if (inquiry_form_supported := self.reviewed_ir_inquiry_after_privacy(record, pairs)) is not None:
            form_supported = inquiry_form_supported
        if (consent_form_supported := self.reviewed_ir_consent_two_hop_form(record, pairs)) is not None:
            form_supported = consent_form_supported
        if (group_form_supported := self.reviewed_ir_group_destination_form(record, pairs)) is not None:
            form_supported = group_form_supported
        if (japanese_form_supported := self.reviewed_ir_japanese_reply_operation(record, pairs)) is not None:
            form_supported = japanese_form_supported
        if (dedicated_child_supported := self.reviewed_ir_dedicated_financial_child(record, pairs)) is not None:
            form_supported = dedicated_child_supported
        if (holdings_store_supported := self.reviewed_ir_holdings_and_store_separation(record, pairs)) is not None:
            form_supported = holdings_store_supported
        if (faq_repeat_supported := self.reviewed_ir_faq_repeat_contact(record, pairs)) is not None:
            form_supported = faq_repeat_supported
        if (opaque_radio_supported := self.reviewed_ir_opaque_reply_radio_form(record, pairs)) is not None:
            form_supported = opaque_radio_supported
        if (enterprise_ir_supported := self.reviewed_ir_enterprise_row_category(record, pairs)) is not None:
            form_supported = enterprise_ir_supported
        if (financial_purpose_supported := self.reviewed_ir_financial_purpose_and_site_seal(record, pairs)) is not None:
            form_supported = financial_purpose_supported
        strong = email_supported or form_supported
        if level == "ir_email_verified" and not email_supported:
            self.issue(code, "email_level", "ir_email_verified has no attributed email evidence")
        if level == "form_fields_verified" and not form_supported:
            self.issue(code, "form_level", "form_fields_verified lacks a bound email/question form; search/auth/empty controls do not qualify")
        if status == "confirmed" and (not strong or level in {"official_form_link_only", "none"}):
            self.issue(code, "confirmed_without_channel", "confirmed requires a specific verified IR email or question form")
        if status == "confirmed" and isinstance(previous, dict) and previous.get("verification_level") == "official_link_only":
            # A fresh strong channel is allowed to improve a previous link-only record.
            if level == "previous_verified":
                self.issue(code, "legacy_link_promoted", "Legacy link-only evidence cannot become confirmed merely through inheritance")
        quotes = " ".join(e["quote"] for e, _ in pairs)
        outreach = record.get("outreach_suitability")
        if outreach not in {"candidate", "restricted", "no_individual_reply", "unconfirmed"}:
            self.issue(code, "outreach_suitability", "Unknown outreach suitability")
        no_reply = bool(NO_REPLY.search(quotes)) or self.reviewed_monthly_ir_faq_no_reply(record, pairs, seed)
        if no_reply and outreach != "no_individual_reply":
            self.issue(code, "reply_policy", "Explicit refusal of individual inquiries must be no_individual_reply")
        if outreach == "no_individual_reply" and not no_reply:
            self.issue(code, "reply_policy_basis", "No broad no-reply policy is evidenced; conditional delays/opinions are not equivalent")
        access = record.get("individual_access")
        if access not in {"not_stated", "explicit", "explicitly_allowed", "restricted"}:
            self.issue(code, "individual_access", "Unknown individual access value")
        if access in {"explicit", "explicitly_allowed"} and not (
            individual_access_supported(pairs, target_url=url_key(record.get("contact_url")), reviewed=manual_review_valid(record))
            or self.reviewed_individual_form_access(record, pairs, seed)
            or self.reviewed_individual_email_access(record, pairs, email_supported=email_supported)
        ):
            self.issue(code, "individual_access_basis", "Individual access needs bound form choices/instructions or a public IR email audience, not navigation")
        if outreach == "restricted" and access != "restricted":
            self.issue(code, "restricted_access", "Restricted outreach must retain restricted access")
        if outreach == "restricted" and not (
            re.search(
                r"機関投資家|アナリスト|限定|対象者|取引先|"
                r"個人(?!情報)(?:の方)?[^。]{0,50}(?:ご遠慮|受け付けておりません|お断り|対象外)|"
                r"メディア関係(?:者|の方)[^。]{0,120}専用窓口", quotes
            ) or self.reviewed_phone_limited_ir_form(record, pairs)
        ):
            self.issue(code, "restriction_basis", "Restriction requires a saved scoped eligibility quote")
        company_required = False
        for evidence, source in pairs:
            field_quote = evidence["quote"]
            if manual_review_valid(record) and any(
                reviewed_question_form(f) and re.match(r"\s*任意\s*会社名\s*必須\s*お名前(?=\s|$)", f.get("text", ""))
                for f in source.get("forms", [])
            ):
                # In a captured form beginning with prefix field markers,
                # "任意 会社名 必須 お名前" labels company OPTIONAL and name
                # REQUIRED. The next field's marker is not a company mandate.
                # This removes a warning only; it never confers personal access.
                field_quote = re.sub(r"任意\s*会社名\s*必須\s*お名前(?=\s|$)", "", field_quote)
            company_required = company_required or bool(re.search(
                r"(?:会社名|団体名|貴社名)(?:[／/][^\s]{1,15})?\s*(?:※\s*)?(?:必須|\*)", field_quote
            ))
        if company_required and access == "not_stated":
            self.issue(code, "company_field_unresolved", "Required company field with no individual instructions needs review", "warning")
        if status == "confirmed":
            flag = record.get("manual_review_required")
            if not isinstance(flag, bool):
                self.issue(code, "manual_review_flag", "Confirmed records require a boolean manual_review_required")
            if flag is False and previous is None:
                if not manual_review_valid(record):
                    self.issue(code, "manual_review_missing", "New records cleared of review require reviewed_at, reviewer, and notes")
        attempted = self.actual_official_get(record, seed)
        errors = [i for i in self.issues[before:] if i["severity"] == "error"]
        return {"security_code": code, "terminal": status in STATUSES, "investigation_status": status,
                "official_get_attempted": attempted, "channel_verified": status == "confirmed" and strong and not errors,
                "outreach_suitability": outreach, "individual_access": access,
                "manual_review_required": record.get("manual_review_required"),
                "error_count": len(errors)}

    def run(self, require_complete: bool = False) -> dict:
        seed_map = {}
        seed_path = self.root / "seeds-current.json"
        if not seed_path.exists():
            seed_path = self.root / "seeds.json"
        if seed_path.exists():
            seeds = json.loads(seed_path.read_text(encoding="utf-8"))
            if not isinstance(seeds, list):
                raise ValueError("seeds.json must contain an array")
            for seed in seeds:
                if not isinstance(seed, dict) or not isinstance(seed.get("security_code"), str) or not CODE.fullmatch(seed["security_code"]):
                    self.issue(str(seed.get("security_code") if isinstance(seed, dict) else None), "seed_code", "Seed must belong to universe")
                    continue
                code = seed["security_code"]
                if code not in self.universe:
                    self.issue(code, "outside_universe_seed_ignored", "Discovery cache contains a code outside this survey scope; ignored", "warning")
                    continue
                if code in seed_map:
                    self.issue(code, "duplicate_seed", "Duplicate seed")
                if not url_key(seed.get("official_url")):
                    self.issue(code, "seed_url", "Seed lacks an HTTP(S) official_url")
                seed_map[code] = seed
        evaluated = {}
        for path in sorted((self.root / "records").glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(record, dict):
                    raise ValueError("Record must be an object")
            except (OSError, ValueError) as error:
                self.issue(path.stem, "record_unreadable", type(error).__name__)
                continue
            code = record.get("security_code")
            if path.stem != code:
                self.issue(str(code), "record_filename", "Record filename must match security_code")
            if code in evaluated:
                self.issue(str(code), "duplicate_record", "Duplicate record code")
                continue
            result = self.validate_record(record, seed_map.get(code))
            if code in self.universe:
                evaluated[code] = result
        missing = sorted(set(self.universe) - set(evaluated))
        if require_complete and missing:
            self.issue("*", "incomplete_universe", f"{len(missing)} issuers have no record")
        n = len(self.universe)
        terminal = sum(r["terminal"] for r in evaluated.values())
        attempted = sum(r["official_get_attempted"] for r in evaluated.values())
        verified = sum(r["channel_verified"] for r in evaluated.values())
        candidates = sum(r["channel_verified"] and r["outreach_suitability"] == "candidate" for r in evaluated.values())
        reviewed_candidates = sum(r["channel_verified"] and r["outreach_suitability"] == "candidate" and r["manual_review_required"] is False for r in evaluated.values())
        def coverage(count: int) -> dict:
            return {"numerator": count, "denominator": n, "fraction": f"{count / n:.6f}"}
        return {"format": "ir_universe_validation", "format_version": 1,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "universe_count": n, "scope": sorted(DOMESTIC_MARKETS),
                "record_count": len(evaluated), "declared_status_counts": dict(Counter(r.get("investigation_status") for r in evaluated.values())),
                "terminal_record_coverage": coverage(terminal), "official_get_attempt_coverage": coverage(attempted),
                "channel_verified_coverage": coverage(verified), "verified_outreach_candidate_count": candidates,
                "reviewed_verified_outreach_candidate_count": reviewed_candidates,
                "missing_record_codes": missing, "error_count": sum(i["severity"] == "error" for i in self.issues),
                "warning_count": sum(i["severity"] == "warning" for i in self.issues),
                "issues": self.issues, "records": list(evaluated.values()), "known_false_positive_patterns": KNOWN_RISKS,
                "limitations": ["構造・引用・状態の検証であり、全社の分類精度の実測ではない。",
                                "公式サイトの選定自体とメール/フォームの送信・到達・返信はこの検証器の対象外。",
                                "confirmedは実証された窓口の意味で、投資推奨や個人受付の保証ではない。"]}


class ValidationTests(unittest.TestCase):
    def test_preserves_query(self):
        self.assertNotEqual(url_key("https://example.jp/form?cd=ir"), url_key("https://example.jp/form?cd=product"))
        self.assertEqual(url_key("https://example.jp/form?cd=ir#top"), url_key("https://example.jp/form?cd=ir"))

    def test_same_form_required(self):
        self.assertFalse(question_form({"controls": [{"type": "email", "name": "email"}]}))
        self.assertFalse(question_form({"controls": [{"name": "message", "tag": "textarea"}]}))
        self.assertTrue(question_form({"controls": [{"name": "email", "type": "text"}, {"name": "message", "tag": "textarea"}]}))

    def test_search_and_hidden_are_not_question_form(self):
        self.assertFalse(question_form({"controls": [{"name": "email", "type": "hidden"}, {"name": "message", "type": "search"}]}))
        self.assertFalse(question_form({"controls": []}))

    def test_generic_names_are_not_proof(self):
        self.assertFalse(question_form({"controls": [{"name": "field1", "type": "email"}, {"name": "field2", "type": "text"}]}))

    def test_email_scope(self):
        quote = "MAIL info@baycurrent.co.jp IRに関するお問い合わせ ir@baycurrent.co.jp"
        self.assertFalse(associated_email(quote, "info@baycurrent.co.jp"))
        self.assertTrue(associated_email(quote, "ir@baycurrent.co.jp"))
        self.assertFalse(associated_email("IRに関するお問い合わせ 個人情報窓口 privacy@example.co.jp", "privacy@example.co.jp"))

    def test_example_email(self):
        self.assertFalse(associated_email("IRに関するお問い合わせ メール入力例 example@issuer.co.jp", "example@issuer.co.jp"))

    def test_obfuscation_requires_instruction(self):
        self.assertFalse(associated_email("IRお問い合わせ ir★issuer.co.jp", "ir@issuer.co.jp"))
        self.assertTrue(associated_email("IRお問い合わせ ir★issuer.co.jp （★部分を@に置き換えてください）", "ir@issuer.co.jp"))

    def test_no_reply_is_not_delay_or_opinion_exclusion(self):
        self.assertTrue(NO_REPLY.search("個別の問い合わせにつきましては取次も含めて回答しない方針としております。"))
        self.assertFalse(NO_REPLY.search("内容によっては回答できかねる場合があります。"))
        self.assertFalse(NO_REPLY.search("ご意見やご感想は個別の回答を差し控えます。"))

    def fixture(self, directory: Path, *, text="IRに関するお問い合わせフォーム", forms=None, status=200):
        evidence = {"requested_url": "https://issuer.co.jp/ir/contact", "url": "https://issuer.co.jp/ir/contact",
                    "http_status": status, "text": text, "links": [], "forms": forms or [],
                    "submitted": False, "retrieved_at": "2026-10-11T01:00:00+00:00"}
        (directory / "evidence").mkdir(exist_ok=True)
        (directory / "evidence/page.json").write_text(json.dumps(evidence), encoding="utf-8")
        record = {"security_code": "1301", "company_name": "Fixture", "market": "プライム（内国株式）",
                  "investigation_status": "confirmed", "verification_level": "form_fields_verified",
                  "contact_url": evidence["url"], "channels": ["form"], "public_ir_emails": [],
                  "individual_access": "not_stated", "outreach_suitability": "candidate",
                  "attempted_at": "2026-10-11T01:00:00+00:00", "completed_at": "2026-10-11T01:01:00+00:00",
                  "manual_review_required": True, "fetches": [{"snapshot": "evidence/page.json"}],
                  "identity_status": "name_or_security_code_observed", "identity_matches": [{"snapshot": "evidence/page.json"}],
                  "evidence": [{"snapshot": "evidence/page.json", "url": evidence["url"],
                                "retrieved_at": evidence["retrieved_at"], "quote": text}]}
        # The ordinary fixture has an explicit name witness. Individual tests
        # may alter that evidence to exercise an identity failure instead.
        evidence["text"] += " Fixture"
        (directory / "evidence/page.json").write_text(json.dumps(evidence), encoding="utf-8")
        validator = SurveyValidator(directory, {"1301": {"market": "プライム（内国株式）", "company_name": "Fixture"}})
        return validator, record

    def test_confirmed_bound_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), forms=[{"controls": [{"name": "email"}, {"name": "message"}]}])
            result = validator.validate_record(record, {"official_url": "https://issuer.co.jp/"})
            self.assertTrue(result["channel_verified"])
            self.assertTrue(result["official_get_attempted"])

    def test_phone_ir_does_not_transfer_to_customer_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), text="製品のお問い合わせフォーム IR情報に関するお問い合わせ 電話のみ",
                                             forms=[{"text": "製品について 店舗を選択", "controls": [{"name": "email"}, {"name": "message"}]}])
            # The first page title is product contact, not an IR title. Narrow
            # quote demonstrates only the phone section, not a form binding.
            record["evidence"][0]["quote"] = "IR情報に関するお問い合わせ 電話のみ"
            result = validator.validate_record(record)
            self.assertFalse(result["channel_verified"])

    def test_empty_fields_cannot_confirm(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp))
            self.assertFalse(validator.validate_record(record)["channel_verified"])

    def test_failed_page_cannot_confirm(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), status=403, forms=[{"controls": [{"name": "email"}, {"name": "message"}]}])
            self.assertFalse(validator.validate_record(record, {"official_url": "https://issuer.co.jp/"})["channel_verified"])

    def test_quote_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), forms=[{"controls": [{"name": "email"}, {"name": "message"}]}])
            record["evidence"][0]["quote"] = "Invented quote"
            self.assertFalse(validator.validate_record(record)["channel_verified"])
            self.assertIn("quote_mismatch", [i["kind"] for i in validator.issues])

    def test_no_reply_policy_is_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), text="IRお問い合わせ 個別の問い合わせにつきましては取次も含めて回答しない方針です。")
            record.update(investigation_status="provisional", verification_level="official_form_link_only")
            validator.validate_record(record)
            self.assertIn("reply_policy", [i["kind"] for i in validator.issues])

    def test_navigation_not_individual_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), text="IRお問い合わせ 個人投資家の皆様へ", forms=[{"controls": [{"name": "email"}, {"name": "message"}]}])
            record["individual_access"] = "explicit"
            validator.validate_record(record)
            self.assertIn("individual_access_basis", [i["kind"] for i in validator.issues])

    def test_manual_review_must_be_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp), forms=[{"controls": [{"name": "email"}, {"name": "message"}]}])
            record["manual_review_required"] = False
            self.assertFalse(validator.validate_record(record)["channel_verified"])
            self.assertIn("manual_review_missing", [i["kind"] for i in validator.issues])

    def test_seed_missing_is_processing_not_get_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "records").mkdir()
            validator, record = self.fixture(root)
            record.update(investigation_status="unconfirmed", verification_level="none",
                          outreach_suitability="unconfirmed", fetches=[], evidence=[])
            (root / "records/1301.json").write_text(json.dumps(record), encoding="utf-8")
            report = validator.run(require_complete=True)
            self.assertEqual(report["terminal_record_coverage"]["numerator"], 1)
            self.assertEqual(report["official_get_attempt_coverage"]["numerator"], 0)
            self.assertEqual(report["channel_verified_coverage"]["numerator"], 0)

    def test_legacy_link_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp))
            record.update(verification_level="previous_verified", manual_review_required=False,
                          previous_record={"security_code": "1301", "verification_level": "official_link_only"})
            validator.validate_record(record)
            self.assertIn("legacy_link_promoted", [i["kind"] for i in validator.issues])

    def test_wrong_previous_company(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp))
            record.update(verification_level="previous_verified", previous_record={"security_code": "1302"})
            validator.validate_record(record)
            self.assertIn("previous_company", [i["kind"] for i in validator.issues])

    def test_numeric_code_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            validator, record = self.fixture(Path(tmp)); record["security_code"] = 1301
            self.assertFalse(validator.validate_record(record)["terminal"])

    def test_universe_filter_and_letter_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "universe.csv"
            path.write_text("security_code,company_name,market\n590A,Example,プライム（内国株式）\n1305,Fund,ETF・ETN\n131A,Pro,PRO Market\n25935,Class,プライム（内国株式）\n", encoding="utf-8-sig")
            self.assertEqual(set(read_universe(path)), {"590A"})

    def test_universe_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "universe.csv"
            path.write_text("security_code,market\n590A,プライム（内国株式）\n590A,プライム（内国株式）\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_universe(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--universe", type=Path)
    parser.add_argument("--previous-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ValidationTests))
        return 0 if result.wasSuccessful() else 1
    if args.directory is None:
        parser.error("directory is required unless --self-test is used")
    try:
        universe = read_universe(args.universe or args.directory / "universe.csv")
        report = SurveyValidator(args.directory, universe, args.previous_root).run(args.require_complete)
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key not in {"issues", "records", "known_false_positive_patterns", "missing_record_codes"}}, ensure_ascii=False))
    else:
        print(encoded, end="")
    return 1 if report["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
