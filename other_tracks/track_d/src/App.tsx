import {Routes,Route,Navigate,Outlet} from 'react-router-dom';import {useAuth,homeOf} from './context/Auth';import {AdminShell,CitizenShell} from './components/Shell';
import Login from './pages/Login';import Submit from './pages/Submit';import Track from './pages/Track';import Overview from './pages/Overview';import Queue from './pages/Queue';import Detail from './pages/Detail';import Alerts from './pages/Alerts';import Analytics from './pages/Analytics';
const Guard=({roles}:any)=>{const {user}=useAuth();if(!user)return <Navigate to="/login" replace/>;return roles.includes(user.role)?<Outlet/>:<Navigate to={homeOf(user.role)} replace/>};
export default function App(){return <Routes><Route path="/login" element={<Login/>}/>
<Route element={<Guard roles={['Citizen']}/>}><Route element={<CitizenShell/>}><Route path="/" element={<Submit/>}/><Route path="/track" element={<Track/>}/><Route path="/track/:id" element={<Track/>}/></Route></Route>
<Route element={<Guard roles={['Admin','Department']}/>}><Route element={<AdminShell/>}><Route path="/admin" element={<Overview/>}/><Route path="/admin/queue" element={<Queue/>}/><Route path="/admin/analytics" element={<Analytics/>}/><Route path="/admin/alerts" element={<Alerts/>}/>
<Route path="/admin/map" element={<Detail/>}/><Route path="/admin/map/:id" element={<Detail/>}/><Route path="/admin/incidents/:id" element={<Detail/>}/></Route></Route>
<Route path="*" element={<Navigate to="/login" replace/>}/></Routes>}
