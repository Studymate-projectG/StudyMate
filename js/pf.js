const bx = $("cs");
crs.forEach(c => {
  const lb = el("label", "ck");
  const ip = el("input");
  ip.type = "checkbox";
  ip.value = c[0];
  lb.appendChild(ip);
  lb.appendChild(document.createTextNode(" " + c[0] + " - " + c[1]));
  bx.appendChild(lb);
});

let me = null;

gd(u => {
  me = u;
  $("em").textContent = u.email;
  db.collection("users").doc(u.uid).get().then(d => {
    const p = d.data() || {};
    $("nm").value = p.name || "";
    $("mj").value = p.major || "";
    const cs = p.courses || [];
    bx.querySelectorAll("input").forEach(i => (i.checked = cs.includes(i.value)));
    if (!p.major || !cs.length) ms("Please add your major and the courses you are taking this term.", true);
    $("fm").style.display = "block";
  });
});

$("fm").addEventListener("submit", e => {
  e.preventDefault();
  cl();
  const nm = $("nm").value.trim();
  const mj = $("mj").value.trim();
  const cs = [...bx.querySelectorAll("input:checked")].map(i => i.value);
  if (!nm) return ms("Please enter your name.");
  if (!mj) return ms("Please enter your major.");
  if (!cs.length) return ms("Please choose at least one course.");
  $("bt").disabled = true;
  db.collection("users").doc(me.uid).set({ name: nm, email: me.email.toLowerCase(), major: mj, courses: cs }, { merge: true })
    .then(() => ms("Your profile was saved.", true))
    .catch(() => ms("Could not save your profile. Please try again."))
    .finally(() => ($("bt").disabled = false));
});
