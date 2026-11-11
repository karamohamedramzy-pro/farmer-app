"""اختبارات نسخة BETA — تعمل على البيانات التجريبية في الذاكرة.
التشغيل:  pip install -r requirements.txt -r requirements-dev.txt && pytest
عند ربط القواعد أعِد استعمالها (غيّر فقط طريقة تجهيز البيانات)."""
import re
import secrets
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

import app.main as m


@pytest.fixture(autouse=True)
def reset_state():
    """يصفّر الحالة المشتركة (أكواد الاشتراك، المحاولات، الأكواد المؤقتة) قبل كل اختبار."""
    for c in m.SubscriptionCode:
        c.pop("used_by", None)
        c.pop("expires", None)
    m.SubFails.clear()
    m.PhoneCode.clear()
    m.StorageSetting.clear()
    yield


def new_client():
    return TestClient(m.app, follow_redirects=False)


def path_of(url):
    p = urlsplit(url)
    return p.path + ("?" + p.query if p.query else "")


def register(c, email=None, phone="+966501234567", name="Ali", password="secret1"):
    email = email or f"u{secrets.token_hex(4)}@example.com"
    r = c.post("/register", data={"name": name, "email": email, "phone": phone, "password": password})
    return email, r


def full_login(c, email):
    """الدخول الكامل: إيميل ← رابط ← كود واتساب ← /home"""
    r = c.post("/login", data={"email": email})
    assert r.status_code == 200
    link = re.search(r'id="dev-link" href="([^"]+)"', r.text).group(1)
    r = c.get(path_of(link))
    assert r.status_code == 303 and r.headers["location"] == "/verify-phone"
    r = c.get("/verify-phone")
    code = re.search(r'id="dev-code">(\d{6})<', r.text).group(1)
    r = c.post("/verify-phone", data={"code": code})
    assert r.status_code == 303 and r.headers["location"] == "/home"


@pytest.fixture
def user():
    """عميل مسجَّل الدخول بحساب جديد."""
    c = new_client()
    email, r = register(c)
    assert r.status_code == 200
    full_login(c, email)
    return c, email


# ---------------------------------------------------------------- التسجيل
def test_register_validation():
    c = new_client()
    ok = dict(name="Ali", email="a@b.co", phone="+966501234567", password="secret1")
    for field, bad, err in [("name", " ", "err_name_required"), ("email", "nope", "err_email_invalid"),
                            ("phone", "12ab", "err_phone_invalid"), ("password", "123", "err_pass_short")]:
        r = c.post("/register", data={**ok, field: bad})
        assert r.status_code == 400 and f'data-i18n="{err}"' in r.text, field


def test_register_duplicate_email_and_normalization():
    c = new_client()
    email, r = register(c)
    assert r.status_code == 200 and 'id="dev-link"' in r.text       # رابط الدخول يُرسل بعد التسجيل
    _, r = register(new_client(), email=email.upper())               # نفس الإيميل بحروف كبيرة
    assert r.status_code == 400 and "err_email_exists" in r.text


def test_phone_is_normalized_on_register():
    c = new_client()
    email, _ = register(c, phone="+966 50-123 4567")
    assert m.get_user_by_email(email)["phone"] == "+966501234567"


# ---------------------------------------------------------------- الدخول
def test_unregistered_email_is_not_auto_created():
    c = new_client()
    n = len(m.User)
    r = c.post("/login", data={"email": "ghost@example.com"})
    assert r.status_code == 404 and "err_no_account" in r.text and 'href="/register"' in r.text
    assert len(m.User) == n and m.get_user_by_email("ghost@example.com") is None


def test_pages_require_full_login():
    c = new_client()
    for p in ["/home", "/products", "/sources", "/sources/new"]:
        assert c.get(p).status_code == 303, p
    assert c.post("/entry", data={"product_id": 1}).status_code == 303
    assert c.post("/storage/local", data={"products_url": "http://x.co"}).status_code == 303


def test_email_link_alone_is_not_enough():
    c = new_client()
    email, _ = register(c)
    r = c.post("/login", data={"email": email})
    link = re.search(r'id="dev-link" href="([^"]+)"', r.text).group(1)
    c.get(path_of(link))                       # الخطوة 1 فقط
    assert c.get("/home").status_code == 303   # ما زال ممنوعاً من الصفحات الرئيسية
    assert c.get("/verify-phone").status_code == 200


def test_bad_token_rejected():
    c = new_client()
    for t in ["", "garbage", "x.y.z"]:
        r = c.get("/auth/verify", params={"token": t})
        assert r.status_code == 400 and "err_link_invalid" in r.text


