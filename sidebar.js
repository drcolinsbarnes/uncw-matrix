// Shared sidebar nav for the UNCW Women's Soccer site. One source of truth
// for the nav item list -- add/rename/reorder a page here and every page
// picks it up, instead of editing six copies of the same markup.
//
// Each page sets <body data-page="..."> to one of NAV_ITEMS' `key` values
// so the matching link gets the "active" highlight. A page not yet built
// (per the site-restructure rollout) still gets a real nav entry pointing
// at its "coming soon" placeholder, so the nav always looks complete even
// mid-migration.
(function () {
  const NAV_ITEMS = [
    { key: "home", label: "Home", emoji: "\u{1F3E0}", href: "home.html" },
    { key: "squad", label: "Squad", emoji: "\u{1F465}", href: "squad.html" },
    { key: "stats", label: "Stats", emoji: "\u{1F4CA}", href: "stats.html" },
    { key: "fixtures", label: "Fixtures", emoji: "\u{1F4C5}", href: "fixtures.html" },
    { key: "caa", label: "CAA", emoji: "\u{1F3C6}", href: "caa.html" },
    { key: "rpi", label: "RPI", emoji: "\u{1F310}", href: "national_rpi.html" },
  ];

  function render() {
    const root = document.getElementById("app-sidebar");
    if (!root) return;
    const current = document.body.dataset.page || "";

    const brand = document.createElement("div");
    brand.className = "brand";
    brand.innerHTML =
      '<img src="https://uncw.edu/media/images/logos/brand/secondary-athletics-logo-notpad-our.png" ' +
      'onerror="this.style.visibility=\'hidden\'">' +
      '<div class="name">UNCW Women’s Soccer<small>Schedule / RPI Matrix</small></div>';
    root.appendChild(brand);

    const nav = document.createElement("nav");
    nav.className = "nav-items";
    NAV_ITEMS.forEach(item => {
      const a = document.createElement("a");
      a.className = "nav-item" + (item.key === current ? " active" : "");
      a.href = item.href;
      a.innerHTML = `<span class="emoji">${item.emoji}</span><span>${item.label}</span>`;
      nav.appendChild(a);
    });
    root.appendChild(nav);

    const footer = document.createElement("div");
    footer.className = "nav-footer";
    footer.innerHTML =
      '<a class="legacy-link" href="index.html">Classic dashboard (legacy)</a>' +
      '<div class="build-note">New site, in progress</div>';
    root.appendChild(footer);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
