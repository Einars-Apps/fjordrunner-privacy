#!/usr/bin/env python3
"""Validate huawei.html only. Does not publish GitHub Pages."""

import hashlib
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUAWEI = ROOT / "huawei.html"
INDEX = ROOT / "index.html"
PRIVACY = ROOT / "privacy.html"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-huawei-privacy.yml"

PLAY_IOS_SHA256 = "3faf5cd211988465efee693964a556da5ba06135a6d82a2ae32f05e2c3db09e2"

ALLOWED_HREFS = {
    "#norsk",
    "#english",
    "mailto:matsjekk@gmail.com",
    "privacy.html",
    "https://einars-apps.github.io/fjordrunner-privacy/huawei.html",
    "https://developer.huawei.com/consumer/en/doc/hmscore-guides/whale-hong-kinetic-energy-sdk-privacy-statement-0000001658283582",
    "https://developer.huawei.com/consumer/en/doc/HMSCore-Guides/sdk-data-security-0000001050044906",
}

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "source", "track", "wbr",
}

NO_REQUIRED = [
    "Personvernerklæring – Fjordrunner Light for Huawei AppGallery",
    "Android-appen for AppGallery, ikke en egen HarmonyOS-applikasjon",
    "Einar Børsheim / Einars-Apps",
    "com.fjordrunner.light",
    "com.huawei.hms:ads-lite:13.4.91.301",
    "com.huawei.hms:iap:6.16.6.305",
    "ALLOW_NON_PERSONALIZED",
    "Det betyr ikke at Huawei lar være å behandle opplysninger.",
    "ingen nettbasert toppliste",
    "fr_ad_consent",
    "remove_ads",
    "starter_pack",
    "coins_500",
    "coins_1000",
    "coins_3000",
    "500 mynter",
    "1200 mynter",
    "3600 mynter",
    "1000 mynter",
    "hvert tredje tapte løp",
    "Annonser: av",
    "Annonser: på",
    "Ikke nå",
    "uttrykkelig ikke autorisert til å aktiveres",
    "annonser er ikke aktive",
    "dersom annonser senere er konfigurert og du har samtykket",
    "fullskjerms interstitial-annonser, som kan være bilde eller video",
    "eller direkte med butikkens av/på-bryter",
    "starter SDK-en ved første forsøk på å vise en annonse",
    "forhåndslaste når appen gjenopptas, når en annonse lukkes, når annonser slås på igjen, og når en annonse ikke er tilgjengelig",
    "Senere visningsforsøk og disse forhåndslastingene kan sende nye forespørsler",
    "Denne stien er ikke aktiv i Huawei-pakken som er ute nå.",
]

EN_REQUIRED = [
    "Privacy policy – Fjordrunner Light for Huawei AppGallery",
    "not a native HarmonyOS application",
    "Einar Børsheim / Einars-Apps",
    "com.fjordrunner.light",
    "com.huawei.hms:ads-lite:13.4.91.301",
    "com.huawei.hms:iap:6.16.6.305",
    "ALLOW_NON_PERSONALIZED",
    "It does not mean Huawei processes no information.",
    "no online leaderboard",
    "fr_ad_consent",
    "remove_ads",
    "starter_pack",
    "coins_500",
    "coins_1000",
    "coins_3000",
    "500 coins",
    "1,200 coins",
    "3,600 coins",
    "1,000 coins",
    "every third failed run",
    "Ads: off",
    "Ads: on",
    "Not now",
    "explicitly not authorized to activate",
    "ads are not active",
    "only if ads are later configured and you have consented",
    "full-screen interstitial ads, which can be an image or a video",
    "or directly with the shop Ads off/on control",
    "starts on the first attempt to show an ad",
    "preload when the app resumes, when an ad is closed, when ads are toggled back on, and when an ad is unavailable",
    "Later show attempts and those preloads can send further requests",
    "This path is not active in the released Huawei package.",
]

FORBIDDEN = [
    "HarmonyOS-appen",
    "the HarmonyOS app",
    "Analytics purpose",
    "Analyseformålet",
    "AppGallery-skjemaet",
    "AppGallery form",
    "meant to include",
    "ment å ha",
    "Petal-annonseplass",
    "Petal ad slot",
    "ikke er konfigurert",
    "not configured",
    "Firebase-nøkkel",
    "Firebase key",
    "IAP-nøkkelen",
    "IAP public key",
    "AdMob",
    "GDPR",
    "CCPA",
    "vi overholder",
    "we comply",
    "Videoannonser kommer",
    "Video ads come from",
    "only after you tap",
    "only when the game then asks",
    "først etter at du trykker",
    "etter Tillat og et faktisk annonsekall",
    "after Allow and an actual ad request",
    "actual ad request",
    "faktisk annonsekall",
    "no ad slot",
    "without an ad slot",
    "without a slot",
    "missing slot",
    "uten annonseplass",
    "annonseplass",
    "Petal",
    "fail-closed",
    "failclosed",
    "under-18 tag",
    "under18",
    "child tag",
    "barnetagg",
    "child-directed",
]


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = []
        self.hrefs = []
        self.h2_ids = []
        self.errors = []
        self.saw_charset = False
        self.section = None
        self.section_text = {"norsk": [], "english": []}
        self.saw_script = False

    def handle_starttag(self, tag, attrs):
        attr = {k: v for k, v in attrs}
        if tag == "script":
            self.saw_script = True
        if tag == "meta" and attr.get("charset", "").lower() == "utf-8":
            self.saw_charset = True
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "h2":
            self.h2_ids.append(attr.get("id"))
        if tag in {"a", "link"} and "href" in attr:
            self.hrefs.append(attr["href"])
        if tag == "section" and attr.get("id") in self.section_text:
            self.section = attr["id"]
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "section" and self.section:
            self.section = None
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}>; open stack {self.stack}")
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.section:
            self.section_text[self.section].append(data)


