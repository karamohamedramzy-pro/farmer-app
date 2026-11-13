import type {Entry, Source, Storage, StorageKind} from './mockData';

export type Session = {csrf:string; user:{name:string;email:string}|null; pending:{phone:string;dev_code:string|null}|null; dev_mode:boolean};
export type LoginResult = {email:string;dev_link:string|null};
export type BackendProduct = {id:number;name_ar:string;name_en:string;type:'veg'|'fruit'};
export type StorageState = Record<StorageKind,Storage>;
export class ApiError extends Error {
  constructor(public status:number, public code:string) { super(code); }
}
async function request<T>(path:string, options:RequestInit = {}):Promise<T> {
  let response:Response;
  try { response = await fetch(`/api${path}`, {...options, cache:'no-store', credentials:'same-origin'}); }
  catch { throw new ApiError(0, 'network'); }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, typeof body.detail === 'string' ? body.detail : 'server');
  return body as T;
}
export const getSession = () => request<Session>('/session');
async function mutate<T>(path:string, body:unknown = {}, method='POST'):Promise<T> {
  const {csrf} = await getSession();
  return request<T>(path, {method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)});
}
export const api = {
  login:(email:string)=>mutate<LoginResult>('/auth/login',{email}),
  register:(form:{name:string;email:string;phone:string;password:string})=>mutate<LoginResult>('/auth/register',form),
  verifyLink:(token:string)=>mutate<Session>('/auth/link',{token}),
  verifyCode:(code:string)=>mutate<Session>('/auth/code',{code}),
  resend:()=>mutate<Session>('/auth/resend'),
  logout:()=>mutate('/auth/logout'),
  products:()=>request<BackendProduct[]>('/products'),
  entries:(id:number)=>request<Entry[]>(`/products/${id}/entries`),
  saveEntry:(entry:Entry)=>mutate('/entries',entry),
  sources:()=>request<Source[]>('/sources'),
  saveSource:(source:Source,editing:boolean)=>mutate<Source>(editing?`/sources/${encodeURIComponent(source.id)}`:'/sources',source,editing?'PUT':'POST'),
  storage:()=>request<StorageState>('/storage'),
  setStorage:(kind:StorageKind,values:Record<string,string>)=>mutate<StorageState>(`/storage/${kind}`,values),
  disconnect:(kind:StorageKind)=>mutate<StorageState>(`/storage/${kind}/disconnect`),
};
