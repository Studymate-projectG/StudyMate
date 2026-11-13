import { initializeTestEnvironment, assertSucceeds, assertFails } from "@firebase/rules-unit-testing";
import { doc, getDoc, setDoc, updateDoc, addDoc, collection, deleteDoc, serverTimestamp } from "firebase/firestore";
import { readFileSync, writeFileSync, mkdirSync } from "fs";

const PJ = "demo-studymate";
const rs = [];
const ms = { "0": 60000 };
const soon = Date.now() + 3 * 86400000;
const past = Date.now() - 86400000;

function iso(t) {
  const d = new Date(t);
  d.setSeconds(0, 0);
  return d.toISOString().slice(0, 16);
}

function base(o) {
  return {
    title: "Algorithms practice", course: "CS 311", desc: "Weekly revision",
    max: 4, time: iso(soon), t: soon, leader: "L", leaderName: "Leader One",
    members: ["L"], closed: false, ...o
  };
}

function ck(id, us, role, name, ok, note = "") {
  rs.push({ id, us, role, name, result: ok ? "Pass" : "Fail", note });
  console.log((ok ? "PASS " : "FAIL ") + id + " [" + role + "] " + name + (note ? " | " + note : ""));
}

const env = await initializeTestEnvironment({
  projectId: PJ,
  firestore: { rules: readFileSync("firestore.rules", "utf8"), host: process.env.FSHOST || "127.0.0.1", port: Number(process.env.FSPORT || 8080) }
});

const L = env.authenticatedContext("L", { email: "leader@university.edu.sa" }).firestore();
const M = env.authenticatedContext("M", { email: "member@university.edu.sa" }).firestore();
const N = env.authenticatedContext("N", { email: "other@university.edu.sa" }).firestore();
const X = env.authenticatedContext("X", { email: "outsider@gmail.com" }).firestore();

async function seed() {
  await env.withSecurityRulesDisabled(async c => {
    const db = c.firestore();
    await setDoc(doc(db, "groups/g1"), base({ id: "g1", members: ["L", "M"] }));
    await setDoc(doc(db, "groups/g2"), base({ id: "g2", title: "Closed group", closed: true, members: ["L", "M"] }));
    await setDoc(doc(db, "groups/g3"), base({ id: "g3", title: "Full group", max: 2, members: ["L", "M"] }));
    await setDoc(doc(db, "groups/g4"), base({ id: "g4", title: "One seat", max: 3, members: ["L", "M"] }));
    await setDoc(doc(db, "users/L"), { name: "Leader One", email: "leader@university.edu.sa", major: "CS", courses: ["CS 311"] });
  });
}

/* ---------- US17 : past meeting time ---------- */
await seed();
try { await setDoc(doc(L, "groups/p1"), base({ leader: "L", members: ["L"], time: iso(past), t: past })); ck("RS-01", "US17", "Leader", "A group with a past meeting time cannot be created directly in Firestore", 0); }
catch (e) { ck("RS-01", "US17", "Leader", "A group with a past meeting time cannot be created directly in Firestore", 1, e.code); }
try { await setDoc(doc(L, "groups/p2"), base({ leader: "L", members: ["L"] })); ck("RS-02", "US17", "Leader", "A group with a future meeting time is accepted", 1); }
catch (e) { ck("RS-02", "US17", "Leader", "A group with a future meeting time is accepted", 0, e.code); }
try { await setDoc(doc(L, "groups/p3"), base({ leader: "M", members: ["M"] })); ck("RS-03", "US3", "Leader", "A user cannot create a group with another student as leader", 0); }
catch (e) { ck("RS-03", "US3", "Leader", "A user cannot create a group with another student as leader", 1, e.code); }

/* ---------- US10 : leave a group ---------- */
const leave = db => updateDoc(doc(db, "groups/g1"), { members: ["L"] });
try { await leave(M); ck("RS-04", "US10", "Member", "A member can leave the group (her UID is removed from members)", 1); }
catch (e) { ck("RS-04", "US10", "Member", "A member can leave the group (her UID is removed from members)", 0, e.code); }
try { await updateDoc(doc(L, "groups/g4"), { members: ["M"] }); ck("RS-05", "US10", "Leader", "The leader cannot remove herself from her own group", 0); }
catch (e) { ck("RS-05", "US10", "Leader", "The leader cannot remove herself from her own group", 1, e.code); }
try { await updateDoc(doc(N, "groups/g4"), { members: ["L"] }); ck("RS-06", "US10", "Non-member", "A student cannot leave (change members of) a group she is not in", 0); }
catch (e) { ck("RS-06", "US10", "Non-member", "A student cannot leave (change members of) a group she is not in", 1, e.code); }
try { await updateDoc(doc(X, "groups/g4"), { members: ["L"] }); ck("RS-07", "US10", "Unauthorized", "An account outside the university domain cannot change the group", 0); }
catch (e) { ck("RS-07", "US10", "Unauthorized", "An account outside the university domain cannot change the group", 1, e.code); }

