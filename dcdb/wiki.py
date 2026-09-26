"""Pure wikitext helpers for DC Database pages (no I/O).

Everything here mirrors what the wiki itself does (templates in the `DC Database:`
namespace, `Template:C`, `Module:StaffCorrection`), confirmed against the dump.
"""
import calendar
import html
import json
import re
from datetime import datetime
from urllib.parse import quote

import mwparserfromhell as mw

BASE_URL = "https://dc.fandom.com/wiki/"

# Infobox template -> page kind
KINDS = {
    "Comic Template": "issue",
    "Digital Comic Template": "issue",
    "Collected Template": "collection",
    "Event Template": "event",
    "Storyline Template": "event",
    "Volume Template": "series",
    "Character Template": "character",
    "Staff Template": "staff",
}

ROLES = {
    "writer": "writer", "penciler": "penciler", "penciller": "penciler", "inker": "inker",
    "colorist": "colorist", "colourist": "colorist", "letterer": "letterer", "editor": "editor",
    "artist": "artist", "breakdowns": "breakdowns", "plotter": "plotter", "scripter": "scripter",
}
CREDIT_RE = re.compile(r"^([A-Za-z]+?)(\d+)(?:_(\d+))?$")
COVER_RE = re.compile(r"^CoverArtist(\d+)$", re.I)
VARIANT_RE = re.compile(r"^Cover(\d+)Artist(\d+)$", re.I)
ISSUE_TITLE_RE = re.compile(r"^(.+) Vol (\d+) (.+?)( \(Digital\))?$")
ISSUE_LINK_RE = re.compile(r"^.+ Vol \d+ \S")
COMMENT_RE = re.compile(r"<!--.*?(?:-->|$)", re.S)
REF_RE = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", re.S | re.I)
BR_RE = re.compile(r"<br\s*/?>", re.I)

