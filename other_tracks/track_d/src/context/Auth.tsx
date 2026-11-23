import {createContext,useContext,useState} from 'react';import {api} from '../api/client';
const Ctx=createContext<any>(null);export const useAuth=()=>useContext(Ctx);export const homeOf=(r:string)=>(r==='Admin'||r==='Department')?'/admin':'/';
export function AuthProvider({children}:any){const [user,setUser]=useState<any>(()=>{try{return JSON.parse(localStorage.getItem('up_user')||'null')}catch{return null}});
const login=async(e:string,p:string,expect?:string)=>{const u=await api.login(e,p);if(expect&&u.role!==expect){localStorage.removeItem('up_token');throw new Error('role')}localStorage.setItem('up_user',JSON.stringify(u));setUser(u);return u};
const logout=()=>{localStorage.removeItem('up_token');localStorage.removeItem('up_user');setUser(null)};
return <Ctx.Provider value={{user,login,logout}}>{children}</Ctx.Provider>}
