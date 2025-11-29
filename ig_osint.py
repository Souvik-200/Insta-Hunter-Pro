#!/usr/bin/env python3
"""
IG OSINT CLI Menu Tool
- Interactive menu for profile analysis, media download, PDF report, zip export.
- Optional: provide INSTALOADER_LOGIN and HIBP_API_KEY when needed.
"""

import os
import time, sys
import re
import sys
import time
import json
import shutil
import getpass
import requests
from tabulate import tabulate
from colorama import Fore, Back, Style, init
from fpdf import FPDF
import instaloader
init(autoreset=True)
# ---------- Config ----------
OUTPUT_DIR = "output"
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")
DOWNLOADS_DIR = os.path.join(OUTPUT_DIR, "downloads")
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# =========================
# Animated UI helpers added
# =========================

def radar_scan(duration=6):
    """
    Animated ASCII radar / scanning indicator.
    Non-blocking to output (blocks only for 'duration' seconds while showing animation).
    """
    frames = [
        " [◐] Scanning target...",
        " [◓] Scanning target...",
        " [◑] Scanning target...",
        " [◒] Scanning target...",
        " [✦] Triangulating signals...",
        " [✸] Checking metadata...",
        " [✹] Collecting intelligence...",
        " [✦] Finalizing OSINT..."
    ]
    start = time.time()
    try:
        while time.time() - start < duration:
            for frame in frames:
                # break early if time exceeded
                if time.time() - start >= duration:
                    break
                sys.stdout.write(f"\r{Fore.CYAN}{frame}{Style.RESET_ALL}")
                sys.stdout.flush()
                time.sleep(0.12)
    except KeyboardInterrupt:
        # allow user to interrupt animations
        sys.stdout.write("\r")
        sys.stdout.flush()
        return
    sys.stdout.write(f"\r{Fore.GREEN}[✔] Scan Completed.{Style.RESET_ALL}          \n")
    sys.stdout.flush()

