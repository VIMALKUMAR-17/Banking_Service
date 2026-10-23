"""Regression harness for the Banking_Service UI redesign.

Usage:  python smoke.py <project_dir> <fingerprint_out.json> [baseline.json]
Uses Django's throwaway test database, never the project's db.sqlite3.
"""
import json, os, sys, re
from html.parser import HTMLParser

project = os.path.abspath(sys.argv[1])
out_path = sys.argv[2]
baseline_path = sys.argv[3] if len(sys.argv) > 3 else None
sys.path.insert(0, project)
os.chdir(project)
os.environ["DJANGO_SETTINGS_MODULE"] = "Banking_Service.settings"

import django
django.setup()
from django.test.utils import setup_test_environment
from django.db import connection
from django.test import Client
from django.contrib.staticfiles import finders

setup_test_environment()
connection.creation.create_test_db(verbosity=0)

results, failures = [], []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    if not cond:
        failures.append(f"{name} {detail}")
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if (detail and not cond) else ""))


class FP(HTMLParser):
    """Collect form controls, forms and stylesheet links."""
    def __init__(self):
        super().__init__()
        self.controls, self.forms, self.css, self.ids = [], [], [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "form":
            self.forms.append([a.get("method", "get").lower(), a.get("action")])
        if tag in ("input", "select", "textarea", "button"):
            name = a.get("name")
            if name or tag == "button":
                typ = a.get("type")
                val = a.get("value") if (typ in ("radio", "hidden") or tag == "button") else None
                if name == "csrfmiddlewaretoken":
                    val = "<token>"
                self.controls.append([tag, name, typ, val, "readonly" in a])
        if tag == "link" and a.get("rel") == "stylesheet":
            self.css.append(a.get("href"))


def fingerprint(html):
    p = FP()
    p.feed(html)
    return {"controls": sorted(p.controls, key=lambda c: [str(x) for x in c]),
            "forms": p.forms, "ids": sorted(p.ids), "css": p.css}


c = Client()
fps = {}


def get(url, key=None):
    r = c.get(url)
    html = r.content.decode()
    if key:
        fps[key] = fingerprint(html)
    return r, html


# ---------- 1. every page renders ----------
for key, url in [("index", "/"), ("home", "/home/"), ("register", "/register/"),
                 ("account", "/account/"), ("transactions", "/transactions/"),
                 ("othertransaction", "/othertransaction/"), ("profile", "/profile/")]:
    r, html = get(url, key)
    check(f"GET {url} -> 200", r.status_code == 200, r.status_code)
    check(f"{url}: no unrendered template tags", "{%" not in html and "{{" not in html)
    if key in ("register", "account", "transactions", "othertransaction"):
        check(f"{url}: CSRF token present", "csrfmiddlewaretoken" in html)

# every stylesheet referenced by a rendered page resolves to a real static file
for key, fp in list(fps.items()):
    for href in fp["css"]:
        if href.startswith("/static/"):
            check(f"static file exists: {href}", finders.find(href[len('/static/'):]) is not None)

# ---------- 2. registration workflow ----------
r, html = get("/register/")
m = re.search(r'name="cust_id"[^>]*value="(\d+)"', html) or re.search(r'value="(\d+)"[^>]*name="cust_id"', html)
check("register: customer id auto-filled", m is not None)
cust_id = m.group(1) if m else "100001"
valid = dict(cust_id=cust_id, first_name="Asha", last_name="Rao", dob="1990-01-02", gender="female",
             phone="9876543210", email="asha@example.com", address="1 Main St", city="Pune",
             state="MH", pincode="411001", aadhar="123456789012", pan="ABCDE1234F",
             created_at="2026-01-01", status="active")
r = c.post("/register/", {**valid, "first_name": ""})
html = r.content.decode()
check("register: missing first name shows error", "First name is required" in html)
check("register: entered data kept after error", 'value="Rao"' in html)
fps["register_error"] = fingerprint(html)
r = c.post("/register/", valid)
check("register: valid post redirects", r.status_code == 302)
r = c.post("/register/", valid)
check("register: duplicate customer id rejected", "already exists" in r.content.decode())

# ---------- 3. account workflow ----------
r = c.post("/account/", {"action": "check", "cust_id": "999"})
check("account: unknown customer error", "Customer ID does not exist" in r.content.decode())
fps["account_error"] = fingerprint(r.content.decode())
r = c.post("/account/", {"action": "check", "cust_id": cust_id})
html = r.content.decode()
check("account: check shows holder name", "Asha" in html)
fps["account_checked"] = fingerprint(html)
acc_no = re.search(r'name="acc_no"[^>]*value="(\d+)"', html) or re.search(r'value="(\d+)"[^>]*name="acc_no"', html)
check("account: account number generated", acc_no is not None)
acc_no = acc_no.group(1)
r = c.post("/account/", {"action": "save", "acc_id": "ACC0001", "acc_no": acc_no, "cust_id": cust_id,
                         "acc_type": "Savings", "balance": "1000", "created_at": "2026-01-01"})
check("account: save redirects", r.status_code == 302)

# ---------- 4. transactions page workflow ----------
r = c.post("/transactions/", {"action": "check", "acc_no": "000000"})
check("transactions: mismatch error", "Account number Mismatch" in r.content.decode())
fps["transactions_error"] = fingerprint(r.content.decode())
r = c.post("/transactions/", {"action": "check", "acc_no": acc_no})
html = r.content.decode()
check("transactions: check shows holder and balance", "Asha" in html and "1000" in html)
fps["transactions_checked"] = fingerprint(html)
check("transactions: JS hooks present", all(i in html for i in ('id="bal"', 'id="amount"', 'id="balance_after"', 'id="error"')))
check("transactions: calculateBalance retained", "function calculateBalance" in html)
r = c.post("/transactions/", {"action": "save", "transaction_id": "1001", "acc_no": acc_no, "acc_name": "Asha",
                              "transaction_type": "deposit", "current_balance": "1000", "amount": "500",
                              "balance_after": "1500", "transaction_date": "2026-01-01"})
check("transactions: save redirects", r.status_code == 302)

# ---------- 5. REST API ----------
r = c.get(f"/getaccount/{acc_no}/")
check("api getaccount returns balance 1500", r.status_code == 200 and r.json().get("balance") == "1500", r.content[:80])
check("api getaccount unknown -> error key", "error" in c.get("/getaccount/nope/").json())
check("api getall lists accounts", len(c.get("/getall/").json()) == 1)
r = c.post("/createtransaction/", {"acc_no": acc_no, "transaction_type": "Deposit", "amount": "100"}, content_type="application/json")
check("api deposit works", r.json().get("message") == "Transaction Successful", r.content[:80])
r = c.post("/createtransaction/", {"acc_no": acc_no, "transaction_type": "Withdraw", "amount": "999999"}, content_type="application/json")
check("api overdraw rejected", r.json().get("error") == "Insufficient Balance")

# ---------- 6. other-bank page (POST validation paths that need no network) ----------
r = c.post("/othertransaction/", {"action": "check", "acc_no": ""})
check("other: missing acc shows error", "Enter the Account Number" in r.content.decode())
fps["other_error"] = fingerprint(r.content.decode())
r = c.post("/othertransaction/", {"action": "check", "acc_no": "1", "banks": ""})
check("other: missing bank shows error", "select the bank" in r.content.decode())

# ---------- 7. profile page hooks ----------
html = get("/profile/")[1]
check("profile: JS hooks present", all(s in html for s in ('id="accountNumber"', 'id="message"', 'id="profileDetails"', "getProfile")))
check("profile: still calls /getaccount/ API", "/getaccount/" in html)

# ---------- 8. nav / layout ----------
for url in ("/", "/register/", "/profile/"):
    html = get(url)[1]
    check(f"{url}: exactly one <footer/.footer>", len(re.findall(r'<footer|class="footer"', html)) == 1)
    for name in ("home", "profile", "register", "account", "transactions", "othertransaction"):
        pass
    check(f"{url}: nav links all present",
          all(f'href="{p}"' in html for p in ("/home/", "/profile/", "/register/", "/account/", "/transactions/", "/othertransaction/")))

json.dump(fps, open(out_path, "w"), indent=1)

# ---------- 9. compare with baseline ----------
if baseline_path:
    base = json.load(open(baseline_path))
    for key, b in base.items():
        n = fps.get(key)
        check(f"[{key}] page still renders", n is not None)
        if not n:
            continue
        check(f"[{key}] form methods/actions unchanged", b["forms"] == n["forms"], f"{b['forms']} vs {n['forms']}")
        norm = lambda lst: [[t, nm, (None if (t == "button" and nm is None) else ty), v, ro] for t, nm, ty, v, ro in lst]
        missing = [x for x in norm(b["controls"]) if x not in norm(n["controls"])]
        check(f"[{key}] all original controls preserved (name/type/value/readonly)", not missing, str(missing))
        # 'heading' was a duplicated, unreferenced id in the old base template (intentionally dropped)
        lost_ids = sorted(set(b["ids"]) - set(n["ids"]) - {"heading"})
        check(f"[{key}] all original element ids preserved", not lost_ids, str(lost_ids))

print("\n%d checks, %d failed" % (len(results), len(failures)))
for f in failures:
    print("  FAILED:", f)
sys.exit(1 if failures else 0)
