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
  const HUB_VERSION = "4.9";
  const HUB_UPDATED = "12 Oct 2026";
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