def progress_bar(task="Processing", duration=4):
    """
    Simple progress bar that runs for 'duration' seconds.
    """
    total = 30
    interval = max(duration / total, 0.01)
    try:
        for i in range(total + 1):
            filled = "█" * i
            empty = "." * (total - i)
            sys.stdout.write(f"\r{Fore.YELLOW}{task}: [{filled}{empty}] {int((i/total)*100)}%{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        return
    sys.stdout.write("\n")
    sys.stdout.flush()

def heartbeat(text="Establishing secure channel"):
    """
    Short heartbeat animation used for authentication / external checks.
    """
    try:
        for i in range(3):
            sys.stdout.write(f"\r{Fore.CYAN}▮▯ {text} ▯▮{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.35)
            sys.stdout.write(f"\r{Fore.CYAN}▯▮ {text} ▮▯{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(0.35)
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        return
    sys.stdout.write(f"\r{Fore.GREEN}[✔] {text} - Done.{Style.RESET_ALL}\n")
    sys.stdout.flush()

# ---------- Helpers ----------
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def extract_username(url_or_username):
    if not url_or_username:
        return None
    url_or_username = url_or_username.strip()
    # If URL provided
    m = re.search(r"instagram\.com/([^/?#]+)", url_or_username, re.IGNORECASE)
    if m:
        return m.group(1).rstrip('/')
    # Bare username
    return url_or_username.split()[0]

def suggest_usernames(username):
    base = re.sub(r'\W+', '', username)[:20]
    return [f"{base}_official", f"{base}_real", f"{base}123", f"{base}_01", f"{base}.official"]

# ---------- Instaloader functions ----------
def create_instaloader_session(login_user=None, login_pass=None, sessionfile=None):
    L = instaloader.Instaloader(dirname_pattern=".", download_pictures=False, download_videos=False,
                                save_metadata=False, post_metadata_txt_pattern="")
    try:
        if login_user and login_pass:
            L.login(login_user, login_pass)
        elif sessionfile:
            L.load_session_from_file(sessionfile)
    except Exception as e:
        print(Fore.YELLOW + f"[!] Instaloader login/session failed: {e}" + Style.RESET_ALL)
    return L

def fetch_profile(L, username):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        # Count reels (video) - try, but can be slow for many posts
        reel_count = None
        try:
            reel_count = sum(1 for p in profile.get_posts() if getattr(p, "typename", "") == "GraphVideo")
        except Exception:
            reel_count = None
        data = {
            "username": profile.username,
            "profile_id": profile.userid,
            "is_private": bool(profile.is_private),
            "is_verified": bool(profile.is_verified),
            "followers": profile.followers,
            "following": profile.followees,
            "total_posts": profile.mediacount,
            "reels": reel_count,
            "biography": profile.biography,
            "profile_pic_url": profile.profile_pic_url,
        }
        return True, data, profile
    except Exception as e:
        return False, str(e), None

# ---------- Download media ----------
def download_media(profile, username, login_user=None, login_pass=None):
    target_folder = os.path.join(DOWNLOADS_DIR, username)
    os.makedirs(target_folder, exist_ok=True)
    # Use instaloader to download profile into target folder
    # We create a new Instaloader with dirname_pattern = target_folder
    L = instaloader.Instaloader(dirname_pattern=target_folder, download_pictures=True, download_videos=True,
                                save_metadata=False, post_metadata_txt_pattern="")
    try:
        if login_user and login_pass:
            try:
                L.login(login_user, login_pass)
            except Exception as e:
                print(Fore.YELLOW + f"[!] Login failed for media download: {e}" + Style.RESET_ALL)
        L.download_profile(profile, profile_pic_only=False)
        return True, target_folder
    except Exception as e:
        return False, str(e)

# ---------- Zip folder ----------
def zip_folder(folder_path, out_base):
    try:
        archive = shutil.make_archive(out_base, 'zip', folder_path)
        return True, archive
    except Exception as e:
        return False, str(e)

# ---------- HIBP breach check (optional) ----------
def hibp_breach_check(account, api_key=None):
    """
    If api_key provided, calls HIBP 'Breached Account' or 'Account' endpoints.
    Otherwise returns a placeholder text.
    """
    # show a heartbeat animation if user provided a real api_key (visual only)
    if api_key:
        heartbeat("Querying breach DB")
    if not api_key:
        return "Not checked (provide HIBP API key in menu to enable)"
    try:
        # HIBP API v3: https://haveibeenpwned.com/API/v3
        # Example: https://haveibeenpwned.com/api/v3/breachedaccount/{account}
        headers = {"hibp-api-key": api_key, "user-agent": "IG-OSINT-CLI"}
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{account}"
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            breaches = r.json()
            return f"Breached in {len(breaches)} breach(es): " + ", ".join([b.get("Name") for b in breaches])
        elif r.status_code == 404:
            return "No breach found"
        else:
            return f"HIBP check error: HTTP {r.status_code}"
    except Exception as e:
        return f"HIBP check failed: {e}"

# ---------- PDF Generation (Unicode-safe) ----------
def find_unicode_font():
    """
    Try common font locations for a Unicode-capable TTF:
    - Windows Arial Unicode MS
    - DejaVuSans in common linux paths
    - current folder DejaVuSans.ttf
    Returns path or None.
    """
    candidates = [
        r"C:\Windows\Fonts\arialuni.ttf",
        r"C:\Windows\Fonts\ARIALUNI.TTF",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        r"/usr/share/fonts/dejavu/DejaVuSans.ttf",
        os.path.join(os.getcwd(), "DejaVuSans.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # search system fonts for DejaVu
    for root, dirs, files in os.walk("/usr/share/fonts", topdown=True):
        for f in files:
            if "DejaVuSans" in f:
                return os.path.join(root, f)
    return None

def remove_emojis(text):
    import re
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

def generate_pdf_report(data_dict, username, pdf_path=None):
    if pdf_path is None:
        pdf_path = os.path.join(REPORTS_DIR, f"{username}_report.pdf")

    # ---------------------------
    # Table data
    # ---------------------------
    rows = [
        ["Username", data_dict.get("username", "")],
        ["Profile ID", data_dict.get("profile_id", "")],
        ["Private?", "Yes" if data_dict.get("is_private") else "No"],
        ["Verified?", "Yes" if data_dict.get("is_verified") else "No"],
        ["Followers", data_dict.get("followers", "")],
        ["Following", data_dict.get("following", "")],
        ["Total Posts", data_dict.get("total_posts", "")],
        ["Reels (videos)", data_dict.get("reels", "Unknown")],
    ]

    # Calculate column width for stable monospace PDF rendering
    max_key_len = max(len(r[0]) for r in rows)
    max_val_len = max(len(str(r[1])) for r in rows)

    # Build manual ASCII table (Adobe-safe)
    top_border    = "╔" + ("═" * (max_key_len + 2)) + "╦" + ("═" * (max_val_len + 2)) + "╗"
    middle_border = "╠" + ("═" * (max_key_len + 2)) + "╬" + ("═" * (max_val_len + 2)) + "╣"
    bottom_border = "╚" + ("═" * (max_key_len + 2)) + "╩" + ("═" * (max_val_len + 2)) + "╝"

    table_lines = [top_border]

    for i, (k, v) in enumerate(rows):
        table_lines.append(
            f"║ {k.ljust(max_key_len)} ║ {str(v).ljust(max_val_len)} ║"
        )
        if i < len(rows) - 1:
            table_lines.append(middle_border)

    table_lines.append(bottom_border)

    suggestion_text = "Suggested usernames → " + ", ".join(suggest_usernames(username))

    full_report = f"INSTAGRAM OSINT REPORT\n\n" + "\n".join(table_lines) + "\n\n" + suggestion_text

    # ---------------------------
    # PDF Setup
    # ---------------------------
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    left_margin = 15
    safe_width = pdf.w - (left_margin * 2)

    # ---------------------------
    # Insert Profile Photo
    # ---------------------------
    profile_pic = None
    downloads_folder = os.path.join(DOWNLOADS_DIR, username)

    if os.path.isdir(downloads_folder):
        for file in os.listdir(downloads_folder):
            if "profile" in file.lower() and file.lower().endswith((".jpg", ".jpeg", ".png")):
                profile_pic = os.path.join(downloads_folder, file)
                break

    if profile_pic:
        try:
            pdf.image(profile_pic, x=left_margin, y=15, w=35, h=35)
        except:
            pass

    pdf.set_y(60)

    # ---------------------------
    # Use DejaVuSansMono (Adobe Compatible)
    # ---------------------------
    font_path = os.path.join(os.getcwd(), "DejaVuSansMono.ttf")

    if os.path.exists(font_path):
        pdf.add_font("DVMono", "", font_path, uni=True)
        pdf.set_font("DVMono", "", 9)
        safe_text = remove_emojis(full_report)
        for line in safe_text.split("\n"):
            pdf.multi_cell(safe_width, 5, line)
    else:
        # Hard fallback
        pdf.set_font("Courier", size=9)
        safe_text = remove_emojis(full_report)
        for line in safe_text.split("\n"):
            pdf.multi_cell(safe_width, 5, line)

    # ---------------------------
    # Footer Branding
    # ---------------------------
    pdf.set_y(-18)
    pdf.set_font("Courier", "I", 9)
    pdf.cell(0, 6, "Generated by CYBER-OPERATION-X", align="C")

    pdf.output(pdf_path)

    # ---------------------------
    # TXT + JSON Export
    # ---------------------------
    txt_path = os.path.join(REPORTS_DIR, f"{username}_report.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_report)

    json_path = os.path.join(REPORTS_DIR, f"{username}_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4, ensure_ascii=False)

    return True, pdf_path


# ---------- CLI Menu ----------
def print_banner():
    clear()
    print(Fore.RED+r"""
  _ _|   \  |   ___| __ __|   \           |   |  |   |   \  | __ __|  ____|   _ \        _ \    _ \    _ \  
   |     \ | \___ \    |    _ \          |   |  |   |    \ |    |    __|    |   |      |   |  |   |  |   | 
   |   |\  |       |   |   ___ \ _____|  ___ |  |   |  |\  |    |    |      __ <       ___/   __ <   |   | 
 ___| _| \_| _____/   _| _/    _\       _|  _| \___/  _| \_|   _|   _____| _| \_\     _|     _| \_\ \___/  
                                                                                                           
            ⚔  IG OSINT FRAMEWORK — CYBER OPERATION-X  ⚔
                       🔰 Souvik Sarkar🔰
    """ + Style.RESET_ALL)

def main_menu():
    print_banner()
    print(Fore.YELLOW+"====================================================\n")
    print(f"{Fore.RED} 📌 FIRST RUN OPTION 1:{Style.RESET_ALL} {Fore.GREEN} FETCH METADATA 📌{Style.RESET_ALL}\n")
    print(Fore.YELLOW+"====================================================\n")
    print(Fore.BLUE+"⚔️  TOOLS MENU:📃\n")
    print(Fore.GREEN+"1️⃣   Analyze Instagram profile 🔎 (Fetch Metadata)")
    print(Fore.GREEN+"2️⃣   Download posts & reels for a Profile 📩")
    print(Fore.GREEN+"3️⃣   Generate PDF report for last fetched profile 📂")
    print(Fore.GREEN+"4️⃣   Create ZIP of downloaded media for last profile 🗂️")
    print(Fore.GREEN+"5️⃣   Set Instaloader login 🌐 (for private profile access🛡️ )")
    print(Fore.GREEN+"6️⃣   HIBP breach check (optional API key 🗝️  )")
    print(Fore.GREEN+"7️⃣   Show last fetched profile summary 🔁")
    print(Fore.RED +"\n0️⃣   Exit↩️")
    print("")

# ---------- State ----------
STATE = {
    "last_profile_data": None,
    "last_profile_obj": None,
    "instaloader_login": {"user": None, "pass": None},
    "hibp_api_key": None
}

def analyze_flow():
    url = input(Fore.BLUE + "🔗 Enter Instagram profile URL or username: " + Style.RESET_ALL).strip()
    username = extract_username(url)
    if not username:
        print(Fore.RED + "Invalid input." + Style.RESET_ALL)
        return
    print("Fetching profile metadata...")
    # Animated radar while fetching metadata (non-blocking to logic)
    radar_scan(duration=3)
    L = create_instaloader_session(STATE['instaloader_login']['user'], STATE['instaloader_login']['pass'])
    ok, result, profile_obj = fetch_profile(L, username)
    if not ok:
        print(Fore.RED + f"Failed to fetch profile: {result}" + Style.RESET_ALL)
        return
    STATE['last_profile_data'] = result
    STATE['last_profile_obj'] = profile_obj
    # Present table
    table = [
        ["Username", result["username"]],
        ["Profile ID", result["profile_id"]],
        ["Private?", "Yes" if result["is_private"] else "No"],
        ["Verified?", "Yes" if result["is_verified"] else "No"],
        ["Followers", result["followers"]],
        ["Following", result["following"]],
        ["Total Posts", result["total_posts"]],
        ["Reels (videos)", result["reels"] if result["reels"] is not None else "Unknown"],
    ]
    print("\n" + tabulate(table, headers=["Field", "Value"], tablefmt="fancy_grid"))
    print(Fore.GREEN + "\nProfile fetched and stored in session (use other menu options)." + Style.RESET_ALL)

def download_flow():
    if not STATE['last_profile_obj']:
        print(Fore.RED + "No profile fetched. Run option 1 first." + Style.RESET_ALL)
        return
    username = STATE['last_profile_data']['username']
    print(Fore.BLUE + f"Downloading media for @{username} into {DOWNLOADS_DIR}/{username} ..." + Style.RESET_ALL)
    # Show radar while starting download
    radar_scan(duration=4)
    ok, res = download_media(STATE['last_profile_obj'], username,
                             STATE['instaloader_login']['user'], STATE['instaloader_login']['pass'])
    if ok:
        print(Fore.GREEN + f"Download completed: {res}" + Style.RESET_ALL)
    else:
        print(Fore.RED + f"Download failed: {res}" + Style.RESET_ALL)

def generate_pdf_flow():
    if not STATE['last_profile_data']:
        print(Fore.RED + "No profile fetched. Run option 1 first." + Style.RESET_ALL)
        return
    username = STATE['last_profile_data']['username']
    data = STATE['last_profile_data'].copy()
    # Add breach status if HIBP key present
    data['BreachStatus'] = hibp_breach_check(username, STATE['hibp_api_key'])
    # Short radar and progress indicator for PDF creation
    radar_scan(duration=2)
    progress_bar("Generating PDF report", duration=2)
    ok, path = generate_pdf_report(data, username)
    if ok:
        print(Fore.GREEN + f"PDF generated: {path}" + Style.RESET_ALL)
    else:
        print(Fore.RED + f"PDF generation failed: {path}" + Style.RESET_ALL)

def create_zip_flow():
    if not STATE['last_profile_data']:
        print(Fore.RED + "No profile fetched. Run option 1 first." + Style.RESET_ALL)
        return
    username = STATE['last_profile_data']['username']
    folder = os.path.join(DOWNLOADS_DIR, username)
    if not os.path.isdir(folder):
        print(Fore.RED + f"No downloads found at: {folder}" + Style.RESET_ALL)
        return
    zip_base = os.path.join(DOWNLOADS_DIR, f"{username}_media")
    ok, res = zip_folder(folder, zip_base)
    if ok:
        print(Fore.GREEN + f"Created ZIP archive: {res}" + Style.RESET_ALL)
    else:
        print(Fore.RED + f"ZIP creation failed: {res}" + Style.RESET_ALL)

def set_instaloader_login():
    user = input("Enter Instaloader username (leave blank to clear): ").strip()
    if not user:
        STATE['instaloader_login'] = {"user": None, "pass": None}
        print("Cleared stored login.")
        return
    pwd = getpass.getpass("Enter password (input hidden): ")
    STATE['instaloader_login'] = {"user": user, "pass": pwd}
    # Test login
    L = create_instaloader_session(user, pwd)
    try:
        L.check_login()
        print(Fore.GREEN + "Login appears successful (or at least session established)." + Style.RESET_ALL)
    except Exception:
        print(Fore.YELLOW + "Could not fully verify login; instaloader may still work for downloads." + Style.RESET_ALL)

def set_hibp_key():
    key = input("Enter HIBP API key (leave blank to clear): ").strip()
    if not key:
        STATE['hibp_api_key'] = None
        print("HIBP key cleared.")
        return
    STATE['hibp_api_key'] = key
    print("HIBP API key set (will be used for breach checks).")

def show_last_summary():
    if not STATE['last_profile_data']:
        print(Fore.YELLOW + "No profile fetched yet." + Style.RESET_ALL)
        return
    d = STATE['last_profile_data']
    table = [
        ["Username", d["username"]],
        ["Private?", "Yes" if d["is_private"] else "No"],
        ["Followers", d["followers"]],
        ["Following", d["following"]],
        ["Posts", d["total_posts"]],
        ["Reels", d["reels"] if d["reels"] is not None else "Unknown"],
    ]
    print("\n" + tabulate(table, headers=["Field", "Value"], tablefmt="fancy_grid"))
    print("Suggested usernames:", ", ".join(suggest_usernames(d["username"])))


def run_cli():
    while True:
        main_menu()
        try:
            choice = input(Fore.YELLOW + "✅  Choose an option>>> " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return
        if choice == "1":
            analyze_flow()
        elif choice == "2":
            download_flow()
        elif choice == "3":
            generate_pdf_flow()
        elif choice == "4":
            create_zip_flow()
        elif choice == "5":
            set_instaloader_login()
        elif choice == "6":
            set_hibp_key()
        elif choice == "7":
            show_last_summary()
        elif choice == "0":
            print(Fore.RED+"⚠️  STAY INVISIBLE & ETHICAL ⚠️")
            return
        else:
            print("Invalid option❌")
        input(Fore.CYAN + "\nPress Enter to continue..." + Style.RESET_ALL)

if __name__ == "__main__":
    run_cli()
