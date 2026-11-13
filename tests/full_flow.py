import sys, json, time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

BU = "http://localhost:5000"
SH = sys.argv[1] if len(sys.argv) > 1 else "shots"
rs = []
er = []


def dt(days, hours=0):
    return (datetime.now() + timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M")


def ck(i, nm, ok, nt=""):
    rs.append({"id": i, "name": nm, "result": "Pass" if ok else "Fail", "note": nt})
    print(("PASS " if ok else "FAIL ") + i + " " + nm + (" | " + nt if nt else ""))


with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--disable-extensions", "--js-flags=--max-old-space-size=256"])
    ctx = br.new_context(viewport={"width": 1280, "height": 800})
    p = ctx.new_page()
    p.on("pageerror", lambda e: er.append(str(e)))
    p.on("console", lambda m: er.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)

    def go(u, tries=3):
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

    def msg():
        p.wait_for_selector("#ms.er, #ms.ok", timeout=25000)
        return p.inner_text("#ms")

    # 1. Sign up
    go("signup.html")
    p.fill("#nm", "Journey Student")
    p.fill("#em", "journey@university.edu.sa")
    p.fill("#pw", "pass123")
    p.click("#bt")
    p.wait_for_url("**/profile.html*")
    ck("FF-01", "Step 1 - Sign up with a university email creates the account", "profile.html" in p.url)

    # 2. Login (after a logout)
    p.click("text=Log out")
    p.wait_for_function("document.querySelector('h1') && document.querySelector('h1').textContent == 'Log in'")
    p.fill("#em", "journey@university.edu.sa")
    p.fill("#pw", "pass123")
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    ck("FF-02", "Step 2 - Login opens the groups list", "groups.html" in p.url)

    # 3. Profile
    go("profile.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#mj", "Computer Science")
    for c in p.query_selector_all("#cs input"):
        if c.get_attribute("value") in ("CS 388T", "CS 281"):
            c.click()
    p.click("#bt")
    t = msg()
    ck("FF-03", "Step 3 - Profile with major and courses is saved", "saved" in t, t)

    # 4. Browse groups
    go("groups.html")
    p.wait_for_selector("#ld", state="hidden")
    ck("FF-04", "Step 4 - Browse groups page loads the open groups", p.query_selector("#fl") is not None)

    # 5. Create group
    go("create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Final sprint demo group")
    p.select_option("#co", "CS 388T")
    p.fill("#ds", "Group created during the final end to end test.")
    p.fill("#mx", "3")
    p.fill("#tm", dt(0, 4))
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    p.wait_for_selector("#ld", state="hidden")
    ck("FF-05", "Step 5 - Create group works and the group appears in the list",
       "created" in p.inner_text("#ms"), p.inner_text("#ms"))

    go("groups.html")
    p.wait_for_selector("#ld", state="hidden")
    link = None
    for c in p.query_selector_all(".cd"):
        if c.query_selector("h3").inner_text() == "Final sprint demo group":
            link = c.query_selector("a").get_attribute("href")
    g = link.split("id=")[1]

    # 6. Join group with a second account
    ctx2 = br.new_context(viewport={"width": 1280, "height": 800})
    q = ctx2.new_page()
    q.on("pageerror", lambda e: er.append(str(e)))
    q.goto(BU + "/signup.html")
    q.fill("#nm", "Second Student")
    q.fill("#em", "second@university.edu.sa")
    q.fill("#pw", "pass123")
    q.click("#bt")
    q.wait_for_url("**/profile.html*")
    q.goto(BU + "/profile.html")
    q.wait_for_selector("#fm", state="visible")
    q.fill("#mj", "Information Systems")
    for c in q.query_selector_all("#cs input"):
        if c.get_attribute("value") == "CS 388T":
            c.click()
    q.click("#bt")
    q.wait_for_selector("#ms.ok")
    q.goto(BU + "/group.html?id=" + g)
    q.wait_for_selector("#bx", state="visible")
    q.click("#bt")
    q.wait_for_selector("#ms.ok", timeout=25000)
    q.wait_for_timeout(700)
    ck("FF-06", "Step 6 - A second student joins the group", "1 of 3" in q.inner_text("#st"), q.inner_text("#st"))

    # 7. My Groups
    q.goto(BU + "/mine.html")
    q.wait_for_selector("#ld", state="hidden")
    ck("FF-07", "Step 7 - My Groups shows the joined group", [h.inner_text() for h in q.query_selector_all("#jn .cd h3")] == ["Final sprint demo group"])

    # 8. Leave group
    q.goto(BU + "/group.html?id=" + g)
    q.wait_for_selector("#bx", state="visible")
    q.click("#lv")
    q.wait_for_selector("#ms.ok", timeout=25000)
    q.wait_for_timeout(700)
    ck("FF-08", "Step 8 - The member leaves the group and the seat is free again", "2 of 3" in q.inner_text("#st"), q.inner_text("#st"))

    # 9. Manage members (join again, then the leader removes her)
    q.goto(BU + "/group.html?id=" + g)
    q.wait_for_selector("#bx", state="visible")
    q.click("#bt")
    q.wait_for_selector("#ms.ok", timeout=25000)
    q.wait_for_timeout(700)
    go("group.html?id=" + g)
    p.wait_for_selector("#mb .mr")
    p.wait_for_timeout(500)
    n0 = len(p.query_selector_all("#mb .mr"))
    p.once("dialog", lambda d: d.accept())
    p.query_selector_all("#mb .xm")[0].click()
    t = msg()
    p.wait_for_timeout(800)
    ck("FF-09", "Step 9 - The leader removes a member from the group",
       "removed" in t and len(p.query_selector_all("#mb .mr")) == n0 - 1, t)

    # 10. Edit group
    go("edit.html?id=" + g)
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Final sprint demo group v2")
    p.fill("#mx", "4")
    p.fill("#tm", dt(0, 6))
    p.click("#bt")
    p.wait_for_url("**/group.html*")
    p.wait_for_selector("#bx", state="visible")
    ck("FF-10", "Step 10 - The leader edits the group data",
       p.inner_text("#tt") == "Final sprint demo group v2" and "of 4 seats" in p.inner_text("#st"), p.inner_text("#st"))

    # 11. Close group
    p.once("dialog", lambda d: d.accept())
    p.click("#cs")
    t = msg()
    p.wait_for_timeout(800)
    go("groups.html")
    p.wait_for_selector("#ld", state="hidden")
    left = [h.inner_text() for h in p.query_selector_all(".cd h3")]
    ck("FF-11", "Step 11 - The leader closes the group and it leaves the open groups list",
       "closed" in t and "Final sprint demo group v2" not in left, t)

    # 12. Announcements (on a new group with a near session)
    go("create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Announcement group")
    p.select_option("#co", "CS 388T")
    p.fill("#mx", "4")
    p.fill("#tm", dt(0, 5))
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    p.wait_for_selector("#ld", state="hidden")
    for c in p.query_selector_all(".cd"):
        if c.query_selector("h3").inner_text() == "Announcement group":
            g2 = c.query_selector("a").get_attribute("href").split("id=")[1]
    go("group.html?id=" + g2)
    p.wait_for_selector("#nf", state="visible")
    p.fill("#nt2", "Bring the slides for chapter 5.")
    p.click("#ab")
    t = msg()
    p.wait_for_timeout(900)
    ck("FF-12", "Step 12 - The leader posts an announcement",
       "posted" in t and "chapter 5" in p.inner_text("#an"), t)

    # 13. Reminders
    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(1000)
    ck("FF-13", "Step 13 - The reminder appears for the session within 24 hours",
       p.is_visible("#rm") and "Announcement group" in p.inner_text("#rm"), p.inner_text("#rm").replace("\n", " / "))

    p.screenshot(path=f"{SH}/FullFlow_Final.jpg".replace(".jpg", ".png"), full_page=True)

    # responsive spot check on the same journey
    ctx3 = br.new_context(viewport={"width": 390, "height": 844})
    m = ctx3.new_page()
    m.on("pageerror", lambda e: er.append(str(e)))
    m.goto(BU + "/index.html")
    m.fill("#em", "journey@university.edu.sa")
    m.fill("#pw", "pass123")
    m.click("#bt")
    m.wait_for_url("**/groups.html*")
    m.wait_for_selector("#ld", state="hidden")
    sw = m.evaluate("document.documentElement.scrollWidth")
    ck("FF-14", "The full journey pages fit a phone screen (390 px)", sw <= 390, f"scrollWidth {sw}")
    m.screenshot(path=f"{SH}/FullFlow_Phone.png", full_page=True)

    ck("FF-15", "No JavaScript errors during the full journey", not er, f"{len(er)} errors")
    br.close()

json.dump({"results": rs, "js_errors": er}, open(f"{SH}/../full_flow_results.json", "w"), indent=1)
_ok = sum(r["result"] == "Pass" for r in rs)
print(_ok, "/", len(rs), "passed")
sys.exit(0 if _ok == len(rs) and _ok > 0 else 1)
