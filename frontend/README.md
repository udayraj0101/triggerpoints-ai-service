# TriggerPoints AI — Frontend

React + Vite frontend for the TriggerPoints3D AI chatbot.

**React 19** | **Vite** | **PM2** | **Port 5174**

---

## Project Structure

```
src/
├── App.jsx        # Main app component
├── App.css        # Styles
├── main.jsx       # Entry point
└── index.css      # Global styles

.env               # Environment variables (not committed)
.env.example       # Template
vite.config.js     # Vite config (port 5174)
```

---

## Local Development Setup

### 1. Clone & install

```bash
git clone https://github.com/YOUR_REPO/triggerpoints-ai-service-frontend.git
cd triggerpoints-ai-service-frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Local development
VITE_API_URL=http://localhost:8010
VITE_API_KEY=your_api_key
```

### 3. Run dev server

```bash
npm run dev
```

App runs at: http://localhost:5174

Make sure the backend is running at http://localhost:8010

---

## Server Deployment with PM2

### Prerequisites on server

```bash
# Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# PM2
sudo npm install -g pm2
```

### Deploy steps

```bash
# 1. Clone repo
git clone https://github.com/YOUR_REPO/triggerpoints-ai-service-frontend.git
cd triggerpoints-ai-service-frontend

# 2. Install dependencies
npm install

# 3. Create .env with production backend URL
cp .env.example .env
nano .env
```

Set in `.env` on the server:

```env
VITE_API_URL=http://YOUR_SERVER_IP:8010
VITE_API_KEY=your_production_api_key
```

```bash
# 4. Build for production
npm run build

# 5. Start with PM2 using vite preview
pm2 start ecosystem.config.cjs --only triggerpoints-frontend

# 6. Save and enable startup on reboot
pm2 save
pm2 startup   # follow the printed command
```

> The `ecosystem.config.cjs` file is in the backend repo root. Copy it to the server or run pm2 from the backend directory.

### PM2 commands

```bash
pm2 status                           # check running processes
pm2 logs triggerpoints-frontend      # view frontend logs
pm2 restart triggerpoints-frontend   # restart
pm2 stop triggerpoints-frontend      # stop
```

### Update deployed code

```bash
cd triggerpoints-ai-service-frontend
git pull origin main
npm install
npm run build
pm2 restart triggerpoints-frontend
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend URL (e.g. `http://YOUR_SERVER_IP:8010`) |
| `VITE_API_KEY` | Yes | Must match backend `API_KEY` |

> Vite embeds these at build time. After changing `.env` you must run `npm run build` again and restart PM2.

---

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server on port 5174 |
| `npm run build` | Build for production into `dist/` |
| `npm run preview` | Preview production build on port 5174 |
| `npm run lint` | Run ESLint |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API calls failing | Check `VITE_API_URL` points to correct backend port (8010) |
| 401 errors | Check `VITE_API_KEY` matches backend `API_KEY` in `.env` |
| CORS errors | Backend allows all origins by default — check backend is running |
| Port 5174 in use | `lsof -i :5174` then kill the process |
| Changes not showing | Rebuild: `npm run build` then `pm2 restart triggerpoints-frontend` |
