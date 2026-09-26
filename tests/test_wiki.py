"""Parser unit tests on wikitext shaped like the real dump (see docs/muestras.md)."""
from dcdb.wiki import c_ref, clean_person, credits, issue_dates, list_items, page_url, process_page


def test_c_ref_follows_template_c():
    assert c_ref("Batman #676") == "Batman Vol 1 676"
    assert c_ref("Batman Vol 1 676") == "Batman Vol 1 676"
    assert c_ref("Green Lantern Vol 4 #25").split() == ["Green", "Lantern", "Vol", "4", "25"]
    assert c_ref("Final Crisis Aftermath: Run! #1") == "Final Crisis Aftermath: Run! Vol 1 1"


def test_issue_dates():
    # cover month/year only -> publication estimated as cover - 2 months
    assert issue_dates({"Month": "June", "Year": "2008"}) == ("2008-06", "2008-04", "estimated")
    # Day = on-sale day, month = cover - 2 (Batman Vol 3 125)
    assert issue_dates({"Day": "5", "Month": "9", "Year": "2022"}) == ("2022-09", "2022-07-05", "day")
    # January/February cover wraps to previous year (Batman Vol 1 682)
    assert issue_dates({"Day": "3", "Month": "1", "Year": "2009"}) == ("2009-01", "2008-11-03", "day")
    assert issue_dates({"Month": "12", "Year": "1987", "Pubmonth": "8 <!-- GCD -->", "Pubyear": "1987",
                        "Day": "2"}) == ("1987-12", "1987-08-02", "pub_fields")
    assert issue_dates({"Month": "7", "Year": "2011", "ReleaseDate": "May 11, 2011"})[1:] == ("2011-05-11",
                                                                                           "release_date")
    assert issue_dates({"Day": "26", "Month": "3", "Year": "2014"}, digital=True) == (None, "2014-03-26", "digital")


def test_clean_person():
    assert clean_person("[[Tony S. Daniel|Daniel]]") == "Tony S. Daniel"
    assert clean_person("Alex Ross <!-- paints -->") == "Alex Ross"
    assert clean_person("N/A") == "Uncredited"
    assert clean_person("  ") is None


def test_credits_issue_and_collection():
    p = {"Writer1_1": "Grant Morrison", "Penciler1_1": "Tony S. Daniel", "Editor1_2": "Jeanine Schaefer <!-- x -->",
         "Writer2_1": "Chip Zdarsky", "CoverArtist1": "Alex Ross", "Cover2Artist3": "Guy Major",
         "Executive Editor": "Dan DiDio", "WriterPages1_1": "1-5", "Image2": "x.jpg", "Inker1_1": ""}
    got = {(s, r, o, n) for s, r, o, _, n in credits(p, "issue")}
    assert got == {(1, "writer", 1, "Grant Morrison"), (1, "penciler", 1, "Tony S. Daniel"),
                   (1, "editor", 2, "Jeanine Schaefer"), (2, "writer", 1, "Chip Zdarsky"),
                   (0, "cover_artist", 1, "Alex Ross"), (0, "variant_cover_artist", 203, "Guy Major"),
                   (0, "executive_editor", 1, "Dan DiDio")}
    assert [(s, r, o) for s, r, o, _, _ in credits({"Writer3": "Geoff Johns"}, "collection")] == [(0, "writer", 3)]


ISSUE_LIST = """
This trade paperback reprints stories from the following issues:
'''Core Issues''':
* {{c|Final Crisis Vol 1 5}}: "Into Oblivion"
* {{C|Batman #682}} (''The Butler Did It'')
*[[Batman Vol 1 683|Batman #683]] - "The Butler Did It Again"
<!--
* {{c|Batman Vol 1 999}}
-->
* {{c|Action Comics Vol 1 1}}
** "First Sighting - The Man of Steel"
* {{c|World's Finest Vol 1 77}} - "The Super Bat-Man!" (starring [[Kal-El (Earth-One)|Superman]])
"""


def test_list_items_order_story_and_section():
    items = list_items(ISSUE_LIST)
    assert [i["title"] for i in items] == ["Final Crisis Vol 1 5", "Batman Vol 1 682", "Batman Vol 1 683",
                                           "Action Comics Vol 1 1", "World's Finest Vol 1 77"]
    assert [i["story"] for i in items][:4] == ["Into Oblivion", "The Butler Did It", "The Butler Did It Again",
                                               "First Sighting - The Man of Steel"]
    assert items[0]["section"] == "Core Issues"


def test_process_page_issue():
    text = """{{DC Database:Comic Template
| Title = Batman
| Volume = 1
| Issue = 676
| Month = June
| Year = 2008
| Event = Batman R.I.P.
| Writer1_1 = Grant Morrison
| StoryTitle1 = [[Batman R.I.P.]]—Midnight in the House of Hurt
| Notes = * Reprinted in {{Co|Batman R.I.P. (Collected)}}.
}}
{{BatRIP}}
[[Category:Test]]"""
    r = process_page((7, "Batman Vol 1 676", text, "2026-01-01T00:00:00Z"))
    assert r["page"][4] == "issue" and r["categories"] == ["Test"]
    pid, series, vol, num, series_page, cover, pub, src, *_ = r["issue"]
    assert (series, vol, num, series_page, cover, pub) == ("Batman", 1, "676", "Batman Vol 1", "2008-06", "2008-04")
    assert ("Batman R.I.P.", "Batman Vol 1 676", "issue_event_param", None, None) in r["members"]
    assert ("Batman R.I.P.", "Batman Vol 1 676", "story_title_link", None, None) in r["members"]
    assert r["headline"] == ["Batman R.I.P.—Midnight in the House of Hurt"]
    assert "Batman R.I.P. (Collected)" in r["page"][7]  # plain text keeps {{Co}} display text


def test_page_url():
    assert page_url("Batman Vol 1 676") == "https://dc.fandom.com/wiki/Batman_Vol_1_676"
    assert page_url("Green Lantern: The Sinestro Corps War (Collected)") == \
        "https://dc.fandom.com/wiki/Green_Lantern:_The_Sinestro_Corps_War_(Collected)"
