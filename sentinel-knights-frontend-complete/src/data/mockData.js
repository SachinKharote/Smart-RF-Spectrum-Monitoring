// FRONTEND-ONLY MOCK DATA. Replace with FastAPI/WebSocket data later.
export const dashboardKpis={detection_rate:78.4,false_alarm_rate:6.8,average_intercept_time:3.2,average_intercept_rate:4.7,current_scan:'2.45 GHz'};
export const scanTimeline=[
{time:1,band:2400,result:'miss'},{time:2,band:4800,result:'hit'},{time:3,band:5200,result:'miss'},{time:4,band:2450,result:'hit'},{time:5,band:3300,result:'miss'},{time:6,band:4800,result:'hit'},{time:7,band:2450,result:'hit'},{time:8,band:5200,result:'miss'},{time:9,band:2800,result:'hit'},{time:10,band:2450,result:'hit'},{time:11,band:5100,result:'miss'},{time:12,band:2450,result:'hit'}];
export const currentScan={band:2450,dwell_ms:150,priority:.91,bandwidth_mhz:20,signal_strength:-58,detection_probability:.72};
export const bandPriority=[{band:'2.4 GHz',priority:.91},{band:'4.8 GHz',priority:.73},{band:'5.2 GHz',priority:.51},{band:'3.3 GHz',priority:.43},{band:'900 MHz',priority:.29}];
export const detectionLog=[
{time:'12:14:32',frequency:2450,power:-52,result:'DETECTED',emitter:'E-07'},
{time:'12:14:28',frequency:5180,power:-61,result:'DETECTED',emitter:'E-03'},
{time:'12:14:15',frequency:1720,power:-68,result:'DETECTED',emitter:'E-11'},
{time:'12:13:52',frequency:4600,power:-55,result:'DETECTED',emitter:'E-02'},
{time:'12:13:21',frequency:3330,power:-70,result:'TRACKING',emitter:'E-09'},
{time:'12:12:48',frequency:900,power:-72,result:'DETECTED',emitter:'E-01'},
{time:'12:12:31',frequency:2800,power:-67,result:'MISSED',emitter:'—'}];
export const performance=[{time:0,adaptive:34,fixed:22},{time:5,adaptive:47,fixed:27},{time:10,adaptive:55,fixed:31},{time:15,adaptive:62,fixed:35},{time:20,adaptive:69,fixed:38},{time:25,adaptive:72,fixed:41},{time:30,adaptive:75,fixed:44},{time:35,adaptive:77,fixed:46},{time:40,adaptive:79,fixed:48},{time:45,adaptive:81,fixed:50},{time:50,adaptive:83,fixed:52},{time:55,adaptive:85,fixed:54},{time:60,adaptive:87,fixed:56}];
export const emitters=[
{id:'E-01',name:'Control Link',frequency:900,power:-72,bandwidth:10,status:'ACTIVE',hop:'2.1 s'},
{id:'E-02',name:'Wideband Node',frequency:4600,power:-55,bandwidth:40,status:'ACTIVE',hop:'1.5 s'},
{id:'E-03',name:'Telemetry',frequency:5180,power:-61,bandwidth:20,status:'TRACKING',hop:'4.2 s'},
{id:'E-07',name:'Tactical Radio',frequency:2450,power:-52,bandwidth:20,status:'ACTIVE',hop:'0.8 s'},
{id:'E-09',name:'Data Burst',frequency:3330,power:-70,bandwidth:25,status:'TRACKING',hop:'3.7 s'},
{id:'E-11',name:'Mobile Relay',frequency:1720,power:-68,bandwidth:12,status:'INACTIVE',hop:'—'}];
export const spectrumBands=[{band:900,strength:-72,activity:'LOW'},{band:1720,strength:-68,activity:'MEDIUM'},{band:2400,strength:-58,activity:'HIGH'},{band:2800,strength:-67,activity:'MEDIUM'},{band:3330,strength:-70,activity:'MEDIUM'},{band:4600,strength:-55,activity:'HIGH'},{band:4800,strength:-61,activity:'HIGH'},{band:5180,strength:-61,activity:'HIGH'}];
