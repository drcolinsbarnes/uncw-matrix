// Shared sidebar nav for the UNCW Women's Soccer site. One source of truth
// for the nav item list -- add/rename/reorder a page here and every page
// picks it up, instead of editing six copies of the same markup.
//
// Each page sets <body data-page="..."> to one of NAV_ITEMS' `key` values
// so the matching link gets the "active" highlight. A page not yet built
// (per the site-restructure rollout) still gets a real nav entry pointing
// at its "coming soon" placeholder, so the nav always looks complete even
// mid-migration.
//
// Two display modes -- "full" (icons + labels) and "icons" (icons only,
// narrower sidebar) -- toggled by the button in the sidebar header. The
// choice is saved to localStorage so it carries over as the visitor moves
// between pages on this multi-file site, not just within one page.
(function () {
  // Single-color (white, via stroke="currentColor") line icons -- replaces
  // the earlier full-color emoji glyphs, which rendered in whatever hue
  // each OS's emoji font picked and didn't read as part of the navy
  // sidebar's own palette. currentColor means each icon automatically
  // matches the nav-item text color already used for hover/active states
  // (see sidebar.css .nav-item / .nav-item:hover / .nav-item.active),
  // with no separate icon-color rule needed.
  const ICONS = {
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>',
    squad: '<circle cx="8.5" cy="8" r="3"/><circle cx="16.5" cy="9" r="2.5"/><path d="M2.5 20c0-3.6 2.7-6 6-6s6 2.4 6 6"/><path d="M14.5 14.5c2.6.3 4.5 2.4 4.5 5.5"/>',
    stats: '<path d="M4 20V10"/><path d="M11 20V4"/><path d="M18 20v-7"/><path d="M2.5 20.5h19"/>',
    matrix: '<rect x="3.5" y="3.5" width="17" height="17" rx="1.5"/><path d="M3.5 9.2h17"/><path d="M3.5 14.8h17"/><path d="M9.2 3.5v17"/><path d="M14.8 3.5v17"/>',
    fixtures: '<rect x="3.5" y="5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17"/><path d="M8 3v3.5"/><path d="M16 3v3.5"/>',
    caa: '<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4.5A1.5 1.5 0 0 0 3 7.5C3 9.4 4.4 11 7 11"/><path d="M17 6h2.5A1.5 1.5 0 0 1 21 7.5c0 1.9-1.4 3.5-4 3.5"/><path d="M12 14v3.5"/><path d="M8.5 21h7"/><path d="M9.5 17.5h5l1 3.5h-7l1-3.5Z"/>',
    rpi: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><path d="M12 3.5c2.6 2.3 4 5.3 4 8.5s-1.4 6.2-4 8.5c-2.6-2.3-4-5.3-4-8.5s1.4-6.2 4-8.5Z"/>',
    recruiting: '<path d="M12 3.5l2.5 5.2 5.7.8-4.1 4 1 5.6L12 16.4l-5.1 2.7 1-5.6-4.1-4 5.7-.8L12 3.5Z"/>',
    transfer: '<path d="M4 8h14"/><path d="M14.5 4.5 18 8l-3.5 3.5"/><path d="M20 16H6"/><path d="M9.5 12.5 6 16l3.5 3.5"/>',
    elo: '<path d="M3.5 20.5h17"/><path d="M4.5 16l4.5-5 4 3 6.5-8"/><path d="M15 6h4.5v4.5"/>',
    bracketology: '<path d="M3.5 5h5v5h-5"/><path d="M3.5 14h5v5h-5"/><path d="M8.5 7.5h4v9h-4"/><path d="M12.5 12h3"/><path d="M15.5 9.5h5v5h-5Z"/>',
    players: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 20c0-3.4 2.5-5.8 5.5-5.8s5.5 2.4 5.5 5.8"/><circle cx="17" cy="8.5" r="2.4"/><path d="M15.5 14.5c2.3.3 4 2.3 4 5.5"/>',
  };
  function iconSvg(key) {
    return `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICONS[key] || ""}</svg>`;
  }

  // Recruiting and Transfer Portal (2026-09-24) are Matrix pages that frame
  // the live Supabase-backed apps from the uncw-recruiting-app Cloudflare
  // project -- see recruiting.html / transfer.html.
  const NAV_ITEMS = [
    { key: "home", label: "Home", href: "home.html" },
    { key: "squad", label: "Squad", href: "squad.html" },
    { key: "stats", label: "Stats", href: "stats.html" },
    { key: "fixtures", label: "Fixtures", href: "fixtures.html" },
    { key: "matrix", label: "Matrix", href: "matrix.html" },
    { key: "caa", label: "CAA", href: "caa.html" },
    { key: "recruiting", label: "Recruiting", href: "recruiting.html" },
    { key: "transfer", label: "Transfer Portal", href: "transfer.html" },
    { key: "rpi", label: "Rankings", href: "national_rpi.html" },
    { key: "elo", label: "Elo Predictions", href: "elo.html" },
    { key: "bracketology", label: "Bracketology", href: "bracketology.html" },
    // "Players" nav item removed 2026-09-28 per Colin: the directory-style
    // search wasn't useful for him, and it highlighted "Elo Predictions" as
    // active instead of itself (no page sets data-page="players", since
    // it's a route inside elo.html, not its own file) -- confusing on top
    // of not being needed. Individual players are still reachable via each
    // team's roster/scouting tables (per-team search, which Colin said is
    // enough for now). The #/players route and renderPlayersDirectory() in
    // elo_template.html are UNTOUCHED -- a roster row's player link and a
    // "back to all players" link still resolve -- only the standing nav
    // promotion of it is gone. Revisit if/when player rankings/percentiles
    // (a real reason to browse players directly) get built -- see the
    // punch-list item on ranking players nationally/by conference.
  ];

  // Coaching Hub version -- stamped by bump_hub_version.py (do not hand-edit).
  // HUB_VERSION_START
  const HUB_VERSION = "6.3";
  const HUB_UPDATED = "26 Oct 2026";
  // HUB_VERSION_END

  const MODE_KEY = "uncwSidebarMode"; // stored value: "full" | "icons"

  function getSavedMode() {
    try {
      return window.localStorage.getItem(MODE_KEY) === "icons" ? "icons" : "full";
    } catch (e) {
      return "full"; // localStorage unavailable (private mode, etc.) -- just default to full
    }
  }

  function saveMode(mode) {
    try {
      window.localStorage.setItem(MODE_KEY, mode);
    } catch (e) {
      // Ignore -- worst case the choice doesn't persist across pages.
    }
  }

  function render() {
    const root = document.getElementById("app-sidebar");
    if (!root) return;
    const current = document.body.dataset.page || "";
    if (getSavedMode() === "icons") root.classList.add("icons-only");

    const header = document.createElement("div");
    header.className = "sidebar-header";

    const brand = document.createElement("div");
    brand.className = "brand";
    brand.innerHTML =
      '<img src="uncw-logo.png" alt="UNCW Seahawks" ' +
      'onerror="this.style.visibility=\'hidden\'">' +
      '<div class="name">UNCW Women’s Soccer<small>Coaching Hub</small></div>';
    header.appendChild(brand);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sidebar-toggle";
    function syncToggle() {
      const collapsed = root.classList.contains("icons-only");
      toggle.textContent = collapsed ? "▶" : "◀";
      toggle.title = collapsed ? "Show full sidebar" : "Show icons only";
      toggle.setAttribute("aria-label", toggle.title);
    }
    syncToggle();
    toggle.addEventListener("click", () => {
      const collapsed = root.classList.toggle("icons-only");
      saveMode(collapsed ? "icons" : "full");
      syncToggle();
    });
    header.appendChild(toggle);
    root.appendChild(header);

    const nav = document.createElement("nav");
    nav.className = "nav-items";
    NAV_ITEMS.forEach(item => {
      const a = document.createElement("a");
      a.className = "nav-item" + (item.key === current ? " active" : "");
      a.href = item.href;
      a.title = item.label;
      a.innerHTML = `<span class="emoji">${iconSvg(item.key)}</span><span class="label">${item.label}</span>`;
      nav.appendChild(a);
    });

    root.appendChild(nav);

    const footer = document.createElement("div");
    footer.className = "nav-footer";
    footer.innerHTML =
      '<a class="legacy-link" href="index.html" title="Classic dashboard (legacy)">' +
      '<span class="icon">←</span><span class="label">Classic dashboard (legacy)</span></a>' +
      '<div class="build-note" title="Coaching Hub version">Coaching Hub v' + HUB_VERSION +
      (HUB_UPDATED ? ' &middot; ' + HUB_UPDATED : '') + '</div>';
    root.appendChild(footer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();

/* ======================================================================
   Site-wide norms (added 2026-10-12, Colin): every page gets
   1. a Back button at the top of the page (returns to wherever the visitor
      started before going down a team/player/game rabbit hole),
   2. fixed (sticky) table headers and a frozen Team / Player / Opponent
      column on every data table, with no per-page code,
   3. links from every Division I team name to its Elo/RPI/box-score team page.
   Tables and names that a page draws later (innerHTML re-renders) are picked
   up by a MutationObserver. Opt a table out with class "no-sticky"; opt an
   element out of auto-linking with data-nolink.
   ====================================================================== */
// TEAM_INDEX_START
const TEAM_INDEX = ["Abilene Christian","Air Force","Akron","Alabama","Alabama A&M","Alabama State","Albany","Alcorn State","American","Appalachian State","Arizona","Arizona State","Arkansas","Arkansas State","Army","Auburn","Austin Peay","BYU","Ball State","Baylor","Bellarmine","Belmont","Binghamton","Boise State","Boston College","Boston University","Bowling Green","Brown","Bryant","Bucknell","Buffalo","Butler","CSU Bakersfield","CSUN","Cal Poly","Cal State Fullerton","California","California Baptist","Campbell","Canisius","Central Arkansas","Central Connecticut","Central Michigan","Charleston Southern","Charlotte","Chicago State","Cincinnati","Clemson","Cleveland State","Coastal Carolina","Colgate","College of Charleston","Colorado","Colorado College","Colorado State","Columbia","Connecticut","Cornell","Creighton","Dartmouth","Davidson","Dayton","DePaul","Delaware","Delaware State","Denver","Detroit Mercy","Drake","Drexel","Duke","Duquesne","East Carolina","East Tennessee State","East Texas A&M","Eastern Illinois","Eastern Kentucky","Eastern Michigan","Eastern Washington","Elon","Evansville","FGCU","Fairfield","Fairleigh Dickinson","Florida","Florida Atlantic","Florida International","Florida State","Fordham","Fresno State","Furman","Gardner-Webb","George Mason","George Washington","Georgetown","Georgia","Georgia Southern","Georgia State","Gonzaga","Grambling State","Grand Canyon","Hampton University","Harvard","Hawaii","High Point","Hofstra","Holy Cross","Houston","Houston Christian","Howard","IU Indianapolis","Idaho","Idaho State","Illinois","Illinois State","Incarnate Word","Indiana","Indiana State","Iona University","Iowa","Iowa State","Jackson State","Jacksonville","Jacksonville State","James Madison","Kansas","Kansas City","Kansas State","Kennesaw State","Kent State","Kentucky","LIU","LSU","La Salle","Lafayette","Lamar","Le Moyne","Lehigh","Liberty","Lindenwood","Lipscomb","Little Rock","Long Beach State","Longwood","Louisiana","Louisiana Tech","Louisiana-Monroe","Louisville","Loyola (MD)","Loyola Chicago","Loyola Marymount","Maine","Manhattan","Marist","Marquette","Marshall","Maryland","Massachusetts","Massachusetts-Lowell","Memphis","Mercer","Mercyhurst","Merrimack","Miami (FL)","Miami (OH)","Michigan","Michigan State","Middle Tennessee","Minnesota","Mississippi","Mississippi State","Missouri","Missouri State","Monmouth","Montana","Morehead State","Mount St. Mary's","Murray State","NC State","NJIT","Navy","Nebraska","Nevada","New Hampshire","New Haven","New Mexico","New Mexico State","Niagara","Nicholls","North Alabama","North Carolina","North Dakota","North Dakota State","North Florida","North Texas","Northeastern","Northern Arizona","Northern Colorado","Northern Illinois","Northern Iowa","Northern Kentucky","Northwestern","Northwestern State","Notre Dame","Oakland","Ohio State","Ohio University","Oklahoma","Oklahoma State","Old Dominion","Omaha","Oral Roberts","Oregon","Oregon State","Pacific","Penn","Penn State","Pepperdine","Pittsburgh","Portland","Portland State","Prairie View A&M","Presbyterian","Princeton","Providence","Purdue","Purdue Fort Wayne","Queens (N.C.)","Quinnipiac","Radford","Rhode Island","Rice","Richmond","Rider","Robert Morris","Rutgers","SIUE","SMU","Sacramento State","Sacred Heart","Saint Joseph's","Saint Louis","Saint Peter's","Sam Houston State","Samford","San Diego","San Diego State","San Francisco","San Jose State","Santa Clara","Seattle","Seton Hall","Siena College","South Alabama","South Carolina","South Carolina State","South Dakota","South Dakota State","South Florida","Southeast Missouri State","Southeastern Louisiana","Southern Illinois","Southern Indiana","Southern Mississippi","Southern University","Southern Utah","St. Bonaventure","St. John's","St. Mary's (CA)","St. Thomas (Minn.)","Stanford","Stephen F. Austin","Stetson","Stonehill","Stony Brook","Syracuse","TCU","Tarleton State","Temple","Tennessee","Tennessee Tech","Texas","Texas A&M","Texas A&M-Corpus Christi","Texas Southern","Texas State","Texas Tech","The Citadel","Toledo","Towson","Troy","Tulsa","UAB","UC Davis","UC Irvine","UC Riverside","UC San Diego","UC Santa Barbara","UCF","UCLA","UIC","UMBC","UNC Asheville","UNC Greensboro","UNC Wilmington","UNLV","USC","USC Upstate","UT Chattanooga","UT Martin","UTEP","UTSA","Utah","Utah State","Utah Tech","Utah Valley","VCU","VMI","Valparaiso","Vanderbilt","Vermont","Villanova","Virginia","Virginia Tech","Wagner","Wake Forest","Washington","Washington State","Weber State","West Georgia","West Virginia","Western Carolina","Western Illinois","Western Kentucky","Western Michigan","William & Mary","Winthrop","Wisconsin","Wisconsin-Green Bay","Wisconsin-Milwaukee","Wofford","Wright State","Wyoming","Xavier","Yale","Youngstown State"];
const TEAM_LOGOS = {"Abilene Christian":"https://a.espncdn.com/i/teamlogos/ncaa/500/2000.png","Air Force":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Air_Force_Falcons_logo.svg/1280px-Air_Force_Falcons_logo.svg.png","Akron":"https://a.espncdn.com/i/teamlogos/ncaa/500/2006.png","Alabama":"https://a.espncdn.com/i/teamlogos/ncaa/500/333.png","Alabama A&M":"https://a.espncdn.com/i/teamlogos/ncaa/500/2010.png","Alabama State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2011.png","Albany":"https://upload.wikimedia.org/wikipedia/en/thumb/c/c7/UAlbany_Great_Danes_logo.svg/120px-UAlbany_Great_Danes_logo.svg.png","Alcorn State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2016.png","American":"https://a.espncdn.com/i/teamlogos/ncaa/500/44.png","Appalachian State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2026.png","Arizona":"https://a.espncdn.com/i/teamlogos/ncaa/500/12.png","Arizona State":"https://a.espncdn.com/i/teamlogos/ncaa/500/9.png","Arkansas":"https://upload.wikimedia.org/wikipedia/en/3/30/Arkansas_razorbacks_logo.png","Arkansas State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2032.png","Army":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Army_West_Point_logo.svg/1920px-Army_West_Point_logo.svg.png","Auburn":"https://a.espncdn.com/i/teamlogos/ncaa/500/2.png","Austin Peay":"https://a.espncdn.com/i/teamlogos/ncaa/500/2046.png","BYU":"https://a.espncdn.com/i/teamlogos/ncaa/500/252.png","Ball State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2050.png","Baylor":"https://a.espncdn.com/i/teamlogos/ncaa/500/239.png","Bellarmine":"logos/bellarmine.png","Belmont":"logos/belmont.png","Binghamton":"https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/Binghamton_Bearcats_logo.svg/1920px-Binghamton_Bearcats_logo.svg.png","Boise State":"https://a.espncdn.com/i/teamlogos/ncaa/500/68.png","Boston College":"https://a.espncdn.com/i/teamlogos/ncaa/500/103.png","Boston University":"https://a.espncdn.com/i/teamlogos/ncaa/500/103.png","Bowling Green":"https://a.espncdn.com/i/teamlogos/ncaa/500/189.png","Brown":"https://a.espncdn.com/i/teamlogos/ncaa/500/225.png","Bryant":"https://a.espncdn.com/i/teamlogos/ncaa/500/2803.png","Bucknell":"https://a.espncdn.com/i/teamlogos/ncaa/500/2083.png","Buffalo":"https://upload.wikimedia.org/wikipedia/en/5/5e/Buffalo_Bulls_Athletic_Logo.svg","Butler":"https://a.espncdn.com/i/teamlogos/ncaa/500/2086.png","CSU Bakersfield":"https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Cal_State_Bakersfield_Roadrunners_logo.svg/1280px-Cal_State_Bakersfield_Roadrunners_logo.svg.png","CSUN":"https://upload.wikimedia.org/wikipedia/en/thumb/5/51/CSUN_Matadors_logo.svg/960px-CSUN_Matadors_logo.svg.png","Cal Poly":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Cal_Poly_Mustangs_logo.svg/960px-Cal_Poly_Mustangs_logo.svg.png","Cal State Fullerton":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Cal_State_Fullerton_Titans_logo.svg/1920px-Cal_State_Fullerton_Titans_logo.svg.png","California":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/California_Golden_Bears_logo.svg/1280px-California_Golden_Bears_logo.svg.png","California Baptist":"https://upload.wikimedia.org/wikipedia/en/3/3f/Cbu_lancers_logo.png","Campbell":"https://a.espncdn.com/i/teamlogos/ncaa/500/2097.png","Canisius":"https://a.espncdn.com/i/teamlogos/ncaa/500/2099.png","Central Arkansas":"https://a.espncdn.com/i/teamlogos/ncaa/500/2110.png","Central Connecticut":"https://a.espncdn.com/i/teamlogos/ncaa/500/2115.png","Central Michigan":"https://a.espncdn.com/i/teamlogos/ncaa/500/2117.png","Charleston Southern":"https://a.espncdn.com/i/teamlogos/ncaa/500/2127.png","Charlotte":"https://upload.wikimedia.org/wikipedia/commons/3/33/Charlotte_49ers_logo.svg","Chicago State":"https://a.espncdn.com/i/teamlogos/ncaa/500/80.png","Cincinnati":"https://a.espncdn.com/i/teamlogos/ncaa/500/2132.png","Clemson":"https://a.espncdn.com/i/teamlogos/ncaa/500/228.png","Cleveland State":"https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Cleveland_State_Vikings_logo.svg/1280px-Cleveland_State_Vikings_logo.svg.png","Coastal Carolina":"https://a.espncdn.com/i/teamlogos/ncaa/500/324.png","Colgate":"https://a.espncdn.com/i/teamlogos/ncaa/500/2142.png","College of Charleston":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/College_of_Charleston_Cougars_logo.svg/120px-College_of_Charleston_Cougars_logo.svg.png","Colorado":"https://upload.wikimedia.org/wikipedia/en/thumb/d/d3/Colorado_Buffaloes_logo.svg/1280px-Colorado_Buffaloes_logo.svg.png","Colorado College":"logos/colorado-college.png","Colorado State":"https://a.espncdn.com/i/teamlogos/ncaa/500/36.png","Columbia":"https://upload.wikimedia.org/wikipedia/en/5/5f/Columbia_Lions_logo.svg","Connecticut":"https://a.espncdn.com/i/teamlogos/ncaa/500/41.png","Cornell":"https://a.espncdn.com/i/teamlogos/ncaa/500/172.png","Creighton":"https://a.espncdn.com/i/teamlogos/ncaa/500/156.png","Dartmouth":"https://a.espncdn.com/i/teamlogos/ncaa/500/159.png","Davidson":"https://a.espncdn.com/i/teamlogos/ncaa/500/2166.png","Dayton":"https://a.espncdn.com/i/teamlogos/ncaa/500/2168.png","DePaul":"https://a.espncdn.com/i/teamlogos/ncaa/500/305.png","Delaware":"https://a.espncdn.com/i/teamlogos/ncaa/500/48.png","Delaware State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2169.png","Denver":"https://a.espncdn.com/i/teamlogos/ncaa/500/2172.png","Detroit Mercy":"https://a.espncdn.com/i/teamlogos/ncaa/500/2174.png","Drake":"https://a.espncdn.com/i/teamlogos/ncaa/500/2181.png","Drexel":"https://a.espncdn.com/i/teamlogos/ncaa/500/2182.png","Duke":"https://a.espncdn.com/i/teamlogos/ncaa/500/150.png","Duquesne":"https://a.espncdn.com/i/teamlogos/ncaa/500/2184.png","East Carolina":"https://a.espncdn.com/i/teamlogos/ncaa/500/151.png","East Tennessee State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2193.png","East Texas A&M":"https://a.espncdn.com/i/teamlogos/ncaa/500/2837.png","Eastern Illinois":"https://a.espncdn.com/i/teamlogos/ncaa/500/2197.png","Eastern Kentucky":"https://a.espncdn.com/i/teamlogos/ncaa/500/2198.png","Eastern Michigan":"https://a.espncdn.com/i/teamlogos/ncaa/500/2199.png","Eastern Washington":"https://a.espncdn.com/i/teamlogos/ncaa/500/331.png","Elon":"https://a.espncdn.com/i/teamlogos/ncaa/500/2210.png","Evansville":"https://a.espncdn.com/i/teamlogos/ncaa/500/339.png","FGCU":"https://upload.wikimedia.org/wikipedia/en/thumb/9/95/Florida_Gulf_Coast_Eagles_logo.svg/250px-Florida_Gulf_Coast_Eagles_logo.svg.png","Fairfield":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Fairfield_Stags_logo.svg/250px-Fairfield_Stags_logo.svg.png","Fairleigh Dickinson":"https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/Fdu_knights_main_logo.png/250px-Fdu_knights_main_logo.png","Florida":"https://a.espncdn.com/i/teamlogos/ncaa/500/57.png","Florida Atlantic":"https://a.espncdn.com/i/teamlogos/ncaa/500/2226.png","Florida International":"https://a.espncdn.com/i/teamlogos/ncaa/500/2229.png","Florida State":"https://a.espncdn.com/i/teamlogos/ncaa/500/52.png","Fordham":"https://a.espncdn.com/i/teamlogos/ncaa/500/2230.png","Fresno State":"https://upload.wikimedia.org/wikipedia/en/thumb/7/7c/Fresno_State_Bulldogs_logo.svg/1280px-Fresno_State_Bulldogs_logo.svg.png","Furman":"https://a.espncdn.com/i/teamlogos/ncaa/500/231.png","Gardner-Webb":"https://a.espncdn.com/i/teamlogos/ncaa/500/2241.png","George Mason":"https://a.espncdn.com/i/teamlogos/ncaa/500/2244.png","George Washington":"https://a.espncdn.com/i/teamlogos/ncaa/500/45.png","Georgetown":"https://a.espncdn.com/i/teamlogos/ncaa/500/46.png","Georgia":"https://a.espncdn.com/i/teamlogos/ncaa/500/61.png","Georgia Southern":"https://a.espncdn.com/i/teamlogos/ncaa/500/290.png","Georgia State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2247.png","Gonzaga":"https://a.espncdn.com/i/teamlogos/ncaa/500/2250.png","Grambling State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2755.png","Grand Canyon":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Grand_Canyon_University_2023_Logo_Update.svg/250px-Grand_Canyon_University_2023_Logo_Update.svg.png","Hampton University":"https://a.espncdn.com/i/teamlogos/ncaa/500/2261.png","Harvard":"https://a.espncdn.com/i/teamlogos/ncaa/500/108.png","Hawaii":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Hawaii_Warriors_logo.svg/1280px-Hawaii_Warriors_logo.svg.png","High Point":"https://upload.wikimedia.org/wikipedia/commons/2/2c/High_Point_Panthers_logo.svg","Hofstra":"https://a.espncdn.com/i/teamlogos/ncaa/500/2275.png","Holy Cross":"https://upload.wikimedia.org/wikipedia/commons/f/f5/Holy_Cross_Crusaders_logo.svg","Houston":"https://a.espncdn.com/i/teamlogos/ncaa/500/248.png","Houston Christian":"https://upload.wikimedia.org/wikipedia/en/thumb/b/b8/Houston_Baptist_Huskies_logo.svg/250px-Houston_Baptist_Huskies_logo.svg.png","Howard":"https://a.espncdn.com/i/teamlogos/ncaa/500/47.png","IU Indianapolis":"https://upload.wikimedia.org/wikipedia/en/d/d9/UIndyGreyhounds.png","Idaho":"logos/idaho.png","Idaho State":"https://a.espncdn.com/i/teamlogos/ncaa/500/304.png","Illinois":"https://upload.wikimedia.org/wikipedia/commons/9/91/Illinois_Fighting_Illini_logo.svg","Illinois State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2287.png","Incarnate Word":"https://a.espncdn.com/i/teamlogos/ncaa/500/2916.png","Indiana":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Indiana_Hoosiers_logo.svg/120px-Indiana_Hoosiers_logo.svg.png","Indiana State":"https://a.espncdn.com/i/teamlogos/ncaa/500/282.png","Iona University":"https://upload.wikimedia.org/wikipedia/en/thumb/1/19/Iona_Gaels_logo.svg/250px-Iona_Gaels_logo.svg.png","Iowa":"https://a.espncdn.com/i/teamlogos/ncaa/500/2294.png","Iowa State":"https://a.espncdn.com/i/teamlogos/ncaa/500/66.png","Jackson State":"https://upload.wikimedia.org/wikipedia/en/thumb/2/20/Jacksonville_State_Gamecocks_logo.svg/250px-Jacksonville_State_Gamecocks_logo.svg.png","Jacksonville":"https://a.espncdn.com/i/teamlogos/ncaa/500/294.png","Jacksonville State":"https://a.espncdn.com/i/teamlogos/ncaa/500/55.png","James Madison":"https://a.espncdn.com/i/teamlogos/ncaa/500/256.png","Kansas":"https://a.espncdn.com/i/teamlogos/ncaa/500/2305.png","Kansas City":"https://a.espncdn.com/i/teamlogos/ncaa/500/140.png","Kansas State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2306.png","Kennesaw State":"https://a.espncdn.com/i/teamlogos/ncaa/500/338.png","Kent State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2309.png","Kentucky":"https://a.espncdn.com/i/teamlogos/ncaa/500/96.png","LIU":"https://upload.wikimedia.org/wikipedia/en/thumb/f/fd/LIU_Sharks_logo.svg/1280px-LIU_Sharks_logo.svg.png","LSU":"https://a.espncdn.com/i/teamlogos/ncaa/500/99.png","La Salle":"https://a.espncdn.com/i/teamlogos/ncaa/500/2325.png","Lafayette":"https://a.espncdn.com/i/teamlogos/ncaa/500/322.png","Lamar":"https://a.espncdn.com/i/teamlogos/ncaa/500/2320.png","Le Moyne":"https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Le_Moyne_Dolphins_logo.svg/250px-Le_Moyne_Dolphins_logo.svg.png","Lehigh":"https://a.espncdn.com/i/teamlogos/ncaa/500/2329.png","Liberty":"https://a.espncdn.com/i/teamlogos/ncaa/500/2335.png","Lindenwood":"https://a.espncdn.com/i/teamlogos/ncaa/500/2815.png","Lipscomb":"https://upload.wikimedia.org/wikipedia/en/thumb/5/52/Lipscomb_Athletics_primary.svg/120px-Lipscomb_Athletics_primary.svg.png","Little Rock":"https://upload.wikimedia.org/wikipedia/en/thumb/d/d0/Little_Rock_Trojans_logo.svg/1280px-Little_Rock_Trojans_logo.svg.png","Long Beach State":"https://a.espncdn.com/i/teamlogos/ncaa/500/299.png","Longwood":"https://upload.wikimedia.org/wikipedia/en/thumb/5/5f/Longwood_Lancers_logo.svg/250px-Longwood_Lancers_logo.svg.png","Louisiana":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/La-lafayette_logo_from_NCAA.svg/1280px-La-lafayette_logo_from_NCAA.svg.png","Louisiana Tech":"https://a.espncdn.com/i/teamlogos/ncaa/500/2348.png","Louisiana-Monroe":"https://a.espncdn.com/i/teamlogos/ncaa/500/2433.png","Louisville":"https://a.espncdn.com/i/teamlogos/ncaa/500/97.png","Loyola (MD)":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Loyola_Greyhounds_logo.svg/250px-Loyola_Greyhounds_logo.svg.png","Loyola Chicago":"https://a.espncdn.com/i/teamlogos/ncaa/500/2350.png","Loyola Marymount":"https://a.espncdn.com/i/teamlogos/ncaa/500/2351.png","Maine":"https://a.espncdn.com/i/teamlogos/ncaa/500/311.png","Manhattan":"https://a.espncdn.com/i/teamlogos/ncaa/500/2363.png","Marist":"https://upload.wikimedia.org/wikipedia/en/5/5b/Marist_Red_Foxes_logo.svg","Marquette":"https://a.espncdn.com/i/teamlogos/ncaa/500/269.png","Marshall":"https://a.espncdn.com/i/teamlogos/ncaa/500/276.png","Maryland":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Maryland_Terrapins_logo.svg/1280px-Maryland_Terrapins_logo.svg.png","Massachusetts":"https://upload.wikimedia.org/wikipedia/commons/0/0a/UMass_primary_logo.png","Massachusetts-Lowell":"https://upload.wikimedia.org/wikipedia/en/thumb/4/43/UMass_Lowell_River_Hawks_logo.svg/1280px-UMass_Lowell_River_Hawks_logo.svg.png","Memphis":"https://a.espncdn.com/i/teamlogos/ncaa/500/235.png","Mercer":"https://a.espncdn.com/i/teamlogos/ncaa/500/2382.png","Mercyhurst":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Mercyhurst_logo_from_NCAA.svg/250px-Mercyhurst_logo_from_NCAA.svg.png","Merrimack":"https://a.espncdn.com/i/teamlogos/ncaa/500/2771.png","Miami (FL)":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Miami_Hurricanes_logo.svg/1280px-Miami_Hurricanes_logo.svg.png","Miami (OH)":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Miami_Redhawks_logo.svg/250px-Miami_Redhawks_logo.svg.png","Michigan":"https://a.espncdn.com/i/teamlogos/ncaa/500/130.png","Michigan State":"https://a.espncdn.com/i/teamlogos/ncaa/500/127.png","Middle Tennessee":"https://a.espncdn.com/i/teamlogos/ncaa/500/2393.png","Minnesota":"https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/University_of_Minnesota_Logo.svg/250px-University_of_Minnesota_Logo.svg.png","Mississippi":"https://a.espncdn.com/i/teamlogos/ncaa/500/145.png","Mississippi State":"https://a.espncdn.com/i/teamlogos/ncaa/500/344.png","Missouri":"https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/Missouri_Tigers_logo.svg/1280px-Missouri_Tigers_logo.svg.png","Missouri State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2623.png","Monmouth":"https://a.espncdn.com/i/teamlogos/ncaa/500/2405.png","Montana":"https://a.espncdn.com/i/teamlogos/ncaa/500/149.png","Morehead State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2413.png","Mount St. Mary's":"https://a.espncdn.com/i/teamlogos/ncaa/500/116.png","Murray State":"https://a.espncdn.com/i/teamlogos/ncaa/500/93.png","NC State":"https://a.espncdn.com/i/teamlogos/ncaa/500/152.png","NJIT":"https://upload.wikimedia.org/wikipedia/en/thumb/3/30/NJIT_Highlanders_logo.svg/250px-NJIT_Highlanders_logo.svg.png","Navy":"https://upload.wikimedia.org/wikipedia/commons/7/78/Navy_Athletics_logo.png","Nebraska":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Nebraska_Cornhuskers_logo.svg/1280px-Nebraska_Cornhuskers_logo.svg.png","Nevada":"https://upload.wikimedia.org/wikipedia/en/thumb/2/21/Nevada_Wolf_Pack_logo.svg/1280px-Nevada_Wolf_Pack_logo.svg.png","New Hampshire":"https://a.espncdn.com/i/teamlogos/ncaa/500/160.png","New Haven":"https://a.espncdn.com/i/teamlogos/ncaa/500/2441.png","New Mexico":"https://a.espncdn.com/i/teamlogos/ncaa/500/167.png","New Mexico State":"https://a.espncdn.com/i/teamlogos/ncaa/500/166.png","Niagara":"https://a.espncdn.com/i/teamlogos/ncaa/500/315.png","Nicholls":"https://a.espncdn.com/i/teamlogos/ncaa/500/2447.png","North Alabama":"https://a.espncdn.com/i/teamlogos/ncaa/500/2453.png","North Carolina":"https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/UNC_primary_mark_blue.svg/3840px-UNC_primary_mark_blue.svg.png","North Dakota":"https://a.espncdn.com/i/teamlogos/ncaa/500/155.png","North Dakota State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2449.png","North Florida":"https://www.ncaa.com/sites/default/files/images/logos/schools/bgd/north-florida.svg","North Texas":"https://a.espncdn.com/i/teamlogos/ncaa/500/249.png","Northeastern":"https://a.espncdn.com/i/teamlogos/ncaa/500/111.png","Northern Arizona":"https://a.espncdn.com/i/teamlogos/ncaa/500/2464.png","Northern Colorado":"https://a.espncdn.com/i/teamlogos/ncaa/500/2458.png","Northern Illinois":"https://a.espncdn.com/i/teamlogos/ncaa/500/2459.png","Northern Iowa":"https://a.espncdn.com/i/teamlogos/ncaa/500/2460.png","Northern Kentucky":"https://upload.wikimedia.org/wikipedia/en/thumb/4/45/Northern_Kentucky_Norse_logo.svg/250px-Northern_Kentucky_Norse_logo.svg.png","Northwestern":"https://a.espncdn.com/i/teamlogos/ncaa/500/77.png","Northwestern State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2466.png","Notre Dame":"https://a.espncdn.com/i/teamlogos/ncaa/500/87.png","Oakland":"https://upload.wikimedia.org/wikipedia/en/thumb/8/86/Oakland_Golden_Grizzlies_logo.svg/250px-Oakland_Golden_Grizzlies_logo.svg.png","Ohio State":"https://upload.wikimedia.org/wikipedia/commons/c/c1/Ohio_State_Buckeyes_logo.svg","Ohio University":"https://a.espncdn.com/i/teamlogos/ncaa/500/195.png","Oklahoma":"https://a.espncdn.com/i/teamlogos/ncaa/500/201.png","Oklahoma State":"https://a.espncdn.com/i/teamlogos/ncaa/500/197.png","Old Dominion":"https://a.espncdn.com/i/teamlogos/ncaa/500/295.png","Omaha":"https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Omaha_Mavericks_logo.svg/1280px-Omaha_Mavericks_logo.svg.png","Oral Roberts":"https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/Oral_Roberts_Golden_Eagles_logo.svg/250px-Oral_Roberts_Golden_Eagles_logo.svg.png","Oregon":"https://a.espncdn.com/i/teamlogos/ncaa/500/2483.png","Oregon State":"https://a.espncdn.com/i/teamlogos/ncaa/500/204.png","Pacific":"https://upload.wikimedia.org/wikipedia/en/5/5e/Pacific_Tigers_logo.svg","Penn":"https://a.espncdn.com/i/teamlogos/ncaa/500/219.png","Penn State":"https://a.espncdn.com/i/teamlogos/ncaa/500/213.png","Pepperdine":"https://a.espncdn.com/i/teamlogos/ncaa/500/2492.png","Pittsburgh":"https://a.espncdn.com/i/teamlogos/ncaa/500/221.png","Portland":"https://a.espncdn.com/i/teamlogos/ncaa/500/2501.png","Portland State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2502.png","Prairie View A&M":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Prairie_view_univ_athletics_textlogo.png/250px-Prairie_view_univ_athletics_textlogo.png","Presbyterian":"https://a.espncdn.com/i/teamlogos/ncaa/500/2506.png","Princeton":"https://a.espncdn.com/i/teamlogos/ncaa/500/163.png","Providence":"https://a.espncdn.com/i/teamlogos/ncaa/500/2507.png","Purdue":"https://a.espncdn.com/i/teamlogos/ncaa/500/2509.png","Purdue Fort Wayne":"logos/purdue-fort-wayne.png","Queens (N.C.)":"https://upload.wikimedia.org/wikipedia/en/8/8a/Queens_univ_athletics_logo_2023.png","Quinnipiac":"https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/Quinnipiac_Bobcats_logo.svg/1280px-Quinnipiac_Bobcats_logo.svg.png","Radford":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Radford_Highlanders_logo.svg/1280px-Radford_Highlanders_logo.svg.png","Rhode Island":"https://a.espncdn.com/i/teamlogos/ncaa/500/227.png","Rice":"https://a.espncdn.com/i/teamlogos/ncaa/500/242.png","Richmond":"https://a.espncdn.com/i/teamlogos/ncaa/500/257.png","Rider":"https://upload.wikimedia.org/wikipedia/en/thumb/6/62/Rider_Broncs.svg/1280px-Rider_Broncs.svg.png","Robert Morris":"https://a.espncdn.com/i/teamlogos/ncaa/500/2523.png","Rutgers":"https://upload.wikimedia.org/wikipedia/commons/b/b6/Rutgers_Scarlet_Knights_logo.svg","SIUE":"https://upload.wikimedia.org/wikipedia/en/6/6e/SIU_cougars_logo_2023.png","SMU":"https://upload.wikimedia.org/wikipedia/commons/3/33/SMU_Mustang_logo.svg","Sacramento State":"https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Sacramento_State_Hornets_logo.svg/960px-Sacramento_State_Hornets_logo.svg.png","Sacred Heart":"https://a.espncdn.com/i/teamlogos/ncaa/500/2529.png","Saint Joseph's":"https://upload.wikimedia.org/wikipedia/en/7/76/Saint_Joseph%27s_Hawks_logo.svg","Saint Louis":"https://a.espncdn.com/i/teamlogos/ncaa/500/139.png","Saint Peter's":"https://upload.wikimedia.org/wikipedia/en/thumb/9/97/Saint_Peter%27s_Peacocks_logo.svg/250px-Saint_Peter%27s_Peacocks_logo.svg.png","Sam Houston State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2534.png","Samford":"https://a.espncdn.com/i/teamlogos/ncaa/500/2535.png","San Diego":"https://a.espncdn.com/i/teamlogos/ncaa/500/301.png","San Diego State":"https://a.espncdn.com/i/teamlogos/ncaa/500/21.png","San Francisco":"https://a.espncdn.com/i/teamlogos/ncaa/500/2539.png","San Jose State":"https://a.espncdn.com/i/teamlogos/ncaa/500/23.png","Santa Clara":"https://a.espncdn.com/i/teamlogos/ncaa/500/2541.png","Seattle":"https://upload.wikimedia.org/wikipedia/en/5/53/Seattle_redhawks_ncaa_logo.png","Seton Hall":"https://a.espncdn.com/i/teamlogos/ncaa/500/2550.png","Siena College":"https://upload.wikimedia.org/wikipedia/en/9/91/Siena_Saints_New_Logo.png","South Alabama":"https://a.espncdn.com/i/teamlogos/ncaa/500/6.png","South Carolina":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/South_Carolina_Gamecocks_logo.svg/1280px-South_Carolina_Gamecocks_logo.svg.png","South Carolina State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2569.png","South Dakota":"https://a.espncdn.com/i/teamlogos/ncaa/500/233.png","South Dakota State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2571.png","South Florida":"https://a.espncdn.com/i/teamlogos/ncaa/500/58.png","Southeast Missouri State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2546.png","Southeastern Louisiana":"https://a.espncdn.com/i/teamlogos/ncaa/500/2545.png","Southern Illinois":"https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Southern_Illinois_Salukis_logo.svg/1280px-Southern_Illinois_Salukis_logo.svg.png","Southern Indiana":"https://upload.wikimedia.org/wikipedia/en/thumb/1/12/Southern_Indiana_Screaming_Eagles_logo.svg/1280px-Southern_Indiana_Screaming_Eagles_logo.svg.png","Southern Mississippi":"https://a.espncdn.com/i/teamlogos/ncaa/500/2572.png","Southern University":"https://a.espncdn.com/i/teamlogos/ncaa/500/2582.png","Southern Utah":"https://a.espncdn.com/i/teamlogos/ncaa/500/253.png","St. Bonaventure":"https://a.espncdn.com/i/teamlogos/ncaa/500/179.png","St. John's":"https://upload.wikimedia.org/wikipedia/commons/6/63/St_johns_wordmark_red_2015.png","St. Mary's (CA)":"https://upload.wikimedia.org/wikipedia/commons/7/7c/Saint_Mary%27s_College_Gaels_logo.svg","St. Thomas (Minn.)":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/St-thomas-mn_logo_from_NCAA.svg/1280px-St-thomas-mn_logo_from_NCAA.svg.png","Stanford":"https://a.espncdn.com/i/teamlogos/ncaa/500/24.png","Stephen F. Austin":"https://a.espncdn.com/i/teamlogos/ncaa/500/2617.png","Stetson":"https://a.espncdn.com/i/teamlogos/ncaa/500/56.png","Stonehill":"https://a.espncdn.com/i/teamlogos/ncaa/500/284.png","Stony Brook":"https://a.espncdn.com/i/teamlogos/ncaa/500/2619.png","Syracuse":"https://a.espncdn.com/i/teamlogos/ncaa/500/183.png","TCU":"https://a.espncdn.com/i/teamlogos/ncaa/500/2628.png","Tarleton State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2627.png","Temple":"https://a.espncdn.com/i/teamlogos/ncaa/500/218.png","Tennessee":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Tennessee_Volunteers_logo.svg/3840px-Tennessee_Volunteers_logo.svg.png","Tennessee Tech":"https://upload.wikimedia.org/wikipedia/en/thumb/f/f8/Tennessee_Tech_Golden_Eagles_logo.svg/1280px-Tennessee_Tech_Golden_Eagles_logo.svg.png","Texas":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Texas_Longhorns_logo.svg/1280px-Texas_Longhorns_logo.svg.png","Texas A&M":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Texas_A%26M_University_logo.svg/1280px-Texas_A%26M_University_logo.svg.png","Texas A&M-Corpus Christi":"https://a.espncdn.com/i/teamlogos/ncaa/500/357.png","Texas Southern":"https://a.espncdn.com/i/teamlogos/ncaa/500/2640.png","Texas State":"https://a.espncdn.com/i/teamlogos/ncaa/500/326.png","Texas Tech":"https://a.espncdn.com/i/teamlogos/ncaa/500/2641.png","The Citadel":"https://a.espncdn.com/i/teamlogos/ncaa/500/2643.png","Toledo":"https://a.espncdn.com/i/teamlogos/ncaa/500/2649.png","Towson":"https://a.espncdn.com/i/teamlogos/ncaa/500/119.png","Troy":"https://a.espncdn.com/i/teamlogos/ncaa/500/2653.png","Tulsa":"https://upload.wikimedia.org/wikipedia/commons/c/c4/Tulsa_Golden_Hurricane_logo.svg","UAB":"logos/uab.png","UC Davis":"https://a.espncdn.com/i/teamlogos/ncaa/500/302.png","UC Irvine":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/UC_Irvine_Anteaters_logo.svg/1280px-UC_Irvine_Anteaters_logo.svg.png","UC Riverside":"https://a.espncdn.com/i/teamlogos/ncaa/500/27.png","UC San Diego":"https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/San_Diego_Toreros_logo.svg/250px-San_Diego_Toreros_logo.svg.png","UC Santa Barbara":"https://a.espncdn.com/i/teamlogos/ncaa/500/2540.png","UCF":"https://a.espncdn.com/i/teamlogos/ncaa/500/2116.png","UCLA":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/UCLA_Bruins_logo.svg/1280px-UCLA_Bruins_logo.svg.png","UIC":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/UIC_Flames_wordmark.svg/1280px-UIC_Flames_wordmark.svg.png","UMBC":"https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/UMBC_Retrievers_logo.svg/1280px-UMBC_Retrievers_logo.svg.png","UNC Asheville":"https://upload.wikimedia.org/wikipedia/en/7/73/UNC_asheville_bulldog_head.png","UNC Greensboro":"https://upload.wikimedia.org/wikipedia/en/7/70/UNCG_Spartans_logo.svg","UNC Wilmington":"https://uncw.edu/media/images/logos/brand/secondary-athletics-logo-notpad-our.png","UNLV":"https://a.espncdn.com/i/teamlogos/ncaa/500/2439.png","USC":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/USC_Trojans_logo.svg/250px-USC_Trojans_logo.svg.png","USC Upstate":"https://upload.wikimedia.org/wikipedia/commons/8/8e/USC_Upstate_Spartans_logo.svg","UT Chattanooga":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Chattanooga_Mocs_logo.svg/1280px-Chattanooga_Mocs_logo.svg.png","UT Martin":"https://upload.wikimedia.org/wikipedia/en/thumb/2/2c/UT_Martin_Skyhawks_logo.svg/1280px-UT_Martin_Skyhawks_logo.svg.png","UTEP":"logos/utep.png","UTSA":"https://upload.wikimedia.org/wikipedia/en/thumb/1/1b/UTSA_Athletics_logo.svg/1280px-UTSA_Athletics_logo.svg.png","Utah":"https://a.espncdn.com/i/teamlogos/ncaa/500/254.png","Utah State":"https://a.espncdn.com/i/teamlogos/ncaa/500/328.png","Utah Tech":"https://upload.wikimedia.org/wikipedia/en/thumb/e/ec/Utah_Tech_Trailblazers_logo_2022.svg/250px-Utah_Tech_Trailblazers_logo_2022.svg.png","Utah Valley":"https://upload.wikimedia.org/wikipedia/en/thumb/c/c8/Utah_Valley_Wolverines_logo.svg/1280px-Utah_Valley_Wolverines_logo.svg.png","VCU":"https://upload.wikimedia.org/wikipedia/en/thumb/1/18/VCU_Athletics_Logo.svg/1280px-VCU_Athletics_Logo.svg.png","VMI":"https://a.espncdn.com/i/teamlogos/ncaa/500/2678.png","Valparaiso":"https://a.espncdn.com/i/teamlogos/ncaa/500/2674.png","Vanderbilt":"https://a.espncdn.com/i/teamlogos/ncaa/500/238.png","Vermont":"https://a.espncdn.com/i/teamlogos/ncaa/500/261.png","Villanova":"https://a.espncdn.com/i/teamlogos/ncaa/500/222.png","Virginia":"https://a.espncdn.com/i/teamlogos/ncaa/500/258.png","Virginia Tech":"https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Virginia_Tech_Hokies_logo.svg/1280px-Virginia_Tech_Hokies_logo.svg.png","Wagner":"https://a.espncdn.com/i/teamlogos/ncaa/500/2681.png","Wake Forest":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Wake_Forest_University_Athletic_logo.svg/1280px-Wake_Forest_University_Athletic_logo.svg.png","Washington":"https://a.espncdn.com/i/teamlogos/ncaa/500/264.png","Washington State":"https://a.espncdn.com/i/teamlogos/ncaa/500/265.png","Weber State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2692.png","West Georgia":"https://a.espncdn.com/i/teamlogos/ncaa/500/2698.png","West Virginia":"https://a.espncdn.com/i/teamlogos/ncaa/500/277.png","Western Carolina":"https://a.espncdn.com/i/teamlogos/ncaa/500/2717.png","Western Illinois":"https://a.espncdn.com/i/teamlogos/ncaa/500/2710.png","Western Kentucky":"https://a.espncdn.com/i/teamlogos/ncaa/500/98.png","Western Michigan":"https://a.espncdn.com/i/teamlogos/ncaa/500/2711.png","William & Mary":"https://a.espncdn.com/i/teamlogos/ncaa/500/2729.png","Winthrop":"https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Winthrop_Eagles_logo.svg/1280px-Winthrop_Eagles_logo.svg.png","Wisconsin":"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Wisconsin_Badgers_logo.svg/1280px-Wisconsin_Badgers_logo.svg.png","Wisconsin-Green Bay":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Green_Bay_Phoenix_logo.svg/1280px-Green_Bay_Phoenix_logo.svg.png","Wisconsin-Milwaukee":"https://a.espncdn.com/i/teamlogos/ncaa/500/270.png","Wofford":"https://a.espncdn.com/i/teamlogos/ncaa/500/2747.png","Wright State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2750.png","Wyoming":"https://a.espncdn.com/i/teamlogos/ncaa/500/2751.png","Xavier":"https://a.espncdn.com/i/teamlogos/ncaa/500/2752.png","Yale":"https://a.espncdn.com/i/teamlogos/ncaa/500/43.png","Youngstown State":"https://a.espncdn.com/i/teamlogos/ncaa/500/2754.png"};
// TEAM_INDEX_END
(function () {
  const TEAMS = new Set(TEAM_INDEX);
  const ALIAS = { "UNCW": "UNC Wilmington" };

  /* ---------- 1. Back button ---------- */
  function addBackBar() {
    const main = document.querySelector(".app-main");
    if (!main || main.querySelector(".back-bar")) return;
    const bar = document.createElement("div");
    bar.className = "back-bar";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "back-btn";
    const canBack = window.history.length > 1;
    btn.innerHTML = canBack ? "&#8592; Back" : "&#8592; Home";
    btn.title = canBack ? "Return to the page you came from" : "Go to the Home page";
    btn.addEventListener("click", () => {
      if (window.history.length > 1) window.history.back();
      else window.location.href = "home.html";
    });
    bar.appendChild(btn);
    main.insertBefore(bar, main.firstChild);
  }

  /* ---------- 2. Sticky headers + frozen team column ---------- */
  const SKIP = ".no-sticky, #pdrawer, .cal, .cal-grid";
  function wrapFor(t) {
    const p = t.parentElement;
    if (!p) return null;
    if (p.classList.contains("stk-wrap")) return p;
    if (p.children.length === 1 && (p.classList.contains("table-wrap") || p.classList.contains("scroll-wrap"))) {
      p.classList.add("stk-wrap");
      return p;
    }
    const w = document.createElement("div");
    w.className = "stk-wrap";
    p.insertBefore(w, t);
    w.appendChild(t);
    return w;
  }
  function stickTable(t) {
    if (t.closest(SKIP) || !t.tHead || !t.tHead.rows.length) return;
    if (t.rows.length < 6) return;
    const w = wrapFor(t);
    if (!w) return;
    t.classList.add("stk");
    // header rows: each row sticks under the one above it
    let top = 0;
    [...t.tHead.rows].forEach(r => {
      [...r.cells].forEach(c => {
        c.classList.add("stk-h");
        c.style.top = top + "px";
        if (getComputedStyle(c).backgroundColor === "rgba(0, 0, 0, 0)") { c.style.backgroundColor = "#e9f0f3"; }
      });
      top += r.offsetHeight;
    });
    freezeLeft(t, w);
  }
  function freezeLeft(t, w) {
    const hr = t.tHead.rows[t.tHead.rows.length - 1];
    const hc = [...hr.cells];
    let idx = -1;
    for (let i = 0; i < Math.min(hc.length, 5); i++) {
      if (hc[i].colSpan > 1) break;
      if (/^(team|player|name|opponent|opp\b|school)/i.test(hc[i].textContent.trim())) { idx = i; break; }
    }
    const rows = [...t.querySelectorAll("tbody tr")];
    const clear = () => t.querySelectorAll(".stk-l").forEach(c => { c.classList.remove("stk-l", "stk-last"); c.style.left = ""; });
    if (idx < 0 || !rows.length) { clear(); return; }
    // rows with row/col spans in the frozen area would misalign: leave those tables alone
    if (rows.slice(0, 4).some(r => r.cells.length !== hc.length)) { clear(); return; }
    const lefts = []; let left = 0;
    for (let i = 0; i <= idx; i++) { lefts.push(left); left += hc[i].offsetWidth; }
    if (left > w.clientWidth * 0.55) { clear(); return; }   // too wide a frozen block on a small screen
    const mark = (row) => {
      for (let i = 0; i <= idx; i++) {
        const c = row.cells[i];
        if (!c) continue;
        c.classList.add("stk-l");
        c.style.left = lefts[i] + "px";
        if (i === idx) c.classList.add("stk-last");
      }
    };
    mark(hr);
    rows.forEach(mark);
  }

  /* ---------- 3. Team links ---------- */
  function colHeader(td) {
    const t = td.closest("table");
    if (!t || !t.tHead) return "";
    const hr = t.tHead.rows[t.tHead.rows.length - 1];
    const c = hr && hr.cells[td.cellIndex];
    return c ? c.textContent : "";
  }
  const NOLINK_TAGS = new Set(["A", "BUTTON", "SELECT", "OPTION", "TEXTAREA", "SCRIPT", "STYLE", "TH", "LABEL", "H1", "H2", "SUMMARY", "TITLE"]);
  function linkTeams(root) {
    if (!TEAMS.size) return;
    const onElo = document.body.dataset.page === "elo";
    if (onElo) return;   // the Elo page links its own teams
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const todo = [];
    let n;
    while ((n = walker.nextNode())) {
      const s = n.nodeValue.trim();
      if (!s || s.length > 40) continue;
      const name = TEAMS.has(s) ? s : (ALIAS[s] || null);
      if (!name) continue;
      const p = n.parentElement;
      if (!p || NOLINK_TAGS.has(p.tagName) || p.closest("a,button,select,th,[data-nolink],.app-sidebar,.back-bar")) continue;
      const td = p.closest("td");
      if (td && /conf/i.test(colHeader(td))) continue;   // "American" the league is not "American" the team
      todo.push([n, name]);
    }
    todo.forEach(([node, name]) => {
      const a = document.createElement("a");
      a.className = "auto-tl";
      a.href = "elo.html#/team/" + encodeURIComponent(name);
      a.title = "Open " + name + " (Elo, RPI, schedule, box scores)";
      node.parentNode.insertBefore(a, node);
      if (document.body.dataset.page === "bracketology" && TEAM_LOGOS[name]) {
        const im = document.createElement("img");
        im.className = "tl-logo"; im.alt = ""; im.loading = "lazy"; im.src = TEAM_LOGOS[name];
        im.onerror = () => im.remove();
        a.appendChild(im);
      }
      a.appendChild(node);
    });
  }

  let timer = null;
  function pass() {
    timer = null;
    const main = document.querySelector(".app-main");
    if (!main) return;
    addBackBar();
    main.querySelectorAll("table").forEach(t => { try { stickTable(t); } catch (e) {} });
    try { linkTeams(main); } catch (e) {}
  }
  function schedule() { if (!timer) timer = setTimeout(pass, 180); }
  function start() {
    pass();
    new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
    window.addEventListener("resize", schedule);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
