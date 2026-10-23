import os, json
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/pw-browsers"
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
PAGES = ["/", "/register/", "/account/", "/transactions/", "/othertransaction/", "/profile/"]
WIDTHS = [320, 375, 414, 600, 768, 901, 1024, 1280, 1600]
problems, passes = [], 0

def ok(name, cond, detail=""):
    global passes
    if cond: passes += 1
    else: problems.append(f"{name} {detail}")
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))

with sync_playwright() as p:
    b = p.chromium.launch()
    def newpage(w, h=800, reduced=None):
        ctx = b.new_context(viewport={"width": w, "height": h}, reduced_motion=reduced)
        pg = ctx.new_page()
        pg.route("**/fonts.g*apis.com/**", lambda r: r.abort())
        pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
        pg.errors = []
        pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
        pg.on("response", lambda r: pg.errors.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        return pg

    # ---- layout matrix: overflow, footer position, header ----
    for path in PAGES:
        for w in WIDTHS:
            pg = newpage(w)
            pg.goto(BASE + path); pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(700)  # let entrance animations finish
            m = pg.evaluate("""() => {
                const de = document.documentElement, f = document.querySelector('.site-footer');
                const fb = f.getBoundingClientRect().bottom + scrollY;
                const wide = [...document.querySelectorAll('body *')].filter(e => {
                    const r = e.getBoundingClientRect(); return r.width > 0 && r.right > de.clientWidth + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.site-nav') && getComputedStyle(e).visibility !== 'hidden';
                }).slice(0,3).map(e => e.tagName + '.' + e.className);
                return {sw: de.scrollWidth, cw: de.clientWidth, footerBottom: Math.round(fb), docH: de.scrollHeight, vh: innerHeight,
                        headerH: Math.round(document.querySelector('.site-header').getBoundingClientRect().height), wide};
            }""")
            tag = f"{path} @{w}px"
            ok(f"{tag}: no horizontal overflow", m["sw"] <= m["cw"], f"scrollWidth {m['sw']} > {m['cw']} {m['wide']}")
            ok(f"{tag}: footer reaches bottom of viewport/document", m["footerBottom"] >= m["vh"] - 1 and abs(m["footerBottom"] - m["docH"]) <= 1, str(m))
            if w >= 901: ok(f"{tag}: header stays single row", m["headerH"] <= 70, f"headerH={m['headerH']}")
            ok(f"{tag}: no console/network errors", not pg.errors, str(pg.errors[:3]))
            pg.context.close()

    # ---- mobile menu ----
    pg = newpage(375); pg.goto(BASE + "/transactions/"); pg.wait_for_load_state("networkidle")
    toggle, nav = pg.locator(".nav-toggle"), pg.locator("#site-nav")
    ok("mobile: hamburger visible", toggle.is_visible())
    ok("mobile: menu closed initially", not nav.is_visible())
    toggle.click(); pg.wait_for_timeout(400)
    ok("mobile: menu opens", nav.is_visible() and toggle.get_attribute("aria-expanded") == "true")
    ok("mobile: active page highlighted", pg.locator(".site-nav a.is-active").inner_text() == "Transactions")
    box = nav.bounding_box(); ok("mobile: open menu within viewport", box["x"] >= 0 and box["x"] + box["width"] <= 375.5)
    pg.screenshot(path="/tmp/shots/m_menu_open.png")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    ok("mobile: Escape closes menu", not nav.is_visible())
    toggle.click(); pg.wait_for_timeout(400); pg.mouse.click(8, 780); pg.wait_for_timeout(400)
    ok("mobile: outside click closes menu", not nav.is_visible())
    toggle.click(); pg.wait_for_timeout(400); pg.locator(".site-nav a", has_text="Profile").click(); pg.wait_for_load_state("networkidle")
    ok("mobile: menu link navigates", pg.url.endswith("/profile/"))
    pg.set_viewport_size({"width": 1280, "height": 800}); ok("desktop: nav visible without toggle", pg.locator("#site-nav").is_visible() and not pg.locator(".nav-toggle").is_visible())
    pg.context.close()

    # ---- profile flow ----
    pg = newpage(1280); pg.goto(BASE + "/profile/"); pg.wait_for_load_state("networkidle")
    ok("profile: empty state shown", "Look up an account" in pg.inner_text("#profileDetails"))
    pg.click("#searchBtn"); ok("profile: empty input validation", "Please enter account number" in pg.inner_text("#message") and "Look up an account" in pg.inner_text("#profileDetails"))
    pg.fill("#accountNumber", "482913"); pg.keyboard.press("Enter"); pg.wait_for_selector(".profile-card"); pg.wait_for_timeout(500)
    t = pg.inner_text("#profileDetails")
    ok("profile: Enter key searches + shows holder", "Asha" in t and "482913" in t and "ACC0001" in t and "100001" in t)
    ok("profile: balance formatted as INR", "₹ 12,50,000.50" in t, t[:200])
    ok("profile: type badge rendered", pg.locator(".badge--savings").count() == 1)
    ok("profile: button restored after load", pg.inner_text("#searchBtn").strip() == "Search" and not pg.is_disabled("#searchBtn"))
    pg.screenshot(path="/tmp/shots/d_profile_result.png", full_page=True)
    pg.fill("#accountNumber", "000000"); pg.click("#searchBtn"); pg.wait_for_selector(".state--error")
    ok("profile: not-found state", "Account not found" in pg.inner_text("#profileDetails"))
    pg.fill("#accountNumber", "555555"); pg.click("#searchBtn"); pg.wait_for_selector(".profile-card")
    ok("profile: XSS payload NOT executed", pg.evaluate("window.__xss") is None)
    ok("profile: payload shown as literal text", "<img src=x" in pg.inner_text(".profile-card__who h2") and pg.locator("#profileDetails img").count() == 0)
    ok("profile: no console errors in flow", not pg.errors, str(pg.errors))
    pg.context.close()
    # loading state: delay the API
    pg = newpage(375); pg.route("**/getaccount/**", lambda r: (pg.wait_for_timeout(900), r.continue_()))
    pg.goto(BASE + "/profile/"); pg.fill("#accountNumber", "482913"); pg.click("#searchBtn"); pg.wait_for_timeout(250)
    ok("profile: loading state (spinner + disabled button)", pg.locator("#searchBtn .spinner").count() == 1 and pg.is_disabled("#searchBtn") and "Loading" in pg.inner_text("#message"))
    pg.wait_for_selector(".profile-card"); pg.screenshot(path="/tmp/shots/m_profile_result.png", full_page=True)
    ok("profile@375: result has no overflow", pg.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
    pg.context.close()
    # network failure state
    pg = newpage(375); pg.route("**/getaccount/**", lambda r: r.abort()); pg.goto(BASE + "/profile/"); pg.fill("#accountNumber", "1"); pg.click("#searchBtn"); pg.wait_for_selector(".state--error")
    ok("profile: connection-error state", "Unable to connect to server" in pg.inner_text("#profileDetails") and not pg.is_disabled("#searchBtn"))
    pg.context.close()

    # ---- transactions flow (real server round trip) ----
    pg = newpage(1280); pg.goto(BASE + "/transactions/"); pg.wait_for_load_state("networkidle")
    pg.fill("#acc_no", "482913"); pg.click("button[value=check]"); pg.wait_for_load_state("networkidle")
    ok("transactions: Check loads holder + balance", pg.input_value("#acc_name") == "Asha" and pg.input_value("#bal") == "1250000.5")
    pg.check("#type_deposit", force=True); pg.fill("#amount", "500"); pg.press("#amount", "Tab")
    ok("transactions: deposit balance preview", pg.input_value("#balance_after") == "1250500.5", pg.input_value("#balance_after"))
    pg.check("#type_withdraw", force=True); pg.fill("#amount", "99999999"); pg.press("#amount", "Tab")
    ok("transactions: insufficient-balance message", pg.inner_text("#error") == "Insufficient Balance")
    pg.screenshot(path="/tmp/shots/d_transactions.png", full_page=True)
    pg.fill("#amount", "250"); pg.press("#amount", "Tab")
    ok("transactions: withdraw preview + message cleared", pg.input_value("#balance_after") == "1249750.5" and pg.inner_text("#error") == "")
    pg.click("button[value=save]"); pg.wait_for_load_state("networkidle")
    pg.fill("#acc_no", "482913"); pg.click("button[value=check]"); pg.wait_for_load_state("networkidle")
    ok("transactions: saved balance persisted", pg.input_value("#bal") == "1249750.5", pg.input_value("#bal"))
    pg.context.close()
    pg = newpage(1280); pg.goto(BASE + "/transactions/"); pg.fill("#amount", "5"); pg.press("#amount", "Tab")
    ok("transactions: amount before type selected -> no JS error (guard)", not pg.errors, str(pg.errors)); pg.context.close()
    pg = newpage(1280); pg.goto(BASE + "/transactions/"); pg.fill("#acc_no", "999999"); pg.press("#acc_no", "Enter"); pg.wait_for_load_state("networkidle")
    ok("transactions: Enter in account field still triggers Check (not Save)", "Account number Mismatch" in pg.inner_text("main")); pg.context.close()

    # ---- registration validation UX ----
    pg = newpage(375); pg.goto(BASE + "/register/"); pg.fill("[name=last_name]", "Rao"); pg.click("button.btn--primary"); pg.wait_for_load_state("networkidle")
    ok("register: error shown, '* ' prefix stripped", pg.inner_text("#first_name_error").strip() == "First name is required...", pg.inner_text("#first_name_error"))
    ok("register: first invalid field focused", pg.evaluate("document.activeElement.name") == "first_name")
    ok("register: entered data preserved after error", pg.input_value("[name=last_name]") == "Rao")
    pg.screenshot(path="/tmp/shots/m_register_error.png", full_page=True); pg.context.close()
    # accounts: Check keeps typed type/balance now
    pg = newpage(1280); pg.goto(BASE + "/account/"); pg.fill("#cust_id", "100001"); pg.check("#acc_type_current", force=True); pg.fill("#balance", "777"); pg.click("button[value=check]"); pg.wait_for_load_state("networkidle")
    ok("account: holder loaded + acc no generated", pg.input_value("#acc_holder") == "Asha" and len(pg.input_value("#acc_no")) == 6)
    ok("account: chosen type & balance survive Check", pg.is_checked("#acc_type_current") and pg.input_value("#balance") == "777"); pg.context.close()
    # other-bank page missing-bank validation
    pg = newpage(375); pg.goto(BASE + "/othertransaction/"); pg.fill("#acc_no", "1"); pg.click("button[value=check]"); pg.wait_for_load_state("networkidle")
    ok("other: bank validation message styled", "Please select the bank" in pg.inner_text("#banks_error")); pg.screenshot(path="/tmp/shots/m_other.png", full_page=True); pg.context.close()

    # ---- keyboard / a11y basics ----
    pg = newpage(1280); pg.goto(BASE + "/register/"); pg.keyboard.press("Tab"); 
    ok("a11y: skip link is first tab stop", pg.evaluate("document.activeElement.className") == "skip-link"); 
    pg.focus("[name=first_name]"); ring = pg.evaluate("getComputedStyle(document.activeElement).boxShadow")
    ok("a11y: inputs show a visible focus ring", ring != "none" and "rgba" in ring, ring)
    ok("a11y: every form control has a label", pg.evaluate("""[...document.querySelectorAll('main input:not([type=hidden]):not([type=radio]), main select, main textarea')].every(e => e.labels && e.labels.length)"""))
    pg.context.close()

    # ---- reduced motion ----
    pg = newpage(1280, reduced="reduce"); pg.goto(BASE + "/"); pg.wait_for_load_state("networkidle")
    ok("reduced-motion: entrance animations disabled", pg.evaluate("getComputedStyle(document.querySelector('.reveal')).animationName") == "none")
    pg.context.close()
    pg = newpage(1280); pg.goto(BASE + "/"); 
    ok("motion allowed: entrance animation active", pg.evaluate("getComputedStyle(document.querySelector('.reveal')).animationName") != "none")
    pg.wait_for_timeout(900); pg.screenshot(path="/tmp/shots/d_home.png", full_page=True); pg.context.close()
    pg = newpage(375); pg.goto(BASE + "/"); pg.wait_for_timeout(1200); pg.screenshot(path="/tmp/shots/m_home.png", full_page=True); pg.context.close()
    pg = newpage(1280); pg.goto(BASE + "/register/"); pg.wait_for_timeout(900); pg.screenshot(path="/tmp/shots/d_register.png", full_page=True); pg.context.close()
    b.close()

print(f"\n{passes} passed, {len(problems)} failed")
for x in problems: print("  FAILED:", x)
