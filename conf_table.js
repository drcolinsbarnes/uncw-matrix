/* conf_table.js -- the CAA-page standings table, shared (2026-10-04).
 *
 * One renderer for every page that shows a conference as a standings table:
 * the Elo conference page, the Elo team page's conference card, and the RPI
 * page when a conference is picked. Same columns and look as caa.html:
 *   Rk | logo | Team | P W L D | GF GA GD | Pts | RPI | (SOS) | Non-Conf | Overall | Form | USC
 * Conference record and points are CONFERENCE games only (3 for a win, 1 for
 * a draw; tie-break head-to-head, goal difference, goals scored -- the order
 * is computed in build_conf_data.py and arrives already sorted).
 * A conference with divisions (only the CAA: South / North) is drawn as one
 * table per division plus an Overall table that also carries SOS, exactly as
 * on caa.html.
 *
 * ConfTable.render(el, payload, opts)
 *   payload = {conf, confFull, divisions, rows:[{name, logo, rank, p, w, l, d, gf, ga, gd, pts,
 *              rpiRank, sos, nonConf, overall, form, division}]}
 *   opts    = {href: name => url, usc: <ELO.usc / NATIONAL.usc>, highlight: team name}
 * ConfTable.uscLabel(usc, team) -> "NR (#8 East Region)", "#3 (#1 Southeast Region)", "NR"
 */
(function () {
  var css = [
    ".ct-label{font-weight:600;font-size:13px;margin:14px 0 4px;color:var(--navy,#003366)}",
    ".ct-label:first-child{margin-top:0}",
    ".ct-wrap{overflow-x:auto;padding-bottom:8px}",
    "table.ct th.num,table.ct td.num{text-align:center}",
    "table.ct td.usc{white-space:nowrap;font-size:11.5px}",
    "table.ct .form{display:inline-flex;gap:3px;justify-content:center}",
    "table.ct .form-circle{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:50%;font-size:10px;font-weight:700;color:#fff;flex:none}",
    "table.ct .form-w{background:#2e7d32}table.ct .form-l{background:#c62828}table.ct .form-d{background:#78909c}",
    ".ct-note{font-size:11.5px;color:var(--muted,#5c7280);margin:6px 0 0}"
  ].join("\n");
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c];
    });
  }

  function formCircles(results) {
    if (!results || !results.length) return "—";
    return '<span class="form">' + results.map(function (r) {
      var cls = r === "W" ? "form-w" : r === "L" ? "form-l" : "form-d";
      var title = r === "W" ? "Win" : r === "L" ? "Loss" : "Draw";
      return '<span class="form-circle ' + cls + '" title="' + title + '">' + r + "</span>";
    }).join("") + "</span>";
  }

  // National rank first, region in brackets: "NR (#8 East Region)".
  function uscLabel(usc, team) {
    if (!usc || !usc.polls || !usc.polls.length) return "—";
    var t = usc.teams[team];
    if (!t) return "NR";
    var i = usc.polls.length - 1;
    var nat = t.nat[i], reg = t.reg[i];
    var n = nat == null ? "NR" : "#" + nat;
    if (!t.region) return n;
    return n + " (" + (reg == null ? "NR" : "#" + reg) + " " + t.region + " Region)";
  }

  function table(rows, opts, showSos) {
    var hdr = '<thead><tr><th class="num">Rk</th><th></th><th>Team</th><th class="num">P</th><th class="num">W</th>' +
      '<th class="num">L</th><th class="num">D</th><th class="num">GF</th><th class="num">GA</th><th class="num">GD</th>' +
      '<th class="num">Pts</th>' +
      '<th class="num" title="National rank by current-season RPI. 1 = best.">RPI</th>' +
      (showSos ? '<th class="num" title="Average current RPI rank of every opponent on the full schedule. Lower = tougher.">SOS</th>' : "") +
      '<th title="Non-conference record (W-L-D).">Non-Conf</th><th title="Overall record (W-L-D).">Overall</th>' +
      '<th title="Last 5 results, oldest to newest.">Form</th>' +
      '<th title="United Soccer Coaches poll: national rank, with the regional rank in brackets. NR = not ranked.">USC</th></tr></thead>';
    var body = rows.map(function (t, i) {
      var link = opts.href ? '<a class="team-link" href="' + esc(opts.href(t.name)) + '">' + esc(t.name) + "</a>" : esc(t.name);
      var gd = t.gd > 0 ? "+" + t.gd : String(t.gd);
      return '<tr' + (opts.highlight && t.name === opts.highlight ? ' class="uncw-row"' : "") + ">" +
        '<td class="num">' + (i + 1) + "</td>" +
        "<td>" + (t.logo ? '<img class="logo" src="' + esc(t.logo) + '" alt="" onerror="this.style.visibility=\'hidden\'">' : "") + "</td>" +
        "<td>" + link + "</td>" +
        '<td class="num">' + t.p + '</td><td class="num">' + t.w + '</td><td class="num">' + t.l + '</td><td class="num">' + t.d + "</td>" +
        '<td class="num">' + t.gf + '</td><td class="num">' + t.ga + '</td><td class="num">' + gd + "</td>" +
        '<td class="num"><b>' + t.pts + "</b></td>" +
        '<td class="num">' + (t.rpiRank != null ? t.rpiRank : "—") + "</td>" +
        (showSos ? '<td class="num">' + (t.sos != null ? t.sos : "—") + "</td>" : "") +
        "<td>" + esc(t.nonConf || "—") + "</td><td>" + esc(t.overall || "—") + "</td>" +
        "<td>" + formCircles(t.form) + "</td>" +
        '<td class="usc">' + esc(uscLabel(opts.usc, t.name)) + "</td></tr>";
    }).join("");
    return '<div class="ct-wrap"><table class="std ct">' + hdr + "<tbody>" + body + "</tbody></table></div>";
  }

  function render(el, payload, opts) {
    opts = opts || {};
    if (!payload || !payload.rows || !payload.rows.length) {
      el.innerHTML = '<p class="ct-note">No standings for this conference yet.</p>';
      return;
    }
    var html = "";
    if (payload.divisions && payload.divisions.length) {
      payload.divisions.forEach(function (dv) {
        var rs = payload.rows.filter(function (r) { return r.division === dv; });
        if (rs.length) html += '<div class="ct-label">' + esc(dv) + "</div>" + table(rs, opts, false);
      });
      html += '<div class="ct-label">Overall</div>' + table(payload.rows, opts, true);
    } else {
      html += table(payload.rows, opts, true);
    }
    html += '<p class="ct-note">W-L-D, points and goals are conference games only (3 for a win, 1 for a draw). Ties broken by head-to-head, then goal difference, then goals scored.</p>';
    el.innerHTML = html;
  }

  window.ConfTable = {render: render, uscLabel: uscLabel, formCircles: formCircles};
})();
