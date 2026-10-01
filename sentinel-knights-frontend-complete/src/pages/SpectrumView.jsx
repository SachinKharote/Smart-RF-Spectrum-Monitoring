import { Activity, Antenna, Gauge, Signal, Waves } 
from "lucide-react"; 
import LiveSpectrum from '../components/LiveSpectrum';
import WaterfallPanel from '../components/WaterfallPanel';
import EwBandTable from '../components/EwBandTable';
import {currentScan,spectrumBands} 
from '../data/mockData';
function SpectrumView()
{return <div className="space-y-4"><div className="grid grid-cols-4 gap-3">{[[Antenna,'Receiver Frequency','2.45 GHz','Current tune','text-blue-600','bg-blue-50'],[Gauge2,'Bandwidth',`${currentScan.bandwidth_mhz} MHz`,'Occupied BW','text-violet-600','bg-violet-50'],[Signal,'Signal Strength',`${currentScan.signal_strength} dBm`,'Current band','text-amber-600','bg-amber-50'],[Activity,'Active Bands','8','Across 0–6 GHz','text-emerald-600','bg-emerald-50']].map(([Icon,l,v,d,t,b])=><div key={l} className="card p-4"><div className="flex items-center gap-3"><div className={`grid h-10 w-10 place-items-center rounded-xl ${b}`}><Icon size={19} className={t}/></div><div><div className="text-[11px] text-slate-500">{l}</div><div className="mt-1 text-xl font-bold text-slate-900">{v}</div><div className="text-[10px] text-slate-400">{d}</div></div></div></div>)}</div><div className="grid grid-cols-[minmax(0,1.6fr)_1fr] gap-4"><LiveSpectrum bands={spectrumBands}/><EwBandTable bands={spectrumBands}/></div><WaterfallPanel/></div>}
export default SpectrumView;