/* ---------- US6 : remove a member ---------- */
await seed();
try { await updateDoc(doc(L, "groups/g1"), { members: ["L"] }); ck("RS-08", "US6", "Leader", "The leader can remove a member", 1); }
catch (e) { ck("RS-08", "US6", "Leader", "The leader can remove a member", 0, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["M"] }); ck("RS-09", "US6", "Member", "A normal member cannot remove another member", 0); }
catch (e) { ck("RS-09", "US6", "Member", "A normal member cannot remove another member", 1, e.code); }
try { await updateDoc(doc(N, "groups/g4"), { members: [] }); ck("RS-10", "US6", "Non-member", "A non-member cannot empty the members list", 0); }
catch (e) { ck("RS-10", "US6", "Non-member", "A non-member cannot empty the members list", 1, e.code); }
try { await updateDoc(doc(L, "groups/g4"), { members: ["L", "M", "N", "X"] }); ck("RS-11", "US5", "Leader", "The leader cannot push the members over the maximum by writing the list directly", 0); }
catch (e) { ck("RS-11", "US5", "Leader", "The leader cannot push the members over the maximum by writing the list directly", 1, e.code); }

/* ---------- US8 : edit and close ---------- */
await seed();
try { await updateDoc(doc(L, "groups/g4"), { title: "Algorithms practice 2", desc: "New", max: 5, time: iso(soon + 86400000), t: soon + 86400000 }); ck("RS-12", "US8", "Leader", "The leader can edit the group data with valid values", 1); }
catch (e) { ck("RS-12", "US8", "Leader", "The leader can edit the group data with valid values", 0, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { title: "Changed by a member" }); ck("RS-13", "US8", "Member", "A normal member cannot edit the group", 0); }
catch (e) { ck("RS-13", "US8", "Member", "A normal member cannot edit the group", 1, e.code); }
try { await updateDoc(doc(L, "groups/g4"), { title: "Too late", time: iso(past), t: past }); ck("RS-14", "US8", "Leader", "Editing the meeting time to a past date is refused", 0); }
catch (e) { ck("RS-14", "US8", "Leader", "Editing the meeting time to a past date is refused", 1, e.code); }
await seed();
try { await updateDoc(doc(L, "groups/g4"), { max: 1 }); ck("RS-15", "US8", "Leader", "Maximum members cannot be lower than the current members", 0); }
catch (e) { ck("RS-15", "US8", "Leader", "Maximum members cannot be lower than the current members", 1, e.code); }
try { await updateDoc(doc(L, "groups/g4"), { max: 2 }); ck("RS-16", "US8", "Leader", "Maximum members equal to the current members is allowed", 1); }
catch (e) { ck("RS-16", "US8", "Leader", "Maximum members equal to the current members is allowed", 0, e.code); }
try { await updateDoc(doc(L, "groups/g4"), { closed: true }); ck("RS-17", "US8", "Leader", "The leader can close the group", 1); }
catch (e) { ck("RS-17", "US8", "Leader", "The leader can close the group", 0, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { closed: true }); ck("RS-18", "US8", "Member", "A normal member cannot close the group", 0); }
catch (e) { ck("RS-18", "US8", "Member", "A normal member cannot close the group", 1, e.code); }
try { await updateDoc(doc(N, "groups/g4"), { closed: true }); ck("RS-19", "US8", "Non-member", "A non-member cannot close the group", 0); }
catch (e) { ck("RS-19", "US8", "Non-member", "A non-member cannot close the group", 1, e.code); }

/* ---------- join rules ---------- */
await seed();
try { await updateDoc(doc(N, "groups/g4"), { members: ["L", "M", "N"] }); ck("RS-20", "US5", "Non-member", "A student can join a group that has a free seat", 1); }
catch (e) { ck("RS-20", "US5", "Non-member", "A student can join a group that has a free seat", 0, e.code); }
await seed();
try { await updateDoc(doc(N, "groups/g3"), { members: ["L", "M", "N"] }); ck("RS-21", "US5", "Non-member", "Joining a full group is refused", 0); }
catch (e) { ck("RS-21", "US5", "Non-member", "Joining a full group is refused", 1, e.code); }
try { await updateDoc(doc(N, "groups/g2"), { members: ["L", "M", "N"] }); ck("RS-22", "US8", "Non-member", "Joining a closed group is refused", 0); }
catch (e) { ck("RS-22", "US8", "Non-member", "Joining a closed group is refused", 1, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["L", "M", "M"] }); ck("RS-23", "US5", "Member", "A member cannot add the same UID twice", 0); }
catch (e) { ck("RS-23", "US5", "Member", "A member cannot add the same UID twice", 1, e.code); }
try { await updateDoc(doc(N, "groups/g4"), { members: ["L", "M", "N", "M"] }); ck("RS-24", "US5", "Non-member", "A join request that adds more than one UID is refused", 0); }
catch (e) { ck("RS-24", "US5", "Non-member", "A join request that adds more than one UID is refused", 1, e.code); }

