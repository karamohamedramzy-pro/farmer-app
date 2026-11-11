# =====================================================================
# ⛔ غير مفعّل في نسخة BETA — لا يستورده أي ملف.
# يبقى هنا جاهزاً ليُفعَّل بعد التأكد من واجهة التطبيق (انظر doc.md).
# تحذير: استيراده بدون DATABASE_URL يسبب الخطأ:
#   ArgumentError: Could not parse SQLAlchemy URL from given URL string
# =====================================================================
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "")
# Coolify يعطي الرابط بصيغة postgres:// و SQLAlchemy تحتاج postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# MongoDB — مصادري (Source)            ⛔ كله تعليق، أزل التعليق عند التفعيل
# =====================================================================
# الملاحظات:
#  1) التبعية:  pymongo>=4.6,<5   (موجودة في requirements-db.txt).
#  2) على Coolify: New Resource ← Databases ← MongoDB ← Start، ثم انسخ الرابط
#     الداخلي (Internal URL) إلى متغير البيئة MONGODB_URI، وسمِّ القاعدة في MONGODB_DB.
#     فعّل Backups هناك أيضاً.
#  3) معمارية مزدوجة: PostgreSQL للمستخدمين والمنتجات والإدخالات، و MongoDB لـ sources فقط.
#     الربط بينهما عبر الحقل user_id (نص = id المستخدم في PostgreSQL). لا توجد مفاتيح
#     أجنبية بين القاعدتين، فاحذف مصادر المستخدم يدوياً عند حذف حسابه.
#  4) مسارات main.py دوال عادية (def) فتعمل مع pymongo المتزامن دون مشاكل.
#     لو حوّلتها إلى async def فاستعمل motor بدل pymongo.
#  5) في Mongo الـ id هو ObjectId: حوّله إلى نص عند الإرجاع (str(doc["_id"]))
#     وحوّل النص إلى ObjectId عند البحث. ولا تفترض أن النص صالح (ابتلع InvalidId).
#  6) تحقق من المدخلات في الخادم دائماً (الاسم إجباري، الصور ≤ 4 وروابطها http/https)،
#     ولا تعتمد على مستند الـ validator وحده. ويمكنك استعمال نموذج Source في models.py.
#  7) كل استعلام يجب أن يُقيَّد بـ user_id (انظر الدوال) حتى لا يرى مستخدم مصادر غيره.
#
# import os
# from bson import ObjectId
# from bson.errors import InvalidId
# from pymongo import MongoClient, ASCENDING
#
# MONGODB_URI = os.getenv("MONGODB_URI", "")
# MONGODB_DB = os.getenv("MONGODB_DB", "tbfarm")
#
# mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
# mongo_db = mongo_client[MONGODB_DB]
# sources = mongo_db["sources"]
# sources.create_index([("user_id", ASCENDING)])      # يُنفَّذ مرة عند الإقلاع (آمن للتكرار)
#
# # اختياري: قيد على مستوى القاعدة (إنشاء المجموعة مرة واحدة)
# # mongo_db.create_collection("sources", validator={"$jsonSchema": {
# #     "bsonType": "object", "required": ["user_id", "name"],
# #     "properties": {
# #         "name":   {"bsonType": "string", "minLength": 1, "maxLength": 100},
# #         "images": {"bsonType": "array", "maxItems": 4, "items": {"bsonType": "string"}},
# #     }}})
#
# def _src(doc):
#     """مستند Mongo ← dict بنفس شكل البيانات التجريبية في main.py"""
#     if not doc:
#         return None
#     doc["id"] = str(doc.pop("_id"))
#     return doc
#
# # ↓ هذه هي نفسها دوال "طبقة الوصول للبيانات" في main.py (نفس الأسماء والمدخلات)
# def list_sources(user_id):
#     return [_src(d) for d in sources.find({"user_id": str(user_id)}).sort("name", ASCENDING)]
#
# def get_source(user_id, source_id):
#     try:
#         oid = ObjectId(source_id)
#     except InvalidId:
#         return None
#     return _src(sources.find_one({"_id": oid, "user_id": str(user_id)}))
#
# def create_source(user_id, data):
#     doc = {**data, "user_id": str(user_id)}
#     doc["id"] = str(sources.insert_one(doc).inserted_id)   # insert_one يضيف _id إلى doc
#     doc.pop("_id", None)
#     return doc
#
# def update_source(user_id, source_id, data):
#     try:
#         oid = ObjectId(source_id)
#     except InvalidId:
#         return None
#     r = sources.update_one({"_id": oid, "user_id": str(user_id)}, {"$set": data})
#     return get_source(user_id, source_id) if r.matched_count else None
