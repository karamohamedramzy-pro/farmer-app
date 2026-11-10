from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    type = Column(String, nullable=False)  # veg / fruit


class DailyEntry(Base):
    __tablename__ = "daily_entries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    qty_start = Column(Float, default=0)     # كمية بداية اليوم (+)
    qty_end = Column(Float, default=0)       # ما بيع (-)
    money_start = Column(Float, default=0)   # المبلغ المدفوع (-)
    money_end = Column(Float, default=0)     # المبلغ المقبوض (+)
