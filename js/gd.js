const id = new URLSearchParams(location.search).get("id");
let me = null;
let g = null;
let nm = {};

function sh(d) {
  g = d;
  const fr = free(g);
  const im = my(g);
  const il = ld(g);
  $("tg").textContent = cn(g.course);
  $("cl").textContent = g.closed ? "Closed" : "";
  $("tt").textContent = g.title;
  $("ds").textContent = g.desc || "No description.";
  $("tm").textContent = ft(g.time);
  $("ln").textContent = g.leaderName;
  $("mc").textContent = g.members.length;
  $("st").textContent = g.closed ? "Closed group" : g.time <= now() ? "Session passed" : fr > 0 ? fr + " of " + g.max + " seats free" : "Full (" + g.max + " of " + g.max + ")";
  $("bt").style.display = "none";
  $("lv").style.display = "none";
  $("ed").style.display = "none";
  $("cs").style.display = "none";
  $("nf").style.display = "none";
  $("in").textContent = "";
  if (il) $("in").textContent = "You are the leader of this group.";
  else if (im) $("in").textContent = "You are a member of this group.";
  else if (g.closed) $("in").textContent = "This group is closed.";
  else if (g.time <= now()) $("in").textContent = "The session of this group already passed.";
  else if (fr <= 0) $("in").textContent = "This group is full.";
  else $("bt").style.display = "inline-block";
  if (im && !il && !g.closed && g.time > now()) $("lv").style.display = "inline-block";
  if (il && !g.closed) {
    $("ed").style.display = "inline-block";
    $("ed").href = "edit.html?id=" + id;
    $("cs").style.display = "inline-block";
    $("nf").style.display = "block";
  }
  const r = rmsg(g);
  $("rm").style.display = im && r ? "block" : "none";
  $("rm").textContent = r || "";
  mm();
  an();
  $("bx").style.display = "block";
}

function mm() {
  const b = $("mb");
  b.innerHTML = "";
  g.members.forEach(u => {
    const r = el("div", "mr");
    r.appendChild(el("span", null, (nm[u] || "Student") + (u == g.leader ? " (leader)" : "")));
    if (u == g.leader) r.appendChild(el("span", "tg", "Leader"));
    else if (ld(g)) {
      const x = el("button", "bt xm", "Remove");
      x.addEventListener("click", () => rm(u));
      r.appendChild(x);
    }
    b.appendChild(r);
  });
}

function an() {
  const b = $("an");
  b.innerHTML = "";
  if (!g.members.includes(me.uid)) {
    b.appendChild(el("p", "sm", "Announcements are visible to the members of this group."));
    return;
  }
  db.collection("groups").doc(id).collection("notes").orderBy("at", "desc").get().then(s => {
    if (!s.docs.length) {
      b.appendChild(el("p", "sm", "No announcements yet."));
      return;
    }
    s.docs.forEach(d => {
      const x = d.data();
      const bx2 = el("div", "an1");
      bx2.appendChild(el("p", null, x.text));
      bx2.appendChild(el("p", "sm", "Posted " + ft(x.at ? x.at.toDate() : "")));
      b.appendChild(bx2);
    });
  }).catch(() => b.appendChild(el("p", "sm", "Could not load the announcements.")));
}

function ld2() {
  return db.collection("groups").doc(id).get().then(d => {
    if (!d.exists) {
      ms("This group was not found.");
      return;
    }
    const u = [...new Set([...d.data().members])];
    return Promise.all(u.map(x => db.collection("users").doc(x).get().then(p => [x, p.exists ? p.data().name : ""])))
      .then(ps => {
        nm = {};
        ps.forEach(p => (nm[p[0]] = p[1]));
        sh(d.data());
      });
  });
}

function dn(e) {
  ms(e.code == "permission-denied" ? "This action is not allowed." : "Could not save the change. Please try again.");
  ld2();
}

gd(u => {
  me = u;
  if (!id) return ms("This group was not found.");
  ld2();
});

$("bt").addEventListener("click", () => {
  cl();
  $("bt").disabled = true;
  const rf = db.collection("groups").doc(id);
  db.runTransaction(t => t.get(rf).then(d => {
    const x = d.data();
    if (x.members.includes(me.uid)) throw new Error("tw");
    if (x.closed || x.members.length >= x.max) throw new Error("fu");
    t.update(rf, { members: firebase.firestore.FieldValue.arrayUnion(me.uid) });
  }))
    .then(() => ld2())
    .then(() => ms("You joined the group.", true))
    .catch(() => rf.get().then(d => {
      const x = d.data();
      if (x.closed) ms("This group is closed. You cannot join it.");
      else if (x.members.includes(me.uid)) ms("You already joined this group.");
      else if (x.members.length >= x.max) ms("Sorry, this group is full now.");
      else ms("Could not join the group. Please try again.");
      sh(x);
    }))
    .finally(() => ($("bt").disabled = false));
});

$("lv").addEventListener("click", () => {
  cl();
  $("lv").disabled = true;
  const rf = db.collection("groups").doc(id);
  db.runTransaction(t => t.get(rf).then(d => {
    const x = d.data();
    if (x.leader == me.uid) throw new Error("ld");
    if (!x.members.includes(me.uid)) throw new Error("nm");
    t.update(rf, { members: firebase.firestore.FieldValue.arrayRemove(me.uid) });
  }))
    .then(() => ld2())
    .then(() => ms("You left the group. Your seat is free again.", true))
    .catch(e => {
      if (e.message == "ld") ms("The leader cannot leave her own group. Close the group instead.");
      else if (e.message == "nm") ms("You are not a member of this group.");
      else ms("Could not leave the group. Please try again.");
      ld2();
    })
    .finally(() => ($("lv").disabled = false));
});

$("cs").addEventListener("click", () => {
  if (!window.confirm("Close this group? Nobody can join it after that.")) return;
  cl();
  db.collection("groups").doc(id).update({ closed: true })
    .then(() => ld2())
    .then(() => ms("The group is closed. It no longer appears in the groups list.", true))
    .catch(dn);
});

function rm(u) {
  if (!window.confirm("Remove this member from the group?")) return;
  cl();
  const rf = db.collection("groups").doc(id);
  db.runTransaction(t => t.get(rf).then(d => {
    const x = d.data();
    if (!x.members.includes(u)) throw new Error("nm");
    t.update(rf, { members: firebase.firestore.FieldValue.arrayRemove(u) });
  }))
    .then(() => ld2())
    .then(() => ms("The member was removed and the seat is free again.", true))
    .catch(dn);
}

$("ab").addEventListener("click", () => {
  cl();
  const tx = $("nt2").value.trim();
  if (!tx) return ms("Please write the announcement text first.");
  $("ab").disabled = true;
  db.collection("groups").doc(id).collection("notes").add({
    text: tx,
    author: me.uid,
    authorName: nm[me.uid] || me.email,
    at: firebase.firestore.FieldValue.serverTimestamp()
  })
    .then(() => {
      $("nt2").value = "";
      return ld2();
    })
    .then(() => ms("Your announcement was posted.", true))
    .catch(e => ms(e.code == "permission-denied" ? "Only the leader can post an announcement." : "Could not post the announcement. Please try again."))
    .finally(() => ($("ab").disabled = false));
});
