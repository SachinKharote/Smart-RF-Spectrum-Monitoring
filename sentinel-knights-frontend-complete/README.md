# Sentinel Knights — Complete Frontend

Frontend-only React/Vite dashboard matching the supplied Sentinel Knights reference and the two frontend responsibilities: live dashboard + analytics/scenario UI.

## Includes
- Dashboard with KPI cards, adaptive scan timeline, current scan, band priority, detection performance, detection log
- Spectrum View with live-spectrum-style visualization, band activity and waterfall view
- Scan Strategy with scenario/simulation UI and scheduler decision placeholder
- Emitters page with searchable emitter table
- Analytics page with comparison and performance charts
- Logs page with search/filter
- Settings page
- React + Tailwind CSS + Chart.js + Lucide icons

## Important
Mock data only. No RF simulator, ML algorithm, scheduler logic, FastAPI, WebSocket, or database is implemented.

## Run
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
```

Replace values in `src/data/mockData.js` or wire component props to the backend team's REST/WebSocket service later.
