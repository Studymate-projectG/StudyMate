let me = null;
let pr = null;

gd(u => {
  me = u;
  db.collection("users").doc(u.uid).get().then(d => {
    pr = d.data() || {};
    const cs = pr.courses || [];
    if (!cs.length) {
      $("np").style.display = "block";
      return;
    }
    cs.forEach(c => {
      const o = el("option", null, cn(c));
      o.value = c;
      $("co").appendChild(o);
    });
    $("fm").style.display = "block";
  });
});

$("fm").addEventListener("submit", e => {
  e.preventDefault();
  cl();
  const tt = $("tt").value.trim();
  const co = $("co").value;
  const ds = $("ds").value.trim();
  const mx = Number($("mx").value);
  const tm = $("tm").value;
  if (!tt) return ms("Please enter a group title.");
  if (!co) return ms("Please choose a course.");
  if (!tm) return ms("Please choose the meeting time.");
  if (!Number.isInteger(mx) || mx < 2) return ms("Maximum members must be a whole number greater than 1.");
  $("bt").disabled = true;
  db.collection("groups").add({
    title: tt,
    course: co,
    desc: ds,
    max: mx,
    time: tm,
    leader: me.uid,
    leaderName: pr.name || me.email,
    members: [me.uid],
    created: firebase.firestore.FieldValue.serverTimestamp()
  })
    .then(() => (location.href = "groups.html?new=1"))
    .catch(() => {
      $("bt").disabled = false;
      ms("Could not create the group. Please try again.");
    });
});
