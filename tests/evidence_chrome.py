import json, os, subprocess, time, urllib.request
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

BU = "http://localhost:5000"
PJ = "demo-studymate"
OUT = os.path.abspath(os.environ.get("SHOTDIR", "../Evidence/Screenshots"))
os.makedirs(OUT, exist_ok=True)
DISP = ":99"
shots = []
PWA = "pass123"


def reset():
    def rq(u):
        urllib.request.urlopen(urllib.request.Request(u, method="DELETE", headers={"Authorization": "Bearer owner"})).read()
    rq(f"http://localhost:8080/emulator/v1/projects/{PJ}/databases/(default)/documents")
    rq(f"http://localhost:9099/emulator/v1/projects/{PJ}/accounts")


def dt(days, hours=0):
    return (datetime.now() + timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M")


xv = subprocess.Popen(["Xvfb", DISP, "-screen", "0", "1400x1000x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
reset()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome-stable", headless=False,
                            args=["--no-sandbox", "--window-position=0,0", "--window-size=1300,880",
                                  "--lang=en-GB", "--disable-features=Translate", "--disable-session-crashed-bubble"])
    ctx = br.new_context(viewport=None, locale="en-GB")
    p = ctx.new_page()
    p.set_default_timeout(20000)
    p.set_default_navigation_timeout(20000)
    s = ctx.new_cdp_session(p)
    wid = s.send("Browser.getWindowForTarget")["windowId"]
    s.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "normal", "left": 0, "top": 0, "width": 1300, "height": 880}})
    time.sleep(2)

    def snap(name, full=True):
        time.sleep(1.0)
        b = s.send("Browser.getWindowForTarget")["bounds"]
        subprocess.run(["import", "-window", "root", "/tmp/_root.png"],
                       env={"DISPLAY": DISP, "PATH": "/usr/bin:/bin"}, check=True)
        subprocess.run(["convert", "/tmp/_root.png", "-crop", f"{b['width']}x{b['height']}+{b['left']}+{b['top']}",
                        "+repage", f"{OUT}/{name}.png"], check=True)
        if full:
            p.screenshot(path=f"{OUT}/{name}_page.png", full_page=True)
        shots.append({"file": f"{name}.png", "url": p.url, "time": datetime.now().isoformat(timespec="seconds")})
        print("shot", name, "|", p.url, flush=True)

    def go(u):
        p.goto(BU + "/" + u)
        p.wait_for_load_state("load")

    def msg():
        p.wait_for_selector("#ms.er, #ms.ok", timeout=25000)
        return p.inner_text("#ms")

    def win(w, h):
        s.send("Browser.setWindowBounds", {"windowId": wid, "bounds": {"windowState": "normal", "left": 0, "top": 0, "width": w, "height": h}})
        time.sleep(0.9)

    def signup(nm, em):
        go("signup.html")
        p.fill("#nm", nm)
        p.fill("#em", em)
        p.fill("#pw", PWA)
        p.click("#bt")
        p.wait_for_url("**/profile.html*")

    def profile(mj, courses):
        p.wait_for_selector("#fm", state="visible")
        p.fill("#mj", mj)
        for c in p.query_selector_all("#cs input"):
            if c.get_attribute("value") in courses:
                c.click()
        p.click("#bt")
        return msg()

    def login(em):
        go("index.html")
        p.fill("#em", em)
        p.fill("#pw", PWA)
        p.click("#bt")
        p.wait_for_url("**/groups.html*")

    def logout():
        p.click("text=Log out")
        p.wait_for_function("document.querySelector('h1') && document.querySelector('h1').textContent == 'Log in'")

    def gid(title):
        go("groups.html")
        p.wait_for_selector("#ld", state="hidden")
        for c in p.query_selector_all(".cd"):
            if c.query_selector("h3").inner_text() == title:
                return c.query_selector("a").get_attribute("href").split("id=")[1]

    # ---------------- account 1 : leader ----------------
    go("signup.html")
    p.fill("#nm", "Abeer Alharbi")
    p.fill("#em", "abeer@university.edu.sa")
    p.fill("#pw", PWA)
    snap("US01_Signup")
    p.click("#bt")
    p.wait_for_url("**/profile.html*")

    p.wait_for_selector("#fm", state="visible")
    p.fill("#mj", "Computer Science")
    for c in p.query_selector_all("#cs input"):
        if c.get_attribute("value") in ("CS 388T", "CS 281"):
            c.click()
    snap("US02_Profile")
    p.click("#bt")
    msg()

    go("create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Sprint 2 demo group")
    p.select_option("#co", "CS 388T")
    p.fill("#ds", "We solve the sprint exercises together and prepare the demo.")
    p.fill("#mx", "4")
    p.fill("#tm", dt(3))
    snap("US03_Create_Group")

    p.fill("#tm", dt(-2))
    p.click("#bt")
    msg()
    snap("US17_PastTime")

    p.fill("#tm", dt(0, 3))
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    p.wait_for_selector("#ld", state="hidden")

    go("create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Database lab revision")
    p.select_option("#co", "CS 281")
    p.fill("#ds", "SQL practice before the lab quiz.")
    p.fill("#mx", "3")
    p.fill("#tm", dt(5))
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    p.wait_for_selector("#ld", state="hidden")
    snap("US04_Groups_List")
    g = gid("Sprint 2 demo group")

    # ---------------- account 2 : member ----------------
    logout()
    signup("Basma Alqahtani", "basma@university.edu.sa")
    profile("Information Systems", ["CS 388T"])
    go("group.html?id=" + g)
    p.wait_for_selector("#bx", state="visible")
    p.click("#bt")
    msg()
    p.wait_for_timeout(900)
    snap("US05_Join_Group")

    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(800)
    snap("US07_MyGroups_Member")

    go("group.html?id=" + g)
    p.wait_for_selector("#bx", state="visible")
    p.wait_for_timeout(700)
    p.click("#lv")
    msg()
    p.wait_for_timeout(1100)
    snap("US10_LeaveGroup")

    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(700)
    snap("US10_MyGroups_AfterLeave")

    go("group.html?id=" + g)
    p.wait_for_selector("#bx", state="visible")
    p.click("#bt")
    msg()
    p.wait_for_timeout(800)

    # ---------------- account 3 : no groups ----------------
    logout()
    signup("Dana Alamri", "dana@university.edu.sa")
    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(800)
    snap("US07_MyGroups_Empty")

    # ---------------- back to the leader ----------------
    logout()
    login("abeer@university.edu.sa")
    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(800)
    snap("US07_MyGroups")

    # a third member joins, so the maximum can be tested against the member count
    logout()
    login("dana@university.edu.sa")
    go("group.html?id=" + g)
    p.wait_for_selector("#bx", state="visible")
    p.click("#bt")
    msg()
    p.wait_for_timeout(700)
    logout()
    login("abeer@university.edu.sa")
    go("edit.html?id=" + g)
    p.wait_for_selector("#fm", state="visible")
    p.wait_for_timeout(700)
    p.fill("#mx", "2")
    p.click("#bt")
    msg()
    p.wait_for_timeout(700)
    snap("US08_MaxBelowMembers")

    go("edit.html?id=" + g)
    p.wait_for_selector("#fm", state="visible")
    p.wait_for_timeout(800)
    snap("US08_EditGroup")

    go("group.html?id=" + g)
    p.wait_for_selector("#mb .mr")
    p.wait_for_timeout(900)
    snap("US06_Members")
    p.once("dialog", lambda d: d.accept())
    p.query_selector_all("#mb .xm")[0].click()
    msg()
    p.wait_for_timeout(1100)
    snap("US06_Members_Remove")

    go("edit.html?id=" + g)
    p.wait_for_selector("#fm", state="visible")
    p.wait_for_timeout(700)
    p.fill("#mx", "1")
    p.click("#bt")
    msg()
    p.wait_for_timeout(600)
    snap("US08_EditGroup_MaxCheck")
    p.fill("#mx", "4")
    p.fill("#tt", "Sprint 2 demo group (final)")
    p.click("#bt")
    p.wait_for_url("**/group.html*")
    p.wait_for_selector("#bx", state="visible")
    p.wait_for_timeout(600)
    snap("US08_EditGroup_Saved")


    go("group.html?id=" + g)
    p.wait_for_selector("#bx", state="visible")
    p.once("dialog", lambda d: d.accept())
    p.click("#cs")
    msg()
    p.wait_for_timeout(1100)
    snap("US08_Closed")
    go("groups.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(900)
    snap("US08_Groups_After_Close")

    # ---------------- announcements and reminders ----------------
    go("create.html")
    p.wait_for_selector("#fm", state="visible")
    p.fill("#tt", "Algorithms midterm revision")
    p.select_option("#co", "CS 388T")
    p.fill("#ds", "Two hours of exercises before the midterm.")
    p.fill("#mx", "5")
    p.fill("#tm", dt(0, 6))
    p.click("#bt")
    p.wait_for_url("**/groups.html*")
    p.wait_for_selector("#ld", state="hidden")
    g2 = gid("Algorithms midterm revision")

    go("group.html?id=" + g2)
    p.wait_for_selector("#nf", state="visible")
    p.click("#ab")
    msg()
    p.wait_for_timeout(500)
    snap("US09_Empty_Announcement")
    p.fill("#nt2", "The session moves to room 204. Please bring your laptops and the chapter 4 slides.")
    p.click("#ab")
    msg()
    p.wait_for_timeout(900)
    p.fill("#nt2", "The room booking is confirmed for 6 PM.")
    p.click("#ab")
    msg()
    p.wait_for_timeout(1100)
    snap("US09_Announcements")

    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(1000)
    snap("US11_Reminders")

    # ---------------- views ----------------
    go("groups.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(900)
    snap("Desktop_View")

    win(420, 880)
    go("mine.html")
    p.wait_for_selector("#ld", state="hidden")
    p.wait_for_timeout(1200)
    snap("Mobile_View")
    go("group.html?id=" + g2)
    p.wait_for_selector("#bx", state="visible")
    p.wait_for_timeout(900)
    snap("Mobile_Group_Details")

    win(1300, 880)
    go("group.html?id=" + g2)
    p.wait_for_selector("#bx", state="visible")
    p.wait_for_timeout(900)
    snap("Group_Details_Desktop")

    br.close()

xv.terminate()
json.dump(shots, open("Evidence/Screenshots/screenshot_index.json", "w"), indent=1)
print(len(shots), "screenshots written")
