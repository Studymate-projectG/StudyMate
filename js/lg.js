au.onAuthStateChanged(u => {
  if (u && !window.bz) location.href = "groups.html";
});

$("fm").addEventListener("submit", e => {
  e.preventDefault();
  cl();
  const em = $("em").value.trim();
  const pw = $("pw").value;
  if (!em || !pw) return ms("Please enter your email and password.");
  if (!dm(em)) return ms("Please use your university email (" + dom + ").");
  window.bz = true;
  $("bt").disabled = true;
  au.signInWithEmailAndPassword(em, pw)
    .then(() => (location.href = "groups.html"))
    .catch(er => {
      window.bz = false;
      $("bt").disabled = false;
      $("pw").value = "";
      ms(ae(er.code));
    });
});