/* ---------- US9 : announcements ---------- */
await seed();
try { await addDoc(collection(L, "groups/g1/notes"), { text: "Session moved to 7 PM", author: "L", authorName: "Leader One", at: serverTimestamp() }); ck("RS-25", "US9", "Leader", "The leader can post an announcement", 1); }
catch (e) { ck("RS-25", "US9", "Leader", "The leader can post an announcement", 0, e.code); }
await seed();
try { await addDoc(collection(M, "groups/g1/notes"), { text: "A member tries to post", author: "M", at: new Date() }); ck("RS-26", "US9", "Member", "A normal member cannot post an announcement", 0); }
catch (e) { ck("RS-26", "US9", "Member", "A normal member cannot post an announcement", 1, e.code); }
try { await addDoc(collection(N, "groups/g1/notes"), { text: "A non-member tries to post", author: "N", at: new Date() }); ck("RS-27", "US9", "Non-member", "A non-member cannot post an announcement", 0); }
catch (e) { ck("RS-27", "US9", "Non-member", "A non-member cannot post an announcement", 1, e.code); }
try { await addDoc(collection(L, "groups/g1/notes"), { text: "", author: "L", at: new Date() }); ck("RS-28", "US9", "Leader", "An empty announcement is refused", 0); }
catch (e) { ck("RS-28", "US9", "Leader", "An empty announcement is refused", 1, e.code); }
try { await addDoc(collection(L, "groups/g1/notes"), { text: "Fake time", author: "L", at: new Date(2020, 1, 1) }); ck("RS-29", "US9", "Leader", "An announcement with a hand-made date is refused (server time only)", 0); }
catch (e) { ck("RS-29", "US9", "Leader", "An announcement with a hand-made date is refused (server time only)", 1, e.code); }
try { await setDoc(doc(M, "groups/g1/notes/x1"), { text: "Direct write", author: "M", at: new Date() }); ck("RS-30", "US9", "Member", "A member cannot create an announcement with a chosen document ID", 0); }
catch (e) { ck("RS-30", "US9", "Member", "A member cannot create an announcement with a chosen document ID", 1, e.code); }
await seed();
try { await deleteDoc(doc(L, "groups/g1/notes/none")); ck("RS-31", "US9", "Leader", "Announcements cannot be deleted through the client", 0); }
catch (e) { ck("RS-31", "US9", "Leader", "Announcements cannot be deleted through the client", 1, e.code); }

/* ---------- US10 : leaving cannot touch the other members ---------- */
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["L"] }); ck("RS-37", "US10", "Member", "A member leaves and only her own UID is removed", 1); }
catch (e) { ck("RS-37", "US10", "Member", "A member leaves and only her own UID is removed", 0, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["M"] }); ck("RS-38", "US10", "Member", "Leaving cannot remove another member at the same time", 0); }
catch (e) { ck("RS-38", "US10", "Member", "Leaving cannot remove another member at the same time", 1, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["L", "N"] }); ck("RS-39", "US10", "Member", "Leaving cannot add a new student to the group", 0); }
catch (e) { ck("RS-39", "US10", "Member", "Leaving cannot add a new student to the group", 1, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["L", "N", "M"] }); ck("RS-40", "US10", "Member", "Leaving cannot swap her UID for another student", 0); }
catch (e) { ck("RS-40", "US10", "Member", "Leaving cannot swap her UID for another student", 1, e.code); }
await seed();
try { await updateDoc(doc(M, "groups/g4"), { members: ["N"] }); ck("RS-41", "US10", "Member", "Leaving with fewer members and without the leader is refused", 0); }
catch (e) { ck("RS-41", "US10", "Member", "Leaving with fewer members and without the leader is refused", 1, e.code); }

