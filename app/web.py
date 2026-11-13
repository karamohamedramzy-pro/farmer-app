"""Same-origin React/PWA host and JSON API for the existing in-memory BETA.

The data layer is deliberately the existing app.main data store, not a database.
Run with: uvicorn app.web:app --host 0.0.0.0 --port 8000
"""
import hmac
import math
import os
import re
import secrets
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app import main as data

WEB_SECRET = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
serializer = URLSafeTimedSerializer(WEB_SECRET, salt="react-login-link")
app = FastAPI(title="TB-farm API")
app.add_middleware(SessionMiddleware, secret_key=WEB_SECRET, same_site="lax", https_only=data.HTTPS_ONLY)
DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parent.parent / "frontend" / "dist")).resolve()


@app.middleware("http")
async def private_api_responses(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


def csrf(request: Request):
    expected = request.session.get('csrf')
    supplied = request.headers.get('X-CSRF-Token', '')
    if not expected or not hmac.compare_digest(expected.encode('utf-8'), supplied.encode('utf-8')):
        raise HTTPException(403, detail='csrf_invalid')


def current_user(request: Request):
    user = data.get_user_by_id(request.session.get('user_id') or 0)
    if not user:
        raise HTTPException(401, detail='not_authenticated')
    return user


def pending_user(request: Request):
    user = data.get_user_by_id(request.session.get('pending_user_id') or 0)
    if not user:
        raise HTTPException(401, detail='no_pending_login')
    return user


class EmailForm(BaseModel):
    email: str = Field(max_length=254)


class RegisterForm(EmailForm):
    name: str = Field(max_length=100)
    phone: str = Field(max_length=40)
    password: str = Field(max_length=200)


class TokenForm(BaseModel):
    token: str = Field(max_length=2048)


class CodeForm(BaseModel):
    code: str = Field(max_length=100)


class EntryForm(BaseModel):
    product_id: int
    qty_start: float = 0
    qty_end: float = 0
    money_start: float = 0
    money_end: float = 0


class SourceForm(BaseModel):
    name: str = Field(default='', max_length=100)
    field: str = Field(default='', max_length=100)
    description: str = Field(default='', max_length=1000)
    phone: str = Field(default='', max_length=40)
    location: str = Field(default='', max_length=300)
    images: list[str] = Field(default_factory=list, max_length=4)


class UrlForm(BaseModel):
    products_url: str = Field(default='', max_length=500)
    sources_url: str = Field(default='', max_length=500)
    sql_api: str = Field(default='', max_length=500)
    nosql_api: str = Field(default='', max_length=500)


def session_payload(request: Request):
    token = request.session.setdefault('csrf', secrets.token_urlsafe(32))
    user = data.get_user_by_id(request.session.get('user_id') or 0)
    pending = data.get_user_by_id(request.session.get('pending_user_id') or 0)
    code = data.PhoneCode.get(pending['id']) if pending else None
    return {
        'csrf': token,
        'user': {'name': user['name'], 'email': user['email']} if user else None,
        'pending': {'phone': data.mask_phone(pending['phone']),
                    'dev_code': code['code'] if data.DEV_SHOW_CODES and code else None} if pending else None,
        'dev_mode': data.DEV_SHOW_CODES,
    }


@app.get('/api/session')
def session(request: Request):
    return session_payload(request)


def send_link(request: Request, user: dict):
    token = serializer.dumps({"uid": user["id"], "n": secrets.token_hex(8)})
    base = data.BASE_URL or str(request.base_url).rstrip("/")
    link = f"{base}/auth/verify?token={token}"
    data.send_email(user['email'], 'TB-farm — رابط الدخول / Login link',
                    f'افتح الرابط للدخول (صالح 15 دقيقة):\nOpen this link to log in (valid 15 minutes):\n{link}\n')
    return {'email': user['email'], 'dev_link': link if data.DEV_SHOW_CODES else None}


@app.post('/api/auth/login', dependencies=[Depends(csrf)])
def login(form: EmailForm, request: Request):
    user = data.get_user_by_email(data.norm_email(form.email))
    if not user:
        raise HTTPException(404, detail='no_account')
    return send_link(request, user)


@app.post('/api/auth/register', dependencies=[Depends(csrf)])
def register(form: RegisterForm, request: Request):
    name, email, phone = form.name.strip(), data.norm_email(form.email), data.norm_phone(form.phone)
    if not name:
        raise HTTPException(400, detail='name_invalid')
    if not data.EMAIL_RE.fullmatch(email):
        raise HTTPException(400, detail='email_invalid')
    if not data.PHONE_RE.fullmatch(phone):
        raise HTTPException(400, detail='phone_invalid')
    if len(form.password) < 6:
        raise HTTPException(400, detail='password_invalid')
    if data.get_user_by_email(email):
        raise HTTPException(409, detail='email_exists')
    return send_link(request, data.create_user(name, email, phone, form.password))


@app.post('/api/auth/link', dependencies=[Depends(csrf)])
def verify_link(form: TokenForm, request: Request):
    try:
        uid = serializer.loads(form.token, max_age=data.LOGIN_LINK_MAX_AGE)["uid"]
    except (BadSignature, KeyError, TypeError):
        uid = None
    user = data.get_user_by_id(uid) if uid else None
    if not user:
        raise HTTPException(400, detail='link_invalid')
    request.session.clear()
    request.session['pending_user_id'] = user['id']
    data.issue_phone_code(user)
    return session_payload(request)


@app.post('/api/auth/code', dependencies=[Depends(csrf)])
def verify_code(form: CodeForm, request: Request):
    user = pending_user(request)
    entry = data.PhoneCode.get(user['id'])
    if not entry or entry['expires'] < time.time():
        raise HTTPException(400, detail='code_expired')
    if entry['attempts'] >= data.PHONE_CODE_MAX_ATTEMPTS:
        raise HTTPException(429, detail='code_locked')
    if not hmac.compare_digest(entry['code'].encode('utf-8'), form.code.strip().encode('utf-8')):
        entry['attempts'] += 1
        raise HTTPException(429 if entry['attempts'] >= data.PHONE_CODE_MAX_ATTEMPTS else 400,
                            detail='code_locked' if entry['attempts'] >= data.PHONE_CODE_MAX_ATTEMPTS else 'code_invalid')
    data.PhoneCode.pop(user['id'], None)
    request.session.clear()
    request.session['user_id'] = user['id']
    request.session['name'] = user['name']
    return session_payload(request)


@app.post('/api/auth/resend', dependencies=[Depends(csrf)])
def resend(request: Request):
    user = pending_user(request)
    data.issue_phone_code(user)
    return session_payload(request)


@app.post('/api/auth/logout', dependencies=[Depends(csrf)])
def logout(request: Request):
    request.session.clear()
    return {'ok': True}


@app.get('/api/products')
def products(request: Request):
    current_user(request)
    return data.list_products()


@app.get('/api/products/{product_id}/entries')
def entries(product_id: int, request: Request):
    user = current_user(request)
    if not data.get_product(product_id):
        raise HTTPException(404, detail='product_not_found')
    return [{'product_id': row['product_id'], 'date': row['entry_date'].isoformat(),
             'qty_start': row['qty_start'], 'qty_end': abs(row['qty_end']),
             'money_start': abs(row['money_start']), 'money_end': row['money_end']}
            for row in data.list_entries(user['id'], product_id)]


@app.post('/api/entries', dependencies=[Depends(csrf)])
def add_entry(form: EntryForm, request: Request):
    user = current_user(request)
    if not data.get_product(form.product_id):
        raise HTTPException(404, detail='product_not_found')
    values = [form.qty_start, form.qty_end, form.money_start, form.money_end]
    if any(not math.isfinite(n) or n < 0 or n > 1_000_000_000 for n in values):
        raise HTTPException(400, detail='number_invalid')
    data.save_entry(user['id'], form.product_id, *values)
    return {'ok': True}


def public_source(source: dict):
    return {key: source[key] for key in ('id', 'name', 'field', 'description', 'phone', 'location', 'images')}


@app.get('/api/sources')
def sources(request: Request):
    user = current_user(request)
    return [public_source(source) for source in data.list_sources(user['id'])]


def validate_source(form: SourceForm):
    result, error = data.parse_source_form(form.name, form.field, form.description, form.phone, form.location, form.images)
    if error:
        raise HTTPException(400, detail=error)
    if result['location'].lower().startswith(('http:', 'https:', 'www.')) and not data.valid_http_url(result['location']):
        raise HTTPException(400, detail='err_url_invalid')
    return result


@app.post('/api/sources', dependencies=[Depends(csrf)])
def add_source(form: SourceForm, request: Request):
    user = current_user(request)
    return public_source(data.create_source(user['id'], validate_source(form)))


@app.put('/api/sources/{source_id}', dependencies=[Depends(csrf)])
def edit_source(source_id: str, form: SourceForm, request: Request):
    user = current_user(request)
    if not data.get_source(user['id'], source_id):
        raise HTTPException(404, detail='source_not_found')
    return public_source(data.update_source(user['id'], source_id, validate_source(form)))


def storage_payload(uid: int):
    status = data.storage_status(uid)
    subscription = status['sub']
    result = {'subscription': {'status': 'off'}, 'local': {'status': 'off'}, 'cloud': {'status': 'off'}}
    if subscription:
        result['subscription'] = {'status': 'on' if subscription['active'] else 'expired',
            'code': '…' + subscription['tail'], 'days': subscription['days_left'],
            'product_used': subscription['p_used'], 'product_limit': subscription['p_limit'],
            'source_used': subscription['s_used'], 'source_limit': subscription['s_limit']}
    for kind, fields in [('local', ('products_url', 'sources_url')), ('cloud', ('sql_api', 'nosql_api'))]:
        if status[kind]:
            result[kind] = {'status': 'on', 'hosts': [status[kind][key] for key in fields if status[kind].get(key)]}
    return result


@app.get('/api/storage')
def storage(request: Request):
    return storage_payload(current_user(request)['id'])


@app.post('/api/storage/subscription', dependencies=[Depends(csrf)])
def subscription(form: CodeForm, request: Request):
    uid = current_user(request)['id']
    fails = data.SubFails.get(uid, 0)
    if fails >= data.SUB_CODE_MAX_FAILS:
        raise HTTPException(429, detail='too_many')
    rec = data.find_subscription_code(form.code)
    if not rec or rec.get('used_by') not in (None, uid):
        data.SubFails[uid] = fails + 1
        raise HTTPException(400, detail='subscription_invalid')
    rec['used_by'] = uid
    rec.setdefault('expires', date.today() + timedelta(days=rec['days']))
    data.set_storage(uid, 'subscription', rec['code'])
    return storage_payload(uid)


@app.post('/api/storage/{kind}', dependencies=[Depends(csrf)])
def store_urls(kind: str, form: UrlForm, request: Request):
    uid = current_user(request)['id']
    fields = {'local': ('products_url', 'sources_url'), 'cloud': ('sql_api', 'nosql_api')}.get(kind)
    if not fields:
        raise HTTPException(404, detail='storage_not_found')
    values = {key: getattr(form, key).strip() for key in fields if getattr(form, key).strip()}
    if not values or any(not data.valid_http_url(value) for value in values.values()):
        raise HTTPException(400, detail='url_invalid')
    data.set_storage(uid, kind, values)
    return storage_payload(uid)


@app.post('/api/storage/{kind}/disconnect', dependencies=[Depends(csrf)])
def disconnect(kind: str, request: Request):
    uid = current_user(request)['id']
    if kind not in ('subscription', 'local', 'cloud'):
        raise HTTPException(404, detail='storage_not_found')
    data.set_storage(uid, kind, None)
    return storage_payload(uid)


# Explicit SPA routes and public build assets; API paths never fall back to HTML.
SPA_ROUTE = re.compile(r'^/(?:|register|check-email|auth/verify|verify-phone|home|products|sources(?:/new|/[^/]+/edit)?|components)/?$')


@app.get('/{path:path}', include_in_schema=False)
def frontend(path: str, request: Request):
    if path.startswith('api/'):
        raise HTTPException(404)
    candidate = (DIST / path).resolve()
    if candidate.is_relative_to(DIST) and candidate.is_file():
        headers = {'Cache-Control': 'no-cache'} if path in ('sw.js', 'index.html', 'manifest.webmanifest') else {}
        return FileResponse(candidate, headers=headers)
    if SPA_ROUTE.fullmatch(request.url.path) and (DIST / 'index.html').is_file():
        return FileResponse(DIST / 'index.html', headers={'Cache-Control': 'no-cache'})
    raise HTTPException(404, detail='not_found')