# Templates whose text is kept by textify(): display text is the 2nd positional arg if any, else the 1st.
KEEP_TPL = {"c", "cnst", "co", "v", "dig", "a", "wp", "wp2", "idb", "2000ad", "w", "wikipedia"}
ISSUE_TPL = {"c", "cnst", "dig"}

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS |= {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
MONTHS |= {"sept": 9, "winter": 1, "spring": 4, "summer": 7, "fall": 10, "autumn": 10, "holiday": 12}


def norm_title(t):
    """MediaWiki title normalization: entities, underscores, spaces, fragment, first letter."""
    t = html.unescape(t or "").replace("_", " ").split("#", 1)[0]
    t = re.sub(r"\s+", " ", t).strip().lstrip(":").strip()
    return t[:1].upper() + t[1:]


def page_url(title):
    return BASE_URL + quote(title.replace(" ", "_"), safe=";@$!*(),/~:")


def c_ref(s):
    """Target page of {{c|...}} exactly as Template:C builds it ('Batman #676' -> 'Batman Vol 1 676')."""
    s = s.strip()
    if "Vol" in s:
        return s.replace("#", "")
    if "#" in s:
        series, _, num = s.partition(" #") if " #" in s else s.partition("#")
        return f"{series.strip()} Vol 1 {num.strip()}"
    return s


def strip_comments(s):
    return COMMENT_RE.sub("", s or "")


def _positional(t):
    return [str(p.value).strip() for p in t.params if not p.showkey]


def textify(s, link_target=False):
    """Wikitext -> plain text. Keeps link/ref-template display text, drops other templates.
    link_target=True returns link targets instead of display text (used for credit names)."""
    s = BR_RE.sub("\n", REF_RE.sub("", strip_comments(s)))
    if "{" not in s and "[" not in s and "'" not in s and "<" not in s and "&" not in s:
        return s.strip()
    code = mw.parse(s)
    for t in reversed(code.filter_templates()):
        pos = _positional(t)
        name = str(t.name).strip().lower()
        text = ""
        if name in KEEP_TPL and pos:
            text = pos[0] if (link_target or len(pos) < 2) else pos[1]
        try:
            code.replace(t, text)
        except ValueError:
            pass
    for link in code.filter_wikilinks():
        target = str(link.title).strip()
        low = target.lower().lstrip(":")
        try:
            if low.startswith(("file:", "image:", "category:")):
                code.remove(link)
            elif link_target:
                code.replace(link, target)
        except ValueError:
            pass
    text = html.unescape(code.strip_code(normalize=True, collapse=True))
    return re.sub(r"[ \t]+", " ", text).strip()


def infobox(code):
    """First top-level `{{DC Database:X Template}}` -> (template short name, {param: raw value})."""
    for t in code.filter_templates(recursive=False):
        name = str(t.name).strip()
        if name.startswith("DC Database:") and name.endswith("Template"):
            params = {}
            for p in t.params:
                params.setdefault(str(p.name).strip(), str(p.value).strip())
            return name.split(":", 1)[1].strip(), params
    return None, {}


def get(params, *keys):
    """Case-insensitive param lookup; first non-empty value (comments stripped)."""
    low = {k.lower(): v for k, v in params.items()}
    for k in keys:
        v = strip_comments(low.get(k.lower(), "")).strip()
        if v:
            return v
    return ""


def parse_month(v):
    v = textify(v).strip().lower().rstrip(".x")
    v = re.sub(r"^(late|early|mid)\s+", "", v)
    if v.isdigit():
        n = int(v)
        return n if 1 <= n <= 12 else None
    return MONTHS.get(v)


def _int(v, lo=None, hi=None):
    m = re.match(r"\d+", textify(v))
    n = int(m.group()) if m else None
    if n is not None and ((lo is not None and n < lo) or (hi is not None and n > hi)):
        return None
    return n


def fmt_date(y, m=None, d=None):
    if not y:
        return None
    s = f"{y:04d}"
    if m:
        s += f"-{m:02d}"
        if d:
            s += f"-{d:02d}"
    return s


def parse_release_date(v):
    v = textify(v).replace("  ", " ").strip()
    for f in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %B %Y", "%B %d %Y"):
        try:
            d = datetime.strptime(v, f)
            return fmt_date(d.year, d.month, d.day)
        except ValueError:
            pass
    return None


def issue_dates(p, digital=False):
    """(cover_date, pub_date, pub_date_source) following the Comic Template rules:
    Month/Year = cover date; Day = on-sale day; publication = Pubmonth/Pubyear if given,
    else cover month - 2 (the template's own default). No Day and no Pub* -> 'estimated'."""
    y = _int(get(p, "Year"), 1000, 2999)
    m = parse_month(get(p, "Month"))
    d = _int(get(p, "Day", "Pubday"), 1, 31)
    cover = fmt_date(y, m)
    if digital:
        return None, fmt_date(y, m, d), "digital"
    rel = parse_release_date(get(p, "ReleaseDate", "Release Date")) if get(p, "ReleaseDate", "Release Date") else None
    if rel:
        return cover, rel, "release_date"
    py = _int(get(p, "Pubyear"), 1000, 2999)
    if py:
        pm = parse_month(get(p, "Pubmonth"))
        return cover, fmt_date(py, pm, d if pm else None), "pub_fields"
    if y and m:
        pm, py = (m - 2, y) if m > 2 else (m + 10, y - 1)
        return cover, fmt_date(py, pm, d), "day" if d else "estimated"
    return cover, fmt_date(y), "estimated" if y else None


def clean_person(v):
    """Credit value -> person name (link target, no comments/refs). None if empty/unknown."""
    s = textify(v, link_target=True).split("\n")[0].strip().rstrip("?").strip()
    s = re.sub(r"\s+", " ", s)
    low = s.lower()
    if not s or low in ("uncredited", "n/a", "na", "unknown", "-", "&mdash;", "—", "?"):
        return "Uncredited" if low in ("uncredited", "n/a", "na") else None
    return s


def credits(params, kind):
    """[(story_index, role, order_index, raw, person)] from infobox params.
    Issues: Role{story}_{n}; collections: Role{n} (story_index 0); covers are story 0."""
    out = []
    for k, v in params.items():
        if not strip_comments(v).strip():
            continue
        m = COVER_RE.match(k)
        if m:
            out.append((0, "cover_artist", int(m.group(1)), v, clean_person(v)))
            continue
        m = VARIANT_RE.match(k)
        if m:
            out.append((0, "variant_cover_artist", int(m.group(1)) * 100 + int(m.group(2)), v, clean_person(v)))
            continue
        if k.lower() in ("executive editor", "executiveeditor"):
            out.append((0, "executive_editor", 1, v, clean_person(v)))
            continue
        if k.lower() in ("editor-in-chief", "editor in chief"):
            out.append((0, "editor_in_chief", 1, v, clean_person(v)))
            continue
        m = CREDIT_RE.match(k)
        if m and m.group(1).lower() in ROLES:
            role = ROLES[m.group(1).lower()]
            a, b = int(m.group(2)), m.group(3)
            if kind == "collection":
                story, order = 0, a
            else:
                story, order = a, int(b) if b else 1
            out.append((story, role, order, v, clean_person(v)))
    return [c for c in out if c[4]]


def split_list(v):
    """'A; B' / 'A, B' / links -> list of link targets or texts (for Event/StoryArcs params)."""
    v = strip_comments(v)
    code = mw.parse(v)
    links = [str(l.title).strip() for l in code.filter_wikilinks()]
    tpls = [c_ref(_positional(t)[0]) for t in code.filter_templates()
            if str(t.name).strip().lower() in KEEP_TPL and _positional(t)]
    if links or tpls:
        return [x for x in tpls + links if x]
    return [x.strip() for x in re.split(r"[;\n]|<br\s*/?>", textify(v)) if x.strip()]


def list_items(text):
    """Bulleted issue list (collection IssueList, event Issues) -> ordered
    [{'title', 'story', 'section'}]. Refs: {{c}}/{{cnst}}/{{dig}} or [[X Vol N #]] links."""
    items, section = [], None
    for line in strip_comments(text).splitlines():
        s = line.strip()
        if not s:
            continue
        if not s.startswith(("*", "#")):
            if s.startswith(("'''", "=")):
                h = textify(s).strip(" :=")
                if h and len(h) < 100:
                    section = h
            continue
        body = s.lstrip("*#:").strip()
        code = mw.parse(body)
        refs = []
        for t in code.filter_templates():
            if str(t.name).strip().lower() in ISSUE_TPL and _positional(t):
                refs.append(c_ref(_positional(t)[0]))
                try:
                    code.remove(t)
                except ValueError:
                    pass
        if not refs:
            for link in code.filter_wikilinks():
                target = str(link.title).strip()
                if ISSUE_LINK_RE.match(target) and not target.lower().startswith(("file:", "category:")):
                    refs.append(target)
                    try:
                        code.remove(link)
                    except ValueError:
                        pass
        rest = textify(str(code)).strip(" :-–—\t")
        rest = re.sub(r'^\(?\s*"(.*)"\s*\)?$', r"\1", rest)
        rest = re.sub(r"^\((.*)\)$", r"\1", rest).strip()
        if not refs:
            if s.startswith("**") and items and not items[-1]["story"] and rest:
                items[-1]["story"] = rest.strip('"')
            elif rest and len(rest) < 100:
                section = rest  # bullet that is itself a heading (e.g. a sub-series link)
            continue
        for r in refs:
            t = norm_title(r)
            if t:
                items.append({"title": t, "story": (rest or None) if len(refs) == 1 else None, "section": section})
    return items


def parse_issue_title(title):
    """'Batman Vol 1 676' -> ('Batman', 1, '676', False)."""
    m = ISSUE_TITLE_RE.match(title)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3), bool(m.group(4))


