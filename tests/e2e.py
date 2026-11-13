import json, re, sys, time, urllib.request
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

BU = "http://localhost:5000"
PJ = "demo-studymate"
SH = sys.argv[1] if len(sys.argv) > 1 else "shots"

def dt(d, h=18, m=0):
    return (datetime.now() + timedelta(days=d)).strftime("%Y-%m-%dT%H:%M")
rs = []
er = []
nw = []

def rq(m, u, d=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(d).encode() if d else None, headers={"Content-Type": "application/json", "Authorization": "Bearer owner"})
    return urllib.request.urlopen(r).read()

def rd():
    rq("DELETE", f"http://localhost:8080/emulator/v1/projects/{PJ}/databases/(default)/documents")
    rq("DELETE", f"http://localhost:9099/emulator/v1/projects/{PJ}/accounts")

def ck(id, us, nm, ok, nt=""):
    rs.append({"id": id, "us": us, "name": nm, "result": "Pass" if ok else "Fail", "note": nt})
    print(("PASS " if ok else "FAIL ") + id + " " + nm + (" | " + nt if nt else ""))

def pg(br, w=1280, h=800):
    c = br.new_context(viewport={"width": w, "height": h})
    p = c.new_page()
    p.on("pageerror", lambda e: er.append(str(e)))
    p.on("console", lambda m: (nw if "Failed to load resource" in m.text else er).append(m.text) if m.type == "error" else None)
    return c, p

def iz(p):
    return re.search(r"/(index\.html)?$", p.url) is not None and p.query_selector("h1").inner_text() == "Log in"

def go(p, u, tries=3):
    # The page is retried when the emulator is slow: a slow load is not a product bug.
    for i in range(tries):
        try:
            p.goto(BU + "/" + u, timeout=45000)
            p.wait_for_load_state("load", timeout=45000)
            return
        except Exception:
            if i == tries - 1:
                raise
            p.wait_for_timeout(2000)

def ms(p):
    p.wait_for_selector("#ms.er, #ms.ok", timeout=25000)
    return p.inner_text("#ms")

def su(p, nm, em, pw):
    go(p, "signup.html")
    p.fill("#nm", nm); p.fill("#em", em); p.fill("#pw", pw)
    p.click("#bt")

def li(p, em, pw):
    go(p, "index.html")
    p.fill("#em", em); p.fill("#pw", pw)
    p.click("#bt")
    p.wait_for_url("**/groups.html*")

def pf(p, mj, cs):
    go(p, "profile.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#mj", mj)
    for c in p.query_selector_all("#cs input"):
        if c.is_checked() != (c.get_attribute("value") in cs):
            c.click()
    p.click("#bt")
    return ms(p)

def cg(p, tt, co, ds, mx, tm):
    go(p, "create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", tt)
    if co: p.select_option("#co", co)
    p.fill("#ds", ds)
    p.fill("#mx", str(mx))
    if tm: p.fill("#tm", tm)
    p.click("#bt")

def gid(p, tt):
    go(p, "groups.html")
    p.wait_for_selector("#ld", state="hidden")
    for c in p.query_selector_all(".cd"):
        if c.query_selector("h3").inner_text() == tt:
            return c.query_selector("a").get_attribute("href").split("id=")[1]

def sc(p, n, fp=False):
    p.screenshot(path=f"{SH}/{n}.png", full_page=fp)

