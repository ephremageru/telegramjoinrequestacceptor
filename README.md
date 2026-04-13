# 🚀 Auto-Join Acceptor & Broadcast CRM Bot

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Aiogram](https://img.shields.io/badge/Library-Aiogram_3.x-orange.svg)
![AsyncIO](https://img.shields.io/badge/Concurrency-AsyncIO-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Welcome to the **Auto-Join Acceptor & CRM** repository! 

This project is a high-performance, asynchronous Telegram automation tool built with `aiogram` 3.x. Designed for channel administrators and community managers, this bot fully automates the private channel onboarding flow.

---

## 📖 Table of Contents
1. [System Architecture](#-system-architecture)
2. [Tech Stack & Libraries](#-tech-stack--libraries)
3. [Deep Dive: Core Components](#-deep-dive-core-components)
4. [Engineering Challenges Solved](#-engineering-challenges-solved)
5. [Installation & Deployment](#-installation--deployment)
6. [Configuration (Environment Variables)](#-configuration)
7. [Admin Commands & Usage](#-admin-commands)
8. [Future Roadmap](#-future-roadmap)
9. [Security Notice](#-security-notice)

---

## 🏗️ System Architecture

This bot operates on an event-driven architecture, separating the onboarding flow from the administrative broadcast engine to ensure zero bottlenecks.

```text
[ Telegram User ]
       │ 1. Clicks Private Channel Link
       ▼
[ ChatJoinRequest ] ───► ( aiogram Event Router )
                               │
   ┌───────────────────────────┴───────────────────────────┐
   │                                                       │
   ▼ 2. Auto-Approve                                       ▼ 3. State Management
[ Channel Access Granted ]                           [ bot_data.json ]
                                                       - Adds User ID
   │                                                   - Increments Daily/Total Stats
   ▼ 4. Async Follow-up                                    │
[ Welcome DM Sent ] ◄──────────────────────────────────────┘
   (Optional/Toggleable)                                   │
                                                           │ 5. CRM Broadcast
[ Admin User ] ───► ( Sends /broadcast Command ) ──────────┘
                    - Loops through database
                    - Applies 0.05s async sleep (Rate Limit Protection)
                    - Clears blocked users (Handles TelegramForbiddenError)
```

---

## 💻 Tech Stack & Libraries

* **Language:** Python 3.10+
* **Core Framework:** `aiogram` 3.x (Modern, fully asynchronous Telegram Bot API framework)
* **Concurrency:** `AsyncIO` (Non-blocking I/O for high-throughput message broadcasting)
* **State Management:** JSON Persistence (`bot_data.json` for lightweight, dependency-free database tracking)
* **Configuration:** `python-dotenv` (Secure secrets management)

---

## 🔍 Deep Dive: Core Components

### 1. Automated Onboarding Funnel
The bot intercepts `chat_join_request` events. Instead of an admin manually clicking "Approve" hundreds of times, the bot instantly accepts the user and immediately sends a customized direct message welcoming them to the community.

### 2. CRM & State Tracking
Every unique user ID is captured and stored in a persistent `Set()`, which is routinely serialized to a local JSON file. The `BotState` class tracks:
* **All-Time Joins:** Total community acquisition.
* **Daily Joins:** Automatically resets at midnight using `date.today().isoformat()`.
* **Reachable Users:** The exact number of users who currently have an open DM with the bot.

### 3. Smart Broadcast Engine
Admins can push announcements to every user who has ever interacted with the bot. The engine tracks successful deliveries and failures in real-time, providing a post-broadcast analytics report.

---

## 🧠 Engineering Challenges Solved

Building a mass-messaging bot requires navigating strict API limitations. This project implements several production-grade safeguards:

* **Rate-Limit Padding:** Telegram restricts bots to ~30 messages per second. The broadcast engine implements an `await asyncio.sleep(0.05)` buffer between messages, ensuring 100% deliverability without hitting API rate limits.
* **Database Auto-Cleansing:** Over time, users delete their accounts or block the bot. When broadcasting, the script catches `TelegramForbiddenError`, tallies the failure, and automatically purges the blocked user from future broadcasts.
* **Graceful Shutdowns:** By wrapping the execution in a `try/except (KeyboardInterrupt, SystemExit)` block, the bot guarantees a final `state.save()` before the process dies, ensuring zero data loss even on forced termination.

---

## 🚀 Installation & Deployment

### Step 1: Clone the Repository
```bash
git clone https://github.com/ephremageru/telegramjoinrequestacceptor.git
cd telegramjoinrequestacceptor
```

### Step 2: Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
# On Windows use: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `.env` file in the root directory. **Never commit this file to version control.**

```env
# Get this from @BotFather
BOT_TOKEN=1234567890:YOUR_BOT_TOKEN_HERE

# Comma-separated list of Telegram User IDs that have admin access
ADMIN_IDS=1234567890, 0987654321
```

---

## 🛠️ Admin Commands

These commands are restricted via a custom `IsAdmin()` filter and will only respond to the IDs defined in your `.env` file. Furthermore, they only work in Direct Messages (Private Chats) to keep your bot secure.

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Registers the admin/user in the database. | `/start` |
| `/stats` | View daily/total joins and total reachable users. | `/stats` |
| `/status` | Check bot uptime, database health, and feature toggles. | `/status` |
| `/welcome_off` | Disables automated Welcome DMs (silent approvals). | `/welcome_off` |
| `/welcome_on` | Enables automated Welcome DMs. | `/welcome_on` |
| `/broadcast` | Sends a mass message to all users in the CRM. | `/broadcast 🚨 New Movie Uploaded!` |
| `/reset` | Resets analytic counters to 0 (Preserves user list). | `/reset` |

---

## ▶️ Running the Bot

To start the bot in polling mode:
```bash
python main.py
```
*(For production deployment on a VPS, it is recommended to run this script using `systemd`, `pm2`, or `nohup` to ensure it runs in the background 24/7).*

---

## 🗺️ Future Roadmap

- [ ] **SQLite Migration:** Move from `.json` to `aiosqlite` for faster querying when user base exceeds 50,000.
- [ ] **Multi-Channel Support:** Allow the bot to manage join requests across multiple distinct channels simultaneously.
- [ ] **Rich Media Broadcasts:** Upgrade the `/broadcast` command to support photos, videos, and inline buttons.
- [ ] **User Demographics:** Track which specific invite links users clicked to join (Invite Link Tracking).

---

## ⚠️ Security Notice

* **Secrets Management:** Ensure your `.env` file is listed in `.gitignore`.
* **Data Privacy:** The `bot_data.json` file contains the Telegram IDs of your users. Ensure this file is never exposed publicly to prevent scraping.

```text
# Example .gitignore additions
.env
bot_data.json
__pycache__/
venv/
```

---
*Built for scale. Designed for Community Managers.*