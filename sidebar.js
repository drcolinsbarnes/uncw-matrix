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
  const NAV_ITEMS = [
    { key: "home", label: "Home", emoji: "\u{1F3E0}", href: "home.html" },
    { key: "squad", label: "Squad", emoji: "\u{1F465}", href: "squad.html" },
    { key: "stats", label: "Stats", emoji: "\u{1F4CA}", href: "stats.html" },
    { key: "fixtures", label: "Fixtures", emoji: "\u{1F4C5}", href: "fixtures.html" },
    { key: "caa", label: "CAA", emoji: "\u{1F3C6}", href: "caa.html" },
    { key: "rpi", label: "RPI", emoji: "\u{1F310}", href: "national_rpi.html" },
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
      a.innerHTML = `<span class="emoji">${item.emoji}</span><span class="label">${item.label}</span>`;
      nav.appendChild(a);
    });
    root.appendChild(nav);

    const footer = document.createElement("div");
    footer.className = "nav-footer";
    footer.innerHTML =
      '<a class="legacy-link" href="index.html" title="Classic dashboard (legacy)">' +
      '<span class="icon">↩️</span><span class="label">Classic dashboard (legacy)</span></a>' +
      '<div class="build-note">New site, in progress</div>';
    root.appendChild(footer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
