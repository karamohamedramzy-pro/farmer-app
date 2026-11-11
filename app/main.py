"""
مزرعتي (TB-farm) — نسخة BETA
============================
بيانات تجريبية في الذاكرة (تضيع عند إعادة تشغيل الخادم). لا توجد قاعدة بيانات.
الهدف: التأكد من الواجهة والمسارات، ثم يربطها المبرمج التالي بقواعد البيانات (doc.md).

الأقسام:
  0) الإعدادات (متغيرات البيئة)
  1) بيانات تجريبية      (User / Product / DailyEntry / Source / SubscriptionCode ...)
  2) طبقة الوصول للبيانات  ← هي ما يُستبدل بقواعد البيانات (المسارات لا تلمس البيانات)
  3) خدمات: إرسال إيميل / واتساب، رموز الدخول
  4) إعداد التطبيق ودوال مساعدة
  5) المسارات
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import time
from datetime import date, timedelta
from email.message import EmailMessage
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeTimedSerializer
from starlette.middleware.sessions import SessionMiddleware

# =====================================================================
# 0) الإعدادات
# =====================================================================
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")          # ⚠️ غيّره في الإنتاج
# وضع تجريبي: يعرض رابط الدخول وكود واتساب على الشاشة لأن لا يوجد مزوّد إرسال فعلي.
# ⚠️ اضبطه على 0 في الإنتاج (وإلا يستطيع أي شخص الدخول بلا إيميل ولا واتساب).
DEV_SHOW_CODES = os.getenv("DEV_SHOW_CODES", "1") == "1"
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")           # مثال: https://farm.example.com (لروابط الإيميل)
HTTPS_ONLY = os.getenv("HTTPS_ONLY", "0") == "1"           # فعّله خلف HTTPS
TELEGRAM_URL = os.getenv("TELEGRAM_URL", "https://t.me/CHANGE_ME")           # ← ضع حساب المبرمج
DOCS_URL = os.getenv("DOCS_URL", "https://CHANGE_ME.example.com/tb-farm")    # ← صفحة document TB-farm
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "")

LOGIN_LINK_MAX_AGE = 15 * 60      # صلاحية رابط الدخول (ثوانٍ)
PHONE_CODE_MAX_AGE = 5 * 60       # صلاحية كود واتساب
PHONE_CODE_MAX_ATTEMPTS = 5       # محاولات إدخال الكود
SUB_CODE_MAX_FAILS = 10           # محاولات فاشلة لكود الاشتراك لكل مستخدم


# =====================================================================
# 1) بيانات تجريبية — نفس أسماء وحقول الجداول في models.py
# =====================================================================
def hash_password(password: str) -> str:
    salt = os.urandom(8).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${h}"


# جدول products  (type: veg = خضار / fruit = فاكهة)
Product = [
    {"id": 1,  "name_ar": "بطاطا",  "name_en": "Potato",      "type": "veg"},
    {"id": 2,  "name_ar": "طماطم",  "name_en": "Tomato",      "type": "veg"},
    {"id": 3,  "name_ar": "بصل",    "name_en": "Onion",       "type": "veg"},
    {"id": 4,  "name_ar": "خيار",   "name_en": "Cucumber",    "type": "veg"},
    {"id": 5,  "name_ar": "جزر",    "name_en": "Carrot",      "type": "veg"},
    {"id": 6,  "name_ar": "فلفل",   "name_en": "Pepper",      "type": "veg"},
    {"id": 7,  "name_ar": "تفاح",   "name_en": "Apple",       "type": "fruit"},
    {"id": 8,  "name_ar": "برتقال", "name_en": "Orange",      "type": "fruit"},
    {"id": 9,  "name_ar": "عنب",    "name_en": "Grapes",      "type": "fruit"},
    {"id": 10, "name_ar": "تين",    "name_en": "Fig",         "type": "fruit"},
    {"id": 11, "name_ar": "رمان",   "name_en": "Pomegranate", "type": "fruit"},
    {"id": 12, "name_ar": "موز",    "name_en": "Banana",      "type": "fruit"},
]

# جدول users — مستخدم تجريبي: demo@example.com  (احذفه قبل النسخة الرسمية)
# الدخول بالإيميل فقط؛ كلمة السر تُخزَّن للاستعمال لاحقاً (استعادة حساب / عامل إضافي).
User = [
    {"id": 1, "name": "Demo", "email": "demo@example.com", "phone": "+10000000000",
     "password_hash": hash_password("demo123")},
]

# جدول daily_entries — qty_end و money_start تُخزَّن سالبة، والباقي موجبة
_today = date.today()
DailyEntry = [
    {"id": 1, "user_id": 1, "product_id": 1, "entry_date": _today,
     "qty_start": 30, "qty_end": -25, "money_start": -1000, "money_end": 1500},
    {"id": 2, "user_id": 1, "product_id": 1, "entry_date": _today - timedelta(days=1),
     "qty_start": 20, "qty_end": -22, "money_start": -900, "money_end": 700},
]

# مصادري (MongoDB لاحقاً) — الاسم وحده إجباري، والصور من 0 إلى 4
Source = [
    {"id": "a1b2c3d4e5f6", "user_id": 1, "name": "مزرعة الأمل", "field": "خضار ورقية",
     "description": "مورّد خضار طازجة يومياً.", "phone": "+10000000001",
     "location": "", "images": []},
]

# أكواد الاشتراك (الروبوت 1) — أكواد تجريبية؛ expires/used_by يُضبطان عند أول تفعيل
SubscriptionCode = [
    {"code": "FARM-DEMO-30",  "days": 30,  "products_limit_kb": 512,  "sources_limit_kb": 512},
    {"code": "FARM-DEMO-365", "days": 365, "products_limit_kb": 5120, "sources_limit_kb": 5120},
]

# إعدادات التخزين لكل مستخدم: {user_id: {"subscription": code, "local": {...}, "cloud": {...}}}
StorageSetting = {}


# =====================================================================
# 2) طبقة الوصول للبيانات
#    عند ربط القواعد: أعِد كتابة هذه الدوال فقط (بنفس الأسماء والمدخلات والمخرجات).
#    المخرجات: dict أو قائمة dict. (Source ← MongoDB، والباقي ← PostgreSQL)
# =====================================================================
def get_user_by_email(email: str):
    return next((u for u in User if u["email"] == email), None)


def get_user_by_id(user_id: int):
    return next((u for u in User if u["id"] == user_id), None)


def create_user(name: str, email: str, phone: str, password: str) -> dict:
    user = {"id": max((u["id"] for u in User), default=0) + 1, "name": name, "email": email,
            "phone": phone, "password_hash": hash_password(password)}
    User.append(user)
    return user


def list_products() -> list:
    return sorted(Product, key=lambda p: p["id"])


def get_product(product_id: int):
    return next((p for p in Product if p["id"] == product_id), None)


def list_entries(user_id: int, product_id: int) -> list:
    rows = [e for e in DailyEntry if e["user_id"] == user_id and e["product_id"] == product_id]
    return sorted(rows, key=lambda e: (e["entry_date"], e["id"]), reverse=True)


def save_entry(user_id: int, product_id: int, qty_start: float, qty_end: float,
               money_start: float, money_end: float) -> dict:
    """يحفظ إدخال اليوم. إن وُجد سطر لنفس (المستخدم، المنتج، اليوم) تُجمع القيم عليه،
    فيصبح إدخال الصباح وإدخال المساء سطراً واحداً. الإشارات تُضبط هنا."""
    today = date.today()
    row = next((e for e in DailyEntry if e["user_id"] == user_id
                and e["product_id"] == product_id and e["entry_date"] == today), None)
    if row is None:
        row = {"id": max((e["id"] for e in DailyEntry), default=0) + 1, "user_id": user_id,
               "product_id": product_id, "entry_date": today,
               "qty_start": 0, "qty_end": 0, "money_start": 0, "money_end": 0}
        DailyEntry.append(row)
    row["qty_start"] += abs(qty_start)
    row["qty_end"] -= abs(qty_end)
    row["money_start"] -= abs(money_start)
    row["money_end"] += abs(money_end)
    return row


# ---- مصادري (في الإنتاج: MongoDB — الكود جاهز كتعليق في database.py) ----
def list_sources(user_id: int) -> list:
    return sorted((s for s in Source if s["user_id"] == user_id), key=lambda s: s["name"].lower())


def get_source(user_id: int, source_id: str):
    return next((s for s in Source if s["id"] == source_id and s["user_id"] == user_id), None)


def create_source(user_id: int, data: dict) -> dict:
    src = {"id": secrets.token_hex(6), "user_id": user_id, **data}
    Source.append(src)
    return src


def update_source(user_id: int, source_id: str, data: dict):
    src = get_source(user_id, source_id)
    if src:
        src.update(data)
    return src


# ---- التخزين والاشتراك (الروبوتات الثلاثة) ----
def get_storage(user_id: int) -> dict:
    return StorageSetting.setdefault(user_id, {})


def set_storage(user_id: int, mode: str, data):
    """mode: subscription (data = كود نصي) | local | cloud (data = dict). data=None ← فصل."""
    st = get_storage(user_id)
    if data is None:
        st.pop(mode, None)
    else:
        st[mode] = data


def find_subscription_code(code: str):
    code = (code or "").strip().upper()
    return next((c for c in SubscriptionCode if c["code"] == code), None)


def usage_bytes(user_id: int):
    """المساحة المستعملة: (بيانات المنتجات، بيانات المصادر) بالبايت. تقدير بحجم JSON."""
    prod = [e for e in DailyEntry if e["user_id"] == user_id]
    src = [s for s in Source if s["user_id"] == user_id]
    dump = lambda x: len(json.dumps(x, default=str, ensure_ascii=False).encode())
    return dump(prod), dump(src)


# ---- مخزن مؤقت (في الإنتاج: Redis أو جدول مع انتهاء صلاحية) ----
PhoneCode = {}      # user_id → {"code", "expires", "attempts"}
SubFails = {}       # user_id → عدد محاولات كود الاشتراك الفاشلة


# =====================================================================
# 3) خدمات: إيميل / واتساب / رموز
# =====================================================================
def send_email(to: str, subject: str, body: str):
    host = os.getenv("SMTP_HOST")
    if not host:
        print(f"[EMAIL not sent: SMTP_HOST missing] to={to} subject={subject}"
              + (f"\n{body}" if DEV_SHOW_CODES else ""), flush=True)
        return
    try:
        msg = EmailMessage()
        msg["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER", "")
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as s:
            s.starttls()
            if os.getenv("SMTP_USER"):
                s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            s.send_message(msg)
    except Exception as e:  # لا نُسقط الطلب؛ المستخدم يستطيع إعادة المحاولة
        print(f"[EMAIL ERROR] {e!r}", flush=True)


def send_whatsapp(phone: str, text: str):
    """TODO (المبرمج التالي): اربط مزوّداً حقيقياً — WhatsApp Cloud API (Meta) أو Twilio.
    الكود يُرسل كقالب رسالة (template) لأن واتساب يمنع الرسائل الحرة خارج نافذة المحادثة."""
    print(f"[WHATSAPP not sent: provider not configured] to={phone}"
          + (f"\n{text}" if DEV_SHOW_CODES else ""), flush=True)


_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="login-link")


def make_login_link(request: Request, user: dict) -> str:
    token = _serializer.dumps({"uid": user["id"], "n": secrets.token_hex(8)})
    base = BASE_URL or str(request.base_url).rstrip("/")
    return f"{base}/auth/verify?token={token}"


def read_login_token(token: str):
    try:
        return _serializer.loads(token, max_age=LOGIN_LINK_MAX_AGE)["uid"]
    except (BadSignature, KeyError, TypeError):
        return None


def issue_phone_code(user: dict) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    PhoneCode[user["id"]] = {"code": code, "expires": time.time() + PHONE_CODE_MAX_AGE, "attempts": 0}
    send_whatsapp(user["phone"], f"TB-farm: {code}")
    return code


# =====================================================================
# 4) إعداد التطبيق ودوال مساعدة
# =====================================================================
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=HTTPS_ONLY)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def fmt_num(v) -> str:
    """500.0 → 500  /  2.50 → 2.5  /  -25.0 → -25  (في القوالب: {{ x|num }})"""
    s = f"{float(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


templates.env.filters["num"] = fmt_num
templates.env.globals.update(TELEGRAM_URL=TELEGRAM_URL, DOCS_URL=DOCS_URL,
                             SUPPORT_EMAIL=SUPPORT_EMAIL, YEAR=date.today().year)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{8,15}$")


def norm_email(e: str) -> str:
    return (e or "").strip().lower()


def norm_phone(p: str) -> str:
    return re.sub(r"[\s\-()]", "", p or "")


def valid_http_url(u: str) -> bool:
    try:
        p = urlsplit(u)
        _ = p.port  # يرفع ValueError إن كان المنفذ خاطئاً
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and len(u) <= 500


def mask_url(u: str) -> str:
    """نعرض المضيف فقط؛ المسار والاستعلام قد يحويان مفتاحاً سرّياً."""
    p = urlsplit(u)
    return f"{p.scheme}://{p.netloc.split('@')[-1]}/…"


def safe_next(n: str) -> str:
    return n if (n and n.startswith("/") and not n.startswith("//") and "\\" not in n) else "/home"


def redirect_with(path: str, **params) -> RedirectResponse:
    parts = urlsplit(path)
    q = dict(parse_qsl(parts.query))
    q.update({k: v for k, v in params.items() if v})
    return RedirectResponse(urlunsplit(("", "", parts.path, urlencode(q), "")), status_code=303)


def current_path(request: Request) -> str:
    q = [(k, v) for k, v in request.query_params.multi_items() if k not in ("dlg", "msg")]
    return request.url.path + ("?" + urlencode(q) if q else "")


def current_uid(request: Request):
    uid = request.session.get("user_id")
    return uid if uid and get_user_by_id(uid) else None


def storage_status(uid: int) -> dict:
    """حالة الروبوتات الثلاثة للـ footer."""
    st = get_storage(uid)
    out = {"sub": None, "local": None, "cloud": None}
    code = st.get("subscription")
    rec = find_subscription_code(code) if code else None
    if rec and rec.get("expires"):
        days = (rec["expires"] - date.today()).days
        pb, sb = usage_bytes(uid)
        pl, sl = rec["products_limit_kb"], rec["sources_limit_kb"]
        out["sub"] = {
            "active": days > 0, "days_left": max(days, 0), "tail": rec["code"][-4:],
            "p_used": round(pb / 1024, 1), "p_limit": pl, "p_pct": min(100, round(pb / 1024 / pl * 100)),
            "s_used": round(sb / 1024, 1), "s_limit": sl, "s_pct": min(100, round(sb / 1024 / sl * 100)),
        }
    if st.get("local"):
        out["local"] = {"active": True, "products_url": mask_url(st["local"].get("products_url", "")) if st["local"].get("products_url") else "",
                        "sources_url": mask_url(st["local"].get("sources_url", "")) if st["local"].get("sources_url") else ""}
    if st.get("cloud"):
        out["cloud"] = {"active": True, "sql_api": mask_url(st["cloud"].get("sql_api", "")) if st["cloud"].get("sql_api") else "",
                        "nosql_api": mask_url(st["cloud"].get("nosql_api", "")) if st["cloud"].get("nosql_api") else ""}
    out["any_active"] = any(v and v.get("active") for v in (out["sub"], out["local"], out["cloud"]))
    return out


def render(request: Request, name: str, status_code: int = 200, **extra):
    uid = current_uid(request)
    ctx = {"username": request.session.get("name"), "dev": DEV_SHOW_CODES,
           "storage": storage_status(uid) if uid else None, "current": current_path(request),
           "msg": request.query_params.get("msg"), "open_dlg": request.query_params.get("dlg")}
    ctx.update(extra)
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def start_login(request: Request, user: dict):
    """ينشئ رابط الدخول ويرسله للإيميل، ثم يعرض صفحة «تحقق من بريدك»."""
    link = make_login_link(request, user)
    send_email(user["email"], "TB-farm — رابط الدخول / Login link",
               f"افتح الرابط للدخول (صالح 15 دقيقة):\nOpen this link to log in (valid 15 minutes):\n{link}\n")
    return render(request, "check_email.html", email=user["email"], dev_link=link if DEV_SHOW_CODES else None)


def mask_phone(p: str) -> str:
    return "••••" + p[-4:]


# =====================================================================
# 5) المسارات
# =====================================================================
@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


# ---------- تسجيل الدخول (بالإيميل) ----------
@app.get("/")
def login_page(request: Request):
    if current_uid(request):
        return RedirectResponse("/home", status_code=303)
    return render(request, "login.html")


@app.post("/login")
def login(request: Request, email: str = Form(...)):
    email = norm_email(email)
    user = get_user_by_email(email) if EMAIL_RE.match(email) else None
    if not user:
        # لا إنشاء تلقائي للحساب: غير المسجل يُوجَّه لإنشاء حساب
        return render(request, "login.html", status_code=404, error="err_no_account", email=email)
    return start_login(request, user)


# ---------- إنشاء حساب ----------
@app.get("/register")
def register_page(request: Request):
    return render(request, "register.html", form={})


@app.post("/register")
def register(request: Request, name: str = Form(""), email: str = Form(""),
             phone: str = Form(""), password: str = Form("")):
    name, email, phone = name.strip(), norm_email(email), norm_phone(phone)
    form = {"name": name, "email": email, "phone": phone}
    error = None
    if not name or len(name) > 100:
        error = "err_name_required"
    elif not EMAIL_RE.match(email) or len(email) > 254:
        error = "err_email_invalid"
    elif not PHONE_RE.match(phone):
        error = "err_phone_invalid"
    elif len(password) < 6 or len(password) > 200:
        error = "err_pass_short"
    elif get_user_by_email(email):
        error = "err_email_exists"
    if error:
        return render(request, "register.html", status_code=400, error=error, form=form)
    user = create_user(name, email, phone, password)
    return start_login(request, user)     # نرسل رابط الدخول مباشرة بعد إنشاء الحساب


# ---------- الخطوة 1: رابط الإيميل ← الخطوة 2: كود واتساب ----------
@app.get("/auth/verify")
def auth_verify(request: Request, token: str = ""):
    uid = read_login_token(token)
    user = get_user_by_id(uid) if uid else None
    if not user:
        return render(request, "login.html", status_code=400, error="err_link_invalid")
    request.session.clear()                      # منع session fixation
    request.session["pending_user_id"] = user["id"]
    issue_phone_code(user)
    return RedirectResponse("/verify-phone", status_code=303)


@app.get("/verify-phone")
def verify_phone_page(request: Request):
    user = get_user_by_id(request.session.get("pending_user_id") or 0)
    if not user:
        return RedirectResponse("/", status_code=303)
    entry = PhoneCode.get(user["id"])
    return render(request, "verify_phone.html", phone=mask_phone(user["phone"]),
                  dev_code=entry["code"] if (DEV_SHOW_CODES and entry) else None)


@app.post("/verify-phone")
def verify_phone(request: Request, code: str = Form("")):
    user = get_user_by_id(request.session.get("pending_user_id") or 0)
    if not user:
        return RedirectResponse("/", status_code=303)
    entry = PhoneCode.get(user["id"])
    err = None
    if not entry or entry["expires"] < time.time():
        err = "err_code_expired"
    else:
        entry["attempts"] += 1
        if entry["attempts"] > PHONE_CODE_MAX_ATTEMPTS:
            PhoneCode.pop(user["id"], None)
            request.session.clear()
            return render(request, "login.html", status_code=429, error="err_too_many")
        if hmac.compare_digest(entry["code"], code.strip()):
            PhoneCode.pop(user["id"], None)
            request.session.clear()
            request.session["user_id"] = user["id"]
            request.session["name"] = user["name"]
            return RedirectResponse("/home", status_code=303)
        err = "err_bad_code"
    return render(request, "verify_phone.html", status_code=400, error=err, phone=mask_phone(user["phone"]),
                  dev_code=(PhoneCode.get(user["id"]) or {}).get("code") if DEV_SHOW_CODES else None)


@app.post("/verify-phone/resend")
def verify_phone_resend(request: Request):
    user = get_user_by_id(request.session.get("pending_user_id") or 0)
    if not user:
        return RedirectResponse("/", status_code=303)
    issue_phone_code(user)
    return RedirectResponse("/verify-phone", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# ---------- الصفحة الرئيسية ----------
@app.get("/home")
def home(request: Request):
    if not current_uid(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "home.html", active="home")


# ---------- منتجاتي ----------
@app.get("/products")
def products(request: Request, product_id: int = None):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    selected = get_product(product_id) if product_id else None
    rows = list_entries(uid, selected["id"]) if selected else []
    return render(request, "products.html", active="products", products=list_products(),
                  selected=selected, rows=rows)


@app.post("/entry")
def add_entry(request: Request, product_id: int = Form(...),
              qty_start: float = Form(0), qty_end: float = Form(0),
              money_start: float = Form(0), money_end: float = Form(0)):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    if not get_product(product_id):
        return RedirectResponse("/products", status_code=303)
    save_entry(uid, product_id, qty_start, qty_end, money_start, money_end)
    return RedirectResponse(f"/products?product_id={product_id}", status_code=303)


# ---------- مصادري ----------
def parse_source_form(name, field, description, phone, location, images):
    """يتحقق من نموذج المصدر. الاسم وحده إجباري. يرجع (data, error_key)."""
    name, field, description, location = name.strip(), field.strip(), description.strip(), location.strip()
    phone = norm_phone(phone)
    imgs = [i.strip() for i in images if i and i.strip()][:4]
    form = {"name": name, "field": field, "description": description, "phone": phone,
            "location": location, "images": imgs}
    if not name or len(name) > 100:
        return form, "err_src_name"
    if len(field) > 100 or len(description) > 1000 or len(location) > 300:
        return form, "err_too_long"
    if phone and not PHONE_RE.match(phone):
        return form, "err_phone_invalid"
    if any(not valid_http_url(i) for i in imgs):
        return form, "err_url_invalid"
    return form, None


@app.get("/sources")
def sources_page(request: Request):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    return render(request, "sources.html", active="sources", sources=list_sources(uid))


@app.get("/sources/new")
def source_new_page(request: Request):
    if not current_uid(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "source_form.html", active="sources", form={"images": []},
                  action="/sources/new", is_edit=False)


@app.post("/sources/new")
def source_new(request: Request, name: str = Form(""), field: str = Form(""),
               description: str = Form(""), phone: str = Form(""), location: str = Form(""),
               img1: str = Form(""), img2: str = Form(""), img3: str = Form(""), img4: str = Form("")):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    data, err = parse_source_form(name, field, description, phone, location, [img1, img2, img3, img4])
    if err:
        return render(request, "source_form.html", status_code=400, active="sources", form=data,
                      action="/sources/new", is_edit=False, error=err)
    create_source(uid, data)
    return RedirectResponse("/sources", status_code=303)


@app.get("/sources/{source_id}/edit")
def source_edit_page(request: Request, source_id: str):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    src = get_source(uid, source_id)
    if not src:
        return RedirectResponse("/sources", status_code=303)
    return render(request, "source_form.html", active="sources", form=src,
                  action=f"/sources/{source_id}/edit", is_edit=True)


@app.post("/sources/{source_id}/edit")
def source_edit(request: Request, source_id: str, name: str = Form(""), field: str = Form(""),
                description: str = Form(""), phone: str = Form(""), location: str = Form(""),
                img1: str = Form(""), img2: str = Form(""), img3: str = Form(""), img4: str = Form("")):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    if not get_source(uid, source_id):
        return RedirectResponse("/sources", status_code=303)
    data, err = parse_source_form(name, field, description, phone, location, [img1, img2, img3, img4])
    if err:
        return render(request, "source_form.html", status_code=400, active="sources", form=data,
                      action=f"/sources/{source_id}/edit", is_edit=True, error=err)
    update_source(uid, source_id, data)
    return RedirectResponse("/sources", status_code=303)


# ---------- التخزين والاشتراك (الروبوتات الثلاثة في الـ footer) ----------
@app.post("/storage/subscription")
def storage_subscription(request: Request, code: str = Form(""), next_url: str = Form("/home", alias="next")):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    nxt = safe_next(next_url)
    fails = SubFails.get(uid, 0)
    if fails >= SUB_CODE_MAX_FAILS:
        return redirect_with(nxt, dlg="dlg-sub", msg="err_too_many")
    rec = find_subscription_code(code)
    if not rec or rec.get("used_by") not in (None, uid):
        SubFails[uid] = fails + 1
        return redirect_with(nxt, dlg="dlg-sub", msg="err_sub_code")
    rec["used_by"] = uid
    rec.setdefault("expires", date.today() + timedelta(days=rec["days"]))   # مرة واحدة: لا يتجدد بإعادة الإدخال
    set_storage(uid, "subscription", rec["code"])
    return redirect_with(nxt)


def _save_urls(request, mode, dlg, fields, next_url):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    nxt = safe_next(next_url)
    filled = {k: v.strip() for k, v in fields.items() if v and v.strip()}
    if not filled:
        return redirect_with(nxt, dlg=dlg, msg="err_url_required")
    if any(not valid_http_url(v) for v in filled.values()):
        return redirect_with(nxt, dlg=dlg, msg="err_url_invalid")
    set_storage(uid, mode, filled)     # ⚠️ قد يحوي مفاتيح سرّية: شفّر عند التخزين الحقيقي (doc.md)
    return redirect_with(nxt)


@app.post("/storage/local")
def storage_local(request: Request, products_url: str = Form(""), sources_url: str = Form(""),
                  next_url: str = Form("/home", alias="next")):
    return _save_urls(request, "local", "dlg-local",
                      {"products_url": products_url, "sources_url": sources_url}, next_url)


@app.post("/storage/cloud")
def storage_cloud(request: Request, sql_api: str = Form(""), nosql_api: str = Form(""),
                  next_url: str = Form("/home", alias="next")):
    return _save_urls(request, "cloud", "dlg-cloud",
                      {"sql_api": sql_api, "nosql_api": nosql_api}, next_url)


@app.post("/storage/disconnect")
def storage_disconnect(request: Request, mode: str = Form(""), next_url: str = Form("/home", alias="next")):
    uid = current_uid(request)
    if not uid:
        return RedirectResponse("/", status_code=303)
    if mode in ("subscription", "local", "cloud"):
        set_storage(uid, mode, None)
    return redirect_with(safe_next(next_url))