def num_sort(n):
    m = re.match(r"-?\d+(?:\.\d+)?", n or "")
    if m:
        return float(m.group())
    return 0.5 if n in ("½", "1/2") else None


def categories(code):
    return [norm_title(str(l.title).split(":", 1)[1]) for l in code.filter_wikilinks()
            if str(l.title).strip().lower().startswith("category:")]


def process_page(page):
    """(id, title, text, timestamp) of a ns-0 content page -> dict of rows for ingest."""
    pid, title, text, ts = page
    code = mw.parse(text)
    tname, p = infobox(code)
    kind = KINDS.get(tname, "other")
    lines = [title]
    fields = {}
    for k, v in p.items():
        if k.lower().startswith("image") or not strip_comments(v).strip():
            continue
        t = textify(v)
        if t:
            lines.append(f"{k}: {t}")
            if len(t) <= 300:
                fields[k] = t
    cats = categories(code)
    for t in code.filter_templates(recursive=False):
        if str(t.name).strip().startswith("DC Database:"):
            code.remove(t)
            break
    body = textify(str(code))
    if body:
        lines.append(body)
    # Short, high-signal text for search ranking: names/aliases, plus story titles for issues (added below).
    # (An issue's Title param is just the series name, so issues only get their story titles.)
    headline = [] if kind == "issue" else [
        fields[k] for k in ("OfficialName", "Title", "RealName", "MainAlias", "Aliases") if k in fields]
    row = {
        "page": (pid, title, page_url(title), 0, kind, tname, text, "\n".join(lines), ts),
        "headline": headline,
        "fields": fields, "credits": [], "issue": None, "contents": [], "members": [],
        "categories": cats,
    }
    if kind in ("issue", "collection"):
        row["credits"] = [(pid, *c) for c in credits(p, kind)]
    if kind == "issue":
        digital = tname == "Digital Comic Template"
        parsed = parse_issue_title(title)
        if parsed:
            series, vol, num, dig = parsed
        else:
            series, vol, num, dig = get(p, "Title") or title, _int(get(p, "Volume")), get(p, "Issue"), digital
        cover, pub, src = issue_dates(p, digital)
        stories = []
        for k in sorted((k for k in p if re.fullmatch(r"StoryTitle\d+", k)), key=lambda k: int(k[10:])):
            stories.append({"index": int(k[10:]), "title": textify(p[k]) or None})
        row["headline"] += [st["title"] for st in stories if st["title"]]
        series_page = f"{series} Vol {vol}" + (" (Digital)" if dig else "") if vol else None
        row["issue"] = (pid, series, vol, num, series_page, cover, pub, src, num_sort(num),
                        json.dumps(stories, ensure_ascii=False))
        for k in sorted(k for k in p if re.fullmatch(r"Event\d*", k)):
            for e in split_list(p[k]):
                row["members"].append((e, title, "issue_event_param", None, None))
        for s in stories:
            for link in mw.parse(p.get(f"StoryTitle{s['index']}", "")).filter_wikilinks():
                row["members"].append((str(link.title).strip(), title, "story_title_link", None, None))
    elif kind == "collection":
        for i, it in enumerate(list_items(get(p, "IssueList")), 1):
            row["contents"].append((pid, it["title"], it["story"], it["section"], i))
        for e in split_list(get(p, "StoryArcs")):
            row["members"].append((e, title, "collection_storyarcs", None, None))
    elif kind == "event":
        for i, it in enumerate(list_items(get(p, "Issues")), 1):
            row["members"].append((title, it["title"], "event_issues_list", i, it["section"]))
    return row
