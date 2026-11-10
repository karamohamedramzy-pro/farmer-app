import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, engine, get_db, SessionLocal
from .models import User, Product, DailyEntry

DEFAULT_PRODUCTS = [
    ("بطاطا", "Potato", "veg"), ("طماطم", "Tomato", "veg"), ("بصل", "Onion", "veg"),
    ("خيار", "Cucumber", "veg"), ("جزر", "Carrot", "veg"), ("فلفل", "Pepper", "veg"),
    ("تفاح", "Apple", "fruit"), ("برتقال", "Orange", "fruit"), ("عنب", "Grapes", "fruit"),
    ("تين", "Fig", "fruit"), ("رمان", "Pomegranate", "fruit"), ("موز", "Banana", "fruit"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # إنشاء الجداول وإضافة المنتجات الافتراضية عند أول تشغيل
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            for ar, en, t in DEFAULT_PRODUCTS:
                db.add(Product(name_ar=ar, name_en=en, type=t))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-me"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
pwd = CryptContext(schemes=["bcrypt"])


# ---------- الصفحة الأولى: تسجيل الدخول ----------
@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # أول مرة: إنشاء حساب تلقائي (احذف هذا الجزء لمنع التسجيل الحر)
        user = User(username=username, password_hash=pwd.hash(password))
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not pwd.verify(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "wrong_password"})
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse("/welcome", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# ---------- الصفحة الثانية: الترحيب والجدول ----------
@app.get("/welcome")
def welcome(request: Request, product_id: int = None, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        return RedirectResponse("/", status_code=303)
    products = db.query(Product).order_by(Product.id).all()
    rows, selected = [], None
    if product_id:
        selected = db.get(Product, product_id)
        rows = (db.query(DailyEntry)
                .filter_by(user_id=uid, product_id=product_id)
                .order_by(DailyEntry.entry_date.desc(), DailyEntry.id.desc()).all())
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "username": request.session["username"],
        "products": products, "selected": selected, "rows": rows})


@app.post("/entry")
def add_entry(request: Request, product_id: int = Form(...),
              qty_start: float = Form(0), qty_end: float = Form(0),
              money_start: float = Form(0), money_end: float = Form(0),
              db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid:
        return RedirectResponse("/", status_code=303)
    # الإشارات تُضبط تلقائياً: الفلاح يكتب أرقاماً عادية فقط
    db.add(DailyEntry(user_id=uid, product_id=product_id, entry_date=date.today(),
                      qty_start=abs(qty_start), qty_end=-abs(qty_end),
                      money_start=-abs(money_start), money_end=abs(money_end)))
    db.commit()
    return RedirectResponse(f"/welcome?product_id={product_id}", status_code=303)
