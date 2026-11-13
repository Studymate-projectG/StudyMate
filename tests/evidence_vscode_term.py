import sys, time
from playwright.sync_api import sync_playwright

cmd, wait, name = sys.argv[1], float(sys.argv[2]), sys.argv[3]
FOLDER = sys.argv[4] if len(sys.argv) > 4 else "/home/user/StudyMate_Phase3_Submission/08_StudyMate_App"
FILE = sys.argv[5] if len(sys.argv) > 5 else "firestore.rules"
import os
OUT = os.path.abspath(os.environ.get("SHOTDIR", "../Evidence/Screenshots")) + "/"


def rows_text(p):
    try:
        return p.locator(".xterm-rows").first.inner_text()
    except Exception:
        return ""


with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    p = br.new_page(viewport={"width": 1400, "height": 900})
    p.set_default_timeout(20000)
    p.goto("http://localhost:8443/?folder=" + FOLDER, wait_until="commit")
    p.wait_for_selector(".monaco-workbench", timeout=120000)
    time.sleep(8)

    # close a dialog that code-server shows on the first visit (for example "Sign in")
    for _ in range(3):
        try:
            p.keyboard.press("Escape")
            time.sleep(1)
        except Exception:
            pass
    try:
        p.locator(".monaco-dialog-box .monaco-button").first.click(timeout=3000)
        time.sleep(1)
    except Exception:
        pass

    # close the welcome tab if it is there
    try:
        p.locator(".tabs-container .tab:has-text('Welcome') .codicon-close").first.click(timeout=5000)
    except Exception:
        pass
    time.sleep(1)

    # open the code file with the keyboard (Ctrl+P), no mouse click on the sidebar
    p.keyboard.press("Control+P")
    time.sleep(2)
    p.keyboard.type(FILE)
    time.sleep(2)
    p.keyboard.press("Enter")
    time.sleep(4)
    print("opened file:", FILE, flush=True)

    # command palette -> create terminal
    p.keyboard.press("F1")
    time.sleep(2)
    p.keyboard.type("Terminal: Create New Terminal")
    time.sleep(2)
    p.keyboard.press("Enter")

    # wait for the shell prompt inside the terminal
    ok = False
    for i in range(40):
        time.sleep(2)
        txt = rows_text(p)
        if "$" in txt or "user@" in txt:
            ok = True
            print("prompt after", 2 * (i + 1), "s:", txt.strip().split("\n")[-1][:120], flush=True)
            break
    if not ok:
        print("no prompt, terminal text:", rows_text(p)[:200], flush=True)
    time.sleep(2)

    def typ(text):
        p.mouse.click(700, 800)
        time.sleep(0.8)
        p.evaluate("document.querySelector('.xterm-helper-textarea').focus()")
        time.sleep(0.5)
        p.evaluate("t => document.execCommand('insertText', false, t)", text)
        time.sleep(0.8)

    typ(cmd)
    p.keyboard.press("Enter")
    print("started:", cmd, flush=True)
    time.sleep(wait)

    txt = rows_text(p)
    print("TERMINAL:", " | ".join(x.strip() for x in txt.split("\n") if x.strip())[-700:], flush=True)
    try:
        p.screenshot(path=OUT + name + ".png", timeout=60000)
    except Exception as e:
        print("screenshot failed:", e, flush=True)
    br.close()
    print("shot saved", name, flush=True)
