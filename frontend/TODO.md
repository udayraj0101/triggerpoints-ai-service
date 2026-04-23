# TODO: Expose Vite Project via Ngrok

## Steps from Approved Plan:
- [x] 1. Edit vite.config.js to add server.allowedHosts: ['all']
- [x] 2. Instruct user to restart Vite dev server (feedback received)
- [x] 3. Instruct user to restart ngrok tunnel (feedback: ngrok now points to wrong port 5143 instead of 5173)
- [x] 5. Update allowedHosts to ['.ngrok-free.dev'] regex (403 persisted with 'all')
- [ ] 4. Verify requests succeed (attempt_completion)

**Additional Issue Identified:**
Ngrok command used `ngrok http 5143` but Vite runs on 5173. Use `ngrok http 5173`. Ensure dev server is running before starting ngrok.

**Next:** Restart `npm run dev`, then `ngrok http 5173`, test URL.

