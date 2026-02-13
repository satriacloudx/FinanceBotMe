# 🚀 Deploy ke Render.com - FREE

## Quick Deploy (5 Menit)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "CuanFlow Bot"
git remote add origin https://github.com/username/cuanflow-bot.git
git push -u origin main
```

### 2. Deploy to Render
1. Login: https://dashboard.render.com
2. New + → **Web Service**
3. Connect GitHub repo
4. Configure:
   ```
   Name: cuanflow-bot
   Runtime: Python 3
   Build: pip install -r requirements.txt
   Start: python main.py
   Instance: Free
   ```
5. Environment Variables:
   ```
   TELEGRAM_BOT_TOKEN = your_token
   ADMIN_IDS = your_telegram_id
   ```
6. Click **Create Web Service**

**IMPORTANT**: Project includes `runtime.txt` which specifies Python 3.11.9 (compatible with all dependencies). Render will automatically use this version.

### 3. Done!
- Wait 2-3 minutes
- Bot is live! 🎉

## Get Credentials

### Bot Token
1. Open Telegram
2. Search @BotFather
3. /newbot
4. Copy token

### Your Telegram ID
1. Search @userinfobot
2. Start chat
3. Copy your ID

## Test Bot
```
/start - Should respond
/admin - Should show admin menu
```

## 💾 Database Persistence

### How It Works
1. **Database di-commit ke GitHub** (`finance.db`)
2. Setiap deploy, database ikut ter-deploy
3. Update code → Push → Redeploy
4. **Database tetap ada!** ✅

### Workflow
```bash
# 1. Update code
nano handlers/start.py

# 2. Commit & push (database ikut)
git add .
git commit -m "Update feature"
git push origin main

# 3. Render auto-redeploy
# Database tetap ada! ✅
```

### Backup Strategy
```
1. Regular backup via /admin
2. Download backup file
3. Replace finance.db di repo
4. Push to GitHub
5. Redeploy
```

### Important
✅ **Database included in repo**
- Persists across deploys
- No data loss on restart
- Update code safely

⚠️ **Backup regularly!**
- Via /admin → Backup
- Save to safe place
- Restore if needed

## 🔧 Troubleshooting

### Build Failed (Python Version)
If you see pandas compilation errors:
- ✅ Make sure `runtime.txt` exists (specifies Python 3.11.9)
- ✅ Render will automatically use the correct Python version
- ✅ Redeploy if needed

### Bot Not Responding
1. Check Render logs
2. Verify TELEGRAM_BOT_TOKEN
3. Check bot is running

### Database Issues
1. Check finance.db in repo
2. Verify .gitignore allows it
3. Restore from backup if needed

---

**Free tier = Always on, no sleep!** 🎉
