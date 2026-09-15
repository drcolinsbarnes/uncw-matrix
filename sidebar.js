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
    fixtures: '<rect x="3.5" y="5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17"/><path d="M8 3v3.5"/><path d="M16 3v3.5"/>',
    caa: '<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4.5A1.5 1.5 0 0 0 3 7.5C3 9.4 4.4 11 7 11"/><path d="M17 6h2.5A1.5 1.5 0 0 1 21 7.5c0 1.9-1.4 3.5-4 3.5"/><path d="M12 14v3.5"/><path d="M8.5 21h7"/><path d="M9.5 17.5h5l1 3.5h-7l1-3.5Z"/>',
    rpi: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17"/><path d="M12 3.5c2.6 2.3 4 5.3 4 8.5s-1.4 6.2-4 8.5c-2.6-2.3-4-5.3-4-8.5s1.4-6.2 4-8.5Z"/>',
  };
  function iconSvg(key) {
    return `<svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICONS[key] || ""}</svg>`;
  }

  const NAV_ITEMS = [
    { key: "home", label: "Home", href: "home.html" },
    { key: "squad", label: "Squad", href: "squad.html" },
    { key: "stats", label: "Stats", href: "stats.html" },
    { key: "fixtures", label: "Fixtures", href: "fixtures.html" },
    { key: "caa", label: "CAA", href: "caa.html" },
    { key: "rpi", label: "RPI", href: "national_rpi.html" },
  ];

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
      '<img src="https://uncw.edu/media/images/logos/brand/secondary-athletics-logo-notpad-our.png" ' +
      'onerror="this.style.visibility=\'hidden\'">' +
      '<div class="name">UNCW Women’s Soccer<small>Schedule / RPI Matrix</small></div>';
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
      '<div class="build-note">New site, in progress</div>';
    root.appendChild(footer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