/* ---------- US8 : the leader removes one member and cannot change the rest ---------- */
await seed();
try { await updateDoc(doc(L, "groups/g4"), { members: ["L"] }); ck("RS-42", "US6", "Leader", "The leader removes one member at a time", 1); }
catch (e) { ck("RS-42", "US6", "Leader", "The leader removes one member at a time", 0, e.code); }
await seed();
try { await updateDoc(doc(L, "groups/g4"), { members: ["L", "N"] }); ck("RS-43", "US6", "Leader", "The leader cannot add a student through the members list", 0); }
catch (e) { ck("RS-43", "US6", "Leader", "The leader cannot add a student through the members list", 1, e.code); }
await seed();
try { await updateDoc(doc(L, "groups/g4"), { members: [] }); ck("RS-44", "US6", "Leader", "The leader cannot remove herself from the group", 0); }
catch (e) { ck("RS-44", "US6", "Leader", "The leader cannot remove herself from the group", 1, e.code); }

/* ---------- US20 : a closed group cannot be reopened in this version ---------- */
await seed();
try { await updateDoc(doc(L, "groups/g2"), { closed: false }); ck("RS-45", "US8", "Leader", "A closed group cannot be reopened (US20 is not implemented)", 0); }
catch (e) { ck("RS-45", "US8", "Leader", "A closed group cannot be reopened (US20 is not implemented)", 1, e.code); }
await seed();
try { await updateDoc(doc(L, "groups/g2"), { closed: false, title: "Reopened" }); ck("RS-46", "US8", "Leader", "Reopening a closed group is refused even together with an edit", 0); }
catch (e) { ck("RS-46", "US8", "Leader", "Reopening a closed group is refused even together with an edit", 1, e.code); }
await seed();
await updateDoc(doc(L, "groups/g4"), { closed: true });
try { await updateDoc(doc(N, "groups/g4"), { members: ["L", "M", "N"] }); ck("RS-47", "US8", "Non-member", "A closed group refuses a new member even when a seat is free", 0); }
catch (e) { ck("RS-47", "US8", "Non-member", "A closed group refuses a new member even when a seat is free", 1, e.code); }

/* ---------- US17 : a session that already started cannot accept a join ---------- */
await seed();
await env.withSecurityRulesDisabled(async c => {
  const db = c.firestore();
  await setDoc(doc(db, "groups/g5"), base({ id: "g5", title: "Past session", time: iso(past), t: past, members: ["L"], max: 4 }));
});
try { await updateDoc(doc(N, "groups/g5"), { members: ["L", "N"] }); ck("RS-48", "US17", "Non-member", "Joining a group whose session already passed is refused", 0); }
catch (e) { ck("RS-48", "US17", "Non-member", "Joining a group whose session already passed is refused", 1, e.code); }
try { await updateDoc(doc(L, "groups/g5"), { title: "Late edit", course: "CS 311", desc: "x", max: 4, time: iso(past), t: past }); ck("RS-49", "US17", "Leader", "A group whose session passed keeps its old meeting time", 0); }
catch (e) { ck("RS-49", "US17", "Leader", "A group whose session passed keeps its old meeting time", 1, e.code); }

/* ---------- read rules ---------- */
await seed();
try { await getDoc(doc(X, "groups/g1")); ck("RS-32", "US1", "Unauthorized", "A non-university account cannot read the groups", 0); }
catch (e) { ck("RS-32", "US1", "Unauthorized", "A non-university account cannot read the groups", 1, e.code); }
try { await getDoc(doc(N, "groups/g1")); ck("RS-33", "US4", "Non-member", "A signed student can read the groups list", 1); }
catch (e) { ck("RS-33", "US4", "Non-member", "A signed student can read the groups list", 0, e.code); }
try { await getDoc(doc(X, "groups/g1/notes/none")); ck("RS-34", "US9", "Unauthorized", "A non-university account cannot read the announcements", 0); }
catch (e) { ck("RS-34", "US9", "Unauthorized", "A non-university account cannot read the announcements", 1, e.code); }

/* ---------- users ---------- */
try { await setDoc(doc(M, "users/L"), { name: "Hacked", email: "member@university.edu.sa", major: "CS", courses: [] }); ck("RS-35", "US2", "Member", "A student cannot write another student's profile", 0); }
catch (e) { ck("RS-35", "US2", "Member", "A student cannot write another student's profile", 1, e.code); }
try { await setDoc(doc(M, "users/M"), { name: "Member Two", email: "member@university.edu.sa", major: "IS", courses: ["CS 311"] }); ck("RS-36", "US2", "Member", "A student can write her own profile", 1); }
catch (e) { ck("RS-36", "US2", "Member", "A student can write her own profile", 0, e.code); }

await env.cleanup();
const pass = rs.filter(r => r.result === "Pass").length;
console.log("\n" + pass + " / " + rs.length + " security rule tests passed");
mkdirSync("shots", { recursive: true });
writeFileSync("shots/rules_results.json", JSON.stringify({ ran_at: new Date().toISOString(), results: rs }, null, 1));
