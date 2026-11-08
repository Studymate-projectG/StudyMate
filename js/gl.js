let all = [];

const fl = $("fl");
crs.forEach(c => {
  const o = el("option", null, c[0] + " - " + c[1]);
  o.value = c[0];
  fl.appendChild(o);
});

function sh() {
  const c = fl.value;
  const ls = all.filter(g => !g.closed).filter(g => (c ? g.course == c : true));
  const bx = $("ls");
  bx.innerHTML = "";
  $("nt").textContent = "";
  if (!ls.length) {
    $("nt").textContent = c ? "There are no study groups for " + c + " yet." : "There are no study groups yet. Be the first to create one!";
    return;
  }
  ls.forEach(g => bx.appendChild(gr(g)));
}

gd(() => {
  if (new URLSearchParams(location.search).get("new")) ms("Your group was created.", true);
  rm();
  db.collection("groups").get().then(s => {
    all = s.docs.map(d => ({ id: d.id, ...d.data() }));
    all.sort((a, b) => (a.time > b.time ? 1 : -1));
    $("ld").style.display = "none";
    sh();
  }).catch(() => {
    $("ld").style.display = "none";
    ms("Could not load the groups. Please refresh the page.");
  });
});

fl.addEventListener("change", sh);

function rm() {
  db.collection("groups").where("members", "array-contains", au.currentUser.uid).get().then(s => {
    const ls = s.docs.map(d => ({ id: d.id, ...d.data() })).filter(g => isopen(g) && rmsg(g));
    const b = $("rm");
    b.innerHTML = "";
    ls.sort((a, c) => (a.time > c.time ? 1 : -1)).forEach(g => {
      const r = el("div", "rem");
      r.appendChild(el("b", null, "Reminder - " + cn(g.course) + ": " + g.title));
      r.appendChild(el("p", null, rmsg(g)));
      const a = el("a", null, "Open group");
      a.href = "group.html?id=" + g.id;
      r.appendChild(a);
      b.appendChild(r);
    });
    b.style.display = ls.length ? "block" : "none";
  });
}
