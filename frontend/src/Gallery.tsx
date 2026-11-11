import React, {useState} from 'react';
import {Alert, Button, CodeInput, EmptyState, ImageMosaic, ProductTile, RobotButton, StatCard, StorageDialog, TextField, UsageBar} from './components';
import {products, type Storage, type StorageKind} from './mockData';
import type {Dict, Lang} from './i18n';

/** A small visual handoff: interaction controls intentionally use only mock state. */
export function Gallery({t,lang}:{t:Dict;lang:Lang}) {
 const [kind,setKind]=useState<StorageKind|null>(null);
 const [code,setCode]=useState('');
 const [state,setState]=useState<Record<StorageKind,Storage>>({subscription:{status:'off'},local:{status:'off'},cloud:{status:'off'}});
 return <><div className="page-heading"><div><span className="eyebrow">TB-FARM / UI</span><h1>{lang==='ar'?'مكتبة المكونات':'Component library'}</h1><p>{lang==='ar'?'عينة تفاعلية من حالات الواجهة':'An interactive sample of interface states'}</p></div></div>
 <div className="gallery-grid"><section className="panel gallery-panel"><h2>{lang==='ar'?'الأزرار والتنبيهات':'Buttons & alerts'}</h2><div className="gallery-buttons"><Button>{t.save}</Button><Button variant="outline">{t.cancel}</Button><Button variant="danger">{t.disconnect}</Button></div><Alert>{t.noAccount}</Alert><Alert kind="success">{t.saved}</Alert><TextField id="sample-field" label={t.email} error={t.invalidEmail} defaultValue="invalid"/><CodeInput value={code} onChange={setCode} t={t}/></section>
 <section className="panel gallery-panel"><h2>{lang==='ar'?'المنتجات والأرقام':'Products & numbers'}</h2><div className="gallery-tiles"><ProductTile product={products[0]} lang={lang} selected onClick={()=>{}}/><ProductTile product={products[6]} lang={lang} selected={false} onClick={()=>{}}/></div><div className="stat-grid"><StatCard label={t.latestRemaining} value={5}/><StatCard label={t.latestProfit} value={-200} sub={`${t.totalProfit}: +300$`}/></div><EmptyState icon="🌱">{t.noRecords}</EmptyState><EmptyState icon="🤝">{t.noSources}</EmptyState></section>
 <section className="panel gallery-panel"><h2>{lang==='ar'?'الصور':'Image mosaics'}</h2><div className="gallery-mosaics">{[0,1,2,3,4].map(n=><div key={n}><ImageMosaic images={Array(n).fill('/farm.jpg')} alt={t.sources}/><span>{n} / 4</span></div>)}</div></section>
 <section className="panel gallery-panel"><h2>{lang==='ar'?'الروبوتات وحالات التخزين':'Robots & storage states'}</h2><div className="gallery-robots"><RobotButton label={t.subscription} storage={{status:'off'}} onClick={()=>setKind('subscription')} t={t}/><RobotButton label={t.local} storage={{status:'on'}} onClick={()=>setKind('local')} t={t}/><RobotButton label={t.cloud} storage={{status:'expired'}} onClick={()=>setKind('cloud')} t={t}/></div><UsageBar label={t.productSpace} amount={500} max={512}/><p className="muted">{t.demoStorage}</p><div className="gallery-buttons">{(['subscription','local','cloud'] as const).map(k=><Button variant="outline" key={k} onClick={()=>setKind(k)}>{t[k]}</Button>)}</div></section></div>
 {kind&&<StorageDialog kind={kind} storage={state[kind]} t={t} onClose={()=>setKind(null)} onChange={s=>setState({...state,[kind]:s})}/>}</>;
}