def test_wrong_code_then_lockout():
    c = new_client()
    email, _ = register(c)
    r = c.post("/login", data={"email": email})
    c.get(path_of(re.search(r'id="dev-link" href="([^"]+)"', r.text).group(1)))
    real = m.PhoneCode[m.get_user_by_email(email)["id"]]["code"]
    wrong = "000000" if real != "000000" else "111111"
    for _ in range(m.PHONE_CODE_MAX_ATTEMPTS):
        r = c.post("/verify-phone", data={"code": wrong})
        assert r.status_code == 400 and "err_bad_code" in r.text
    r = c.post("/verify-phone", data={"code": real})        # حتى الصحيح مرفوض بعد الحد
    assert r.status_code == 429 and "err_too_many" in r.text
    assert c.get("/home").status_code == 303


def test_resend_issues_new_code(user):
    c = new_client()
    email, _ = register(c)
    r = c.post("/login", data={"email": email})
    c.get(path_of(re.search(r'id="dev-link" href="([^"]+)"', r.text).group(1)))
    uid = m.get_user_by_email(email)["id"]
    old = m.PhoneCode[uid]["code"]
    c.post("/verify-phone/resend")
    assert m.PhoneCode[uid]["expires"] > 0 and m.PhoneCode[uid]["attempts"] == 0
    assert re.fullmatch(r"\d{6}", m.PhoneCode[uid]["code"]) and old is not None


def test_dev_codes_hidden_when_disabled(monkeypatch):
    monkeypatch.setattr(m, "DEV_SHOW_CODES", False)
    c = new_client()
    email, r = register(c)
    assert 'id="dev-link"' not in r.text and "token=" not in r.text


def test_logout(user):
    c, _ = user
    assert c.get("/home").status_code == 200
    c.get("/logout")
    assert c.get("/home").status_code == 303


# ---------------------------------------------------------------- الصفحات + navbar/footer
def test_home_has_navbar_and_footer(user):
    c, _ = user
    t = c.get("/home").text
    assert 'class="navbar"' in t and 'href="/products"' in t and 'href="/sources"' in t and 'href="/home"' in t
    assert "<footer" in t and t.count('class="robot off"') == 3 and 'class="robot on"' not in t
    assert "t.me/" in t and 'data-i18n="contact_a"' in t           # نص التواصل يظهر والروبوتات رمادية


def test_products_flow_morning_evening_merge(user):
    c, _ = user
    c.post("/entry", data={"product_id": 2, "qty_start": 30, "money_start": 1000})
    c.post("/entry", data={"product_id": 2, "qty_end": 25, "money_end": 1500})
    t = c.get("/products?product_id=2").text
    assert t.count("<tr>") == 2                                    # العنوان + سطر واحد
    for s in ["+30</td>", "-25</td>", "+5</td>", "-1000$", "+1500$", "+500$"]:
        assert s in t


def test_demo_user_sees_green_red(user):
    c = new_client()
    full_login(c, "demo@example.com")
    t = c.get("/products?product_id=1").text
    assert 'class="plus"' in t and 'class="minus"' in t and "+500$" in t and "-200$" in t


def test_users_do_not_see_each_others_data(user):
    c, _ = user
    t = c.get("/products?product_id=1").text
    assert "<tr>" not in t and 'class="empty"' in t               # لا سجلات demo، وتظهر حالة فارغة مرشِدة
    assert "مزرعة الأمل" not in c.get("/sources").text


# ---------------------------------------------------------------- مصادري
def test_source_requires_name_only(user):
    c, _ = user
    r = c.post("/sources/new", data={"name": "  "})
    assert r.status_code == 400 and "err_src_name" in r.text
    r = c.post("/sources/new", data={"name": "مزرعة النور"})        # كل الباقي فارغ
    assert r.status_code == 303
    t = c.get("/sources").text
    assert "مزرعة النور" in t and 'class="imgs none"' in t


def test_source_images_limit_and_validation(user):
    c, _ = user
    imgs = {f"img{i}": f"https://img.example.com/{i}.jpg" for i in range(1, 5)}
    assert c.post("/sources/new", data={"name": "A", **imgs}).status_code == 303
    assert 'class="imgs n4"' in c.get("/sources").text
    r = c.post("/sources/new", data={"name": "B", "img1": "javascript:alert(1)"})
    assert r.status_code == 400 and "err_url_invalid" in r.text
    r = c.post("/sources/new", data={"name": "C", "phone": "abc"})
    assert r.status_code == 400 and "err_phone_invalid" in r.text


def test_source_edit_and_ownership(user):
    c, _ = user
    c.post("/sources/new", data={"name": "قديم"})
    sid = m.list_sources(m.get_user_by_email(user[1])["id"])[0]["id"]
    assert "قديم" in c.get(f"/sources/{sid}/edit").text
    r = c.post(f"/sources/{sid}/edit", data={"name": "جديد", "field": "فواكه", "phone": "+966500000000",
                                               "location": "https://maps.example.com/x", "img1": "https://i.co/a.png"})
    assert r.status_code == 303
    t = c.get("/sources").text
    assert "جديد" in t and "فواكه" in t and "فتح الخريطة" in t and 'class="imgs n1"' in t
    # مستخدم آخر لا يستطيع فتح أو تعديل مصدر غيره
    other = new_client()
    email2, _ = register(other)
    full_login(other, email2)
    assert other.get(f"/sources/{sid}/edit").status_code == 303
    other.post(f"/sources/{sid}/edit", data={"name": "اختراق"})
    assert "اختراق" not in c.get("/sources").text


