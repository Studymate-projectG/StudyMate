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