rd()
with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-extensions", "--js-flags=--max-old-space-size=256"])
    c1, p = pg(br)

    go(p, "groups.html")
    p.wait_for_function("document.querySelector('h1') && document.querySelector('h1').textContent == 'Log in'"); p.wait_for_load_state("load")
    ck("TC-01", "US1", "Opening the groups page without login goes back to the login page", iz(p))

    su(p, "Test Gmail", "student@gmail.com", "pass123")
    t = ms(p)
    n = json.loads(rq("POST", f"http://localhost:9099/identitytoolkit.googleapis.com/v1/projects/{PJ}/accounts:query", {}) or b"{}")
    ck("TC-02", "US1", "Sign up with a non-university email is refused", "Only university emails" in t and p.url.endswith("signup.html") and int(n.get("recordsCount", 0)) == 0, t)
    sc(p, "01_signup_refused")

    su(p, "Sara Test", "sara@university.edu.sa", "123")
    t = ms(p)
    ck("TC-03", "US1", "Sign up with a short password shows an error", "at least 6" in t, t)

    su(p, "Sara Test", "sara@university.edu.sa", "pass123")
    p.wait_for_url("**/profile.html*")
    p.wait_for_selector("#fm", state="visible")
    ck("TC-04", "US1", "Sign up with a university email creates the account and opens the profile page", "profile.html" in p.url)
    sc(p, "02_new_profile")

    p.click("text=Log out"); p.wait_for_function("document.querySelector('h1') && document.querySelector('h1').textContent == 'Log in'"); p.wait_for_load_state("load")
    su(p, "Sara Again", "sara@university.edu.sa", "pass123")
    t = ms(p)
    ck("TC-05", "US1", "Sign up again with the same email shows an error", "already has an account" in t, t)

    go(p, "index.html")
    p.fill("#em", "sara@university.edu.sa"); p.fill("#pw", "wrongpass"); p.click("#bt")
    t = ms(p)
    time.sleep(1)
    ck("TC-06", "US1", "Wrong password shows an error and the user stays on the login page", "Wrong email or password" in t and iz(p), t)
    sc(p, "03_login_wrong_password")

    go(p, "index.html")
    p.fill("#em", "sara@gmail.com"); p.fill("#pw", "pass123"); p.click("#bt")
    t = ms(p)
    ck("TC-07", "US1", "Login with a non-university email is refused", "university email" in t and iz(p), t)

    li(p, "sara@university.edu.sa", "pass123")
    ck("TC-08", "US1", "Correct login opens the groups list page", "groups.html" in p.url)

    go(p, "profile.html"); p.wait_for_selector("#fm", state="visible")
    p.fill("#mj", ""); p.click("#bt"); t = ms(p)
    ck("TC-09", "US2", "Profile is not saved when the major is empty", "enter your major" in t, t)

    p.fill("#mj", "Computer Science")
    for c in p.query_selector_all("#cs input:checked"): c.click()
    p.click("#bt"); t = ms(p)
    ck("TC-10", "US2", "Profile is not saved when no course is chosen", "at least one course" in t, t)
    sc(p, "04_profile_no_course")

    ip = p.query_selector_all("#cs input")
    ck("TC-11", "US2", "Courses are picked from the list (checkboxes), not typed", len(ip) == 10 and all(i.get_attribute("type") == "checkbox" for i in ip), f"{len(ip)} courses in the list")

    t = pf(p, "Computer Science", ["CS 388T", "CS 281"])
    sc(p, "05_profile_saved", True)
    p.reload(); p.wait_for_selector("#fm", state="visible")
    sv = [i.get_attribute("value") for i in p.query_selector_all("#cs input:checked")]
    ck("TC-12", "US2", "Saved profile data appears again when the page is opened", "saved" in t and p.input_value("#mj") == "Computer Science" and sorted(sv) == ["CS 281", "CS 388T"], f"courses: {sv}")

    pf(p, "Software Engineering", ["CS 388T", "CS 361"])
    p.reload(); p.wait_for_selector("#fm", state="visible")
    sv = [i.get_attribute("value") for i in p.query_selector_all("#cs input:checked")]
    ck("TC-13", "US2", "Editing the profile saves the new major and courses", p.input_value("#mj") == "Software Engineering" and sorted(sv) == ["CS 361", "CS 388T"], f"courses: {sv}")

    cg(p, "", "CS 388T", "", 4, dt(2)); t = ms(p)
    ck("TC-14", "US3", "Group is not created when the title is empty", "group title" in t, t)
    sc(p, "06_create_empty_title")
    cg(p, "Sprint review prep", "", "", 4, dt(2)); t = ms(p)
    ck("TC-15", "US3", "Group is not created when no course is chosen", "choose a course" in t, t)
    cg(p, "Sprint review prep", "CS 388T", "", 4, ""); t = ms(p)
    ck("TC-16", "US3", "Group is not created when the meeting time is empty", "meeting time" in t, t)
    cg(p, "Sprint review prep", "CS 388T", "", 1, dt(2)); t = ms(p)
    ck("TC-17", "US3", "Group is not created when maximum members is 1", "greater than 1" in t, t)
    sc(p, "07_create_max_one")
    n = len(json.loads(urllib.request.urlopen(urllib.request.Request(f"http://localhost:8080/v1/projects/{PJ}/databases/(default)/documents/groups", headers={"Authorization": "Bearer owner"})).read()).get("documents", []))
    ck("TC-18", "US3", "No group was saved by the four wrong tries above", n == 0, f"groups in database: {n}")

    cg(p, "Agile midterm revision", "CS 388T", "We revise the Scrum chapters together.", 3, dt(2))
    p.wait_for_url("**/groups.html*"); p.wait_for_selector("#ld", state="hidden")
    tt = [h.inner_text() for h in p.query_selector_all(".cd h3")]
    ck("TC-19", "US3", "New group appears in the groups list right after it is created", "Agile midterm revision" in tt and "created" in p.inner_text("#ms"))
    sc(p, "08_group_created")
    cg(p, "Web project help", "CS 361", "", 2, dt(1, 16, 30))
    p.wait_for_url("**/groups.html*")

    c2, q = pg(br)
    su(q, "Lama Test", "lama@university.edu.sa", "pass123")
    q.wait_for_url("**/profile.html*")
    go(q, "create.html"); q.wait_for_selector("#np", state="visible")
    ck("TC-20", "US3", "A student with no courses is asked to add her courses before creating a group", "add your courses first" in q.inner_text("#np"))
    pf(q, "Information Systems", ["CS 281", "CS 388T", "CS 361"])
    cg(q, "Database quiz practice", "CS 281", "SQL questions", 5, dt(5, 10, 0))
    q.wait_for_url("**/groups.html*")

    go(p, "groups.html"); p.wait_for_selector("#ld", state="hidden")
    cd = p.query_selector_all(".cd")
    ok = len(cd) == 3 and all(c.query_selector(".tg") and c.query_selector("h3") and c.query_selector(".sm") and c.query_selector(".st") for c in cd)
    f1 = [c.inner_text().replace("\n", " / ") for c in cd]
    ck("TC-21", "US4", "List shows course code, title, meeting time and free seats of every group", ok and "2 free seats of 3" in " ".join(f1), f1[0])
    sc(p, "09_groups_list", True)

    p.select_option("#fl", "CS 388T"); time.sleep(0.3)
    tg = [c.inner_text() for c in p.query_selector_all(".cd .tg")]
    ck("TC-22", "US4", "Choosing a course code shows only the groups of that course", tg == ["CS 388T"], f"shown: {tg}")
    sc(p, "10_filter_course")
    p.select_option("#fl", "CS 211"); time.sleep(0.3)
    t = p.inner_text("#nt")
    ck("TC-23", "US4", "A clear message is shown when the chosen course has no group", "no study groups for CS 211" in t and not p.query_selector_all(".cd"), t)
    sc(p, "11_filter_empty")
    p.select_option("#fl", ""); time.sleep(0.3)
    ck("TC-24", "US4", "Choosing All courses shows all the groups again", len(p.query_selector_all(".cd")) == 3)

    g1 = gid(p, "Agile midterm revision")
    g2 = gid(p, "Web project help")
    go(p, "group.html?id=" + g1); p.wait_for_selector("#bx", state="visible")
    ck("TC-25", "US5", "The leader does not see a join button on her own group", not p.is_visible("#bt") and "leader" in p.inner_text("#in"))

    go(q, "group.html?id=" + g1); q.wait_for_selector("#bx", state="visible")
    b4 = q.inner_text("#st")
    sc(q, "12_group_before_join")
    q.click("#bt"); t = ms(q); time.sleep(0.5)
    af = q.inner_text("#st")
    ck("TC-26", "US5", "Joining a group with a free seat works and free seats go down by one", "joined" in t and b4.startswith("2 of 3") and af.startswith("1 of 3"), f"before: {b4} / after: {af}")
    ck("TC-27", "US5", "After joining, the join button is hidden so she cannot join twice", not q.is_visible("#bt") and "member" in q.inner_text("#in"))
    sc(q, "13_group_after_join")

    r = q.evaluate("""id => db.collection('groups').doc(id).update({members: firebase.firestore.FieldValue.arrayUnion(au.currentUser.uid)}).then(() => 'saved').catch(e => e.code)""", g1)
    ck("TC-28", "US5", "A second join sent directly to Firebase (not from the page) is refused", r == "permission-denied", r)

    q.evaluate("id => db.runTransaction(t => t.get(db.collection('groups').doc(id)).then(() => {}))", g2)
    go(q, "group.html?id=" + g2); q.wait_for_selector("#bx", state="visible")
    q.click("#bt"); ms(q); time.sleep(0.5)

    c3, w = pg(br)
    su(w, "Nora Test", "nora@university.edu.sa", "pass123")
    w.wait_for_url("**/profile.html*", timeout=60000)
    go(w, "groups.html"); w.wait_for_selector("#ld", state="hidden")
    fu = [c.inner_text() for c in w.query_selector_all(".cd") if "Web project help" in c.inner_text()][0]
    go(w, "group.html?id=" + g2); w.wait_for_selector("#bx", state="visible")
    ck("TC-29", "US5", "The join button is not shown when the group is full", not w.is_visible("#bt") and "full" in w.inner_text("#in") and "Full" in fu, w.inner_text("#st"))
    sc(w, "14_group_full")
    r = w.evaluate("""id => db.collection('groups').doc(id).update({members: firebase.firestore.FieldValue.arrayUnion(au.currentUser.uid)}).then(() => 'saved').catch(e => e.code)""", g2)
    ck("TC-30", "US5", "Joining a full group directly through Firebase is refused", r == "permission-denied", r)

    g3 = gid(w, "Database quiz practice")
    c4, x = pg(br)
    su(x, "Hind Test", "hind@university.edu.sa", "pass123")
    x.wait_for_url("**/profile.html*", timeout=60000)
    for i in range(3):
        cz, z = pg(br)
        su(z, f"Extra {i}", f"extra{i}@university.edu.sa", "pass123")
        z.wait_for_url("**/profile.html*", timeout=60000)
        go(z, "group.html?id=" + g3); z.wait_for_selector("#bx", state="visible", timeout=45000)
        z.click("#bt"); ms(z); cz.close()
    go(w, "group.html?id=" + g3); w.wait_for_selector("#bx", state="visible")
    go(x, "group.html?id=" + g3); x.wait_for_selector("#bx", state="visible")
    s0 = w.inner_text("#st")
    w.evaluate("document.getElementById('bt').click()"); x.evaluate("document.getElementById('bt').click()")
    t1 = ms(w); t2 = ms(x); time.sleep(0.5)
    jn = [t1, t2].count("You joined the group.")
    ck("TC-31", "US5", "Two students click join on the last seat at the same time: only one joins", s0.startswith("1 of 5") and jn == 1 and "full now" in (t1 + t2), f"{t1} | {t2}")
    c4.close()

    c5, y = pg(br)
    go(y, "signup.html")
    rq("POST", f"http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo-key", {"email": "out@gmail.com", "password": "pass123"})
    r = y.evaluate("""() => au.signInWithEmailAndPassword('out@gmail.com','pass123').then(() => db.collection('groups').get()).then(() => 'read').catch(e => e.code)""")
    ck("TC-32", "US1", "Firebase rules refuse a non-university account even if it skips the sign up page", r == "permission-denied", r)
    c5.close()

    c6, m = pg(br, 390, 844)
    for u, n in [("index.html", "15_phone_login"), ("groups.html", "16_phone_groups"), ("create.html", "17_phone_create"), ("group.html?id=" + g1, "18_phone_group")]:
        if u == "groups.html":
            m.fill("#em", "sara@university.edu.sa"); m.fill("#pw", "pass123"); m.click("#bt"); m.wait_for_url("**/groups.html*")
        else:
            go(m, u)
        m.wait_for_load_state("load"); time.sleep(1.5)
        if "15" in n:
            pass
        sw = m.evaluate("document.documentElement.scrollWidth")
        if sw > 390: ck("TC-33", "DoD", "Page fits a phone screen", False, u)
        sc(m, n, True)
    ck("TC-33", "DoD", "All pages fit a phone screen (390 px) with no side scrolling", not any(r["id"] == "TC-33" for r in rs))
    m.wait_for_timeout(300)

    go(p, "index.html"); p.wait_for_url("**/groups.html*"); p.wait_for_selector("#ld", state="hidden")
    sc(p, "19_groups_after_joins", True)
    go(p, "signup.html"); sc(p, "20_signup_page")
    p.click("text=Log out") if p.is_visible("text=Log out") else None
    br.close()

er2 = [e for e in er if "permission" not in e.lower() and "PERMISSION_DENIED" not in e]
ck("TC-34", "DoD", "No JavaScript errors in the browser console during all tests", not er2, f"{len(er2)} JS errors; {len(nw)} expected 400/403 network messages from the refused login, sign up and rule tests")
json.dump({"results": rs, "js_errors": er2, "all_console_errors": er, "network_msgs": nw}, open(f"{SH}/../results.json", "w"), indent=1)
_ok = sum(r["result"] == "Pass" for r in rs)
print(_ok, "/", len(rs), "passed")
sys.exit(0 if _ok == len(rs) and _ok > 0 else 1)
