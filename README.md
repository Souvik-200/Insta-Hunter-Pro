# 🕵️‍♂️ Insta-Hunter Pro
**Advanced Instagram OSINT & Digital Forensics CLI Tool**

Insta-Hunter Pro is a command-line OSINT toolkit for investigating Instagram profiles. It collects profile metadata, downloads media (posts & reels), and generates forensic reports (PDF / TXT / JSON). Designed for security researchers, incident responders, and privacy audits — use only on accounts you own or have permission to analyze.

---

## 🔥 Key Features

- Fetch profile metadata: username, followers, following, posts, reels, bio, profile picture URL.  
- Auto download: posts, reels and profile picture (uses `instaloader`).  
- Generate reports: PDF (with profile picture + QR code), TXT and JSON exports.  
- ZIP export: package downloaded evidence for sharing or analysis.  
- Animated CLI UI: radar scanner, progress bars, heartbeat animations for a tactical feel.  
- Username suggestion helper for follow-up reconnaissance.  
- Optional HaveIBeenPwned (HIBP) breach check integration (API key required).  
- Supports private profile access via Instaloader login (use only with authorization).  
- Unicode-safe PDF generation (tries system fonts, falls back safely).

---

## ⚠️ IMPORTANT — Responsible Use & Disclaimer

This tool is **for lawful** and **ethical** use only.  
Do **NOT** use it to invade privacy, harass, stalk, or collect data without permission.

You are solely responsible for compliance with local laws and platform terms of service. The author is not liable for misuse.

---

## 📦 Requirements

Tested on Python 3.8+.

Install dependencies:

```bash
pip install -r requirements.txt
# if not install any module then one by one install by pip command [for eg: pip install <module>]

OSINT_IG/
├── ig_osint.py          # Main CLI tool (entry point)
├── requirements.txt
├── README.md
└── output/
    ├── reports/         # PDF, TXT, JSON outputs
    └── downloads/       # Media downloads per username

cd /d/OSINT_IG        # Windows PowerShell/CMD
# or
cd ~/path/to/OSINT_IG # macOS / Linux

Run the tool
python ig_osint.py #[vscode terminal]

> ⚠️ **IMPORTANT WARNING – READ BEFORE USING**

Using this tool to send **too many requests to Instagram** (such as repeated metadata scans, automated profile scraping, or continuous downloading of posts/reels) may trigger Instagram’s **rate-limiting, temporary bans, security challenges, or permanent access blocks.**

Instagram may:

- 🚫 Temporarily block your **IP address**
- 🚫 Lock or restrict your **Instagram account**
- 🚫 Flag your **device / browser fingerprint**
- 🚫 Enforce **CAPTCHA, login verification, or 2FA**
- 🚫 Shadow-ban or fully revoke network access

This tool is intended for **moderate, controlled use** — not automated mass scraping.

To avoid being blocked:

- ⏳ Add delay between scans  
- 🌐 Use rotating IP/VPN only where legally allowed  
- 🔑 Use authenticated Instaloader login (only for accounts you own)  
- 🧪 Avoid running repeated high-volume tests  

**You are fully responsible for how you operate this tool. Unauthorized or excessive use may violate platform rules or applicable laws.**

