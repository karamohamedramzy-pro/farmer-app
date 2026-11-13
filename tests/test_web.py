"""JSON integration contract for the React/PWA host."""
from copy import deepcopy
from urllib.parse import urlsplit, parse_qs
import secrets

import pytest
from fastapi.testclient import TestClient
from app import main as data
from app import web


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    users, entries, sources, subs = map(deepcopy, (data.User, data.DailyEntry, data.Source, data.SubscriptionCode))
    phone_codes, settings, sub_fails = map(deepcopy, (data.PhoneCode, data.StorageSetting, data.SubFails))
    monkeypatch.setattr(data, 'DEV_SHOW_CODES', True)
    monkeypatch.setattr(data, 'send_email', lambda *args: None)
    monkeypatch.setattr(data, 'send_whatsapp', lambda *args: None)
    yield
    data.User[:], data.DailyEntry[:], data.Source[:], data.SubscriptionCode[:] = users, entries, sources, subs
    for d, original in ((data.PhoneCode, phone_codes), (data.StorageSetting, settings), (data.SubFails, sub_fails)):
        d.clear(); d.update(original)


def client():
    return TestClient(web.app, follow_redirects=False)


def mutate(c, path, payload, method='post'):
    token = c.get('/api/session').json()['csrf']
    return getattr(c, method)(path, json=payload, headers={'X-CSRF-Token': token})


def new_user(c):
    email = f'test-{secrets.token_hex(5)}@example.com'
    response = mutate(c, '/api/auth/register', {'name':'Test', 'email':email, 'phone':'+966500001234', 'password':'secret1'})
    assert response.status_code == 200
    return email, response.json()['dev_link']


def sign_in(c, link):
    token = parse_qs(urlsplit(link).query)['token'][0]
    response = mutate(c, '/api/auth/link', {'token':token})
    assert response.status_code == 200
    code = response.json()['pending']['dev_code']
    response = mutate(c, '/api/auth/code', {'code':code})
    assert response.status_code == 200


def test_csrf_and_authentication():
    c=client()
    assert c.get('/api/products').status_code == 401
    assert c.post('/api/auth/login', json={'email':'demo@example.com'}).status_code == 403
    token=c.get('/api/session').json()['csrf']
    assert c.post('/api/auth/login', json={'email':'demo@example.com'}, headers={'X-CSRF-Token':token}).status_code == 200
    assert c.get('/api/session').headers['cache-control'] == 'no-store'
    assert mutate(c, '/api/auth/link', {'token':'invalid'}).status_code == 400


def test_registration_two_step_and_logout():
    c=client(); email, link=new_user(c)
    assert urlsplit(link).path == '/auth/verify'
    assert mutate(c, '/api/auth/register', {'name':'Test','email':email,'phone':'+966500001234','password':'secret1'}).status_code == 409
    token=parse_qs(urlsplit(link).query)['token'][0]
    pending=mutate(c,'/api/auth/link',{'token':token}).json()
    assert pending['pending']['phone'].endswith('1234')
    assert c.get('/api/products').status_code == 401
    code=pending['pending']['dev_code']
    wrong='000000' if code!='000000' else '111111'
    assert mutate(c, '/api/auth/code', {'code':wrong}).status_code == 400
    assert mutate(c, '/api/auth/code', {'code':code}).status_code == 200
    assert c.get('/api/session').json()['user']['email'] == email
    assert len(c.get('/api/products').json()) == 12
    assert mutate(c,'/api/auth/logout',{}).status_code == 200
    assert c.get('/api/products').status_code == 401


def test_lock_resend_and_hidden_development_codes(monkeypatch):
    c=client(); _,link=new_user(c)
    token=parse_qs(urlsplit(link).query)['token'][0]
    first=mutate(c,'/api/auth/link',{'token':token}).json()
    wrong='000000' if first['pending']['dev_code']!='000000' else '111111'
    for _ in range(4): assert mutate(c,'/api/auth/code',{'code':wrong}).status_code==400
    assert mutate(c,'/api/auth/code',{'code':wrong}).status_code==429
    assert mutate(c,'/api/auth/code',{'code':first['pending']['dev_code']}).status_code==429
    monkeypatch.setattr(data,'DEV_SHOW_CODES',False)
    assert mutate(c,'/api/auth/resend',{}).json()['pending']['dev_code'] is None
    assert mutate(c,'/api/auth/login',{'email':'demo@example.com'}).json()['dev_link'] is None


def test_entries_sources_and_owner_isolation():
    a,b=client(),client(); _,link_a=new_user(a); _,link_b=new_user(b);sign_in(a,link_a);sign_in(b,link_b)
    assert mutate(a,'/api/entries',{'product_id':2,'qty_start':30,'money_start':1000}).status_code==200
    assert mutate(a,'/api/entries',{'product_id':2,'qty_end':25,'money_end':1500}).status_code==200
    rows=a.get('/api/products/2/entries').json(); assert len(rows)==1
    assert [rows[0][k] for k in ('qty_start','qty_end','money_start','money_end')]==[30,25,1000,1500]
    assert b.get('/api/products/2/entries').json()==[]
    assert mutate(a,'/api/entries',{'product_id':2,'qty_start':-1}).status_code==400
    assert mutate(a,'/api/entries',{'product_id':999}).status_code==404
    assert mutate(a,'/api/sources',{'name':'','images':[]}).status_code==400
    assert mutate(a,'/api/sources',{'name':'bad','images':['javascript:alert(1)']}).status_code==400
    src=mutate(a,'/api/sources',{'name':'Farm','phone':'+966500001234','images':[]}).json()
    assert len(a.get('/api/sources').json())==1 and b.get('/api/sources').json()==[]
    assert mutate(b,f"/api/sources/{src['id']}",{'name':'other'},'put').status_code==404
    assert mutate(a,f"/api/sources/{src['id']}",{'name':'Updated'},'put').json()['name']=='Updated'


def test_storage_masks_urls_and_uses_server_values():
    c=client();_,link=new_user(c);sign_in(c,link)
    result=mutate(c,'/api/storage/local',{'products_url':'https://user:secret@example.com/private?key=secret'}).json()
    assert result['local']['status']=='on'
    assert 'example.com' in str(result) and 'secret' not in str(result) and 'private' not in str(result)
    sub=mutate(c,'/api/storage/subscription',{'code':'FARM-DEMO-365'}).json()['subscription']
    assert sub['status']=='on' and sub['days']==365 and sub['product_limit']==5120
    assert mutate(c,'/api/storage/local/disconnect',{}).json()['local']['status']=='off'


def test_spa_routing_and_no_api_html_fallback(tmp_path,monkeypatch):
    (tmp_path/'index.html').write_text('REACT-SHELL')
    (tmp_path/'sw.js').write_text('WORKER')
    monkeypatch.setattr(web,'DIST',tmp_path)
    c=client()
    assert c.get('/sources/abc123/edit').text=='REACT-SHELL'
    assert c.get('/auth/verify?token=xyz').text=='REACT-SHELL'
    assert c.get('/sw.js').headers['cache-control']=='no-cache'
    assert c.get('/api/missing').status_code==404
    assert c.get('/assets/missing.js').status_code==404