def test_source_xss_is_escaped(user):
    c, _ = user
    c.post("/sources/new", data={"name": "<script>alert(1)</script>", "description": "<img src=x onerror=1>"})
    t = c.get("/sources").text
    assert "<script>alert(1)</script>" not in t and "&lt;script&gt;" in t


# ---------------------------------------------------------------- الروبوتات (التخزين والاشتراك)
def test_subscription_activation_turns_robot_green(user):
    c, _ = user
    r = c.post("/storage/subscription", data={"code": "WRONG", "next": "/home"})
    assert r.status_code == 303 and "msg=err_sub_code" in r.headers["location"] and "dlg=dlg-sub" in r.headers["location"]
    r = c.post("/storage/subscription", data={"code": " farm-demo-30 ", "next": "/products?product_id=1"})
    assert r.status_code == 303 and r.headers["location"] == "/products?product_id=1"
    t = c.get("/home").text
    assert t.count('class="robot on"') == 1 and t.count('class="robot off"') == 2
    assert "<b>الأيام المتبقية</b>" not in t and "30" in t and "512" in t
    assert 'data-i18n="contact_a"' not in t                         # نص التواصل يختفي مع روبوت أخضر


def test_subscription_code_single_owner_and_not_renewable(user):
    c, _ = user
    c.post("/storage/subscription", data={"code": "FARM-DEMO-365"})
    rec = m.find_subscription_code("FARM-DEMO-365")
    first = rec["expires"]
    c.post("/storage/disconnect", data={"mode": "subscription"})
    c.post("/storage/subscription", data={"code": "FARM-DEMO-365"})
    assert m.find_subscription_code("FARM-DEMO-365")["expires"] == first   # لا تجديد بإعادة الإدخال
    other = new_client()
    e, _ = register(other)
    full_login(other, e)
    r = other.post("/storage/subscription", data={"code": "FARM-DEMO-365"})
    assert "err_sub_code" in r.headers["location"]                          # كود مستعمل من غيره


def test_expired_subscription_shows_gray(user):
    c, email = user
    c.post("/storage/subscription", data={"code": "FARM-DEMO-30"})
    from datetime import date, timedelta
    m.find_subscription_code("FARM-DEMO-30")["expires"] = date.today() - timedelta(days=1)
    t = c.get("/home").text
    assert 'class="robot on"' not in t and "sub_expired" in t


def test_subscription_bruteforce_limit(user):
    c, _ = user
    for _ in range(m.SUB_CODE_MAX_FAILS):
        c.post("/storage/subscription", data={"code": "NOPE"})
    r = c.post("/storage/subscription", data={"code": "FARM-DEMO-365"})
    assert "err_too_many" in r.headers["location"]


def test_local_and_cloud_storage_and_masking(user):
    c, _ = user
    r = c.post("/storage/local", data={"products_url": "ftp://x", "next": "/home"})
    assert "err_url_invalid" in r.headers["location"]
    r = c.post("/storage/local", data={"next": "/home"})
    assert "err_url_required" in r.headers["location"]
    c.post("/storage/local", data={"products_url": "http://192.168.1.5:9000/p", "sources_url": "https://h.co/s"})
    c.post("/storage/cloud", data={"sql_api": "https://sql.example.com/api?key=SECRET123",
                                   "nosql_api": "https://user:pw@nosql.example.com/v1/token/ABC"})
    t = c.get("/home").text
    assert t.count('class="robot on"') == 2 and t.count('class="robot off"') == 1
    assert "SECRET123" not in t and "ABC" not in t and "pw@" not in t          # المفاتيح لا تُعرض
    assert "sql.example.com" in t and "192.168.1.5:9000" in t
    c.post("/storage/disconnect", data={"mode": "local"})
    c.post("/storage/disconnect", data={"mode": "cloud"})
    assert c.get("/home").text.count('class="robot off"') == 3


def test_open_redirect_blocked(user):
    c, _ = user
    for bad in ["https://evil.com", "//evil.com", "/\\evil.com", "javascript:alert(1)"]:
        r = c.post("/storage/subscription", data={"code": "X", "next": bad})
        assert r.headers["location"].startswith("/home"), bad


def test_error_dialog_reopened_via_query(user):
    c, _ = user
    t = c.get("/home?dlg=dlg-sub&msg=err_sub_code").text
    assert 'data-i18n="err_sub_code"' in t


def test_misc():
    c = new_client()
    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/static/css/style.css").status_code == 200
    assert c.get("/static/js/i18n.js").status_code == 200
    assert c.get("/static/js/app.js").status_code == 200
    assert c.get("/register").status_code == 200
    assert c.get("/").status_code == 200
