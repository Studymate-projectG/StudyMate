$("dm").textContent = dom;

$("fm").addEventListener("submit", e => {
  e.preventDefault();
  cl();
  const nm = $("nm").value.trim();
  const em = $("em").value.trim();
  const pw = $("pw").value;
  if (!nm || !em || !pw) return ms("Please fill all the fields.");
  if (!dm(em)) return ms("Only university emails (" + dom + ") can register.");
  if (pw.length < 6) return ms("Password must be at least 6 characters.");
  $("bt").disabled = true;
  au.createUserWithEmailAndPassword(em, pw)
    .then(r => db.collection("users").doc(r.user.uid).set({
      name: nm,
      email: em.toLowerCase(),
      major: "",
      courses: [],
      created: firebase.firestore.FieldValue.serverTimestamp()
    }))
    .then(() => (location.href = "profile.html?new=1"))
    .catch(er => {
      $("bt").disabled = false;
      ms(ae(er.code));
    });
});
