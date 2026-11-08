gd(u => {
  if (new URLSearchParams(location.search).get("left")) ms("You left the group.", true);
  db.collection("groups").where("members", "array-contains", u.uid).get().then(s => {
    const all = s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => (a.time > b.time ? 1 : -1));
    $("ld").style.display = "none";
    const cr = all.filter(g => g.leader == u.uid);
    const jn = all.filter(g => g.leader != u.uid);
    cr.forEach(g => $("cr").appendChild(gr(g)));
    jn.forEach(g => $("jn").appendChild(gr(g)));
    if (!cr.length) $("ec").textContent = "You have not created any group yet.";
    if (!jn.length) $("ej").textContent = "You have not joined any group yet.";
    if (!all.length) {
      $("nt").innerHTML = 'You are not in any study group yet. <a href="groups.html">Browse the study groups</a> to join one, or create your own group.';
    }
    const ls = all.filter(g => isopen(g) && rmsg(g));
    const b = $("rm");
    b.innerHTML = "";
    ls.forEach(g => {
      const r = el("div", "rem");
      r.appendChild(el("b", null, "Reminder - " + cn(g.course) + ": " + g.title));
      r.appendChild(el("p", null, rmsg(g)));
      const a = el("a", null, "Open group");
      a.href = "group.html?id=" + g.id;
      r.appendChild(a);
      b.appendChild(r);
    });
    b.style.display = ls.length ? "block" : "none";
  }).catch(() => {
    $("ld").style.display = "none";
    ms("Could not load your groups. Please refresh the page.");
  });
});
