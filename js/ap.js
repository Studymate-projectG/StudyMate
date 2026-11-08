firebase.initializeApp(cfg);
const au = firebase.auth();
const db = firebase.firestore();

if (emu) {
  au.useEmulator("http://" + location.hostname + ":9099");
  db.useEmulator(location.hostname, 8080);
}

function $(i) {
  return document.getElementById(i);
}

function ms(t, ok) {
  const e = $("ms");
  e.textContent = t;
  e.className = ok ? "ms ok" : "ms er";
}

function cl() {
  $("ms").className = "ms";
  $("ms").textContent = "";
}

function el(tg, c, t) {
  const e = document.createElement(tg);
  if (c) e.className = c;
  if (t != null) e.textContent = t;
  return e;
}

function dm(e) {
  return e.toLowerCase().endsWith(dom);
}

function ae(c) {
  if (c == "auth/email-already-in-use") return "This email already has an account. Please log in.";
  if (c == "auth/weak-password") return "Password must be at least 6 characters.";
  if (c == "auth/invalid-email") return "Please enter a valid email.";
  if (c == "auth/too-many-requests") return "Too many tries. Please wait a little and try again.";
  if (c == "auth/wrong-password" || c == "auth/user-not-found" || c == "auth/invalid-credential" || c == "auth/invalid-login-credentials") return "Wrong email or password.";
  return "Something went wrong. Please try again.";
}

function ft(s) {
  const d = new Date(s);
  if (isNaN(d)) return s;
  return d.toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function gd(fn) {
  au.onAuthStateChanged(u => {
    if (!u) {
      location.href = "index.html";
      return;
    }
    const n = $("nv");
    if (n) n.style.display = "flex";
    fn(u);
  });
}

function lo() {
  au.signOut().then(() => (location.href = "index.html"));
}

function my(g) {
  return g.members.includes(au.currentUser.uid);
}

function ld(g) {
  return g.leader == au.currentUser.uid;
}

function isopen(g) {
  return !g.closed && g.time > now();
}

function now() {
  const d = new Date();
  d.setSeconds(0);
  d.setMilliseconds(0);
  return d.toISOString().slice(0, 16);
}

function free(g) {
  return g.max - g.members.length;
}

function hrs(c, t) {
  const d = new Date(c);
  if (isNaN(d) || d.getTime() <= Date.now()) return null;
  const h = (d.getTime() - Date.now()) / 3600000;
  if (h > t) return null;
  return Math.round(h);
}

function rmsg(g) {
  const h = hrs(g.time, 24);
  if (h == null) return null;
  return "Session in " + h + (h == 1 ? " hour" : " hours") + ": " + ft(g.time) + ".";
}

function gr(g) {
  const fr = free(g);
  const cd = el("div", "cd");
  cd.appendChild(el("span", "tg", g.course));
  cd.appendChild(el("h3", null, g.title));
  cd.appendChild(el("p", "sm", "Meeting: " + ft(g.time)));
  if (g.closed) cd.appendChild(el("p", "st fu", "Closed"));
  else if (fr > 0) cd.appendChild(el("p", "st", fr + " free seat" + (fr > 1 ? "s" : "") + " of " + g.max));
  else cd.appendChild(el("p", "st fu", "Full (" + g.max + " of " + g.max + ")"));
  if (g.leader == au.currentUser.uid) cd.appendChild(el("p", "sm", "You are the leader"));
  const a = el("a", "bt sc", "View group");
  a.href = "group.html?id=" + g.id;
  cd.appendChild(a);
  return cd;
}