def fail(messages):
    for message in messages:
        print(f"FAIL {message}")
    sys.exit(1)


def main():
    errors = []
    if not HUAWEI.is_file():
        fail(["huawei.html is missing"])

    raw = HUAWEI.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("huawei.html must be UTF-8 without a BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail([f"huawei.html is not UTF-8: {exc}"])

    for mark in ("æ", "ø", "å", "Børsheim", "Personvernerklæring"):
        if mark not in text:
            errors.append(f"missing UTF-8 text {mark!r}")

    parser = Checker()
    parser.feed(text)
    parser.close()
    errors.extend(parser.errors)
    if parser.stack:
        errors.append(f"unclosed tags: {parser.stack}")
    if not text.lstrip().startswith("<!DOCTYPE html>"):
        errors.append("missing HTML5 doctype")
    if not parser.saw_charset:
        errors.append("missing meta charset utf-8")
    if parser.saw_script:
        errors.append("script elements are not allowed")

    ids = parser.ids
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate ids: {ids}")
    for anchor in ("norsk", "english"):
        if ids.count(anchor) != 1:
            errors.append(f"missing anchor id {anchor}")
        if f"#{anchor}" not in parser.hrefs:
            errors.append(f"missing link to #{anchor}")

    if any(not h2_id for h2_id in parser.h2_ids):
        errors.append(f"h2 without id: {parser.h2_ids}")
    if len(parser.h2_ids) != 14:
        errors.append(f"expected 14 section headings, found {parser.h2_ids}")

    unknown = sorted(set(parser.hrefs) - ALLOWED_HREFS)
    if unknown:
        errors.append(f"unexpected links: {unknown}")
    for href in (
        "mailto:matsjekk@gmail.com",
        "privacy.html",
        "https://developer.huawei.com/consumer/en/doc/hmscore-guides/whale-hong-kinetic-energy-sdk-privacy-statement-0000001658283582",
        "https://developer.huawei.com/consumer/en/doc/HMSCore-Guides/sdk-data-security-0000001050044906",
    ):
        if parser.hrefs.count(href) < 2:
            errors.append(f"expected {href} in both languages")

    norsk = "".join(parser.section_text["norsk"])
    english = "".join(parser.section_text["english"])
    if not norsk or not english:
        errors.append("Norwegian and English sections must both contain text")
    if text.find('id="norsk"') > text.find('id="english"'):
        errors.append("Norwegian section must come before English")
    for snippet in NO_REQUIRED:
        if snippet not in norsk:
            errors.append(f"Norwegian section missing {snippet!r}")
    for snippet in EN_REQUIRED:
        if snippet not in english:
            errors.append(f"English section missing {snippet!r}")
    for snippet in FORBIDDEN:
        if snippet in text:
            errors.append(f"forbidden wording present: {snippet!r}")

    for path in (INDEX, PRIVACY):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != PLAY_IOS_SHA256:
            errors.append(f"{path.name} changed; Play/iOS pages must stay untouched")
        page = path.read_text(encoding="utf-8")
        if "4. september 2026" not in page or "4 September 2026" not in page:
            errors.append(f"{path.name} lost the 4 September 2026 policy date")
        if "13.4.91.301" in page or "huawei.html" in page:
            errors.append(f"{path.name} must not advertise the Huawei edition")

    if not WORKFLOW.is_file():
        errors.append("validation workflow is missing")
    else:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        active = "\n".join(
            line for line in workflow.splitlines() if not line.strip().startswith("#")
        )
        for banned in ("workflow_dispatch", "deploy-pages", "upload-pages-artifact", "peaceiris"):
            if banned in active:
                errors.append(f"workflow must not publish or dispatch: found {banned}")
        if "python3 tests/test_huawei_privacy.py" not in workflow:
            errors.append("workflow does not run the HTML test")

    if errors:
        fail(errors)
    print("ok huawei.html utf-8 anchors no+en links; index.html and privacy.html unchanged")


if __name__ == "__main__":
    main()
