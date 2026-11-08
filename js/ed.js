const id = new URLSearchParams(location.search).get("id");
let me = null;
let g = null;

crs.forEach(c => {
  const o = el("option", null, cn(c[0]));
  o.value = c[0];
  $("co").appendChild(o);
});

gd(u => {
  me = u;
  if (!id) return ms("This group was not found.");
  $("bk").href = "group.html?id=" + id;
  db.collection("groups").doc(id).get().then(d => {
    if (!d.exists) return ms("This group was not found.");
    g = d.data();
    if (g.leader != me.uid) {
      $("np").style.display = "block";
      return;
    }
    $("tt").value = g.title;
    $("co").value = g.course;
    $("ds").value = g.desc || "";
    $("mx").value = g.max;
    $("mx").min = Math.max(2, g.members.length);
    $("ct").textContent = g.members.length;
    $("tm").value = g.time;
    $("fm").style.display = "block";
  });
});

$("fm").addEventListener("submit", e => {
  e.preventDefault();
  cl();
  const tt = $("tt").value.trim();
  const ds = $("ds").value.trim();
  const mx = Number($("mx").value);
  const tm = $("tm").value;
  if (!tt) return ms("Please enter a group title.");
  if (!tm) return ms("Please choose the meeting time.");
  if (tm <= now()) return ms("The meeting time is in the past. Please choose a future date and time.");
  if (!Number.isInteger(mx) || mx < 2) return ms("Maximum members must be a whole number greater than 1.");
  if (mx < g.members.length) return ms("The maximum cannot be lower than the current number of members (" + g.members.length + ").");
  $("bt").disabled = true;
  db.collection("groups").doc(id).update({ title: tt, desc: ds, max: mx, time: tm, t: new Date(tm).getTime() })
    .then(() => (location.href = "group.html?id=" + id))
    .catch(e => {
      $("bt").disabled = false;
      ms(e.code == "permission-denied" ? "Only the leader can edit this group, and the new values must pass the same checks as creating a group." : "Could not save the changes. Please try again.");
    });
});
