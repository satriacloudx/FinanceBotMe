# 🏦 FinanceHub - Business Finance Manager

Professional finance management platform for businesses and individuals. Comprehensive tracking, intelligent reporting, and actionable insights—all in one powerful Telegram bot.

## ✨ Features

### 💼 User Features
- **💰 Transaction Management** - Record income & expenses with interactive flow
- **📊 Financial Dashboard** - Real-time balance, income, expense tracking with analytics
- **📈 Visual Reports** - Generate professional Pie, Bar & Line charts
- **📥 Data Export** - Download reports in CSV or Excel format
- **💼 Business Mode** - Track debts and receivables for business operations
- **📋 Transaction History** - View recent transactions with detailed info
- **👑 Subscription System** - Free, Basic, and Premium tiers with different limits

### 🔐 Admin Panel
- **📊 System Statistics** - Monitor total users, transactions, and activity
- **📢 Broadcast Messaging** - Send announcements to all users
- **💾 Database Backup** - Download database backup (critical for Render Free Tier)
- **👥 User Management** - Export user list to CSV
- **👑 Subscription Management** - Approve and manage user subscriptions

### 👑 Subscription Tiers

**🆓 Free Plan**
- 50 transactions limit
- Basic features
- Pie charts only

**⭐ Basic Plan - Rp 29,000/month**
- 500 transactions
- All chart types
- Priority support

**👑 Premium Plan - Rp 79,000/month**
- Unlimited everything
- Advanced analytics
- Budget planning
- API access
- 24/7 support

See `SUBSCRIPTION_GUIDE.md` for details.

## 🚀 Quick Deploy to Render.com (FREE)

### Prerequisites
- GitHub account
- Render.com account (free)
- Telegram bot token from @BotFather
- Your Telegram user ID from @userinfobot

### Deployment Steps

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: FinanceHub Bot"
   git branch -M main
   git remote add origin https://github.com/yourusername/financehub-bot.git
   git push -u origin main
   ```

2. **Deploy to Render:**
   - Login to [render.com](https://render.com)
   - Click "New +" → **"Web Service"** (FREE tier!)
   - Connect your GitHub repository
   - Configure:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python bot.py`
   - Set environment variables:
     - `BOT_TOKEN` = Your bot token from @BotFather
     - `ADMIN_ID` = Your Telegram user ID from @userinfobot
     - `PYTHON_VERSION` = `3.10.0`
   - Click "Create Web Service"

3. **Set Webhook:**
   After deployment, open this URL in browser (replace with your values):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RENDER_URL>/<YOUR_BOT_TOKEN>
   ```
   
   Example:
   ```
   https://api.telegram.org/bot123456:ABC-DEF/setWebhook?url=https://financehub-bot.onrender.com/123456:ABC-DEF
   ```
   
   You should see: `{"ok":true,"result":true,"description":"Webhook was set"}`

4. **Done!** Bot is now online 🚀

**📝 Note:** Free tier may sleep after 15 min inactivity. Use [UptimeRobot](https://uptimerobot.com) (free) to ping your URL every 14 minutes to keep it awake.

See `SETUP_INSTRUCTIONS.txt` for detailed step-by-step guide.

## 📁 Project Structure

```
financehub-bot/
├── bot.py              # Main bot application
├── config.py           # Configuration & settings
├── db_helper.py        # Database operations
├── utils.py            # Utility functions (charts, export)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
├── render.yaml         # Render.com deployment config
├── LICENSE             # MIT License
├── README.md           # This file
├── SETUP_INSTRUCTIONS.txt  # Detailed setup guide
└── git_commands.txt    # Git commands reference
```

## 🛠️ Technology Stack

- **Python 3.10+**
- **python-telegram-bot v20+** (Async)
- **SQLite3** (Database)
- **Pandas** (Data processing)
- **Matplotlib & Seaborn** (Visualization)
- **OpenPyXL** (Excel export)

## 💡 Usage Tips

### For Users
1. Record transactions regularly for accurate tracking
2. Use appropriate categories for better reports
3. Review dashboard weekly to monitor finances
4. Export data monthly as backup

### For Admins
1. Backup database regularly (Render Free Tier is ephemeral!)
2. Monitor system stats to track user activity
3. Use broadcast for important announcements
4. Download user list for analysis

## ⚠️ Important Notes

### Render Free Tier
Render Free Tier has **ephemeral storage**. This means:
- Database may be lost on restart/redeploy
- **MUST backup database regularly** via Admin Panel
- Use "Backup Database" feature at least once a week

### Solutions:
1. Regular backups via Admin Panel → Backup Database
2. Upgrade to Render Paid Plan for persistent storage
3. Use external database (PostgreSQL, MongoDB)

## 🔒 Security

- Admin ID stored in environment variables (not in code)
- Bot TOKEN not hardcoded
- Admin panel only accessible by ADMIN_ID
- Silent rejection for non-admin users (no response)
- SQL injection prevention with parameterized queries

## 📝 License

MIT License - Free for personal and commercial use

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📞 Support

If you have questions or issues:
- Create a GitHub Issue
- Check the code documentation
- Review the README

## 🙏 Acknowledgments

- python-telegram-bot team for excellent library
- Telegram for Bot API
- Open source community

---

**Built with ❤️ using Python & python-telegram-bot**

**FinanceHub - Professional Finance Management Solution** 🚀
