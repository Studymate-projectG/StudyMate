import json, re, sys, time, urllib.request
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

BU = "http://localhost:5000"
PJ = "demo-studymate"
SH = sys.argv[1] if len(sys.argv) > 1 else "shots"
rs = []
er = []
nw = []


def dt(days, hours=18, minutes=0):
    return (datetime.now() + timedelta(days=days, hours=hours, minutes=minutes)).strftime("%Y-%m-%dT%H:%M")


def rq(m, u, d=None):
    r = urllib.request.Request(u, method=m, data=json.dumps(d).encode() if d else None,
                               headers={"Content-Type": "application/json", "Authorization": "Bearer owner"})
    return urllib.request.urlopen(r).read()


def cnt(col="groups"):
    u = f"http://localhost:8080/v1/projects/{PJ}/databases/(default)/documents/{col}"
    return len(json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": "Bearer owner"})).read()).get("documents", []))


def ck(i, us, nm, ok, nt=""):
    rs.append({"id": i, "us": us, "name": nm, "result": "Pass" if ok else "Fail", "note": nt})
    print(("PASS " if ok else "FAIL ") + i + " " + nm + (" | " + nt if nt else ""))


def pg(br, w=1280, h=800):
    c = br.new_context(viewport={"width": w, "height": h})
    p = c.new_page()
    p.on("pageerror", lambda e: er.append("pageerror: " + str(e)))
    p.on("console", lambda m: (nw if "Failed to load resource" in m.text else er).append(m.text) if m.type == "error" else None)
    return c, p


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


def su(p, nm, em, pw="pass123"):
    go(p, "signup.html")
    p.fill("#nm", nm)
    p.fill("#em", em)
    p.fill("#pw", pw)
    p.click("#bt")


def li(p, em, pw="pass123"):
    go(p, "index.html")
    p.fill("#em", em)
    p.fill("#pw", pw)
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
    if co:
        p.select_option("#co", co)
    p.fill("#ds", ds)
    p.fill("#mx", str(mx))
    if tm:
        p.fill("#tm", tm)
    p.click("#bt")


def gid(p, tt):
    go(p, "groups.html")
    p.wait_for_selector("#ld", state="hidden")
    for c in p.query_selector_all(".cd"):
        if c.query_selector("h3").inner_text() == tt:
            return c.query_selector("a").get_attribute("href").split("id=")[1]
    return None


def sc(p, n, full=False):
    p.screenshot(path=f"{SH}/{n}.png", full_page=full)


def new(br, nm, em, courses=("CS 388T", "CS 281")):
    c, p = pg(br)
    su(p, nm, em)
    p.wait_for_url("**/profile.html*")
    pf(p, "Computer Science", list(courses))
    return c, p


with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-extensions", "--js-flags=--max-old-space-size=256"])

    # ---------- accounts and data ----------
    ca, a = new(br, "Abeer Leader", "abeer@university.edu.sa")
    cb, b = new(br, "Basma Member", "basma@university.edu.sa")
    cc, c3 = new(br, "Carmen Other", "carmen@university.edu.sa")

    cg(a, "Algorithms revision", "CS 388T", "Solve the exercises of chapter 4.", 4, dt(0, 3))
    a.wait_for_url("**/groups.html*")
    cg(a, "Far session group", "CS 388T", "Session next week.", 3, dt(6))
    a.wait_for_url("**/groups.html*")
    cg(a, "Past demo group", "CS 281", "", 4, dt(2))
    a.wait_for_url("**/groups.html*")
    cg(a, "Missed session group", "CS 388T", "Its session already ended.", 4, dt(0, 1))
    a.wait_for_url("**/groups.html*")
    g5 = gid(a, "Missed session group")

    g1 = gid(a, "Algorithms revision")
    g2 = gid(a, "Far session group")
    g3 = gid(a, "Past demo group")

    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#bx", state="visible")
    b.click("#bt")
    t = ms(b)
    b.wait_for_timeout(800)

    go(c3, "group.html?id=" + g3)
    c3.wait_for_selector("#bx", state="visible")
    c3.click("#bt")
    ms(c3)
    c3.wait_for_timeout(600)

    # ---------- US7 My Groups ----------
    go(a, "mine.html")
    a.wait_for_selector("#ld", state="hidden")
    cr = [h.inner_text() for h in a.query_selector_all("#cr .cd h3")]
    ck("P3-01", "US7", "My Groups page lists the groups the student created",
       sorted(cr) == ["Algorithms revision", "Far session group", "Missed session group", "Past demo group"], str(cr))
    sc(a, "US07_MyGroups", True)

    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    jn = [h.inner_text() for h in b.query_selector_all("#jn .cd h3")]
    mk = b.inner_text("#jn .cd") if jn else ""
    ck("P3-02", "US7", "My Groups page lists the groups the student joined", jn == ["Algorithms revision"] and "CS 388T" in mk and "Meeting:" in mk, str(jn))

    a.query_selector_all("#cr .cd a")[0]
    go(b, "mine.html")
    b.wait_for_selector("#jn .cd a")
    b.click("#jn .cd a")
    b.wait_for_url("**/group.html*")
    b.wait_for_selector("#bx", state="visible")
    ck("P3-03", "US7", "Opening the group details from My Groups works", g1 in b.url and b.inner_text("#tt") == "Algorithms revision")

    gm = [x.inner_text() for x in a.query_selector_all("#cr .cd")]
    ck("P3-04b", "US7", "Each card shows the course code, the title and the meeting time",
       len(gm) == 4 and all(("CS 388T" in x or "CS 281" in x) and "Meeting:" in x for x in gm), str(len(gm)) + " cards")

    ck("P3-04", "US7", "Groups of other students do not appear in My Groups",
       "Far session group" not in jn and "Past demo group" not in jn)

    ce, e = pg(br)
    su(e, "Dana Quiet", "dana@university.edu.sa")
    e.wait_for_url("**/profile.html*")
    go(e, "mine.html")
    e.wait_for_selector("#ld", state="hidden")
    d = e
    nt = d.inner_text("#nt")
    ck("P3-05", "US7", "A student with no group sees a clear message and a link to the groups list",
       "not in any study group yet" in nt and d.query_selector("#nt a") is not None, nt)
    sc(d, "US07_MyGroups_Empty")

    # ---------- US10 Leave a group ----------
    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#bx", state="visible")
    s0 = b.inner_text("#st")
    lb = b.is_visible("#lv")
    sc(b, "US10_LeaveGroup_before", True)
    b.click("#lv")
    t = ms(b)
    b.wait_for_timeout(800)
    s1 = b.inner_text("#st")
    ck("P3-07", "US10", "A member sees the Leave button and can leave the group",
       lb and "left the group" in t, t)
    ck("P3-08", "US10", "After leaving, the free seats number goes up by one",
       s0.startswith("2 of 4") and s1.startswith("3 of 4"), f"before: {s0} / after: {s1}")
    sc(b, "US10_LeaveGroup")

    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    ck("P3-09", "US10", "The group no longer shows under My Groups after leaving",
       b.query_selector_all("#jn .cd") == [] and "not joined any group" in b.inner_text("#ej"))

    go(a, "group.html?id=" + g1)
    a.wait_for_selector("#bx", state="visible")
    ck("P3-10", "US10", "The leader does not see the Leave button on her own group", not a.is_visible("#lv"))

    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#bx", state="visible")
    r = b.evaluate("id => db.collection('groups').doc(id).update({members: firebase.firestore.FieldValue.arrayRemove(au.currentUser.uid)}).then(() => 'saved').catch(e => e.code)", g1)
    ck("P3-11", "US10", "Leaving twice (a second request sent directly to Firestore) is refused", r == "permission-denied", r)
    r = b.evaluate("id => db.collection('groups').doc(id).update({members: ['x']}).then(() => 'saved').catch(e => e.code)", g1)
    ck("P3-12", "US10", "A student cannot leave a group she is not a member of (direct request)", r == "permission-denied", r)
    r = a.evaluate("id => db.collection('groups').doc(id).update({members: []}).then(() => 'saved').catch(e => e.code)", g1)
    ck("P3-13", "US10", "The leader cannot leave her own group through a direct Firestore request", r == "permission-denied", r)

    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#bx", state="visible")
    b.click("#bt")
    t = ms(b)
    b.wait_for_timeout(800)
    ck("P3-13b", "US5", "A student who left a group can join it again while a seat is free",
       "joined the group" in t and b.inner_text("#st").startswith("2 of 4"), t)

    # ---------- US17 Past meeting time ----------
    n0 = cnt()
    cg(a, "Past time group", "CS 388T", "", 4, dt(-2))
    t = ms(a)
    ck("P3-14", "US17", "Creating a group with a meeting time in the past is refused in the page",
       "in the past" in t, t)
    sc(a, "US17_PastTime")
    nowt = datetime.now().strftime("%Y-%m-%dT%H:%M")
    cg(a, "Now time group", "CS 388T", "", 4, nowt)
    t = ms(a)
    ck("P3-15", "US17", "Creating a group with the current time (same minute) is refused", "in the past" in t, t)
    ck("P3-16", "US17", "No group was saved in Firestore by the two refused tries", cnt() == n0, f"groups in database: {cnt()}")
    cg(a, "Future time group", "CS 388T", "", 4, dt(3))
    a.wait_for_url("**/groups.html*")
    a.wait_for_selector("#ld", state="hidden")
    ck("P3-17", "US17", "Creating a group with a correct future time is accepted", "created" in a.inner_text("#ms"), a.inner_text("#ms"))
    g4 = gid(a, "Future time group")

    r = a.evaluate("t => db.collection('groups').add({title: 'Direct past', course: 'CS 388T', desc: '', max: 4, time: t, leader: au.currentUser.uid, leaderName: 'Abeer Leader', members: [au.currentUser.uid], closed: false, created: firebase.firestore.FieldValue.serverTimestamp()}).then(() => 'saved').catch(e => e.code)", dt(-5))
    ck("P3-18", "US17", "A group with a past time sent directly to Firestore is refused (the check is not only in JavaScript)", r == "permission-denied", r)
    ck("P3-19", "US17", "The direct refused attempt did not create a document", gid(a, "Direct past") is None)

    # ---------- US6 Members ----------
    go(b, "group.html?id=" + g4)
    b.wait_for_selector("#bx", state="visible")
    b.click("#bt")
    ms(b)
    b.wait_for_timeout(600)
    go(c3, "group.html?id=" + g4)
    c3.wait_for_selector("#bx", state="visible")
    c3.click("#bt")
    ms(c3)
    c3.wait_for_timeout(600)

    go(a, "group.html?id=" + g4)
    a.wait_for_selector("#mb .mr")
    nmb = [x.inner_text() for x in a.query_selector_all("#mb .mr")]
    ck("P3-20", "US6", "The members list shows every member of the group by name",
       len(nmb) == 3 and "Abeer Leader (leader)" in nmb[0] and "Basma Member" in " ".join(nmb), str(nmb))
    ck("P3-21", "US6", "Only the leader sees the Remove button next to the other members",
       len(a.query_selector_all("#mb .xm")) == 2)
    sc(a, "US06_Members", True)

    go(b, "group.html?id=" + g4)
    b.wait_for_selector("#mb .mr")
    ck("P3-22", "US6", "A normal member does not see any Remove button", len(b.query_selector_all("#mb .xm")) == 0)

    s0 = a.inner_text("#st")
    a.once("dialog", lambda d: d.accept())
    a.query_selector_all("#mb .xm")[1].click()
    t = ms(a)
    a.wait_for_timeout(800)
    nmb = [x.inner_text() for x in a.query_selector_all("#mb .mr")]
    s1 = a.inner_text("#st")
    ck("P3-23", "US6", "The leader can remove a member and the member disappears from the list",
       "was removed" in t and len(nmb) == 2 and "Carmen Other" not in " ".join(nmb), str(nmb))
    ck("P3-24", "US6", "Removing a member frees one seat", s0.startswith("1 of 4") and s1.startswith("2 of 4"), f"before {s0} / after {s1}")
    sc(a, "US06_Members_AfterRemove")

    go(c3, "mine.html")
    c3.wait_for_selector("#ld", state="hidden")
    c3.wait_for_timeout(600)
    names = [h.inner_text() for h in c3.query_selector_all("#jn .cd h3")]
    ck("P3-25", "US6", "The removed member no longer sees that group under My Groups",
       "Future time group updated" not in names, str(names))

    r = b.evaluate("id => db.collection('groups').doc(id).update({members: [au.currentUser.uid]}).then(() => 'saved').catch(e => e.code)", g4)
    ck("P3-26", "US6", "A normal member cannot remove other members through a direct Firestore request", r == "permission-denied", r)

    for pr, who in ((b, "member"), (c3, "other")):
        go(pr, "group.html?id=" + g2)
        pr.wait_for_selector("#bx", state="visible")
        pr.click("#bt")
        ms(pr)
        pr.wait_for_timeout(700)

    # ---------- US8 Edit and close ----------
    go(a, "edit.html?id=" + g4)
    a.wait_for_selector("#fm", state="visible")
    a.fill("#tt", "Future time group updated")
    a.fill("#ds", "Updated description for the session.")
    a.fill("#mx", "5")
    a.fill("#tm", dt(4, 20, 0))
    a.click("#bt")
    a.wait_for_url("**/group.html*")
    a.wait_for_selector("#bx", state="visible")
    ck("P3-27", "US8", "The leader can edit the title, description, meeting time and maximum members",
       a.inner_text("#tt") == "Future time group updated" and "Updated description" in a.inner_text("#ds") and "of 5 seats" in a.inner_text("#st"), a.inner_text("#st"))

    go(b, "edit.html?id=" + g4)
    b.wait_for_selector("#np", state="visible")
    ck("P3-28", "US8", "A member who is not the leader cannot open the edit form", not b.is_visible("#fm"))
    sc(b, "US08_Edit_NotLeader")

    go(a, "edit.html?id=" + g2)
    a.wait_for_selector("#fm", state="visible")
    a.fill("#mx", "2")
    a.click("#bt")
    t = ms(a)
    ck("P3-29", "US8", "The maximum members cannot be lower than the current number of members (3 members, max 2)", "lower than the current" in t, t)
    sc(a, "US08_EditClose_MaxCheck")

    go(a, "edit.html?id=" + g4)
    a.wait_for_selector("#fm", state="visible")
    a.fill("#mx", "1")
    a.click("#bt")
    t = ms(a)
    ck("P3-29b", "US8", "A maximum of 1 member is still refused when editing (same check as creating)", "greater than 1" in t, t)
    a.fill("#mx", "5")
    a.fill("#tm", dt(-1))
    a.click("#bt")
    t = ms(a)
    ck("P3-30", "US8", "The meeting time cannot be edited to a past date", "in the past" in t, t)

    r = b.evaluate("id => db.collection('groups').doc(id).update({title: 'Hacked title'}).then(() => 'saved').catch(e => e.code)", g4)
    ck("P3-31", "US8", "A member cannot edit the group through a direct Firestore request", r == "permission-denied", r)
    r = a.evaluate("id => db.collection('groups').doc(id).update({max: 1}).then(() => 'saved').catch(e => e.code)", g4)
    ck("P3-32", "US8", "Even the leader cannot save a maximum lower than the members with a direct request", r == "permission-denied", r)

    go(a, "group.html?id=" + g4)
    a.wait_for_selector("#bx", state="visible")
    a.once("dialog", lambda d: d.accept())
    a.click("#cs")
    t = ms(a)
    a.wait_for_timeout(800)
    ck("P3-33", "US8", "The leader can close the group", "group is closed" in t and a.inner_text("#cl") == "Closed", t)
    sc(a, "US08_EditClose", True)

    go(a, "groups.html")
    a.wait_for_selector("#ld", state="hidden")
    tt = [h.inner_text() for h in a.query_selector_all(".cd h3")]
    ck("P3-34", "US8", "A closed group does not appear in the open groups list", "Future time group updated" not in tt, str(tt))

    go(c3, "group.html?id=" + g4)
    c3.wait_for_selector("#bx", state="visible")
    r = c3.evaluate("id => db.collection('groups').doc(id).update({members: [au.currentUser.uid]}).then(() => 'saved').catch(e => e.code)", g4)
    ck("P3-35", "US8", "Nobody can join a closed group, even with a direct Firestore request",
       not c3.is_visible("#bt") and r == "permission-denied", r)

    # ---------- US9 Announcements ----------
    go(a, "group.html?id=" + g1)
    a.wait_for_selector("#nf", state="visible")
    a.click("#ab")
    t = ms(a)
    ck("P3-36", "US9", "An empty announcement is refused", "write the announcement" in t, t)

    a.fill("#nt2", "The session moves to room 204. Please bring your laptops.")
    a.click("#ab")
    t = ms(a)
    a.wait_for_timeout(900)
    an = [x.inner_text() for x in a.query_selector_all("#an .an1")]
    ck("P3-37", "US9", "The leader can post an announcement and it shows with the posting date",
       "posted" in t and len(an) == 1 and "room 204" in an[0] and "Posted" in an[0], an[0].replace("\n", " / ") if an else "")

    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#mb .mr")
    b.wait_for_timeout(900)
    anb = [x.inner_text() for x in b.query_selector_all("#an .an1")]
    ck("P3-38", "US9", "The announcement is visible to the group members",
       any("room 204" in x for x in anb), str(len(anb)) + " announcements")
    ck("P3-39", "US9", "A normal member does not see the announcement form", not b.is_visible("#nf"))
    r = b.evaluate("id => db.collection('groups').doc(id).collection('notes').add({text: 'Member post', author: au.currentUser.uid, at: firebase.firestore.FieldValue.serverTimestamp()}).then(() => 'saved').catch(e => e.code)", g1)
    ck("P3-40", "US9", "A member cannot post an announcement even with a direct Firestore request", r == "permission-denied", r)
    sc(a, "US09_Announcements", True)

    nm = a.evaluate("id => db.collection('groups').doc(id).collection('notes').orderBy('at', 'desc').limit(1).get().then(s => s.docs[0].data().at.toDate().toISOString())", g1)
    ck("P3-41", "US9", "The announcement date is saved by the server (Firestore timestamp)", str(datetime.now().year) in str(nm) and "T" in str(nm), nm)

    # ---------- US11 Reminders ----------
    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    b.wait_for_timeout(900)
    ck("P3-42", "US11", "A reminder is shown for a group whose session is within 24 hours",
       b.is_visible("#rm") and "Session in" in b.inner_text("#rm"), b.inner_text("#rm").replace("\n", " / "))
    sc(b, "US11_Reminders", True)

    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    b.wait_for_timeout(700)
    ck("P3-43", "US11", "No reminder is shown for a session that is more than 24 hours away",
       "Far session group" not in b.inner_text("#rm") if b.is_visible("#rm") else True)

    go(a, "groups.html")
    a.wait_for_selector("#ld", state="hidden")
    a.wait_for_timeout(700)
    ck("P3-44", "US11", "No reminder is shown for a closed group", "Future time group" not in (a.inner_text("#rm") if a.is_visible("#rm") else ""))

    go(b, "group.html?id=" + g1)
    b.wait_for_selector("#bx", state="visible")
    b.wait_for_timeout(700)
    ck("P3-45", "US11", "The reminder also shows on the group details page for the members",
       b.is_visible("#rm") and "Session in" in b.inner_text("#rm"), b.inner_text("#rm"))

    go(c3, "groups.html")
    c3.wait_for_selector("#ld", state="hidden")
    c3.wait_for_timeout(700)
    ck("P3-46", "US11", "A student who is not in the group does not get its reminder",
       not c3.is_visible("#rm") or "Algorithms revision" not in c3.inner_text("#rm"))

    go(a, "edit.html?id=" + g1)
    a.wait_for_selector("#fm", state="visible")
    a.fill("#tm", dt(5))
    a.click("#bt")
    a.wait_for_url("**/group.html*")
    a.wait_for_timeout(700)
    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    b.wait_for_timeout(900)
    ck("P3-47", "US11", "The reminder disappears after the session time is moved more than 24 hours away",
       (not b.is_visible("#rm")) or "Algorithms revision" not in b.inner_text("#rm"), b.inner_text("#rm") if b.is_visible("#rm") else "no reminder")

    go(a, "edit.html?id=" + g1)
    a.wait_for_selector("#fm", state="visible")
    a.fill("#tm", dt(0, 2))
    a.click("#bt")
    a.wait_for_url("**/group.html*")
    a.wait_for_timeout(600)
    go(b, "mine.html")
    b.wait_for_selector("#ld", state="hidden")
    b.wait_for_timeout(900)
    ck("P3-48", "US11", "The reminder comes back after the session is moved back inside 24 hours",
       b.is_visible("#rm") and "Algorithms revision" in b.inner_text("#rm"))

    # ---------- responsive ----------
    # The three student contexts are not used any more, so they are closed before the
    # responsive checks: Chromium keeps about 150 MB for each open page.
    for ccx in (ca, cb, cc):
        ccx.close()
    c4, dw = pg(br, 1280, 800)
    go(dw, "index.html")
    d = dw
    d.fill("#em", "abeer@university.edu.sa")
    d.fill("#pw", "pass123")
    d.click("#bt")
    d.wait_for_url("**/groups.html*")
    d.wait_for_selector("#ld", state="hidden")
    wid = d.evaluate("document.documentElement.scrollWidth")
    go(d, "mine.html")
    d.wait_for_selector("#ld", state="hidden")
    wid2 = d.evaluate("document.documentElement.scrollWidth")
    d.wait_for_timeout(500)
    ck("P3-49", "DoD", "The pages fit the laptop screen (1280 x 800) with no horizontal scrolling",
       wid <= 1280 and wid2 <= 1280, f"scrollWidth {wid} / {wid2}")
    sc(d, "Desktop_View", True)

    c5, m = pg(br, 390, 844)
    sw = []
    for u in ["index.html", "groups.html", "mine.html", "create.html", "profile.html", "group.html?id=" + g1, "edit.html?id=" + g1]:
        if u == "groups.html":
            m.fill("#em", "abeer@university.edu.sa")
            m.fill("#pw", "pass123")
            m.click("#bt")
            m.wait_for_url("**/groups.html*")
        else:
            go(m, u)
        m.wait_for_load_state("load")
        m.wait_for_timeout(1200)
        sw.append((u, m.evaluate("document.documentElement.scrollWidth")))
        if u in ("mine.html", "group.html?id=" + g1, "groups.html"):
            sc(m, "phone_" + u.split(".")[0].replace("?", "_"), True)
    ck("P3-50", "DoD", "All pages fit a phone screen (390 x 844) with no horizontal scrolling",
       all(w <= 390 for _, w in sw), str(sw))
    m.screenshot(path=f"{SH}/Mobile_View.png", full_page=True)
    ck("P3-51", "DoD", "The menu, the buttons and the messages are visible on the phone view",
       m.is_visible("#nv") and m.is_visible("#tt"))

    c5.close()  # the phone context is finished before the time-zone checks start

    # ---------- the time check uses the local time of the student, not UTC ----------
    # The student in this block lives in Asia/Riyadh (+03:00) while the test machine runs
    # in UTC, so a value built in UTC is three hours behind her clock.
    ctz = br.new_context(viewport={"width": 1280, "height": 800}, timezone_id="Asia/Riyadh")
    t = ctz.new_page()
    t.set_default_timeout(25000)
    t.on("pageerror", lambda e: er.append("pageerror: " + str(e)))
    t.on("console", lambda m: (nw if "Failed to load resource" in m.text else er).append(m.text) if m.type == "error" else None)
    go(t, "signup.html")
    t.fill("#nm", "Riyadh Time")
    t.fill("#em", "riyadh@university.edu.sa")
    t.fill("#pw", "pass123")
    t.click("#bt")
    t.wait_for_url("**/profile.html*")
    t.wait_for_selector("#fm", state="visible")
    t.fill("#mj", "Computer Science")
    for c in t.query_selector_all("#cs input"):
        if c.get_attribute("value") == "CS 388T":
            c.click()
    t.click("#bt")
    t.wait_for_selector("#ms.ok")

    go(t, "create.html")
    t.wait_for_selector("#fm", state="visible")
    loc90 = t.evaluate("() => { const d = new Date(Date.now() + 90 * 60000), p = n => (n < 10 ? '0' : '') + n; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes()); }")
    utc90 = t.evaluate("() => new Date(Date.now() + 90 * 60000).toISOString().slice(0, 16)")
    t.fill("#tt", "Riyadh time group")
    t.select_option("#co", "CS 388T")
    t.fill("#ds", "A meeting time built in the local time of the student.")
    t.fill("#mx", "4")
    t.fill("#tm", loc90)
    t.click("#bt")
    t.wait_for_url("**/groups.html*")
    ck("P3-53", "US17", "A future meeting time is accepted in the local time of the student (Asia/Riyadh, machine in UTC)",
       loc90 != utc90, "local " + loc90 + " / UTC value would be " + utc90)

    go(t, "create.html")
    t.wait_for_selector("#fm", state="visible")
    t.fill("#tt", "Riyadh past group")
    t.select_option("#co", "CS 388T")
    t.fill("#mx", "4")
    t.fill("#tm", t.evaluate("() => { const d = new Date(Date.now() + 60 * 60000), p = n => (n < 10 ? \"0\" : \"\") + n; return d.getUTCFullYear() + \"-\" + p(d.getUTCMonth() + 1) + \"-\" + p(d.getUTCDate()) + \"T\" + p(d.getUTCHours()) + \":\" + p(d.getUTCMinutes()); }"))
    t.click("#bt")
    t.wait_for_selector("#ms.er, #ms.ok", timeout=25000)
    m2 = t.inner_text("#ms")
    ck("P3-54", "US17", "A time that is in the past for the student is refused (UTC value one hour ahead is in her past)",
       "past" in m2.lower(), m2)

    # ---- a session that already passed is hidden from the list and cannot be joined ----
    # The group is written with the admin rights of the emulator because the rules refuse
    # a new group with a past meeting time; this is the data of an old group.
    uid = t.evaluate("() => au.currentUser.uid")
    past_time = "2026-11-01T10:00"
    past_ms = t.evaluate("() => new Date('2026-11-01T10:00').getTime()")
    body = {"fields": {
        "title": {"stringValue": "Passed session group"},
        "course": {"stringValue": "CS 388T"},
        "desc": {"stringValue": "Session already passed."},
        "max": {"integerValue": "4"},
        "time": {"stringValue": past_time},
        "t": {"integerValue": str(int(past_ms))},
        "leader": {"stringValue": uid},
        "leaderName": {"stringValue": "Riyadh Time"},
        "members": {"arrayValue": {"values": [{"stringValue": uid}]}},
        "closed": {"booleanValue": False},
    }}
    docs = json.loads(rq("POST", f"http://localhost:8080/v1/projects/{PJ}/databases/(default)/documents/groups", body))
    gidp = docs["name"].split("/")[-1]

    go(t, "groups.html")
    t.wait_for_selector("#ld", state="hidden")
    t.wait_for_timeout(900)
    listed = t.inner_text("#ls")
    ck("P3-55", "US17", "A group whose session already passed is not shown in the open groups list",
       "Passed session group" not in listed, "cards shown: " + str(listed.count("View group")))

    # The same browser is used for the second student (an extra context is not created:
    # the test machine keeps its memory low). She is not the leader of that group, so the
    # page must tell her that the session passed and must not offer the join button.
    # Signing out sends the page to the login page, so the destroyed context is expected.
    try:
        t.evaluate("() => au.signOut()")
    except Exception:
        pass
    t.wait_for_timeout(1200)
    go(t, "signup.html")
    t.fill("#nm", "Late Student")
    t.fill("#em", "late@university.edu.sa")
    t.fill("#pw", "pass123")
    t.click("#bt")
    t.wait_for_url("**/profile.html*", timeout=60000)
    go(t, "group.html?id=" + gidp)
    t.wait_for_selector("#bx", state="visible")
    t.wait_for_timeout(500)
    ck("P3-56", "US17", "A student who opens a group whose session already passed sees the message and no join button",
       "already passed" in t.inner_text("#in") and not t.is_visible("#bt"),
       t.inner_text("#in") + " | seats: " + t.inner_text("#st"))
    ctz.close()

    er2 = [e for e in er if "permission" not in e.lower() and "PERMISSION_DENIED" not in e]
    ck("P3-52", "DoD", "No JavaScript errors in the Chrome console during the Phase 3 tests", not er2,
       f"{len(er2)} JS errors; {len(nw)} expected network messages from the refused requests")
    if er2:
        print("JS ERRORS:", er2[:5])

    br.close()

json.dump({"results": rs, "js_errors": er2 if 'er2' in dir() else [], "all_console_errors": er, "network_msgs": nw},
          open(f"{SH}/p3_results_raw.json", "w"), indent=1)
_ok = sum(r["result"] == "Pass" for r in rs)
print(_ok, "/", len(rs), "passed")
sys.exit(0 if _ok == len(rs) and _ok > 0 else 1)
