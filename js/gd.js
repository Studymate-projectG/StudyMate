const id = new URLSearchParams(location.search).get("id");
let me = null;

function sh(g) {
  const fr = g.max - g.members.length;
  const mb = g.members.includes(me.uid);
  $("tg").textContent = cn(g.course);
  $("tt").textContent = g.title;
  $("ds").textContent = g.desc || "No description.";
  $("tm").textContent = ft(g.time);
  $("ln").textContent = g.leaderName;
  $("st").textContent = fr > 0 ? fr + " of " + g.max + " seats free" : "Full (" + g.max + " of " + g.max + ")";
  $("mc").textContent = g.members.length;
  $("bt").style.display = "none";
  $("in").textContent = "";
  if (g.leader == me.uid) $("in").textContent = "You are the leader of this group.";
  else if (mb) $("in").textContent = "You are a member of this group.";
  else if (fr <= 0) $("in").textContent = "This group is full.";
  else $("bt").style.display = "inline-block";
  $("bx").style.display = "block";
}

function ld() {
  return db.collection("groups").doc(id).get().then(d => {
    if (!d.exists) {
      ms("This group was not found.");
      return;
    }
    sh(d.data());
  });
}

gd(u => {
  me = u;
  if (!id) return ms("This group was not found.");
  ld();
});

$("bt").addEventListener("click", () => {
  cl();
  $("bt").disabled = true;
  const rf = db.collection("groups").doc(id);
  db.runTransaction(t => t.get(rf).then(d => {
    const g = d.data();
    if (g.members.includes(me.uid)) throw new Error("tw");
    if (g.members.length >= g.max) throw new Error("fu");
    t.update(rf, { members: firebase.firestore.FieldValue.arrayUnion(me.uid) });
  }))
    .then(() => ld())
    .then(() => ms("You joined the group.", true))
    .catch(() => rf.get().then(d => {
      const g = d.data();
      if (g.members.includes(me.uid)) ms("You already joined this group.");
      else if (g.members.length >= g.max) ms("Sorry, this group is full now.");
      else ms("Could not join the group. Please try again.");
      sh(g);
    }))
    .finally(() => ($("bt").disabled = false));
});
