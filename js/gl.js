let all = [];

const fl = $("fl");
crs.forEach(c => {
  const o = el("option", null, c[0] + " - " + c[1]);
  o.value = c[0];
  fl.appendChild(o);
});

function sh() {
  const c = fl.value;
  const ls = c ? all.filter(g => g.course == c) : all;
  const bx = $("ls");
  bx.innerHTML = "";
  $("nt").textContent = "";
  if (!ls.length) {
    $("nt").textContent = c ? "There are no study groups for " + c + " yet." : "There are no study groups yet. Be the first to create one!";
    return;
  }
  ls.forEach(g => {
    const fr = g.max - g.members.length;
    const cd = el("div", "cd");
    cd.appendChild(el("span", "tg", g.course));
    cd.appendChild(el("h3", null, g.title));
    cd.appendChild(el("p", "sm", ft(g.time)));
    cd.appendChild(el("p", fr > 0 ? "st" : "st fu", fr > 0 ? fr + " free seat" + (fr > 1 ? "s" : "") + " of " + g.max : "Full"));
    const a = el("a", "bt sc", "View group");
    a.href = "group.html?id=" + g.id;
    cd.appendChild(a);
    bx.appendChild(cd);
  });
}

gd(() => {
  if (new URLSearchParams(location.search).get("new")) ms("Your group was created.", true);
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
