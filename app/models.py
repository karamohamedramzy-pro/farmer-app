# =====================================================================
# ⛔ غير مفعّل في نسخة BETA — لا يستورده أي ملف.
# الشكل النهائي للجداول. الأسماء والحقول نفسها مستعملة في البيانات
# التجريبية داخل main.py (Product / User / DailyEntry / Source ...).
#   - PostgreSQL (SQLAlchemy): User, Product, DailyEntry, SubscriptionCode, StorageSetting
#   - MongoDB   (pydantic)   : Source   ← مصادري
# =====================================================================
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Date, Float, DateTime, ForeignKey, JSON, UniqueConstraint
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)   # يُخزَّن بحروف صغيرة
    phone = Column(String, nullable=False)                            # رقم واتساب بصيغة دولية +...
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    type = Column(String, nullable=False)  # veg / fruit


class DailyEntry(Base):
    __tablename__ = "daily_entries"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "entry_date"),)  # سطر واحد لكل يوم
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    qty_start = Column(Float, default=0)     # كمية بداية اليوم (+)
    qty_end = Column(Float, default=0)       # ما بيع (-)
    money_start = Column(Float, default=0)   # المبلغ المدفوع (-)
    money_end = Column(Float, default=0)     # المبلغ المقبوض (+)


class SubscriptionCode(Base):
    """أكواد الاشتراك (الروبوت 1). يولّدها المبرمج ويعطيها للمشتركين."""
    __tablename__ = "subscription_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    days = Column(Integer, nullable=False)               # مدة الاشتراك
    products_limit_kb = Column(Integer, nullable=False)  # حد مساحة المنتجات
    sources_limit_kb = Column(Integer, nullable=False)   # حد مساحة المصادر
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires = Column(Date, nullable=True)                # يُحسب مرة واحدة عند أول تفعيل


class StorageSetting(Base):
    """إعدادات التخزين لكل مستخدم (الروبوتان 2 و3). mode: local | cloud"""
    __tablename__ = "storage_settings"
    __table_args__ = (UniqueConstraint("user_id", "mode"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(String, nullable=False)
    data = Column(JSON, nullable=False)  # ⚠️ قد يحوي مفاتيح سرّية: شفّره قبل الحفظ (انظر doc.md)


# ---------------------------------------------------------------------
# مصادري — مستند MongoDB (collection: sources). الاسم وحده إجباري.
# ---------------------------------------------------------------------
class Source(BaseModel):
    user_id: str                                              # id المستخدم في PostgreSQL كنص
    name: str = Field(min_length=1, max_length=100)           # إجباري
    field: Optional[str] = Field(default=None, max_length=100)        # المجال
    description: Optional[str] = Field(default=None, max_length=1000) # الوصف
    phone: Optional[str] = Field(default=None, max_length=20)         # رقم الهاتف
    location: Optional[str] = Field(default=None, max_length=300)     # الموقع (عنوان أو رابط خريطة)
    images: List[str] = Field(default_factory=list, max_length=4)     # روابط الصور: من 0 إلى 4 (url-img)
