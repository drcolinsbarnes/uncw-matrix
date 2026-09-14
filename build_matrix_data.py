"""
build_matrix_data.py

Turns the weekly scraper output + your RPI/logo master files into
team_schedules.json -- the data file the schedule matrix HTML reads.

Run order each week:
  1. python3 scrape_college_soccer_womens.py 2026
  2. python3 build_matrix_data.py
  3. Open uncw_schedule_matrix_v5.html in a browser, or re-embed the JSON
     if you're regenerating the HTML from a template.

Inputs expected in the same folder (rename with --flags if yours differ):
  womens_di_soccer_2026.xlsx   (from the scraper)
  RPI.xlsx                      (Team, Conference_Short, Team_RPI_25, Conference_RPI_25,
                                  TeamLogo, ConferenceLogo, Conference)
  Master_Teams_Table_Final.xlsx (Team, ..., Team_Logo_URL, Conference_Logo_URL)

Output:
  team_schedules.json

MONDAY/THURSDAY COLLISION HANDLING
-----------------------------------
Default rule: half 'a' = Monday-Thursday, half 'b' = Friday-Sunday, per team,
per week (week 1 starts Monday 2026-08-10).

That default breaks if a team plays BOTH a Monday and a Thursday game in the
same week (e.g. a Sunday rainout gets replayed the following Monday) --
both games would land in half 'a' and silently overwrite each other, since
the matrix shows one game per team per half.

This script detects that case automatically: if a team has a Monday game AND
a Thursday game in the same week, AND no Saturday game that week, it keeps
Monday in half 'a' and moves that week's Thursday game to half 'b' instead
(overriding the normal Thu->'a' rule for that one team, that one week only),
and tags both games with a `"caveat"` note explaining the override. If a
Saturday game is also present that week, the script leaves the default
alone and just prints a warning -- that's a 3-games-in-a-week situation the
matrix's two-slot model can't represent, and needs a manual look.
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import date

import pandas as pd

# ---------------------------------------------------------------------------
# Manual overrides -- edit this section as new facts come in. Anything not
# in the scraper's source (Drexel isn't in TopDrawer at all) or that needs
# a correction over what the scraper found goes here.
# ---------------------------------------------------------------------------

MANUAL_RESULTS = [
    # (team, opponent, date, played, win, result_self_first)
    # Example -- Drexel isn't on TopDrawer, so their whole schedule is manual:
]

# Drexel's full 2026 schedule (from their official athletics site PDF --
# not in the scraper's source at all).
DREXEL_SCHEDULE = [
    # (date, loc, opponent, played, win, result_self_first)
    (date(2026, 8, 12), "A", "Saint Joseph's", True, False, "2-3"),
    (date(2026, 8, 20), "H", "Holy Family", True, True, "5-0"),
    (date(2026, 8, 23), "A", "Seton Hall", True, False, "0-1"),
    (date(2026, 8, 27), "A", "La Salle", True, None, "1-1"),
    (date(2026, 8, 30), "A", "NJIT", True, True, "2-1"),
    (date(2026, 9, 3), "H", "Lehigh", True, True, "2-1"),
    (date(2026, 9, 6), "H", "Lafayette", True, True, "2-1"),
    (date(2026, 9, 13), "H", "Delaware", False, None, None),
    (date(2026, 9, 20), "H", "Northeastern", False, None, None),
    (date(2026, 9, 24), "A", "Hampton", False, None, None),
    (date(2026, 9, 27), "A", "William & Mary", False, None, None),
    (date(2026, 10, 4), "A", "Monmouth", False, None, None),
    (date(2026, 10, 8), "H", "Charleston", False, None, None),
    (date(2026, 10, 11), "H", "UNC Wilmington", False, None, None),
    (date(2026, 10, 18), "H", "Stony Brook", False, None, None),
    (date(2026, 10, 25), "H", "Hofstra", False, None, None),
    (date(2026, 11, 1), "A", "Towson", False, None, None),
]

# Results confirmed directly (e.g. from a team's own site) that the scraper
# hasn't picked up yet. Anything listed here OVERRIDES the scraped score for
# that matchup, so entries must be removed once the scraper catches up --
# otherwise a stale or mistyped line here silently overwrites good data.
#
# Emptied 2026-08-17: the three original entries (UNCW-W. Carolina 2-1,
# Hampton-Temple 0-1, Hofstra-Saint Joseph's 1-3) all now come through the
# scraper with identical scores, so they were doing nothing but adding risk.
#
# Format: (team, opponent, played, win, result_self_first)
# Both names must match the display names in TEAMS below.
#
# 2026-08-25: Colin confirmed Hofstra 1-1 vs Columbia on 8/20 while the
# scraper still had it unplayed. Removed 2026-09-09 -- the scraper has since
# picked up the same fixture (dated 8/21) with the identical 1-1 score, so
# the override was redundant and, per the note above, a good habit to clear
# out once the scraper independently confirms it.
#
# 2026-09-14: Colin confirmed both results directly ("Results against
# Charlotte 2-0 Win and 0-0 Draw with Coastal Carolina") before the scraper
# picked them up. Checked both against the raw scrape before adding either
# (per the standing "remove once the scraper catches up" rule above): the
# Charlotte game turned out to already be in the scraper with an identical
# 2-0 score, so that entry would have been pure dead weight -- left out
# entirely rather than added and immediately removed. Coastal Carolina was
# still unplayed (NaN score) in the raw scrape at the time, so that one
# entry was added for real.
#
# 2026-09-14, same day, later rebuild: the scraper caught up on Coastal
# Carolina too (raw scrape now shows the identical 0-0 -- hand-verified the
# resulting 5-0-4 record comes out the same with or without this entry
# before removing it), so per the module's own hygiene rule this entry is
# now pure dead weight and has been removed entirely. Leaving this comment
# block as a worked example of the pattern for the next time a result needs
# a manual override: check the raw scrape first, add only what's genuinely
# missing, and remove it the moment the scraper (or, for
# PlayerMatchReport.xlsx-derived views, the Coaches Match Booklet data
# entry) independently confirms the same number.
CONFIRMED_RESULTS = [
]

# ---------------------------------------------------------------------------
# Team roster: (display name, scraper name or None, is a CAA member)
# ---------------------------------------------------------------------------

TEAMS = [
    ("UNC Wilmington", "UNC Wilmington", True),
    ("App. State", "Appalachian State", False),
    ("W. Carolina", "Western Carolina", False),
    ("Old Dominion", "Old Dominion", False),
    ("GA Southern", "Georgia Southern", False),
    ("VCU", "VCU", False),
    ("ECU", "East Carolina", False),
    ("High Point", "High Point", False),
    ("Charlotte", "Charlotte", False),
    ("Coastal Carolina", "Coastal Carolina", False),
    ("Hampton", "Hampton University", True),
    ("Monmouth", "Monmouth", True),
    ("Northeastern", "Northeastern", True),
    ("Elon", "Elon", True),
    ("Towson", "Towson", True),
    ("Drexel", None, True),
    ("Charleston", "College of Charleston", True),
    ("William & Mary", "William & Mary", True),
    ("Campbell", "Campbell", True),
    ("Hofstra", "Hofstra", True),
    ("Stony Brook", "Stony Brook", True),
]
CAA_TEAMS = {d for d, s, caa in TEAMS if caa}
SCRAPENAME_TO_DISP = {s: d for d, s, caa in TEAMS if s}

# ---------------------------------------------------------------------------
# Team colors -- FotMob-style category-winner pills on the Fixtures page's
# Match Center (Colin's ask, 2026-09-13: "use the fotmob method ... circle
# the team winning that category ... teal for us, the opponent uses their
# team colors that are different than our teal"). One background + text
# color per school, chosen by hand from each program's real primary/
# secondary brand colors, with two deliberate departures from Colin's own
# working examples:
#   - Coastal Carolina's actual colors include teal, which would be
#     indistinguishable from a UNCW win -- per Colin's own instruction,
#     given an alternate (black) instead of their real teal.
#   - UNC Greensboro's real colors are Navy/Gold (#0f2044 / #ffb71b, per
#     teamcolorcodes.com), not the green Colin's message assumed -- used
#     the real navy here and flagging the correction back to him rather
#     than silently going with green or silently overriding without note.
# Best-effort for the less common non-CAA/historical-only opponents
# (Spring-season and one-off names below); correct freely if any are off.
# Every value picks a shade dark/saturated enough to keep white pill text
# legible (so e.g. Towson's real gold or UNC's pale Carolina Blue are
# swapped for a same-family darker tone rather than used at low contrast).
TEAM_COLORS = {
    "App. State":       {"bg": "#000000", "fg": "#FFFFFF"},  # Mountaineers black
    "W. Carolina":       {"bg": "#4B2E83", "fg": "#FFFFFF"},  # Catamounts purple
    "Old Dominion":      {"bg": "#003057", "fg": "#FFFFFF"},  # Monarchs slate blue
    "GA Southern":       {"bg": "#041E42", "fg": "#FFFFFF"},  # Eagles navy
    "VCU":               {"bg": "#000000", "fg": "#FFFFFF"},  # Rams black
    "ECU":               {"bg": "#592A8A", "fg": "#FFFFFF"},  # Pirates purple
    "High Point":        {"bg": "#542888", "fg": "#FFFFFF"},  # Panthers purple
    "Charlotte":         {"bg": "#046A38", "fg": "#FFFFFF"},  # 49ers green
    "Coastal Carolina":  {"bg": "#000000", "fg": "#FFFFFF"},  # alt. black -- see note above (real colors include teal)
    "Hampton":           {"bg": "#002664", "fg": "#FFFFFF"},  # Pirates "Hampton Blue"
    "Monmouth":          {"bg": "#002649", "fg": "#FFFFFF"},  # Hawks navy
    "Northeastern":      {"bg": "#C8102E", "fg": "#FFFFFF"},  # Huskies red
    "Elon":              {"bg": "#860038", "fg": "#FFFFFF"},  # Phoenix maroon
    "Towson":            {"bg": "#000000", "fg": "#FFFFFF"},  # Tigers black (their gold is too light for white text)
    "Drexel":            {"bg": "#07294D", "fg": "#FFFFFF"},  # Dragons navy
    "Charleston":        {"bg": "#7D1E32", "fg": "#FFFFFF"},  # Cougars maroon
    "William & Mary":    {"bg": "#115740", "fg": "#FFFFFF"},  # Tribe green
    "Campbell":          {"bg": "#C75B00", "fg": "#FFFFFF"},  # Camels orange (darkened for contrast)
    "Hofstra":           {"bg": "#003E7E", "fg": "#FFFFFF"},  # Pride blue
    "Stony Brook":       {"bg": "#A3242A", "fg": "#FFFFFF"},  # Seawolves red
    # Historical / one-off opponents (2024-2025 seasons, exhibitions, Spring):
    "Clemson":           {"bg": "#522D80", "fg": "#FFFFFF"},  # Tigers "Regalia" purple (their orange is too light for white text)
    "Duke":              {"bg": "#001A57", "fg": "#FFFFFF"},  # Blue Devils navy
    "UNC Greensboro":    {"bg": "#0F2044", "fg": "#FFFFFF"},  # Spartans navy -- see note above
    "Citadel":           {"bg": "#0033A0", "fg": "#FFFFFF"},  # Bulldogs blue
    "Longwood":          {"bg": "#00573F", "fg": "#FFFFFF"},  # Lancers green
    "Ohio State":        {"bg": "#BB0000", "fg": "#FFFFFF"},  # Buckeyes scarlet
    "LSU":               {"bg": "#461D7C", "fg": "#FFFFFF"},  # Tigers purple
    "Mt. Olive":         {"bg": "#003DA5", "fg": "#FFFFFF"},  # Trojans blue
    "South Carolina":    {"bg": "#73000A", "fg": "#FFFFFF"},  # Gamecocks garnet
    "NC State":          {"bg": "#CC0000", "fg": "#FFFFFF"},  # Wolfpack red
    "UNC":               {"bg": "#13294B", "fg": "#FFFFFF"},  # Tar Heels navy (their Carolina Blue is too light for white text)
    "UNC Pembroke":      {"bg": "#000000", "fg": "#FFFFFF"},  # Braves black
}
DEFAULT_TEAM_COLOR = {"bg": "#54595F", "fg": "#FFFFFF"}  # fallback for any opponent not yet in TEAM_COLORS

# PlayerMatchReport.xlsx doesn't always spell an opponent's name the same
# way across seasons (e.g. "Citadel" in Fall 2025 vs "The Citadel" in Fall
# 2026; "East Carolina" in 2024/2025 vs "ECU" in 2026). SCRAPENAME_TO_DISP
# resolves the current 21 tracked teams' full scrape-names to their display
# names already; this catches the handful of historical/non-tracked spelling
# variants that map isn't aware of, so both spellings hit the same color.
TEAM_COLOR_ALIASES = {"The Citadel": "Citadel"}

# Raw "Opponent" values that aren't real opponents (intrasquad scrimmages),
# so they shouldn't get a team color or be treated as a normal fixture.
EXCLUDED_OPPONENTS = {"TealWhite", "UNC Club"}


def team_color_for(raw_opponent_name):
    """Resolve a raw PlayerMatchReport.xlsx opponent name to a {bg, fg}
    color pair for the Fixtures page's Match Center category-winner pills.
    Falls back to DEFAULT_TEAM_COLOR for anything not yet mapped above."""
    disp = SCRAPENAME_TO_DISP.get(raw_opponent_name, raw_opponent_name)
    canon = TEAM_COLOR_ALIASES.get(disp, disp)
    return TEAM_COLORS.get(canon, DEFAULT_TEAM_COLOR)


RPI_NAME_ALIASES = {
    "UCLA": "University of California, Los Angeles", "TCU": "Texas Christian University",
    "SMU": "Southern Methodist University", "LSU": "Louisiana State University",
    "BYU": "Brigham Young University", "USC": "University of Southern California",
    "UNLV": "University of Nevada, Las Vegas", "UTEP": "University of Texas at El Paso",
    "UAB": "University of Alabama at Birmingham", "VCU": "Virginia Commonwealth University",
    "UCF": "University of Central Florida", "UMBC": "University of Maryland, Baltimore County",
    "UTSA": "University of Texas at San Antonio", "FGCU": "Florida Gulf Coast University",
    "CSUN": "California State University, Northridge",
    "SIUE": "Southern Illinois University Edwardsville",
    "UIC": "University of Illinois Chicago", "NJIT": "New Jersey Institute of Technology",
    "LIU": "Long Island University", "IU Indianapolis": "Indiana University Indianapolis",
    "Charlotte": "The University of North Carolina at Charlotte",
    "UNC Wilmington": "University of North Carolina Wilmington",
    "UNC Asheville": "University of North Carolina Asheville",
    # RPI.xlsx spells this WITHOUT "at" ("...Carolina Greensboro"); normalize()
    # doesn't strip "at" as a stopword, so a mapping that includes it silently
    # fails to match and every UNC Greensboro game gets skipped as unknown --
    # caught 2026-08-25 while auditing why only ~324 of 350 teams were rated
    # for live RPI. Also affects compute_conference_strength()'s conf/SOS
    # lookups, which use this same alias table.
    "UNC Greensboro": "University of North Carolina Greensboro",
    "Saint Joseph's": "Saint Joeseph's University",
    # Service academies and a few Big West/Southern Conference/CAA-adjacent
    # teams that show up as opponents but had no alias at all -- added
    # 2026-08-25 during the same audit.
    "Army": "U.S. Military Academy West Point",
    "Navy": "U.S. Naval Academy",
    "VMI": "Virginia Military Institute",
    "CSU Bakersfield": "California State University, Bakersfield",
    "USC Upstate": "University of South Carolina Upstate",
    # RPI.xlsx itself misspells this entry ("Farliegh Dickenson University" --
    # transposed/missing letters in both words). Mapping to the misspelling
    # on purpose so the match succeeds; the real fix is correcting the row in
    # RPI.xlsx, at which point this alias should be updated or removed.
    "Fairleigh Dickinson": "Farliegh Dickenson University",
    "Pittsburgh": "University of Pittsburgh", "Kansas City": "University of Missouri-Kansas City",
    "Air Force": "U.S. Air Force Academy", "Albany": "University at Albany",
    "Arkansas": "University of Arkansas, Fayetteville", "Austin Peay": "Austin Peay State University",
    "Bowling Green": "Bowling Green State University", "Buffalo": "University at Buffalo",
    "Cal Poly": "California Polytechnic State University",
    "Cal State Fullerton": "California State University, Fullerton",
    "California": "University of California, Berkeley",
    "Central Connecticut": "Central Connecticut State University",
    "Columbia": "Columbia University-Barnard College",
    "Fresno State": "California State University, Fresno",
    "Hawaii": "University of Hawaii, Manoa", "Illinois": "University of Illinois Urbana-Champaign",
    "Indiana": "Indiana University, Bloomington", "Little Rock": "University of Arkansas, Little Rock",
    "Louisiana": "University of Louisiana at Lafayette",
    "Louisiana-Monroe": "University of Louisiana Monroe",
    "Loyola (MD)": "Loyola University Maryland", "Maryland": "University of Maryland, College Park",
    "Massachusetts": "University of Massachusetts, Amherst",
    "Massachusetts-Lowell": "University of Massachusetts Lowell",
    "Middle Tennessee": "Middle Tennessee State University",
    "Minnesota": "University of Minnesota, Twin Cities", "Missouri": "University of Missouri, Columbia",
    "Nebraska": "University of Nebraska-Lincoln", "Nevada": "University of Nevada, Reno",
    "North Carolina": "University of North Carolina, Chapel Hill",
    "NC State": "North Carolina State University",
    "Omaha": "University of Nebraska at Omaha", "Penn": "University of Pennsylvania",
    "Penn State": "Pennsylvania State University", "Queens (N.C.)": "Queens University of Charlotte",
    "Rio Grande": "The University of Texas Rio Grande Valley",
    "Rutgers": "Rutgers, The State University of New Jersey, New Brunswick",
    "Sacramento State": "California State University, Sacramento",
    "South Carolina": "University of South Carolina, Columbia",
    "Southern Illinois": "Southern Illinois University at Carbondale",
    "St. Mary's (CA)": "Saint Mary's College of California",
    "Stephen F. Austin": "Stephen F. Austin State University",
    "Tennessee": "University of Tennessee, Knoxville",
    "Tennessee Tech": "Tennessee Technological University",
    "Texas": "University of Texas at Austin", "Texas A&M": "Texas A&M University, College Station",
    "Texas A&M-Corpus Christi": "Texas A&M University-Corpus Christi",
    "UC Davis": "University of California, Davis", "UC Irvine": "University of California, Irvine",
    "UC Riverside": "University of California, Riverside",
    "UC San Diego": "University of California, San Diego",
    "UC Santa Barbara": "University of California, Santa Barbara",
    "UT Chattanooga": "University of Tennessee at Chattanooga",
    "UT Martin": "University of Tennessee at Martin",
    "Virginia Tech": "Virginia Polytechnic Institute and State University",
    "Wisconsin": "University of Wisconsin-Madison",
    "App. State": "Appalachian State University", "W. Carolina": "Western Carolina University",
    "GA Southern": "Georgia Southern University", "ECU": "East Carolina University",
    # Colorado's own scrape name is the bare short form, which -- with no
    # alias -- normalize()'d to the same "colorado" key as the completely
    # separate "Colorado College" program (see AMBIGUOUS_NAME_KEYS below);
    # every "Colorado" game was silently being merged into Colorado College's
    # profile (or vice versa) as a result. Caught 2026-09-10 when Colorado's
    # game count looked roughly double a 4-week schedule.
    "Colorado": "University of Colorado, Boulder",
    # Same bug, different flavor: RPI.xlsx spells these out ("Miami University
    # (Ohio)" / "University of Miami (Florida)") but the scraper uses the
    # short parenthetical form, and normalize() strips parentheses entirely --
    # so both "Miami (FL)" and "Miami (OH)" collapsed to the same "miami" key
    # with no alias to stop it.
    "Miami (FL)": "University of Miami (Florida)",
    "Miami (OH)": "Miami University (Ohio)",
}

# A handful of real, distinct D1 programs collide once normalize()'s generic
# stripping runs -- either because the stripped word ("College"/"University")
# is the ONLY thing distinguishing two same-city schools (Boston College vs.
# Boston University), or because both schools' names collapse once
# parentheticals are dropped (the two Miamis). Caught 2026-09-10: Boston
# College's and Miami (OH)'s game counts included another team's entire
# schedule folded in, because whichever school's RPI.xlsx row got processed
# last simply overwrote the other in every normalize()-keyed lookup table
# used across this file (compute_live_rpi's own output dict included -- it's
# keyed by normalize()'d name, so the collision wasn't just a lookup-table
# problem, it meant only one of the two teams could exist as a rated entity
# at all). Fixed at the source in normalize() itself so every downstream
# consumer (known/conf_by_norm/logo_by_norm dicts, compute_live_rpi's
# returned dict, live_of() lookups, etc.) gets the fix for free without
# needing individual patches. Keyed on the exact RPI.xlsx spelling
# (lowercased) so this only ever fires for these specific rows -- every other
# team's normalize() behavior is completely unchanged.
AMBIGUOUS_NAME_KEYS = {
    "boston college": "id:boston-college",
    "boston university": "id:boston-university",
    "colorado college": "id:colorado-college",
    "university of colorado, boulder": "id:colorado-boulder",
    "miami university (ohio)": "id:miami-oh",
    "university of miami (florida)": "id:miami-fl",
}

WEEK1_START = date(2026, 8, 10)  # Monday


# ---------------------------------------------------------------------------
# Logo overrides -- win over whatever Master_Teams_Table_Final.xlsx says.
#
# Use this when a team's logo in the master table is dead, wrong, or simply
# can't be matched by name. Keyed by the DISPLAY name used in TEAMS below.
# Query strings are stripped automatically, so you can paste a URL copied
# straight out of a browser.
# ---------------------------------------------------------------------------

LOGO_OVERRIDES = {
    # High Point's ESPN CDN URL in the master table is dead.
    "High Point":
        "https://upload.wikimedia.org/wikipedia/commons/2/2c/High_Point_Panthers_logo.svg",
    # UNC Greensboro is spelled "...North Carolina Greensboro" in the master
    # table but "...at Greensboro" in the alias dict, so the name match fails.
    "UNC Greensboro":
        "https://upload.wikimedia.org/wikipedia/en/7/70/UNCG_Spartans_logo.svg",
    # Drexel has no scraper name, so the normal lookup never ran for them.
    # NOTE: the sportslogos.net URL that was here renders fine when you open
    # it directly but NOT inside the page -- that host blocks hotlinking
    # (requests carrying an external Referer header). Every other logo on the
    # page comes from ESPN's CDN, which doesn't, so use that. Drexel's master
    # table entry (id 1000701) is dead, same batch of bad 1000xxx ids that
    # broke High Point.
    "Drexel":
        "https://a.espncdn.com/i/teamlogos/ncaa/500/2182.png",
}


def clean_url(url):
    """Drop tracking query strings (?utm_source=...) from a pasted URL."""
    if isinstance(url, str) and "?" in url:
        return url.split("?", 1)[0]
    return url


def to_https(url):
    """
    Force logo URLs to https.

    The ESPN CDN URLs in Master_Teams_Table_Final.xlsx are http://. That's
    harmless when you open the matrix as a local file, but once the page is
    served over https (GitHub Pages), http images are mixed content: current
    Chrome and Safari silently retry them over https and drop them if that
    fails, and older browsers block them outright. Rewriting here means the
    fix applies to every future rebuild without touching the spreadsheet.
    """
    if isinstance(url, str) and url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def normalize(name: str) -> str:
    # A few real, distinct D1 programs would otherwise collapse to the same
    # key once the generic stripping below runs (see AMBIGUOUS_NAME_KEYS for
    # why) -- checked against the exact RPI.xlsx spelling before any of that
    # stripping happens, so this can't affect any other team's normal match.
    override = AMBIGUOUS_NAME_KEYS.get(str(name).strip().lower())
    if override:
        return override
    name = str(name).lower().strip()
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace("&", "and")
    name = re.sub(r"[.']", "", name)
    name = re.sub(r"\b(university|college|the|of)\b", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def week_of(d: date) -> int:
    return (d - WEEK1_START).days // 7 + 1


def default_half(d: date) -> str:
    return "a" if d.weekday() <= 3 else "b"  # Mon-Thu = a, Fri-Sun = b


def find_monday_thursday_collisions(scrape: pd.DataFrame):
    """
    Returns {(team, iso_week): 'override'|'warn'} for teams playing both a
    Monday and Thursday game in the same week. 'override' = safe to split
    Mon->a / Thu->b (no Saturday game that week). 'warn' = also has a
    Saturday game -- three games in one week, needs a manual look.
    """
    scrape = scrape.copy()
    scrape["weekday"] = scrape["match_date"].apply(lambda d: d.weekday())
    scrape["iso_week"] = scrape["match_date"].apply(lambda d: d.isocalendar()[1])

    team_week_days = defaultdict(set)
    for _, r in scrape.iterrows():
        team_week_days[(r["home_team"], r["iso_week"])].add(r["weekday"])
        team_week_days[(r["away_team"], r["iso_week"])].add(r["weekday"])

    result = {}
    for (team, wk), days in team_week_days.items():
        if 0 in days and 3 in days:  # Monday and Thursday both present
            result[(team, wk)] = "warn" if 5 in days else "override"
    return result


def drop_postponed_duplicates(scrape: pd.DataFrame, window_days: int = 14):
    """
    Remove phantom fixtures left behind by postponements.

    When a game is postponed, TopDrawer keeps the original date on the
    schedule with no score AND adds the make-up date with the result. The
    matrix then shows a ghost fixture -- an unplayed game, complete with a
    win-probability prediction, for a match that has already been played.
    (Towson at Mount St. Mary's: listed Aug 16 unplayed, played Aug 17.)

    Rule: if the same two teams appear twice within `window_days`, one
    unplayed and one played, and the unplayed date comes first, drop the
    unplayed row. A genuine home-and-home is never two weeks apart with one
    leg unrecorded, so this is safe.

    Returns (filtered_df, list_of_dropped_descriptions).
    """
    scrape = scrape.copy()
    scrape["_pair"] = scrape.apply(
        lambda r: tuple(sorted([str(r["home_team"]), str(r["away_team"])])), axis=1)

    drop_idx, notes = [], []
    for pair, grp in scrape.groupby("_pair"):
        if len(grp) < 2:
            continue
        played = grp[grp["home_score"].notna()]
        unplayed = grp[grp["home_score"].isna()]
        for ui, urow in unplayed.iterrows():
            for _, prow in played.iterrows():
                gap = (prow["match_date"] - urow["match_date"]).days
                if 0 < gap <= window_days:
                    drop_idx.append(ui)
                    notes.append(
                        f"{pair[0]} vs {pair[1]}: dropped unplayed "
                        f"{urow['match_date']} (played {prow['match_date']}, "
                        f"{gap}d later -- postponement)")
                    break

    if drop_idx:
        scrape = scrape.drop(index=drop_idx)
    return scrape.drop(columns="_pair"), notes


DISP_TO_SCRAPENAME = {d: s for d, s, caa in TEAMS if s}


def augment_scrape_with_manual_results(scrape: pd.DataFrame) -> pd.DataFrame:
    """
    Fold CONFIRMED_RESULTS and DREXEL_SCHEDULE into a COPY of `scrape`, for
    feeding to compute_live_rpi() / compute_conference_strength() -- both of
    which read wins/losses/schedules directly off this dataframe, not off
    the per-team `output` dict that build_team_schedules() eventually
    assembles.

    Without this, a manual correction only patches the *display* -- a
    team's shown record and schedule table -- while the live-RPI network
    and SOS keep computing off the original (stale or absent) data:

      * CONFIRMED_RESULTS entries only ever updated `output[team]["games"]`
        in build_team_schedules(); the underlying scrape row stayed
        NaN-scored, so the team got no credit in its own live-RPI Element 1
        and nobody who played them got credit in Elements 2/3 either.
      * Drexel has no scraper name at all (DREXEL_SCHEDULE is hand-
        maintained), so it's entirely absent from `scrape` -- Drexel can't
        be rated, none of its opponents get it counted in their own
        network, and conference-strength SOS (which reads every scheduled
        game, played or not) is missing every Drexel fixture outright, not
        just the unplayed ones.

    Caller's responsibility: use the *unaugmented* `scrape` for anything
    that builds a team's own game-by-game display list (build_team_schedules'
    main loop), since that already adds Drexel's games and applies
    CONFIRMED_RESULTS separately -- feeding it the augmented frame too would
    double up entries. This function is only for the two aggregate
    computations that read `scrape` as a flat pool of results.

    NOTE (2026-09-09): TopDrawer has started tracking Drexel as a real team
    in the raw scrape as games are played -- as of this date, 7 of Drexel's
    8 played/scheduled-through games already appear natively in `scrape`
    (matching DREXEL_SCHEDULE's scores, occasionally with a 1-day date
    offset). Injecting DREXEL_SCHEDULE unconditionally on top of that would
    double-count those fixtures in the live-RPI network (Drexel's own gp,
    and each opponent's Elements 2/3). So below we skip injecting any
    DREXEL_SCHEDULE row whose opponent already has a real Drexel-involving
    row in the unaugmented scrape, deferring to the scraper's own
    score/date as authoritative for that fixture. This makes the mechanism
    self-cleaning as the scraper's Drexel coverage grows over the season --
    once the scraper has all of Drexel's games, DREXEL_SCHEDULE injection
    naturally goes to zero without further code changes.
    """
    scrape = scrape.copy()

    for team, opp, played, win, result in CONFIRMED_RESULTS:
        if not played or not result:
            continue
        team_scrapename = DISP_TO_SCRAPENAME.get(team, team)
        a, b = (int(x) for x in result.split("-"))
        home_mask = (scrape["home_team"] == team_scrapename) & (scrape["away_team"] == opp)
        away_mask = (scrape["home_team"] == opp) & (scrape["away_team"] == team_scrapename)
        scrape.loc[home_mask, ["home_score", "away_score"]] = [a, b]
        scrape.loc[away_mask, ["home_score", "away_score"]] = [b, a]

    # Opponents Drexel already has a real row against in the (unaugmented)
    # scrape, keyed by scrapename -- the scraper is authoritative for these.
    existing_drexel_opponents = set(
        scrape.loc[scrape["home_team"] == "Drexel", "away_team"]
    ) | set(
        scrape.loc[scrape["away_team"] == "Drexel", "home_team"]
    )

    drexel_rows = []
    for d, loc, opp, played, win, result in DREXEL_SCHEDULE:
        opp_scrapename = DISP_TO_SCRAPENAME.get(opp, opp)
        if opp_scrapename in existing_drexel_opponents:
            continue  # scraper now has this fixture natively; don't double-count
        home_team, away_team = ("Drexel", opp) if loc == "H" else (opp, "Drexel")
        home_score = away_score = None
        if played and result:
            a, b = (int(x) for x in result.split("-"))
            home_score, away_score = (a, b) if loc == "H" else (b, a)
        drexel_rows.append({"match_date": d, "home_team": home_team, "away_team": away_team,
                             "home_score": home_score, "away_score": away_score})
    if drexel_rows:
        scrape = pd.concat([scrape, pd.DataFrame(drexel_rows)], ignore_index=True, sort=False)

    return scrape


def compute_live_rpi(scrape: pd.DataFrame, rpi_df: pd.DataFrame):
    """
    In-season RPI computed from this year's actual results, using the
    standard NCAA 3-element formula (weighted 25/50/25):

      Element 1 -- Win% (ties count as 1/3 of a win, the rule since 2024)
      Element 2 -- opponents' average Win%, excluding the head-to-head
                   game(s) against the team being rated, with each
                   opponent's ties counted as 1/2 of a win here -- NOT the
                   1/3 used for Element 1. This is a real, easy-to-miss
                   NCAA wrinkle (confirmed against
                   https://sites.google.com/site/rpifordivisioniwomenssoccer/rpi-formula,
                   2026-09-11): a team's OWN record weights a tie at 1/3,
                   but that same tie is weighted at 1/2 wherever it feeds
                   into someone else's strength-of-schedule number.
      Element 3 -- opponents' opponents' average Win% (average of each
                   opponent's own Element 2 -- not re-excluded further, so
                   it inherits the 1/2 tie-weighting from Element 2)
      RPI = (Element 1 + 2*Element 2 + Element 3) / 4

    This is deliberately separate from `Team_RPI_25` (last season's FINAL
    rank), which the rest of the page -- SOS, "otherRpi" on every game, the
    RPI column in the CAA standings -- still uses. Elements 2 and 3 only mean
    something once there's real interconnected schedule data behind them; in
    the first few weeks of a season most teams have played a handful of
    games against a small, disconnected slice of the country, so treat this
    as provisional. `gp` (games counted) is returned per team so the page
    can flag a thin sample instead of hiding it.

    On top of that unadjusted 3-element RPI, this also computes the "Adjusted
    RPI" -- the 2024 Women's Soccer Committee's bonus/penalty structure that
    the NCAA itself actually uses for rankings/selection (see
    https://sites.google.com/site/rpifordivisioniwomenssoccer/rpi-formula,
    "Bonus and Penalty Adjustments"; confirmed with Colin 2026-09-10). A team
    gets a small bonus added for a non-conference win/tie against a strong
    D1 opponent, and a small penalty subtracted for a non-conference tie/loss
    against a weak one -- see `bonus_penalty_amount()` below for the exact
    table. Two scope notes worth remembering:
      * Only non-conference, D1-vs-D1 games are eligible -- conference games
        and anything against a non-D1 opponent (which never enters `games`
        below in the first place) never get a bonus or penalty.
      * The bonus/penalty tier is keyed off the OPPONENT's *unadjusted* RPI
        rank, computed in the first pass below, before adjustments are
        applied to anyone. Using each opponent's adjusted rank instead would
        make every game's bonus/penalty depend on the other team's bonus/
        penalty, which depends on this team's -- a circular calculation with
        no clean fixed point. This matches the real committee process, which
        computes and freezes the field's unadjusted RPI first.
      * The raw scrape data (see `womens_di_soccer_2026.xlsx`) has no
        neutral-site flag -- every game is a literal home/away pair. The
        real NCAA scale has a third "Neutral" tier between Home and Away for
        each bracket; since this codebase can't tell a true neutral-site
        game (common in early-season tournaments) from an ordinary one,
        every game is scored Home or Away only. That's a known, minor
        approximation -- the Home/Away/Neutral amounts within a bracket only
        differ by 0.0002-0.0004, so the effect on any one team's Adjusted
        RPI is small, but a team that played several early tournament games
        at a "neutral" site will show a slightly different Adjusted RPI here
        than the NCAA's own number would.

    `row["rank"]` -- the rank every other function in this file reads as
    "the" live rank (main matrix per-game badges, team headers, RPI-band
    bucketing, conference SOS, etc.) -- is the ADJUSTED rank, per Colin's
    2026-09-10 request to use Adjusted RPI for all rankings going forward.
    The unadjusted rank is still returned as `row["unadjustedRank"]` (used
    internally for bracket lookups, and available for anyone who wants it),
    and the unadjusted RPI value itself is still `row["rpi"]` -- only the
    RANKING now comes from the adjusted number, not the plain 3-element one.

    Only teams matched to RPI.xlsx's ~350-team D1 women's soccer universe are
    rated, or count as a rateable opponent for Elements 2/3. Per the actual
    NCAA RPI rule (confirmed 2026-09-09: "take the team's won-lost
    percentage against Division I opponents only" -- non-Division I games
    don't factor into ANY RPI component, not even the team's own record),
    a game against an unmatched (non-D1) opponent is dropped entirely here:
    it doesn't count toward either side's Element 1, and so can't leak into
    anyone's Element 2/3 either. Previously such games counted toward the
    team's own Element 1 only, which let a win over a D2/NAIA opponent
    quietly inflate that team's win% -- and since that win% is exactly what
    feeds every one of *their* opponents' Element 2, a team that padded its
    record against sub-D1 competition could distort the schedule-strength
    score of everyone who played them.

    Returns a dict keyed by normalize()'d RPI.xlsx team name (look teams up
    the same way lookup_rpi() does: RPI_NAME_ALIASES.get(name, name), then
    normalize()), in rank order:
      {normalized_name: {"name", "rpi", "rank", "gp", "elem1", "elem2", "elem3"}}
    """
    known = {}
    for _, r in rpi_df.iterrows():
        known[normalize(r["Team"])] = str(r["Team"]).strip()

    def to_display(scrape_name):
        full = RPI_NAME_ALIASES.get(scrape_name, scrape_name)
        return known.get(normalize(full))

    played = scrape[scrape["home_score"].notna()]

    # team -> [(opponent_display, outcome)], outcome in {1.0, 0.0, "T"} --
    # "T" is a tie sentinel, not a fixed fraction, since the two RPI elements
    # that read it (own Win% vs. an opponent's Win%) weight a tie differently.
    # Games where either side doesn't resolve to a D1 RPI.xlsx team are
    # skipped outright -- they don't count for either team, per the NCAA
    # rule above.
    games = defaultdict(list)
    for _, r in played.iterrows():
        h_disp, a_disp = to_display(r["home_team"]), to_display(r["away_team"])
        if not h_disp or not a_disp:
            continue
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        if hs > as_:
            h_out, a_out = 1.0, 0.0
        elif hs < as_:
            h_out, a_out = 0.0, 1.0
        else:
            # "T" sentinel, not a pre-baked fraction -- ties are worth a
            # different amount depending on which element is reading them
            # (1/3 for Element 1, 1/2 for Element 2/3). See winpct() below.
            h_out = a_out = "T"
        # Third element of each tuple is this team's location for the game
        # ("H"/"A") -- only used by the bonus/penalty pass further down;
        # elem1/2/3 below ignore it entirely, same as before.
        games[h_disp].append((a_disp, h_out, "H"))
        games[a_disp].append((h_disp, a_out, "A"))

    def winpct(team, exclude=None, tie_weight=1 / 3):
        vals = [(tie_weight if out == "T" else out)
                for opp, out, _ in games.get(team, []) if opp != exclude]
        return sum(vals) / len(vals) if vals else None

    # Element 1: the team's own record, ties = 1/3 of a win (the rule since
    # 2024).
    elem1 = {t: winpct(t) for t in games}

    # Element 2: each opponent's record with the head-to-head game(s) against
    # `t` excluded -- but here a tie is worth 1/2 of a win, not 1/3. That's
    # the NCAA's own distinction, not a typo: Element 1 uses the 2024 tie
    # rule for a team's own percentage, while Element 2 (and, through it,
    # Element 3) still values an opponent's tie at 1/2 when using it as a
    # strength-of-schedule input.
    elem2 = {}
    for t in games:
        vals = [winpct(opp, exclude=t, tie_weight=1 / 2)
                for opp, _, _ in games[t] if opp and opp in games]
        vals = [v for v in vals if v is not None]
        elem2[t] = sum(vals) / len(vals) if vals else None

    elem3 = {}
    for t in games:
        vals = [elem2[opp] for opp, _, _ in games[t] if opp and elem2.get(opp) is not None]
        elem3[t] = sum(vals) / len(vals) if vals else None

    rows = []
    for t in games:
        e1 = elem1[t]
        if e1 is None:
            continue
        # Graceful fallback for the earliest weeks, when a team's opponents
        # haven't played anyone else yet either.
        e2 = elem2[t] if elem2.get(t) is not None else e1
        e3 = elem3[t] if elem3.get(t) is not None else e2
        rpi = (e1 + 2 * e2 + e3) / 4
        rows.append({"name": t, "rpi": round(rpi, 4), "gp": len(games[t]),
                      "elem1": round(e1, 4),
                      "elem2": round(elem2[t], 4) if elem2.get(t) is not None else None,
                      "elem3": round(elem3[t], 4) if elem3.get(t) is not None else None})

    rows.sort(key=lambda x: -x["rpi"])
    for i, row in enumerate(rows):
        row["unadjustedRank"] = i + 1

    # ---- 2024 Women's Soccer Committee bonus/penalty adjustment ----
    # See the docstring above for the full explanation. Conference
    # membership comes straight from RPI.xlsx's Conference_Short column, the
    # same source and matching convention build_national_rpi_data() uses for
    # its own confRecord/nonConfRecord split.
    conf_by_norm = {}
    for _, r in rpi_df.iterrows():
        if pd.notna(r.get("Conference_Short")):
            conf_by_norm[normalize(r["Team"])] = str(r["Conference_Short"]).strip()

    rank_by_name = {row["name"]: row["unadjustedRank"] for row in rows}

    adjustment = defaultdict(float)
    for t, glist in games.items():
        t_conf = conf_by_norm.get(normalize(t))
        for opp, out, loc in glist:
            if t_conf and conf_by_norm.get(normalize(opp)) == t_conf:
                continue  # conference games never get a bonus or penalty
            result = "win" if out == 1.0 else "loss" if out == 0.0 else "tie"
            adjustment[t] += bonus_penalty_amount(rank_by_name.get(opp), result, loc)

    for row in rows:
        adj = round(adjustment.get(row["name"], 0.0), 4)
        row["adjustment"] = adj
        row["adjustedRpi"] = round(row["rpi"] + adj, 4)

    rows.sort(key=lambda x: -x["adjustedRpi"])
    for i, row in enumerate(rows):
        row["rank"] = i + 1

    # Keyed by normalize()'d name rather than the literal RPI.xlsx string --
    # callers (e.g. build_team_schedules) look teams up the same way
    # lookup_rpi() does: RPI_NAME_ALIASES.get(name, name), then normalize().
    return {normalize(row["name"]): row for row in rows}


def bonus_penalty_amount(opp_rank, result, loc):
    """
    2024 NCAA Women's Soccer Committee bonus/penalty table (see
    compute_live_rpi()'s docstring for the full explanation and source).

    opp_rank: the opponent's UNADJUSTED live RPI rank (int), or None if the
      opponent isn't a rated D1 team at all -- returns 0.0 in that case,
      since non-D1 games never get a bonus or penalty.
    result: "win" | "tie" | "loss", from this team's perspective.
    loc: "H" or "A" -- this team's location for the game. "N" (neutral site)
      is a real tier in the NCAA's table but is never passed here, since the
      raw scrape data can't distinguish a neutral-site game from a normal
      one; see the docstring note above.

    Bonuses apply only to wins/ties against an opponent ranked 1-100;
    penalties apply only to ties/losses against an opponent ranked 151+.
    Opponents ranked 101-150 are a dead zone (no bonus, no penalty either
    direction), and a win is never penalized regardless of who it came
    against.
    """
    if opp_rank is None:
        return 0.0
    if opp_rank <= 25:
        table = {"win": {"H": 0.0028, "A": 0.0032, "N": 0.0030},
                 "tie": {"H": 0.0016, "A": 0.0020, "N": 0.0018}}
    elif opp_rank <= 50:
        table = {"win": {"H": 0.0022, "A": 0.0026, "N": 0.0024},
                 "tie": {"H": 0.0010, "A": 0.0014, "N": 0.0012}}
    elif opp_rank <= 100:
        table = {"win": {"H": 0.0004, "A": 0.0008, "N": 0.0006}}
    elif opp_rank <= 150:
        table = {}
    elif opp_rank <= 250:
        table = {"tie":  {"H": -0.0008, "A": -0.0004, "N": -0.0006},
                 "loss": {"H": -0.0014, "A": -0.0010, "N": -0.0012}}
    else:
        table = {"tie":  {"H": -0.0020, "A": -0.0016, "N": -0.0018},
                 "loss": {"H": -0.0026, "A": -0.0022, "N": -0.0024}}
    return table.get(result, {}).get(loc, 0.0)


def compute_conference_strength(scrape: pd.DataFrame, rpi_df: pd.DataFrame):
    """
    Each conference's record in NON-conference games -- i.e. how they've done
    against the rest of the country. Computed from every played game in the
    scrape, not just the teams in the matrix.

    Teams whose conference can't be identified (non-DI opponents, mostly) are
    skipped rather than lumped together, so the totals only reflect DI-vs-DI
    games across different conferences.

    Also computes "sos": strength of schedule, the average 2025-final RPI
    RANK of every opponent on every member team's FULL schedule. Unlike the
    W/L/D/GF/GA columns above, this deliberately uses every scheduled game --
    played or not, in-conference or not -- because it's answering "who is on
    this conference's schedule", not "how has this conference done". Since
    Team_RPI_25 is a RANK (1 = best team in the country), a LOWER sos means a
    tougher schedule, not a stronger one -- the opposite direction from the
    win% column next to it.

    Also computes "liveSos": the same idea, but averaging each opponent's
    in-season 2026 RPI RANK (see compute_live_rpi()) instead of last
    season's frozen rank -- a schedule-strength read that updates as the
    season plays out rather than staying fixed all year. Opponents that
    haven't been rated yet (too early, or unresolvable name) are simply
    skipped rather than counted as a gap, same as `sos`.

    `scrape` is augmented with CONFIRMED_RESULTS and DREXEL_SCHEDULE before
    anything else runs (see augment_scrape_with_manual_results()), so a
    manually-confirmed result or a Drexel fixture the scraper can't see
    still counts here -- both for the tally/SOS work in this function and
    for the compute_live_rpi() call below, which otherwise wouldn't know
    about them either.
    """
    scrape = augment_scrape_with_manual_results(scrape)

    conf_by_norm = {}
    rpi_by_norm = {}
    for _, r in rpi_df.iterrows():
        if pd.notna(r.get("Conference_Short")):
            conf_by_norm[normalize(r["Team"])] = str(r["Conference_Short"]).strip()
        if pd.notna(r.get("Team_RPI_25")):
            rpi_by_norm[normalize(r["Team"])] = float(r["Team_RPI_25"])

    live_rpi = compute_live_rpi(scrape, rpi_df)

    def conf_of(scrape_name):
        full = RPI_NAME_ALIASES.get(scrape_name, scrape_name)
        return conf_by_norm.get(normalize(full))

    def rpi_of(scrape_name):
        full = RPI_NAME_ALIASES.get(scrape_name, scrape_name)
        return rpi_by_norm.get(normalize(full))

    def live_rank_of(scrape_name):
        full = RPI_NAME_ALIASES.get(scrape_name, scrape_name)
        lr = live_rpi.get(normalize(full))
        return lr["rank"] if lr else None

    tally = defaultdict(lambda: {"w": 0, "l": 0, "d": 0, "gf": 0, "ga": 0})
    played = scrape[scrape["home_score"].notna()]
    for _, r in played.iterrows():
        ch, ca = conf_of(r["home_team"]), conf_of(r["away_team"])
        if not ch or not ca or ch == ca:
            continue  # unknown conference, or an in-conference game
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        tally[ch]["gf"] += hs; tally[ch]["ga"] += as_
        tally[ca]["gf"] += as_; tally[ca]["ga"] += hs
        if hs > as_:
            tally[ch]["w"] += 1; tally[ca]["l"] += 1
        elif hs < as_:
            tally[ch]["l"] += 1; tally[ca]["w"] += 1
        else:
            tally[ch]["d"] += 1; tally[ca]["d"] += 1

    # SOS: every scheduled game, both directions, regardless of play status
    # or whether it's an in- or out-of-conference matchup.
    sos_sum = defaultdict(float)
    sos_count = defaultdict(int)
    for _, r in scrape.iterrows():
        ch, ca = conf_of(r["home_team"]), conf_of(r["away_team"])
        rh, ra = rpi_of(r["home_team"]), rpi_of(r["away_team"])
        if ch and ra is not None:
            sos_sum[ch] += ra; sos_count[ch] += 1
        if ca and rh is not None:
            sos_sum[ca] += rh; sos_count[ca] += 1

    # liveSos: same idea as SOS above, but averaging each opponent's
    # in-season 2026 live RPI rank instead of last year's frozen rank.
    live_sos_sum = defaultdict(float)
    live_sos_count = defaultdict(int)
    for _, r in scrape.iterrows():
        ch, ca = conf_of(r["home_team"]), conf_of(r["away_team"])
        rh, ra = live_rank_of(r["home_team"]), live_rank_of(r["away_team"])
        if ch and ra is not None:
            live_sos_sum[ch] += ra; live_sos_count[ch] += 1
        if ca and rh is not None:
            live_sos_sum[ca] += rh; live_sos_count[ca] += 1

    rows = []
    names = (set(tally) | {n for n, c in sos_count.items() if c}
             | {n for n, c in live_sos_count.items() if c})
    for name in names:
        t = tally.get(name, {"w": 0, "l": 0, "d": 0, "gf": 0, "ga": 0})
        total = t["w"] + t["l"] + t["d"]
        sos = round(sos_sum[name] / sos_count[name], 1) if sos_count.get(name) else None
        live_sos = (round(live_sos_sum[name] / live_sos_count[name], 1)
                    if live_sos_count.get(name) else None)
        if not total:
            # No inter-conference results yet, but still worth surfacing SOS
            # once the schedule is set.
            if sos is None and live_sos is None:
                continue
            rows.append({"name": name, "w": 0, "l": 0, "d": 0, "gp": 0,
                         "gf": 0, "ga": 0, "gd": 0, "gfpg": None, "gapg": None,
                         "gdpg": None, "pct": None, "sos": sos, "liveSos": live_sos})
            continue
        # Per-game rates, so a conference that has played 30 inter-conference
        # games is comparable with one that has played 9.
        rows.append({"name": name, "w": t["w"], "l": t["l"], "d": t["d"],
                      "gp": total,
                      "gf": t["gf"], "ga": t["ga"], "gd": t["gf"] - t["ga"],
                      "gfpg": round(t["gf"] / total, 2),
                      "gapg": round(t["ga"] / total, 2),
                      "gdpg": round((t["gf"] - t["ga"]) / total, 2),
                      "pct": round((t["w"] + 0.5 * t["d"]) / total, 4),
                      "sos": sos, "liveSos": live_sos})
    rows.sort(key=lambda x: (x["pct"] is None, -(x["pct"] or 0),
                              -(x["w"] + x["l"] + x["d"]), x["name"]))
    return rows


def build_rpi_logo_lookups(rpi_df, master_df):
    rpi_df = rpi_df.copy()
    rpi_df["norm"] = rpi_df["Team"].apply(normalize)
    rpi_exact = dict(zip(rpi_df["Team"], zip(rpi_df["Team_RPI_25"], rpi_df["ConferenceLogo"])))
    rpi_norm = dict(zip(rpi_df["norm"], zip(rpi_df["Team_RPI_25"], rpi_df["ConferenceLogo"])))

    master_df = master_df.copy()
    master_df["norm"] = master_df["Team"].apply(normalize)
    logo_exact = dict(zip(master_df["Team"], master_df["Team_Logo_URL"]))
    logo_norm = dict(zip(master_df["norm"], master_df["Team_Logo_URL"]))

    def lookup_rpi(name):
        full = RPI_NAME_ALIASES.get(name, name)
        if full in rpi_exact:
            val, logo = rpi_exact[full]
        elif normalize(full) in rpi_norm:
            val, logo = rpi_norm[normalize(full)]
        else:
            return None, None
        return (int(val) if pd.notna(val) else None), (to_https(logo) if pd.notna(logo) else None)

    def lookup_logo(name):
        if name in LOGO_OVERRIDES:
            return to_https(clean_url(LOGO_OVERRIDES[name]))
        full = RPI_NAME_ALIASES.get(name, name)
        if full in LOGO_OVERRIDES:
            return to_https(clean_url(LOGO_OVERRIDES[full]))
        if full in logo_exact:
            v = logo_exact[full]
        elif normalize(full) in logo_norm:
            v = logo_norm[normalize(full)]
        else:
            return None
        return to_https(v) if pd.notna(v) else None

    return lookup_rpi, lookup_logo


def build_team_schedules(scrape_path, rpi_path, master_path):
    scrape = pd.read_excel(scrape_path, sheet_name=0)
    scrape["match_date"] = pd.to_datetime(scrape["match_date"]).dt.date
    rpi_df = pd.read_excel(rpi_path, sheet_name=0)
    master_df = pd.read_excel(master_path, sheet_name=0)
    lookup_rpi, lookup_logo = build_rpi_logo_lookups(rpi_df, master_df)

    # For linking out to a team's National page (national_rpi.html#/team/...)
    # -- see build_full_to_short()'s docstring for why this can't just be
    # this page's own display name (e.g. "Hampton"): the National page picks
    # its own short name straight from the raw scrape, which for a handful
    # of teams is the long form ("Hampton University") because that's the
    # only spelling the scrape ever uses for them.
    to_full, full_to_short = build_full_to_short(scrape, rpi_df)

    def nat_name_of(name):
        if not name:
            return None
        full = to_full(name)
        return full_to_short.get(full, name)

    scrape, postponed_notes = drop_postponed_duplicates(scrape)
    for n in postponed_notes:
        print(f"  postponement: {n}")

    # Live RPI needs to see CONFIRMED_RESULTS / DREXEL_SCHEDULE too, or a
    # manually-confirmed result never reaches the win/loss network -- see
    # augment_scrape_with_manual_results(). Use a separate augmented copy
    # for this call only: the per-team games loop below reads the plain
    # `scrape` and adds Drexel's games itself further down, so feeding it
    # the augmented frame too would duplicate every Drexel fixture.
    live_rpi = compute_live_rpi(augment_scrape_with_manual_results(scrape), rpi_df)

    collisions = find_monday_thursday_collisions(scrape)
    for (team, wk), status in collisions.items():
        if status == "warn":
            print(f"WARNING: {team} has Mon+Thu+Sat games in ISO week {wk} -- "
                  f"three games in one week, matrix can't show all three. Check manually.")

    def half_for(team_scrapename, d):
        wk_iso = d.isocalendar()[1]
        status = collisions.get((team_scrapename, wk_iso))
        if status == "override":
            return "a" if d.weekday() == 0 else "b"  # Monday->a, Thursday->b
        return default_half(d)

    def live_rank_of(name):
        # Same resolution path as lookup_rpi()/compute_live_rpi() itself:
        # RPI_NAME_ALIASES.get(name, name), then normalize(). `name` may be
        # either a scrapename or a display name -- both are handled.
        lr = live_rpi.get(normalize(RPI_NAME_ALIASES.get(name, name)))
        return lr["rank"] if lr else None

    output = {}
    for disp, scrapename, _ in TEAMS:
        games = []
        if scrapename:
            rows = scrape[(scrape["home_team"] == scrapename) | (scrape["away_team"] == scrapename)]
            for _, r in rows.iterrows():
                d = r["match_date"]
                w = week_of(d)
                if w < 1 or w > 16:
                    continue
                h = half_for(scrapename, d)
                is_home = r["home_team"] == scrapename
                opp_scrapename = r["away_team"] if is_home else r["home_team"]
                opp_disp = SCRAPENAME_TO_DISP.get(opp_scrapename, opp_scrapename)
                opp_logo = lookup_logo(opp_scrapename)
                opp_lookup_name = opp_disp if opp_disp in SCRAPENAME_TO_DISP.values() else opp_scrapename
                opp_rpi, opp_conflogo = lookup_rpi(opp_lookup_name)
                opp_live_rank = live_rank_of(opp_lookup_name)
                played = pd.notna(r["home_score"])
                result, win = None, None
                if played:
                    hs, as_ = int(r["home_score"]), int(r["away_score"])
                    # win is True / False / None, where None means a draw.
                    # (This used to be `hs > as_`, which recorded every draw
                    # as a loss and made the draw column permanently 0.)
                    if is_home:
                        result = f"{hs}-{as_}"
                        win = None if hs == as_ else hs > as_
                    else:
                        result = f"{as_}-{hs}"
                        win = None if hs == as_ else as_ > hs
                entry = {
                    "week": w, "half": h, "loc": "H" if is_home else "A",
                    "otherName": opp_disp, "otherLogo": opp_logo, "otherRpi": opp_rpi,
                    "otherLiveRpiRank": opp_live_rank,
                    # The exact key to link to on the National page -- see
                    # nat_name_of() above; usually equal to otherName, but
                    # not always (e.g. "Hampton" here is "Hampton
                    # University" there).
                    "otherNatName": nat_name_of(opp_lookup_name),
                    "otherConfLogo": opp_conflogo, "played": played, "win": win, "result": result,
                    "conf": disp in CAA_TEAMS and opp_disp in CAA_TEAMS,
                }
                if collisions.get((scrapename, d.isocalendar()[1])) == "override":
                    entry["caveat"] = ("Monday/Thursday same-week collision -- "
                                        "Monday forced to half a, Thursday forced to half b.")
                games.append(entry)
        own_rpi, _ = lookup_rpi(disp)
        # Fall back to the display name when a team has no scraper name --
        # otherwise Drexel (scrapename None) silently ends up with no logo.
        own_logo = lookup_logo(scrapename) if scrapename else None
        if not own_logo:
            own_logo = lookup_logo(disp)
        lr = live_rpi.get(normalize(RPI_NAME_ALIASES.get(disp, disp)))
        output[disp] = {
            "logo": own_logo, "games": games, "ownRpi": own_rpi,
            # This team's own National-page link target -- see
            # nat_name_of() above.
            "natName": nat_name_of(scrapename) if scrapename else nat_name_of(disp),
            # "liveRpi"/"liveRpiRank" are both Adjusted RPI (see
            # compute_live_rpi()'s docstring) -- kept as one paired decimal +
            # rank rather than mixing an unadjusted decimal with an adjusted
            # rank, which would show a number and a rank that don't actually
            # correspond to each other.
            "liveRpi": lr["adjustedRpi"] if lr else None,
            "liveRpiRank": lr["rank"] if lr else None,
            "liveRpiGp": lr["gp"] if lr else None,
            # How many teams got rated at all this run -- same number for
            # every team, repeated per-team so the page can show "Rank X of
            # N" without needing a separate global.
            "liveRpiTotal": len(live_rpi),
        }

    # ---- Manual: Drexel's full schedule (not in the scraper's source) ----
    drexel_games = []
    for d, loc, opp, played, win, result in DREXEL_SCHEDULE:
        w, h = week_of(d), default_half(d)
        opp_logo = output.get(opp, {}).get("logo") or lookup_logo(opp)
        opp_rpi = output.get(opp, {}).get("ownRpi") if opp in output else lookup_rpi(opp)[0]
        drexel_games.append({
            "week": w, "half": h, "loc": loc, "otherName": opp,
            "otherLogo": opp_logo, "otherRpi": opp_rpi,
            "otherLiveRpiRank": live_rank_of(opp), "otherNatName": nat_name_of(opp),
            "otherConfLogo": None,
            "played": played, "win": win, "result": result, "conf": opp in CAA_TEAMS,
        })
    output["Drexel"]["games"] = drexel_games
    output["Drexel"]["ownRpi"] = lookup_rpi("Drexel")[0]

    # Make sure Drexel shows up on the other side of each of those games too
    for d, loc, opp, played, win, result in DREXEL_SCHEDULE:
        if opp not in output:
            continue
        w, h = week_of(d), default_half(d)
        other_loc = "A" if loc == "H" else "H"
        other_result = None
        if result:
            a, b = result.split("-")
            other_result = f"{b}-{a}"
        already = any(g["otherName"] == "Drexel" and g["week"] == w for g in output[opp]["games"])
        if not already:
            output[opp]["games"].append({
                "week": w, "half": h, "loc": other_loc, "otherName": "Drexel",
                "otherLogo": output["Drexel"]["logo"], "otherRpi": output["Drexel"]["ownRpi"],
                "otherLiveRpiRank": live_rank_of("Drexel"),
                "otherConfLogo": None, "played": played,
                "win": (None if win is None else not win), "result": other_result,
                "conf": True,
            })

    # ---- Manual: confirmed results not yet in the scraper's output ----
    for team, opp, played, win, result in CONFIRMED_RESULTS:
        for g in output[team]["games"]:
            if g["otherName"] == opp:
                g.update({"played": played, "win": win, "result": result})
        for g in output.get(opp, {}).get("games", []):
            if g["otherName"] == team:
                a, b = result.split("-")
                g.update({"played": played, "win": (None if win is None else not win),
                          "result": f"{b}-{a}"})

    # ---- Compute each team's own cumulative record ----
    for disp, obj in output.items():
        played_games = [g for g in obj["games"] if g["played"]]
        w_ = sum(1 for g in played_games if g["win"] is True)
        l_ = sum(1 for g in played_games if g["win"] is False)
        d_ = sum(1 for g in played_games if g["win"] is None)
        obj["ownRecord"] = f"{w_}-{l_}-{d_}"

    return output


def build_conf_strength(scrape_path, rpi_path):
    """Convenience wrapper: load the files and return the conference table."""
    scrape = pd.read_excel(scrape_path, sheet_name=0)
    scrape["match_date"] = pd.to_datetime(scrape["match_date"]).dt.date
    scrape, _ = drop_postponed_duplicates(scrape)
    rpi_df = pd.read_excel(rpi_path, sheet_name=0)
    return compute_conference_strength(scrape, rpi_df)


def build_full_to_short(scrape: pd.DataFrame, rpi_df: pd.DataFrame):
    """
    Maps RPI.xlsx's full institutional name -> the short/common name the
    National page uses to label that team (the first raw scrape spelling
    seen for it, scanning every game in the whole scrape). This is the
    EXACT resolution build_national_rpi_data() uses to build its own
    per-team keys/URLs -- factor it out here so anything else that needs to
    link to a team's National page (e.g. the main matrix's team-name and
    opponent-logo links) computes the same key by construction, instead of
    guessing a name and hoping it matches.

    Bug this fixes (Colin, 2026-09-10): the main matrix's own TEAMS list
    hand-picks a short display name per tracked team ("Hampton", "App.
    State", "W. Carolina", "GA Southern", "ECU", "Charleston" -- see TEAMS
    above) that's DIFFERENT from what the raw scrape actually calls them
    ("Hampton University", "Appalachian State", "Western Carolina",
    "Georgia Southern", "East Carolina", "College of Charleston"). Since
    those raw strings are all the scrape ever uses, the National page's own
    short-name convention picked the long form for exactly these teams --
    so a link built from the matrix's abbreviated display name landed on a
    team name the National page had never heard of ("No national RPI data
    for Hampton"), while the *opponent* of one of these teams elsewhere on
    the site had the same problem in reverse.

    Returns (to_full, full_to_short):
      to_full(raw_scrape_or_display_name) -> RPI.xlsx's full spelling, or
        None if it doesn't resolve to a rated D1 team.
      full_to_short -- dict of {full_name: short_name}, where short_name is
        exactly the string the National page uses as that team's own key.
    """
    known = {}
    for _, r in rpi_df.iterrows():
        known[normalize(r["Team"])] = str(r["Team"]).strip()

    def to_full(name):
        full = RPI_NAME_ALIASES.get(name, name)
        return known.get(normalize(full))

    full_to_short = {}
    for raw in pd.concat([scrape["home_team"], scrape["away_team"]]).unique():
        full = to_full(raw)
        if full and full not in full_to_short:
            full_to_short[full] = raw

    return to_full, full_to_short


def build_national_rpi_data(scrape_path, rpi_path, master_path):
    """
    Nationwide equivalent of build_team_schedules(): every team with at
    least one Division-I-vs-Division-I result gets a full profile plus its
    complete chronological schedule, not just the 21 CAA-matrix teams.

    Scope decisions (documented here since they're not obvious from the
    numbers alone):
      * P/W/L/D, GF/GD, Win%/OppWin%/OppOppWin%, the RPI bands, and Last 5
        are all computed from Division-I-vs-Division-I games ONLY, same
        universe as compute_live_rpi() (see its docstring re: the 2026-09-09
        fix that excludes non-D1 games entirely, matching the real NCAA
        rule) -- this is "the record that counts toward the ranking," which
        is what real RPI tables show next to the RPI itself. "nonConfRecord"
        is the same D1-only universe, split out to D1 games against
        out-of-conference opponents (i.e. d1_games minus confRecord's games).
      * A team's "schedule" list, used on its own detail page, includes
        EVERY game on its calendar, D1 or not (an exhibition win over a D2
        team still happened and belongs on the schedule) -- opponents that
        aren't in the D1 universe just don't get a live-RPI number or a
        clickable link. "cumRecord" (the running record shown next to each
        game) is likewise the team's real overall record including those
        games, not the D1-only counted record -- so it matches what a fan
        watching the season would actually see. Each entry's "gameType" is
        "Conference" or "Non-Conference" (derived from conference
        membership); the raw scrape has no round/neutral-site flag, so
        "Conference Tournament" / "NCAA Tournament" aren't derivable and
        aren't attempted here. Each entry's "oppRecord" is the opponent's
        own D1-only record (their "w"-"l"-"d" below) at time of writing --
        i.e. through-the-full-season-so-far, same convention as "Record" on
        that opponent's own team page, not a point-in-time record as of the
        game date.
      * Conference rank ("confRank") is the CONFERENCE's national rank
        (out of however many conferences have at least one rated member),
        ordered by the average RPI Total of its rated members -- e.g. the
        ACC is #1 if ACC members' average RPI Total is the highest of any
        conference. Every team in a conference shares that conference's
        confRank/confTotal; this is not a team's position within its own
        conference.
      * RPI bands (1-25 / 26-50 / 51-100 / 101+, vs Top 100, vs below 150)
        bucket each opponent by that opponent's CURRENT live RPI rank, the
        same convention basketball's NET "quadrants" use -- so these shift
        under a team's past games as opponents' own ratings move, which is
        expected and matches how these tables work everywhere else.
      * '25 (2025 season) RPI is intentionally not included anywhere in this
        function's output -- last season's numbers aren't relevant once the
        current season is underway. (The main matrix page's separate '25 RPI
        display is untouched by this.)

    Returns {"asOf": "YYYY-MM-DD", "totalRated": N, "teams": {display_name: {...}}}.
    """
    scrape = pd.read_excel(scrape_path, sheet_name=0)
    scrape["match_date"] = pd.to_datetime(scrape["match_date"]).dt.date
    scrape, _ = drop_postponed_duplicates(scrape)
    scrape = augment_scrape_with_manual_results(scrape)

    rpi_df = pd.read_excel(rpi_path, sheet_name=0)
    master_df = pd.read_excel(master_path, sheet_name=0)

    conf_by_norm = {}
    conf_full_by_short = {}
    for _, r in rpi_df.iterrows():
        n = normalize(r["Team"])
        if pd.notna(r.get("Conference_Short")):
            conf_by_norm[n] = str(r["Conference_Short"]).strip()
            if pd.notna(r.get("Conference")):
                conf_full_by_short[str(r["Conference_Short"]).strip()] = str(r["Conference"]).strip()

    logo_by_norm = {}
    conf_logo_by_short = {}
    for _, r in master_df.iterrows():
        if pd.notna(r.get("Team_Logo_URL")):
            logo_by_norm[normalize(r["Team"])] = to_https(clean_url(r["Team_Logo_URL"]))
        if pd.notna(r.get("Conference_Short")) and pd.notna(r.get("Conference_Logo_URL")):
            conf_logo_by_short.setdefault(
                str(r["Conference_Short"]).strip(),
                to_https(clean_url(r["Conference_Logo_URL"])),
            )

    # RPI.xlsx spells teams out formally ("The University of North Carolina
    # at Charlotte"), but the scraper -- and the rest of this site -- uses
    # the name everyone actually calls them ("Charlotte"). `to_full`/
    # `full_to_short` (see build_full_to_short()) map between the two; that
    # common name is the id/label for a team everywhere in this function's
    # output (schedule dict keys, "opp" references, the outer teams_out
    # key) -- only the lookup helpers below (conference/logo) need to go
    # back through to the full name.
    to_full, full_to_short = build_full_to_short(scrape, rpi_df)
    short_to_full = {v: k for k, v in full_to_short.items()}

    def to_short(scrape_name):
        full = to_full(scrape_name)
        return full_to_short.get(full) if full else None

    def conf_of_disp(short_name):
        full = short_to_full.get(short_name, short_name)
        return conf_by_norm.get(normalize(full))

    def logo_of_disp(short_name):
        if short_name in LOGO_OVERRIDES:
            return to_https(clean_url(LOGO_OVERRIDES[short_name]))
        full = short_to_full.get(short_name, short_name)
        if full in LOGO_OVERRIDES:
            return to_https(clean_url(LOGO_OVERRIDES[full]))
        return logo_by_norm.get(normalize(full))

    live_rpi = compute_live_rpi(scrape, rpi_df)

    def live_of(short_name):
        if not short_name:
            return None
        full = short_to_full.get(short_name, short_name)
        return live_rpi.get(normalize(full))

    # ---- Pass 1: every game, resolved to common short names where possible ----
    all_rows = []
    for _, r in scrape.iterrows():
        h_disp, a_disp = to_short(r["home_team"]), to_short(r["away_team"])
        if not h_disp and not a_disp:
            continue  # neither side is a tracked D1 team -- not useful to anyone's page
        played = pd.notna(r["home_score"]) and pd.notna(r["away_score"])
        all_rows.append({
            "date": r["match_date"], "h_disp": h_disp, "a_disp": a_disp,
            "h_raw": r["home_team"], "a_raw": r["away_team"], "played": played,
            "hs": int(r["home_score"]) if played else None,
            "as_": int(r["away_score"]) if played else None,
        })

    schedule = defaultdict(list)
    for row in all_rows:
        if row["h_disp"]:
            schedule[row["h_disp"]].append({
                "date": row["date"], "loc": "H",
                "opp": row["a_disp"] or row["a_raw"], "opp_is_d1": bool(row["a_disp"]),
                "played": row["played"], "gf": row["hs"], "ga": row["as_"],
            })
        if row["a_disp"]:
            schedule[row["a_disp"]].append({
                "date": row["date"], "loc": "A",
                "opp": row["h_disp"] or row["h_raw"], "opp_is_d1": bool(row["h_disp"]),
                "played": row["played"], "gf": row["as_"], "ga": row["hs"],
            })
    for games in schedule.values():
        games.sort(key=lambda g: g["date"])

    def tally(gs):
        w = sum(1 for g in gs if g["gf"] > g["ga"])
        l = sum(1 for g in gs if g["gf"] < g["ga"])
        d = sum(1 for g in gs if g["gf"] == g["ga"])
        gf = sum(g["gf"] for g in gs)
        ga = sum(g["ga"] for g in gs)
        return w, l, d, gf, ga

    def rec(gs):
        w, l, d, _, _ = tally(gs)
        return f"{w}-{l}-{d}"

    # ---- Pass 2: per-team aggregates ----
    teams_out = {}
    for disp, games in schedule.items():
        conf = conf_of_disp(disp)
        d1_games = [g for g in games if g["played"] and g["opp_is_d1"]]
        w, l, d, gf, ga = tally(d1_games)
        p = w + l + d
        if p == 0:
            continue  # nothing rateable yet

        home_games = [g for g in d1_games if g["loc"] == "H"]
        away_games = [g for g in d1_games if g["loc"] == "A"]
        conf_games = [g for g in d1_games if conf and conf_of_disp(g["opp"]) == conf]
        non_conf_games = [g for g in d1_games if not (conf and conf_of_disp(g["opp"]) == conf)]
        # "Last 10" was next to meaningless once a team is only ~4-5 weeks
        # into a ~18-20 game season -- half the season doesn't fit in a
        # 10-game window yet. "Last 5" (Colin, 2026-09-10) both fits inside
        # an early-season sample and is still a genuine "recent form" read
        # later on. `d1_games` is already chronological (oldest first, same
        # ordering `schedule[disp]` was sorted into above), so this is
        # oldest-to-newest, left to right, same reading order as everything
        # else on the page.
        last5_games = d1_games[-5:]
        last5 = ["W" if g["gf"] > g["ga"] else "L" if g["gf"] < g["ga"] else "D" for g in last5_games]

        bands = {"1-25": [], "26-50": [], "51-100": [], "101+": []}
        vs_top100, vs_below150 = [], []
        for g in d1_games:
            lr = live_of(g["opp"])
            rank = lr["rank"] if lr else None
            if rank is None:
                continue
            band = "1-25" if rank <= 25 else "26-50" if rank <= 50 else "51-100" if rank <= 100 else "101+"
            bands[band].append(g)
            if rank <= 100:
                vs_top100.append(g)
            if rank > 150:
                vs_below150.append(g)

        lr_self = live_of(disp)
        teams_out[disp] = {
            "name": disp, "conference": conf,
            "confFull": conf_full_by_short.get(conf, conf),
            "logo": logo_of_disp(disp),
            "confLogo": conf_logo_by_short.get(conf) if conf else None,
            "p": p, "w": w, "l": l, "d": d, "gf": gf, "ga": ga, "gd": gf - ga,
            "winPct": lr_self["elem1"] if lr_self else None,
            "oppWinPct": lr_self["elem2"] if lr_self else None,
            "oppOppWinPct": lr_self["elem3"] if lr_self else None,
            "rpiTotal": lr_self["rpi"] if lr_self else None,
            # Adjusted RPI: the unadjusted 3-element number above, plus the
            # 2024 Women's Soccer Committee's non-conference bonus/penalty
            # (see compute_live_rpi()'s docstring) -- this is the NCAA's
            # actual "RPI" for selection/ranking purposes. `rank` (below) is
            # already based on this, not the unadjusted rpiTotal -- see
            # Colin's 2026-09-10 request to use Adjusted RPI for every
            # ranking on the site going forward.
            "rpiAdjusted": lr_self["adjustedRpi"] if lr_self else None,
            "rpiAdjustment": lr_self["adjustment"] if lr_self else None,
            "rank": lr_self["rank"] if lr_self else None,
            "confRecord": rec(conf_games),
            "nonConfRecord": rec(non_conf_games),
            "homeRecord": rec(home_games),
            "awayRecord": rec(away_games),
            # "last5Record" (a W-L-D string) is a sort-only convenience so
            # the page's existing "rec"-type column sort logic works
            # unchanged; "last5" (an ordered list of "W"/"L"/"D") is what
            # actually renders as the colored form circles.
            "last5Record": rec(last5_games),
            "last5": last5,
            "band1_25": rec(bands["1-25"]),
            "band26_50": rec(bands["26-50"]),
            "band51_100": rec(bands["51-100"]),
            "band101plus": rec(bands["101+"]),
            "vsTop100": rec(vs_top100),
            "vsBelow150": rec(vs_below150),
            "schedule": [
                {
                    "date": g["date"].strftime("%Y-%m-%d"), "loc": g["loc"],
                    "opp": g["opp"], "opp_is_d1": g["opp_is_d1"],
                    "oppLogo": logo_of_disp(g["opp"]) if g["opp_is_d1"] else None,
                    "oppConf": conf_of_disp(g["opp"]) if g["opp_is_d1"] else None,
                    "gameType": "Conference" if (conf and conf_of_disp(g["opp"]) == conf) else "Non-Conference",
                    "oppLiveRank": (live_of(g["opp"])["rank"] if g["opp_is_d1"] and live_of(g["opp"]) else None),
                    "played": g["played"], "gf": g["gf"], "ga": g["ga"],
                }
                for g in games
            ],
        }

    # Cumulative record per game (chronological, ALL games incl. non-D1) --
    # the "seasonal record through this point" trail on the detail page --
    # plus each opponent's own current D1-only record ("oppRecord"), which
    # needs teams_out fully populated first (an opponent played early in the
    # loop above might not have had its own record finalized yet).
    for t in teams_out.values():
        cw = cl = cd = 0
        for entry in t["schedule"]:
            if entry["played"]:
                if entry["gf"] > entry["ga"]:
                    cw += 1
                elif entry["gf"] < entry["ga"]:
                    cl += 1
                else:
                    cd += 1
            entry["cumRecord"] = f"{cw}-{cl}-{cd}"
            opp_t = teams_out.get(entry["opp"]) if entry["opp_is_d1"] else None
            entry["oppRecord"] = f"{opp_t['w']}-{opp_t['l']}-{opp_t['d']}" if opp_t else None

    # Conference rank: the CONFERENCE's national rank (not a team's rank
    # within its own conference) by the average Adjusted RPI of its rated
    # members -- every team in a conference shares that conference's
    # confRank/confTotal. Uses Adjusted RPI (not the plain rpiTotal), same
    # as every other ranking on this page -- see the rpiAdjusted comment
    # above.
    by_conf = defaultdict(list)
    for disp, t in teams_out.items():
        if t["conference"] and t["rpiAdjusted"] is not None:
            by_conf[t["conference"]].append(disp)
    conf_avg_rpi = {
        conf: sum(teams_out[n]["rpiAdjusted"] for n in names) / len(names)
        for conf, names in by_conf.items()
    }
    ranked_confs = sorted(conf_avg_rpi, key=lambda c: -conf_avg_rpi[c])
    conf_rank_by_conf = {c: i + 1 for i, c in enumerate(ranked_confs)}
    conf_total = len(ranked_confs)
    for t in teams_out.values():
        conf = t["conference"]
        if conf in conf_rank_by_conf:
            t["confRank"] = conf_rank_by_conf[conf]
            t["confTotal"] = conf_total
        else:
            t["confRank"] = None
            t["confTotal"] = None

    scored = scrape[scrape["home_score"].notna()]
    as_of = scored["match_date"].max().strftime("%Y-%m-%d") if len(scored) else None

    return {"asOf": as_of, "totalRated": len(teams_out), "teams": teams_out}


# ---- UNCW player leaderboards (Colin's GPS/event-tagging export) ----

# Hardcoded, like TEAMS/CAA_TEAMS/DREXEL_SCHEDULE above -- UNCW's two 2026
# goalkeepers, who split most matches ~45/45. Excluded from every physical
# (speed/distance) leaderboard: comparing a keeper's ground covered to a
# field player's is apples-to-oranges, and their minutes/Distance profile
# would otherwise look like an injury red flag rather than normal keeper
# usage. Update this set if the roster changes.
UNCW_GOALKEEPERS = {"L. White", "Z. Anderson"}

# Non-player rows the export mixes in: match-level team totals, one for
# UNCW and one for the opponent (used only for the goals-conceded number,
# see build_player_leaderboards()'s docstring -- never treated as players).
_PLAYER_DATA_TEAM_ROWS = {"UNCW", "Opponent"}


def build_player_leaderboards(player_xlsx_path):
    """
    UNCW-only player leaderboards, computed from Colin's weekly GPS/event-
    tagging export (one row per player per match; also carries two
    match-level pseudo-rows per game, "UNCW" and "Opponent", used only to
    recover team goals scored/conceded -- see the goalkeeping section
    below). Confirmed with Colin 2026-09-11/12.

    Per-90 qualifying bar: every RATE stat below (everything except GC,
    which Colin wants as a season total, no floor) requires at least
    30 minutes of playing time PER TEAM GAME PLAYED SO FAR -- e.g. 180
    minutes at 6 games, 210 at 7, etc. This isn't a fixed number by
    design: an early-season spot substitute can otherwise post an
    absurd per-90 rate off a handful of minutes (a real example from
    this data: a player who logged 13 minutes total showed the team's
    *best* Win+2-per-90 rate). Scaling the bar with games played keeps
    it meaningful without needing hand-tuning every week. See
    `data-quality-fixes.md` for the full analysis that established this.

    Leaderboards returned (dict keys), all UNCW players only:
      gc            -- Goal + Assist, season total, no qualifier.
      win2          -- Win2 per 90, qualified.
      ropDz         -- "Rest of Pitch" DZ Entries per 90, qualified.
                       DZ Entries = DZ Dribble + DZ Pass + DZ Cross +
                       DZ Set Piece + DZ Shot + DZ Regain; RoP DZ = DZ
                       Entries minus DZ Set Piece (i.e. entries a player
                       created themselves, not off a dead ball).
      faceUp        -- "Face up" per 90, qualified.
      firstContact  -- "First Contact on SP" per 90, qualified.
      dzDefending   -- (CL Secured + CL Successful + BS Successful +
                       BC Successful) per 90, qualified, PLUS a success%
                       alongside it: that same numerator divided by every
                       attempt in the same three families (adding in CL/
                       BS/BC Unsuccessful) -- i.e. of all CL/BS/BC
                       attempts, what fraction were a positive outcome.
                       CL Secured is a genuinely separate tag from CL
                       Successful (confirmed against the raw data: several
                       rows have Secured=1 with Successful=0), not a
                       subset of it, so it's summed in rather than
                       double-counted.
      defContrib    -- "Defending Contribution": (Interceptions + Def
                       Challenge Successful) per 90, qualified. Deliberately
                       excludes Regain Att Half per Colin -- an
                       interception that's also a Regain Att Half would
                       otherwise count twice for the same play.
      goalkeeping   -- NOT computed here; Colin asked to leave GK data out
                       of this round (2026-09-12). The plumbing for it
                       (team goals-conceded per match, split proportionally
                       by each keeper's minutes -- there's no data on which
                       keeper was in goal for which specific goal, since
                       Cleansheet is a match-level result identical for
                       both keepers every game) is documented in
                       `data-quality-fixes.md` for whenever this gets
                       picked back up.
      physTopSpeed  -- average of each player's per-match top speed (not
                       their single best game), qualified, keepers
                       excluded. Also a `trendDir` ("up"/"down"/"flat"/
                       null): compares the average of a player's earlier
                       tracked matches to their more recent ones (split at
                       the midpoint), null unless they have >=3 matches
                       with physical data, "flat" inside a +/-0.3 mph
                       noise band.
      physHiRatio   -- Hi-Intensity Distance / Total Distance, as a
                       percent, qualified, keepers excluded.
      physDistP90   -- Total Distance per 90 minutes (meters), qualified,
                       keepers excluded. This -- not raw season total
                       distance -- is the fair work-rate comparison across
                       players with very different minutes; per Colin's
                       ask for something that doesn't just reward whoever
                       plays the most.

    Also returns `asOf` (latest MatchDate in the file) and `qualifyMinutes`
    (the actual minute floor used this run) so the page can show a note
    explaining why a given player isn't on a list.
    """
    raw = pd.read_excel(player_xlsx_path)
    players = raw[~raw["Player"].isin(_PLAYER_DATA_TEAM_ROWS)].copy()

    match_dates = players["MatchDate"].dropna()
    as_of = match_dates.max().strftime("%Y-%m-%d") if len(match_dates) else None
    games_played = match_dates.nunique()
    qualify_minutes = games_played * 30

    dz_cols = ["DZ Dribble", "DZ Pass", "DZ Cross", "DZ Set Piece", "DZ Shot", "DZ Regain"]
    players["DZ Entries"] = players[dz_cols].sum(axis=1)
    players["RoP DZ"] = players["DZ Entries"] - players["DZ Set Piece"]
    players["DZDef success"] = players[
        ["CL Secured", "CL Successful", "BS Successful", "BC Successful"]
    ].sum(axis=1)
    players["DZDef attempts"] = players[
        ["CL Secured", "CL Successful", "CL Unsuccessful",
         "BS Successful", "BS Unsuccessful", "BC Successful", "BC Unsuccessful"]
    ].sum(axis=1)
    players["Def Contribution"] = players[["Interceptions", "Def Challenge Successful"]].sum(axis=1)

    agg = players.groupby("Player").agg(
        minutes=("Minutes", "sum"),
        goals=("Goal", "sum"),
        assists=("Assist", "sum"),
        win2=("Win2", "sum"),
        ropDz=("RoP DZ", "sum"),
        faceUp=("Face up", "sum"),
        firstContact=("First Contact on SP", "sum"),
        dzdSuccess=("DZDef success", "sum"),
        dzdAttempts=("DZDef attempts", "sum"),
        defContrib=("Def Contribution", "sum"),
    ).reset_index()
    agg["gc"] = agg["goals"] + agg["assists"]

    def per90(total, minutes):
        return round(total / (minutes / 90), 2) if minutes else None

    qual = agg[agg["minutes"] >= qualify_minutes].copy()

    def top_list(frame, value_col, extra=None):
        rows = []
        for _, r in frame.sort_values(value_col, ascending=False).iterrows():
            if r[value_col] is None:
                continue
            row = {"name": r["Player"], "value": r[value_col]}
            if extra:
                row.update(extra(r))
            rows.append(row)
        return rows

    qual["win2P90"] = qual.apply(lambda r: per90(r["win2"], r["minutes"]), axis=1)
    qual["ropDzP90"] = qual.apply(lambda r: per90(r["ropDz"], r["minutes"]), axis=1)
    qual["faceUpP90"] = qual.apply(lambda r: per90(r["faceUp"], r["minutes"]), axis=1)
    qual["firstContactP90"] = qual.apply(lambda r: per90(r["firstContact"], r["minutes"]), axis=1)
    qual["dzdP90"] = qual.apply(lambda r: per90(r["dzdSuccess"], r["minutes"]), axis=1)
    qual["dzdPct"] = qual.apply(
        lambda r: round(r["dzdSuccess"] / r["dzdAttempts"] * 100, 1) if r["dzdAttempts"] else None,
        axis=1,
    )
    qual["defContribP90"] = qual.apply(lambda r: per90(r["defContrib"], r["minutes"]), axis=1)

    # ---- physical: average top speed, trend, hi-intensity ratio, dist/90 ----
    phys_rows = players[~players["Player"].isin(UNCW_GOALKEEPERS)].dropna(
        subset=["MaxSpeed", "HiDistance"]
    )
    phys_agg = phys_rows.groupby("Player").agg(
        minutes=("Minutes", "sum"),
        matches=("MatchDate", "nunique"),
        totalDistance=("Distance", "sum"),
        totalHi=("HiDistance", "sum"),
        avgTopSpeed=("MaxSpeed", "mean"),
    ).reset_index()
    phys_qual = phys_agg[phys_agg["minutes"] >= qualify_minutes].copy()
    phys_qual["avgTopSpeed"] = phys_qual["avgTopSpeed"].round(2)
    phys_qual["hiRatioPct"] = (phys_qual["totalHi"] / phys_qual["totalDistance"] * 100).round(1)
    phys_qual["distP90"] = phys_qual.apply(
        lambda r: round(r["totalDistance"] / (r["minutes"] / 90)) if r["minutes"] else None, axis=1
    )

    def trend_dir(group):
        g = group.sort_values("MatchDate")
        if len(g) < 3:
            return None, None
        half = len(g) // 2
        delta = round(g["MaxSpeed"].iloc[-half:].mean() - g["MaxSpeed"].iloc[:half].mean(), 2)
        if delta >= 0.3:
            return delta, "up"
        if delta <= -0.3:
            return delta, "down"
        return delta, "flat"

    trends = phys_rows.groupby("Player").apply(
        lambda g: pd.Series(trend_dir(g), index=["trend", "trendDir"]), include_groups=False
    )
    phys_qual = phys_qual.merge(trends, on="Player", how="left")

    def phys_list(value_col, name_key="value", extra_cols=None):
        rows = []
        for _, r in phys_qual.sort_values(value_col, ascending=False).iterrows():
            row = {"name": r["Player"], name_key: r[value_col]}
            if extra_cols:
                for k in extra_cols:
                    v = r[k]
                    row[k] = None if pd.isna(v) else v
            rows.append(row)
        return rows

    return {
        "asOf": as_of,
        "gamesPlayed": int(games_played),
        "qualifyMinutes": int(qualify_minutes),
        "gc": [{"name": r["Player"], "value": int(r["gc"])}
               for _, r in agg.sort_values("gc", ascending=False).iterrows() if r["gc"] > 0],
        "win2": [{"name": r["Player"], "value": r["win2P90"]}
                 for _, r in qual.sort_values("win2P90", ascending=False).iterrows()],
        "ropDz": [{"name": r["Player"], "value": r["ropDzP90"]}
                  for _, r in qual.sort_values("ropDzP90", ascending=False).iterrows()],
        "faceUp": [{"name": r["Player"], "value": r["faceUpP90"]}
                   for _, r in qual.sort_values("faceUpP90", ascending=False).iterrows()],
        "firstContact": [{"name": r["Player"], "value": r["firstContactP90"]}
                          for _, r in qual.sort_values("firstContactP90", ascending=False).iterrows()],
        "dzDefending": [{"name": r["Player"], "value": r["dzdP90"], "pct": r["dzdPct"]}
                        for _, r in qual.sort_values("dzdP90", ascending=False).iterrows()],
        "defContrib": [{"name": r["Player"], "value": r["defContribP90"]}
                       for _, r in qual.sort_values("defContribP90", ascending=False).iterrows()],
        "physTopSpeed": phys_list("avgTopSpeed", extra_cols=["trend", "trendDir"]),
        "physHiRatio": phys_list("hiRatioPct"),
        "physDistP90": phys_list("distP90"),
    }


# ---- Match Center (team & match pages) ----
#
# Source files, confirmed 2026-09-12:
#   fDataMatch.xlsx   -- same schema as Matrix_Player_Data.xlsx but "in
#                        full": 2024-02-10 through present, plus (for team
#                        rows only) 6 extra rows per side per match at
#                        Min = 15/30/45/60/75/90 -- these are PER-WINDOW
#                        (not cumulative) snapshots used for the Match
#                        Flow chart, confirmed by Colin and by reproducing
#                        the Coaches Booklet's numbers below.
#   fDataXYPlot.xlsx  -- one row per coded event with an X/Y pitch
#                        coordinate; Shot rows carry xG, Type, Result and
#                        Time (match minute) -- used for team xG and the
#                        xG Flow chart. Team is literally "UNCW" or
#                        "Opponent", same as fDataMatch.
#   PlayerMatchReport.xlsx > "Team" sheet -- one row per match (played and
#                        scheduled), with real Opponent name, Venue,
#                        City, pitch size, halftime/full-time score,
#                        Result (Win/Draw/Loss), and RPI (Fall 2026 only
#                        so far).
#
# All column mappings below were reverse-verified line-by-line against
# Colin's own "Coaches Booklet FA26 LSU.pdf" (08/08/2026 match, final
# 3-2) -- every Match Statistics and Match Objectives number here matches
# that PDF exactly, with ONE known small residual: the Match Flow
# per-match total computed here comes out ~1-2% off the booklet's printed
# total (73.15 vs. printed 72.15 for UNCW; 34.70 vs. 34.50 for the
# opponent) -- close enough to confirm the weight formula and column
# mapping are right in substance, but there's a small definitional
# mismatch on one sub-metric still to track down (candidates: "Second
# Ball Securance" might mean the separate `Securance Successful` column
# rather than `Second Ball`, or "DZ Entry" might exclude one of the six
# sub-types). Flag to Colin before trusting Match Flow to the decimal.
#
# Two Match Objectives rows are NOT tagged symmetrically for both teams
# in the source data -- Colin's tagging only logs these from UNCW's own
# perspective, so the "opponent" side of the comparison is the SAME
# underlying UNCW-tagged number read as its mirror-image event:
#   Att Half Fouls Earned (opp) = UNCW's "Def Foul Conceded"
#   Att Half Regain        (opp) = UNCW's "Lost balls own half"
#   Def Half Lost Ball     (us)  = UNCW's "Lost balls own half"
#   Def Half Lost Ball     (opp) = UNCW's "Regain Att Half"
#   Fouls Conceded          (opp) = UNCW's "Foul Earned"
# (a foul WE earn is a foul THEY conceded; a ball WE regain in their half
# is a ball THEY lost in their own half -- same event, two perspectives).
# Everything else in both blocks (Face Up, Win+2, the DZ sub-types,
# Creative Actions, Switches, First Contact, Second Balls, Block
# Shots/Crosses, Double Downs, Clearances, Corners, Yellow/Red, Throw-in
# %) IS tagged independently for both teams and used directly.

MATCH_FLOW_WEIGHTS = {
    "Att Foul Earned": 0.5,
    "Corner": 1.0,
    "Face up": 0.1,
    "First Contact on SP": 0.25,
    "Goal": 3.0,
    "Regain Att Half": 0.5,
    "Second Ball": 0.25,
    "Shot Off Target": 0.5,
    "Shot Saved": 1.0,
    "Switch": 0.1,
    # DZ Entry (composite of the 6 sub-type columns) is added separately
    # below at the same 1.0 weight -- see DZ_ENTRY_COLS.
}
DZ_ENTRY_COLS = ["DZ Dribble", "DZ Pass", "DZ Cross", "DZ Set Piece", "DZ Shot", "DZ Regain"]


def _team_stats_row(team_df, side):
    """One row (Player == 'UNCW' or 'Opponent') of match-total team stats."""
    row = team_df[(team_df["Player"] == side) & (team_df["Min"].isna())]
    return row.iloc[0] if len(row) else None


def _dz_entries(row):
    total = sum(row.get(c) or 0 for c in DZ_ENTRY_COLS)
    return total, total - (row.get("DZ Set Piece") or 0)


# ---- Shot map (added 2026-09-14, Colin's ask) ----
#
# fDataXYPlot.xlsx's "Result" column has messy/inconsistent tagging (mixed
# case, a couple of stray "Successful"/"Unsuccessful"/"Saved" one-offs found
# during data investigation) -- normalize to a small fixed vocabulary the
# shot map's dot styling switches on, rather than keying front-end CSS off
# raw values that could vary. Unrecognized/missing values map to "other"
# so a new tagging value never silently breaks rendering.
def _norm_shot_result(raw):
    if not isinstance(raw, str):
        return None
    r = raw.strip().lower()
    if r == "goal":
        return "goal"
    if r in ("save", "saved"):
        return "save"
    if r == "block":
        return "block"
    if r == "post":
        return "post"
    if r in ("off", "off target"):
        return "off"
    return "other"


def _shot_points(shot_rows, use_frame):
    """One dict per shot with a location Colin asked for two different ways:

    - `use_frame=True` (UNCW's own shots): (ShotX, ShotY) -- where the shot
      ended up relative to the goal frame (a small, centered-on-goal
      coordinate space; confirmed via direct data inspection that "Goal"/
      "Save" results cluster in roughly [-12, 12] x [0, 8], with "Off"
      results extending further out to represent wide/over misses). Only
      populated for matches tagged since ~Nov 2025 -- rows without it are
      skipped rather than plotted at (0, 0), so an early-season/historical
      match with no frame tagging yet just yields an empty list (rendered
      as a "not tracked for this match" note, not a fake origin cluster).
    - `use_frame=False` (Opponent's shots, per Colin: "I don't think I do
      the shot on goal xy for opponent so it will just be on the pitch
      where they shoot the ball"): (X, Y), the general on-pitch shot
      *origin* location (0-100 scale, both teams' own attacking direction)
      that's populated for essentially every shot back to the earliest
      2024 match -- confirmed via direct inspection, unlike ShotX/ShotY
      this isn't a recently-added tagging field.
    """
    pts = []
    for _, r in shot_rows.iterrows():
        if use_frame:
            x, y = r.get("ShotX"), r.get("ShotY")
        else:
            x, y = r.get("X"), r.get("Y")
        if pd.isna(x) or pd.isna(y):
            continue
        pts.append({
            "x": round(float(x), 1),
            "y": round(float(y), 1),
            "result": _norm_shot_result(r.get("Result")),
            "xg": round(float(r["xG"]), 3) if pd.notna(r.get("xG")) else None,
            "player": r.get("Player") if isinstance(r.get("Player"), str) else None,
        })
    return pts


def build_match_center(match_xlsx_path, xy_xlsx_path, lookup_xlsx_path, season="Fall 2026"):
    """
    Team & Match pages data: one entry per match in `season` (played and
    still-scheduled), each with a Match Statistics comparison, a Match
    Objectives comparison, a Match Flow step-chart series, and an xG Flow
    step-chart series -- modeled directly on Colin's Coaches Booklet
    (see the big comment block above for verified column mappings).

    Scoped to one season at a time (Fall 2026 by default) to match the
    rest of this site's season-at-a-time convention and keep the payload
    small; `fDataMatch.xlsx`/`fDataXYPlot.xlsx` carry multiple seasons of
    history for whenever a career-mode phase revisits this.
    """
    match_data = pd.read_excel(match_xlsx_path)
    match_data["MatchDate"] = pd.to_datetime(match_data["MatchDate"])
    xy = pd.read_excel(xy_xlsx_path)
    xy["MatchDate"] = pd.to_datetime(xy["MatchDate"])
    lookup = pd.read_excel(lookup_xlsx_path, sheet_name="Team")
    lookup["MatchDate"] = pd.to_datetime(lookup["MatchDate"])
    lookup = lookup[lookup["MatchSeason"] == season].sort_values("MatchDate")
    # Drop intrasquad scrimmages (TealWhite, UNC Club) -- not real opponents,
    # shouldn't appear as a fixture or need a team color.
    lookup = lookup[~lookup["Opponent"].isin(EXCLUDED_OPPONENTS)]

    matches = []
    season_table = []
    for _, meta in lookup.iterrows():
        d = meta["MatchDate"]
        d_str = d.strftime("%Y-%m-%d")
        played = pd.notna(meta.get("Result"))

        header = {
            "date": d_str,
            "type": meta.get("Type"),
            "opponent": meta.get("Opponent"),
            "opponentColor": team_color_for(meta.get("Opponent")),
            "venue": meta.get("Venue"),
            "city": meta.get("City"),
            "halftimeScore": meta.get("HalftimeScore"),
            "fullTimeScore": meta.get("FullTimeScore"),
            "teamGoal": meta.get("TeamGoal"),
            "opponentGoal": meta.get("OpponentGoal"),
            "result": meta.get("Result") if played else None,
            "rpi": int(meta["RPI"]) if pd.notna(meta.get("RPI")) else None,
        }

        entry = {**header, "played": bool(played)}
        row_table = {**header}

        if played:
            team_df = match_data[match_data["MatchDate"] == d]
            us_row = _team_stats_row(team_df, "UNCW")
            opp_row = _team_stats_row(team_df, "Opponent")

            if us_row is not None and opp_row is not None:
                shots = xy[(xy["MatchDate"] == d) & (xy["Event"] == "Shot")]
                xg_by_team = shots.groupby("Team")["xG"].sum().to_dict()

                # Shot map (Colin's ask, 2026-09-14): UNCW's own shots
                # plotted by where they ended up on the goal frame,
                # Opponent's shots plotted by where they were taken from
                # on the pitch -- see _shot_points()'s docstring for why
                # the two sides use different coordinate fields.
                entry_shot_map = {
                    "usFrame": _shot_points(shots[shots["Team"] == "UNCW"], use_frame=True),
                    "oppPitch": _shot_points(shots[shots["Team"] == "Opponent"], use_frame=False),
                }

                def stats_side(row, other_row, xg):
                    dz, rop = _dz_entries(row)
                    ti_s, ti_u = row.get("TI Successful") or 0, row.get("TI Unsuccessful") or 0
                    return {
                        "goals": int(row.get("Goal") or 0),
                        "xG": round(float(xg or 0), 3),
                        "shotsTotal": int(row.get("Shot Total") or 0),
                        "shotsOn": int((row.get("Goal") or 0) + (row.get("Shot Saved") or 0)),
                        "shotsOff": int(row.get("Shot Off Target") or 0),
                        "shotsBlocked": int(row.get("Shot Blocked") or 0),
                        "saves": int(other_row.get("Shot Saved") or 0),
                        "corners": int(row.get("Corner") or 0),
                        "throwInPct": round(ti_s / (ti_s + ti_u) * 100, 1) if (ti_s + ti_u) else None,
                        "yellow": int(row.get("Yellow") or 0),
                        "red": int(row.get("Red") or 0),
                        "dzEntries": int(dz),
                        "ropDzEntries": int(rop),
                    }

                stats_us = stats_side(us_row, opp_row, xg_by_team.get("UNCW"))
                stats_opp = stats_side(opp_row, us_row, xg_by_team.get("Opponent"))
                # Fouls conceded aren't tagged for the opponent side directly --
                # see the module comment above for why these two are mirrored.
                stats_us["foulsConceded"] = int(us_row.get("Foul Conceded") or 0)
                stats_opp["foulsConceded"] = int(us_row.get("Foul Earned") or 0)

                def objectives_side(row):
                    return {
                        "faceUp": int(row.get("Face up") or 0),
                        "win2": row.get("Win2"),
                        "dzDribble": int(row.get("DZ Dribble") or 0),
                        "dzPass": int(row.get("DZ Pass") or 0),
                        "dzCross": int(row.get("DZ Cross") or 0),
                        "dzSetPiece": int(row.get("DZ Set Piece") or 0),
                        "dzShot": int(row.get("DZ Shot") or 0),
                        "creativeActions": int(row.get("Creative Action") or 0),
                        "switches": int(row.get("Switch") or 0),
                        "firstContact": int(row.get("First Contact on SP") or 0),
                        "secondBalls": int(row.get("Second Ball") or 0),
                        "clearances": int((row.get("CL Successful") or 0)
                                           + (row.get("CL Unsuccessful") or 0)
                                           + (row.get("CL Secured") or 0)),
                        "blockShots": int(row.get("BS Successful") or 0),
                        "blockCrosses": int(row.get("BC Successful") or 0),
                        "doubleDowns": int(row.get("Double Down") or 0),
                        "professionalFouls": int(row.get("Professional Foul") or 0),
                    }

                obj_us = objectives_side(us_row)
                obj_opp = objectives_side(opp_row)
                # Mirror-image pairs -- see module comment above.
                obj_us["attHalfFoulsEarned"] = int(us_row.get("Att Foul Earned") or 0)
                obj_opp["attHalfFoulsEarned"] = int(us_row.get("Def Foul Conceded") or 0)
                obj_us["attHalfRegain"] = int(us_row.get("Regain Att Half") or 0)
                obj_opp["attHalfRegain"] = int(us_row.get("Lost balls own half") or 0)
                obj_us["defHalfLostBall"] = int(us_row.get("Lost balls own half") or 0)
                obj_opp["defHalfLostBall"] = int(us_row.get("Regain Att Half") or 0)

                # Match Flow: 6 per-15-min-WINDOW rows per side (not
                # cumulative on their own -- confirmed by reproducing the
                # booklet's numbers), turned into a cumulative step series.
                def flow_series(side):
                    seg = team_df[(team_df["Player"] == side) & (team_df["Min"].notna())].sort_values("Min")
                    minutes = [0]
                    values = [0.0]
                    running = 0.0
                    for _, r in seg.iterrows():
                        dz_total, _ = _dz_entries(r)
                        window = dz_total * 1.0
                        for col, w in MATCH_FLOW_WEIGHTS.items():
                            window += (r.get(col) or 0) * w
                        running += window
                        minutes.append(int(r["Min"]))
                        values.append(round(running, 2))
                    return minutes, values

                us_minutes, us_flow = flow_series("UNCW")
                _, opp_flow = flow_series("Opponent")

                # xG Flow: cumulative xG by shot minute, one step series per team.
                def xg_flow_series(team_name):
                    ts = shots[(shots["Team"] == team_name) & shots["Time"].notna()].sort_values("Time")
                    minutes, values, running = [0], [0.0], 0.0
                    for _, r in ts.iterrows():
                        running += float(r["xG"] or 0)
                        minutes.append(float(r["Time"]))
                        values.append(round(running, 3))
                    return minutes, values

                us_xg_minutes, us_xg_flow = xg_flow_series("UNCW")
                opp_xg_minutes, opp_xg_flow = xg_flow_series("Opponent")

                entry["stats"] = {"us": stats_us, "opp": stats_opp}
                entry["objectives"] = {"us": obj_us, "opp": obj_opp}
                entry["matchFlow"] = {"minutes": us_minutes, "us": us_flow, "opp": opp_flow}
                entry["xgFlow"] = {"us": {"minutes": us_xg_minutes, "values": us_xg_flow},
                                    "opp": {"minutes": opp_xg_minutes, "values": opp_xg_flow}}
                entry["shotMap"] = entry_shot_map

                row_table.update({
                    "dzEntries": stats_us["dzEntries"], "win2": obj_us["win2"],
                    "shotsTotal": stats_us["shotsTotal"], "xG": stats_us["xG"],
                })

        matches.append(entry)
        season_table.append(row_table)

    return {"season": season, "matches": matches}


# ---- CAA standings (South/North/Overall) ----
#
# Python port of the tie-break/ranking logic that used to live only in
# uncw_schedule_matrix_v5.html's client-side JS (tallyGames/headToHead/
# caaTeams, added for the v3.8 CAA-links round). Moved here 2026-09-13 as
# part of the site-restructure project (see player-report-cards-plan.md) so
# both the new Home page and the future dedicated CAA page can share one
# pre-computed, pre-ranked source of truth instead of two JS copies of the
# same sort/tie-break rules drifting apart over time.
CAA_DIVISIONS = {
    "Campbell": "South", "Charleston": "South", "Elon": "South", "Hampton": "South",
    "UNC Wilmington": "South", "William & Mary": "South",
    "Drexel": "North", "Hofstra": "North", "Monmouth": "North",
    "Northeastern": "North", "Stony Brook": "North", "Towson": "North",
}


def _split_score(result):
    if not result:
        return None
    m = re.match(r"^(\d+)-(\d+)$", result)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _tally_games(team_schedules, name, keep):
    t = team_schedules.get(name, {})
    out = {"played": 0, "w": 0, "l": 0, "d": 0, "gf": 0, "ga": 0}
    for g in t.get("games", []):
        if not g.get("played") or not keep(g):
            continue
        s = _split_score(g.get("result"))
        if not s:
            continue
        gf, ga = s
        out["played"] += 1
        out["gf"] += gf
        out["ga"] += ga
        if g.get("win") is True:
            out["w"] += 1
        elif g.get("win") is False:
            out["l"] += 1
        else:
            out["d"] += 1
    out["gd"] = out["gf"] - out["ga"]
    out["pts"] = out["w"] * 3 + out["d"]
    return out


def _head_to_head(team_schedules, a, b):
    """>0 if a is ahead of b, <0 if b is ahead, 0 if level/not yet played."""
    t = team_schedules.get(a, {})
    score = 0
    for g in t.get("games", []):
        if not g.get("played") or not g.get("conf") or g.get("otherName") != b:
            continue
        if g.get("win") is True:
            score += 1
        elif g.get("win") is False:
            score -= 1
    return score


def _team_form(team_schedules, name, n=5):
    """
    Last `n` played games' results as an ordered ["W"/"L"/"D", ...] list,
    oldest to newest -- same shape/convention as
    `build_national_rpi_data()`'s own `last5` (see line ~1425) and
    `home.html`'s `renderFormCircles()`, which both consume this exact
    left-to-right ordering. Added 2026-09-15 for the CAA standings tables'
    new Form column (Colin: "add the form at the end of the columns for
    all those tables/standings").

    Sorts by (week, half) rather than trusting `games` list order: Drexel's
    hand-entered schedule (DREXEL_SCHEDULE) gets appended to the END of an
    opponent's games list regardless of its real date (see
    build_team_schedules()'s Drexel-injection block), so a played Drexel
    game could otherwise land out of chronological order and corrupt which
    5 games count as "last". Half "a" (Mon-Thu) always sorts before half
    "b" (Fri-Sun) within the same week, per default_half()'s own
    convention, so (week, half) is a safe, always-available substitute for
    a real date field (this dataset doesn't carry per-game dates).
    """
    HALF_ORDER = {"a": 0, "b": 1}
    games = team_schedules.get(name, {}).get("games", [])
    played = [g for g in games if g.get("played") and _split_score(g.get("result"))]
    played.sort(key=lambda g: (g.get("week") or 0, HALF_ORDER.get(g.get("half"), 0)))
    last_n = played[-n:]
    form = []
    for g in last_n:
        if g.get("win") is True:
            form.append("W")
        elif g.get("win") is False:
            form.append("L")
        else:
            form.append("D")
    return form


def compute_caa_standings(team_schedules):
    """
    Returns {"south": [...], "north": [...], "overall": [...]}, each a list
    of dicts (one per CAA team, pre-sorted, with a "rank" field already
    assigned) using the exact same tie-break order as the original JS:
    points, then head-to-head, then goal difference, goals for, goals
    against, overall win %, overall wins, then name.
    """
    teams = []
    for name, division in CAA_DIVISIONS.items():
        t = team_schedules.get(name, {})
        conf = _tally_games(team_schedules, name, lambda g: g.get("conf"))
        all_ = _tally_games(team_schedules, name, lambda g: True)
        # Non-Conference record (added 2026-09-15, Colin's ask: "I'd like to
        # see the non-conference record between RPI and Overall Record" --
        # both here and on Home's mirrored South table) -- the complement of
        # the existing conference-only tally above, same _tally_games()
        # helper, just inverted keep predicate.
        non_conf = _tally_games(team_schedules, name, lambda g: not g.get("conf"))
        opp_ranks = [g.get("otherLiveRpiRank") for g in t.get("games", [])
                     if isinstance(g.get("otherLiveRpiRank"), (int, float))]
        live_sos = round(sum(opp_ranks) / len(opp_ranks)) if opp_ranks else None
        overall_pct = (all_["w"] + 0.5 * all_["d"]) / all_["played"] if all_["played"] else 0
        teams.append({
            "name": name, "division": division, "logo": t.get("logo"),
            "natName": t.get("natName"),
            "liveRpi": t.get("liveRpi"), "liveRpiRank": t.get("liveRpiRank"),
            "liveRpiGp": t.get("liveRpiGp"), "liveRpiTotal": t.get("liveRpiTotal"),
            "nonConfRecord": f"{non_conf['w']}-{non_conf['l']}-{non_conf['d']}",
            "overall": t.get("ownRecord") or f"{all_['w']}-{all_['l']}-{all_['d']}",
            "overallPct": overall_pct, "overallW": all_["w"], "liveSos": live_sos,
            # Form (last 5 overall results, oldest->newest) -- added
            # 2026-09-15 alongside nonConfRecord, same round, per Colin's
            # follow-up ask to add it "at the end of the columns" on every
            # standings table. Overall (not conference-only) results, same
            # as the Season Record dashboard's own Form tile, since no CAA
            # games have been played yet this season.
            "form": _team_form(team_schedules, name),
            **conf,
        })

    def sort_key_group(group):
        import functools

        def cmp(a, b):
            if b["pts"] != a["pts"]:
                return b["pts"] - a["pts"]
            h2h = _head_to_head(team_schedules, a["name"], b["name"])
            if h2h != 0:
                return -h2h
            if b["gd"] != a["gd"]:
                return b["gd"] - a["gd"]
            if b["gf"] != a["gf"]:
                return b["gf"] - a["gf"]
            if a["ga"] != b["ga"]:
                return a["ga"] - b["ga"]
            if b["overallPct"] != a["overallPct"]:
                return 1 if a["overallPct"] < b["overallPct"] else -1
            if b["overallW"] != a["overallW"]:
                return b["overallW"] - a["overallW"]
            return -1 if a["name"] < b["name"] else (1 if a["name"] > b["name"] else 0)

        ranked = sorted(group, key=functools.cmp_to_key(cmp))
        return [{**t, "rank": i + 1} for i, t in enumerate(ranked)]

    south = sort_key_group([t for t in teams if t["division"] == "South"])
    north = sort_key_group([t for t in teams if t["division"] == "North"])
    overall = sort_key_group(teams)
    return {"south": south, "north": north, "overall": overall}


# ---- Home page summary ----
#
# A small, purpose-built data block for the new Home page (see
# player-report-cards-plan.md's 2026-09-13 site-restructure entry) --
# deliberately NOT the full TEAM_SCHEDULES/MATCH_CENTER/PLAYER_LEADERBOARDS
# trees, so home.html stays light. Draws from all three since Home is a
# one-glance summary of things that live on their own dedicated pages later
# (Fixtures, Squad, CAA).
HOME_LEADER_PREVIEW = [
    ("gc", "Goal Contributions"),
    ("defContrib", "Defensive Contribution / 90"),
    ("physDistP90", "Distance / 90"),
]


def build_home_summary(team_schedules, caa_standings, player_leaderboards,
                        match_center, team_name="UNC Wilmington", national_stats=None):
    t = team_schedules.get(team_name, {})
    caa_row = next((r for r in caa_standings["south"] if r["name"] == team_name), None)

    matches = match_center.get("matches", [])
    next_fixture = None
    last_result = None
    for m in matches:
        if not m.get("played") and next_fixture is None:
            # m["opponent"] comes straight from PlayerMatchReport.xlsx's raw
            # "Opponent" column, which doesn't always match team_schedules'
            # own (sometimes abbreviated) display-name keys -- e.g. it spells
            # out "Western Carolina" in full where team_schedules is keyed
            # "W. Carolina" (see TEAMS). Resolve through SCRAPENAME_TO_DISP
            # first, same alias map build_team_schedules() itself uses.
            opp_disp = SCRAPENAME_TO_DISP.get(m.get("opponent"), m.get("opponent"))
            opp_record = team_schedules.get(opp_disp, {}).get("ownRecord")
            next_fixture = {
                "date": m.get("date"), "opponent": m.get("opponent"),
                "venue": m.get("venue"), "city": m.get("city"),
                "rpi": m.get("rpi"), "opponentRecord": opp_record,
            }
        if m.get("played"):
            last_result = {
                "date": m.get("date"), "opponent": m.get("opponent"),
                "result": m.get("result"), "fullTimeScore": m.get("fullTimeScore"),
                "venue": m.get("venue"), "hasStats": bool(m.get("stats")),
            }

    leaders = []
    for key, label in HOME_LEADER_PREVIEW:
        entries = player_leaderboards.get(key) or []
        if entries:
            leaders.append({"label": label, "name": entries[0]["name"], "value": entries[0]["value"]})

    return {
        "team": team_name, "logo": t.get("logo"),
        "record": t.get("ownRecord"),
        "rpi": {"value": t.get("liveRpi"), "rank": t.get("liveRpiRank"),
                "gp": t.get("liveRpiGp"), "total": t.get("liveRpiTotal")},
        "caaStanding": ({"division": "South", "rank": caa_row["rank"],
                          "of": len(caa_standings["south"]), "pts": caa_row["pts"],
                          "record": f"{caa_row['w']}-{caa_row['l']}-{caa_row['d']}"}
                         if caa_row else None),
        # Full South division standings table (added 2026-09-15, Colin's
        # ask: "add the south division standings to home page") -- the
        # exact same `compute_caa_standings()["south"]` rows the CAA page's
        # own South table renders, so the two pages can never disagree.
        # home.html ports the same renderTable()-style markup CAA page uses
        # (including the new nonConfRecord column) rather than a second
        # implementation.
        "caaSouthStandings": caa_standings.get("south") or [],
        "nextFixture": next_fixture,
        "lastResult": last_result,
        "leaders": leaders,
        "asOf": player_leaderboards.get("asOf"),
        # Season Record dashboard, added 2026-09-14 (Colin: "let's add the
        # season record dashboard to the home page") -- the exact same
        # profile Fixtures' own Season Record section shows, via the same
        # shared helper, so Home/Fixtures/National RPI always agree. None
        # if no national_stats was passed in (e.g. build_national_rpi_data()
        # not available yet -- see do_rebuild.py/weekly_update.py).
        "seasonStats": _season_stats_from_national(national_stats),
    }


def _season_stats_from_national(nat):
    """Shared 12-tile Season Record profile (Nat'l Rank, RPI Total,
    Adjusted RPI, Record, Goals F-A, Goal Diff, Home, Away, Conference,
    Non-Conference, Form, vs Top 100) built from one team's entry in
    `build_national_rpi_data()["teams"]`. Both Fixtures' Season Record
    section and Home's Season Record dashboard (added 2026-09-14, same
    day -- Colin: "let's add the season record dashboard to the home
    page") read the exact same `national_stats` entry through this one
    function, so Home/Fixtures/National RPI never drift out of agreement.
    Returns None if `nat` is None (no national profile available, e.g. a
    historical Fixtures season -- see build_fixtures_summary's docstring)."""
    if not nat:
        return None
    return {
        "rank": nat.get("rank"), "rpiTotal": nat.get("rpiTotal"),
        "rpiAdjusted": nat.get("rpiAdjusted"),
        "record": f"{nat['w']}-{nat['l']}-{nat['d']}",
        "gf": nat.get("gf"), "ga": nat.get("ga"), "gd": nat.get("gd"),
        "homeRecord": nat.get("homeRecord"), "awayRecord": nat.get("awayRecord"),
        "confRecord": nat.get("confRecord"), "nonConfRecord": nat.get("nonConfRecord"),
        "last5": nat.get("last5"), "vsTop100": nat.get("vsTop100"),
    }


# ---- Fixtures page summary ----
#
# Site-restructure Round 3 (see site-restructure-plan.md). Reuses
# MATCH_CENTER's `matches` list as the schedule's source of truth --
# it already carries every game (exhibitions through CAA, played and
# upcoming) with real calendar dates, venue, opponent RPI rank, and score,
# straight from PlayerMatchReport.xlsx's `Team` sheet -- so this function
# adds only what Fixtures needs on top: opponent record (via a
# team_schedules lookup, when the opponent is one of the 21 tracked teams)
# and the four trend series Colin asked for.
def build_fixtures_summary(scrape_path, rpi_path, master_path, team_schedules, match_center,
                            team_name="UNC Wilmington", season=None, current_season="Fall 2026",
                            national_stats=None):
    """
    Returns {"team", "schedule": [...], "trends": {"form", "goals", "rpi", "flow"},
    "seasonStats": {...} or None}.

    - schedule: one row per MATCH_CENTER match (already date-ordered),
      annotated with the opponent's current overall record when they're one
      of the 21 teams tracked in team_schedules (None for one-off
      exhibition/non-tracked opponents like The Citadel or LSU), plus
      cumRecord (see seasonStats below).
    - seasonStats (added 2026-09-14, Colin's ask: "the basic stats of the
      season below the trends. Use the template from the individual team
      page from the National RPI pages"): the exact same per-team profile
      `build_national_rpi_data()` computes for that team's own National RPI
      detail page (Nat'l Rank, RPI Total, Adjusted RPI, Record, Goals F-A,
      Goal Diff, Home, Away, Conference, Non-Conference, Form, vs Top 100)
      -- pass that team's entry from `build_national_rpi_data(...)["teams"]`
      in as `national_stats` so this doesn't have to recompute the
      (nationwide, ~1s) calculation once per season in the fixtures loop.
      Reusing the exact same source as the National RPI page keeps the two
      pages' numbers for the same team always in agreement. Only meaningful
      for the current season (same reasoning as opponentRecord/trends.rpi
      above -- `national_stats` reflects the live scrape's current
      snapshot, not a historical point in time), so this is None whenever
      `is_current` is False or no `national_stats` was passed in. Each
      schedule row's "cumRecord" (the running overall record through that
      match, matching the National page's "Season Record" column) is
      looked up from `national_stats["schedule"]` by date -- the two
      schedules come from different source files (this one from
      PlayerMatchReport.xlsx, national_stats's from the general scraper
      file) so matches are joined by date rather than by name; a date with
      no match on the national side (e.g. an early exhibition the general
      scraper doesn't track) just gets no cumRecord rather than a wrong one.
    - trends.form: last 5 played matches (oldest to newest), each
      {date, result, opponent, logo, loc} -- logo is resolved the same way
      as everywhere else on the site (team_schedules' own per-team logo for
      one of the 21 tracked teams, falling back to the
      Master_Teams_Table_Final/RPI.xlsx-driven lookup_logo() for
      one-off/historical opponents), and is None if no logo can be found
      for that opponent at all. loc is "H"/"A" (or None), straight from
      PlayerMatchReport.xlsx's Venue column.
    - trends.upcoming: just the next not-yet-played scheduled match (added
      2026-09-14, Colin's ask: "add a line after the most recent match and
      the two logos of the next 2 matches"; narrowed the same day to just
      the one next match), {date, opponent, logo, loc} -- no result yet, so
      no W/D/L badge.
    - trends.goals: {date, gf, ga} per played match, season to date.
    - trends.flow: {date, value} -- UNCW's final Match Flow value per
      played+tagged match. Not "Impact" (Colin's original ask) -- the full
      Impact-weight table is still an open item per player-report-cards-plan.md,
      so Match Flow (already verified against the Coaches Booklet) stands in
      for it until that's resolved.
    - trends.rpi: {date, rank} -- UNCW's live Adjusted RPI rank AS OF each
      played match's date, recomputed by re-running compute_live_rpi() on
      the scrape filtered to that date (reusing the exact same, already-
      verified formula as the "now" snapshot everywhere else on the site --
      not a new calculation, just run at several points in time instead of
      one). Known small imprecision: DREXEL_SCHEDULE/CONFIRMED_RESULTS are
      folded in via augment_scrape_with_manual_results() without their own
      date-cutoff awareness, so a manual Drexel entry could in principle be
      counted slightly earlier than it should for an early-season cutoff --
      negligible for UNCW's own rank, several degrees removed through the
      RPI network, but noted here rather than silently assumed away.

    `season`/`current_season` (added 2026-09-13 for the multi-season Fixtures
    rollout -- see site-restructure-plan.md): `team_schedules` and the live
    RPI scrape are both single-snapshot, current-season-only data (only one
    scrape file exists, for the current live season). So opponentRecord and
    the trends.rpi series are only meaningful for `season == current_season`
    -- for any other (historical) season they'd otherwise silently attach
    the CURRENT season's opponent record/live-RPI-rank to a past match,
    which would be wrong, not just incomplete. Both are left None/empty for
    non-current seasons rather than computed from stale-context data.
    """
    is_current = season is None or season == current_season

    scrape = pd.read_excel(scrape_path, sheet_name=0)
    scrape["match_date"] = pd.to_datetime(scrape["match_date"]).dt.date
    rpi_df = pd.read_excel(rpi_path, sheet_name=0)
    master_df = pd.read_excel(master_path, sheet_name=0)
    _, lookup_logo = build_rpi_logo_lookups(rpi_df, master_df)

    def resolve_opp_logo(raw_name, disp_name):
        # Fast path: one of the 21 tracked teams already has its logo
        # resolved (Drexel's no-scrapename special case included) sitting in
        # team_schedules -- reuse it rather than re-deriving. Not gated to
        # is_current: a team's logo isn't a time-sensitive stat the way
        # ownRecord/live-RPI-rank are, so this is safe for historical
        # seasons too.
        ts = team_schedules.get(disp_name)
        if ts and ts.get("logo"):
            return ts["logo"]
        # Fall back to the general lookup for one-off/historical opponents
        # (Clemson, LSU, The Citadel, etc.) that aren't among the 21 tracked
        # teams -- try the raw PlayerMatchReport spelling first, then the
        # resolved display name, same two spellings lookup_logo() already
        # knows how to handle via LOGO_OVERRIDES/RPI_NAME_ALIASES.
        return lookup_logo(raw_name) or lookup_logo(disp_name)

    matches = match_center.get("matches", [])

    # Season Record ("Season Stats" originally, renamed 2026-09-14 -- same
    # data, just a clearer label) + cumulative record -- only meaningful
    # for the current season, same reasoning as opponentRecord/trends.rpi
    # (national_stats reflects the live scrape's current snapshot). See the
    # docstring above.
    nat = national_stats if is_current else None
    cum_by_date = {e["date"]: e["cumRecord"] for e in nat["schedule"]} if nat else {}
    season_stats = _season_stats_from_national(nat)

    schedule = []
    for m in matches:
        # Same raw-name/display-name mismatch as build_home_summary()'s
        # next-fixture lookup above -- resolve through SCRAPENAME_TO_DISP
        # before hitting team_schedules, instead of a literal-string lookup
        # against m["opponent"] (PlayerMatchReport.xlsx's raw "Opponent"
        # column). Real bug found 2026-09-13: Colin noticed Western
        # Carolina's opponent record was blank on the Fixtures page --
        # PlayerMatchReport.xlsx always spells it out in full ("Western
        # Carolina") while team_schedules is keyed by the abbreviated
        # display name ("W. Carolina", per TEAMS), so the un-resolved
        # lookup silently missed. See data-quality-fixes.md.
        opp_disp = SCRAPENAME_TO_DISP.get(m.get("opponent"), m.get("opponent"))
        opp_ts = team_schedules.get(opp_disp) if is_current else None
        schedule.append({
            "date": m.get("date"), "type": m.get("type"), "opponent": m.get("opponent"),
            "opponentColor": m.get("opponentColor") or team_color_for(m.get("opponent")),
            # Added 2026-09-14, Colin's ask: "add opponent logo without
            # saying that's the column, so it shows to the side of the
            # name" -- resolve_opp_logo() is the exact same helper the
            # Form-strip logos already use (team_schedules fast path, then
            # the general lookup_logo() fallback for one-off opponents).
            "opponentLogo": resolve_opp_logo(m.get("opponent"), opp_disp),
            "venue": m.get("venue"), "city": m.get("city"),
            "ownScore": m.get("teamGoal"), "oppScore": m.get("opponentGoal"),
            "fullTimeScore": m.get("fullTimeScore"), "result": m.get("result"),
            "opponentRpiRank": m.get("rpi"),
            "opponentRecord": opp_ts.get("ownRecord") if opp_ts else None,
            "cumRecord": cum_by_date.get(m.get("date")),
            "played": m.get("played"), "hasStats": bool(m.get("stats")),
        })

    played = sorted([m for m in matches if m.get("played")], key=lambda m: m["date"])
    upcoming_matches = sorted([m for m in matches if not m.get("played")], key=lambda m: m["date"])

    def loc_for(m):
        # PlayerMatchReport.xlsx's "Venue" column is literally "Home"/"Away"
        # (not a stadium name -- see the Schedule table's own "venue" field,
        # same source), so this is a plain lookup, not a new derivation.
        v = m.get("venue")
        return "H" if v == "Home" else ("A" if v == "Away" else None)

    form = []
    for m in played[-5:]:
        opp_disp = SCRAPENAME_TO_DISP.get(m.get("opponent"), m.get("opponent"))
        form.append({
            "date": m.get("date"), "result": m.get("result"), "opponent": opp_disp,
            "logo": resolve_opp_logo(m.get("opponent"), opp_disp), "loc": loc_for(m),
        })

    # Just the single next scheduled match (Colin's ask, 2026-09-14: "take
    # the second future opponent away and only have the next opponent and
    # their logo" -- was the next 2).
    upcoming = []
    for m in upcoming_matches[:1]:
        opp_disp = SCRAPENAME_TO_DISP.get(m.get("opponent"), m.get("opponent"))
        upcoming.append({
            "date": m.get("date"), "opponent": opp_disp,
            "logo": resolve_opp_logo(m.get("opponent"), opp_disp), "loc": loc_for(m),
        })

    goals_trend = [{"date": m["date"], "gf": m.get("teamGoal"), "ga": m.get("opponentGoal")}
                   for m in played]
    flow_trend = [{"date": m["date"], "value": round(m["matchFlow"]["us"][-1], 2)}
                  for m in played if m.get("matchFlow") and m["matchFlow"].get("us")]

    rpi_trend = []
    if is_current:
        rpi_key = normalize(RPI_NAME_ALIASES.get(team_name, team_name))
        for m in played:
            cutoff = pd.to_datetime(m["date"]).date()
            scrape_upto = scrape[scrape["match_date"] <= cutoff]
            try:
                live_rpi = compute_live_rpi(augment_scrape_with_manual_results(scrape_upto), rpi_df)
                entry = live_rpi.get(rpi_key)
                rank = entry["rank"] if entry else None
            except Exception:
                rank = None
            rpi_trend.append({"date": m["date"], "rank": rank})
    else:
        # Historical season: no scrape snapshot exists for that point in
        # time, so UNCW's own live-RPI-rank trend can't be honestly
        # recomputed -- leave it empty rather than plot the current season's
        # numbers against a different season's dates.
        rpi_trend = [{"date": m["date"], "rank": None} for m in played]

    return {
        "team": team_name,
        "season": season or current_season,
        "isCurrentSeason": is_current,
        "schedule": schedule,
        "trends": {"form": form, "goals": goals_trend, "rpi": rpi_trend, "flow": flow_trend,
                   "upcoming": upcoming},
        "seasonStats": season_stats,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scrape", default="womens_di_soccer_2026.xlsx")
    ap.add_argument("--rpi", default="RPI.xlsx")
    ap.add_argument("--master", default="Master_Teams_Table_Final.xlsx")
    ap.add_argument("--out", default="team_schedules.json")
    args = ap.parse_args()

    output = build_team_schedules(args.scrape, args.rpi, args.master)

    with open(args.out, "w") as f:
        json.dump(output, f)

    print(f"\nWrote {args.out}")
    for disp, obj in output.items():
        print(f"  {disp:<18} {len(obj['games']):>2} games   record={obj['ownRecord']:<7} RPI={obj['ownRpi']}")


if __name__ == "__main__":
    main()
