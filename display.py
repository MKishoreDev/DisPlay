"""
DisPlay - Lightweight Discord Game Quest Spoofer
Author: Kishore (https://github.com/MKishoreDev)
Repository: https://github.com/MKishoreDev/DisPlay
License: MIT License
"""

import os
import sys
import time
import re
import json
import shutil
import subprocess
import difflib

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import urllib.request

HAS_WINSOUND = False
HAS_MSVCRT   = False

if os.name == 'nt':
    try:
        import winsound
        HAS_WINSOUND = True
    except ImportError:
        pass
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        pass

# Force UTF-8 encoding for standard streams
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DISCORD_API_URL = "https://discord.com/api/applications/detectable"
REPO_URL        = "https://github.com/MKishoreDev/DisPlay"

if os.name == 'nt':
    DISPLAY_HOME = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        "DisPlay", "games"
    )
else:
    DISPLAY_HOME = os.path.join(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
        "DisPlay", "games"
    )

# Enable ANSI color escape sequences on Windows
if os.name == 'nt':
    try:
        os.system("")
    except Exception:
        pass

# ─── Color System ────────────────────────────────────────────────────────────

PINK   = "\033[38;2;255;95;135m"
PURPLE = "\033[38;2;135;95;255m"
CYAN   = "\033[38;2;0;215;255m"
MINT   = "\033[38;2;95;239;150m"
AMBER  = "\033[38;2;255;215;95m"
GRAY   = "\033[38;2;140;140;160m"
WHITE  = "\033[97m"
RED    = "\033[38;2;255;95;95m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

_games_cache        = None
active_spoofer_proc = None
active_spoofer_info = None


# ─── Process Monitoring ──────────────────────────────────────────────────────

def check_spoofer_status():
    """Monitor active spoofer process and reset launcher state when closed."""
    global active_spoofer_proc, active_spoofer_info
    if active_spoofer_proc is not None:
        if active_spoofer_proc.poll() is not None:
            active_spoofer_proc = None
            active_spoofer_info = None


# ─── UI Utilities ────────────────────────────────────────────────────────────

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences for accurate string length calculations."""
    return re.sub(r'\033\[[0-9;]*m', '', text)


def render_box(lines: list, width: int = 66, border_color: str = PURPLE) -> str:
    """Render structured TUI box with rounded borders."""
    inner_width = width - 4
    top_border  = f"  {border_color}╭" + "─" * (width - 2) + f"╮{RESET}"
    bot_border  = f"  {border_color}╰" + "─" * (width - 2) + f"╯{RESET}"
    rows = []
    for line in lines:
        padding = max(0, inner_width - len(strip_ansi(line)))
        rows.append(
            f"  {border_color}│{RESET} {line}" + " " * padding +
            f" {border_color}│{RESET}"
        )
    return top_border + "\n" + "\n".join(rows) + "\n" + bot_border


def play_chime():
    """Play audio chime on action completion."""
    if HAS_WINSOUND:
        try:
            winsound.Beep(523, 100)
            winsound.Beep(659, 100)
            winsound.Beep(784, 150)
        except Exception:
            pass
    else:
        try:
            sys.stdout.write("\007")
            sys.stdout.flush()
        except Exception:
            pass


def show_spinner(message: str = "Querying Discord Database"):
    """Display loading spinner for asynchronous operations."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(12):
        print(f"\r  {PINK}{frames[i % 10]}{RESET} {CYAN}{message}...{RESET}",
              end="", flush=True)
        time.sleep(0.05)
    print(f"\r  {MINT}✓{RESET} {CYAN}{message} complete!{RESET}          \n")


# ─── Discord API & System Checks ──────────────────────────────────────────────

def is_discord_running() -> bool:
    """Check if Discord desktop client is currently active on system."""
    try:
        if os.name == 'nt':
            output = subprocess.check_output(
                ['tasklist'], text=True, errors='ignore',
                creationflags=0x08000000
            )
            return 'Discord.exe' in output or 'discord.exe' in output
        output = subprocess.check_output(['ps', '-ax'], text=True, errors='ignore')
        return 'Discord' in output
    except Exception:
        return False


def get_detectable_games() -> list:
    """Fetch official detectable games list from Discord public API."""
    global _games_cache
    if _games_cache is not None:
        return _games_cache

    if HAS_REQUESTS:
        try:
            res = requests.get(DISCORD_API_URL, timeout=8)
            if res.status_code == 200:
                _games_cache = res.json()
                return _games_cache
        except Exception:
            pass

    try:
        request = urllib.request.Request(
            DISCORD_API_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            _games_cache = json.loads(response.read().decode('utf-8'))
            return _games_cache
    except Exception:
        pass

    _games_cache = []
    return _games_cache


def get_source_binary() -> str:
    """Locate native Win32 ping.exe PE binary to duplicate as game process."""
    if os.name == 'nt':
        candidates = [
            r"C:\Windows\System32\ping.exe",
            r"C:\Windows\System32\conhost.exe"
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
    else:
        candidates = ["/bin/bash", "/usr/bin/python3", "/bin/sh"]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
    return sys.executable


# ─── Screen Rendering ────────────────────────────────────────────────────────

def build_screen(input_buffer: str = "") -> str:
    """Construct full TUI screen layout."""
    check_spoofer_status()

    discord_active = is_discord_running()
    status_text    = f"{MINT}ACTIVE{RESET}" if discord_active else f"{AMBER}OFFLINE{RESET}"
    games_list     = get_detectable_games()
    db_text        = f"{len(games_list):,} Games Loaded" if games_list else "Offline"

    header = render_box([
        f" {PINK}{BOLD}✦  D i s P l a y{RESET}   {GRAY}•{RESET}   "
        f"{CYAN}Discord Game Quest Spoofer{RESET}",
        f" {GRAY}github.com/MKishoreDev/DisPlay{RESET}   {GRAY}•{RESET}   "
        f"{GRAY}© 2026 Kishore{RESET}",
    ], 66, PURPLE) + "\n"

    if active_spoofer_info:
        elapsed = time.time() - active_spoofer_info["start_time"]
        remaining = max(0, 15 * 60 + 30 - elapsed)
        mins, secs = int(remaining) // 60, int(remaining) % 60

        body = render_box([
            f" {MINT}{BOLD}🚀 ACTIVE GAME SPOOFER RUNNING{RESET}",
            f" {WHITE}• Game Name   :{RESET} {CYAN}{active_spoofer_info['game']}{RESET}",
            f" {WHITE}• Process     :{RESET} {MINT}{active_spoofer_info['exe']}{RESET}",
            f" {WHITE}• Quest Timer :{RESET} {PINK}⏱ {mins:02d}m {secs:02d}s remaining{RESET}",
            "",
            f" {AMBER}{BOLD}⚠️ LEAVE THE SPOOFER WINDOW OPEN AS IT IS!{RESET}",
            f" {GRAY}Closing the spoofer window will pause quest progress.{RESET}",
        ], 66, MINT) + "\n"
    else:
        body = render_box([
            f" {CYAN}{BOLD}[ SYSTEM STATUS ]{RESET}",
            f" {WHITE}• Discord Client   :{RESET} {status_text}",
            f" {WHITE}• Games Database   :{RESET} {MINT}{db_text}{RESET}",
            f" {WHITE}• Repository       :{RESET} {CYAN}{REPO_URL}{RESET}",
            "",
            f" {PINK}{BOLD}[ DISCLAIMER & USAGE ]{RESET}",
            f" {WHITE}• Credentials      :{RESET} {MINT}No tokens / passwords requested{RESET}",
            f" {WHITE}• Video/Ad Quests  :{RESET} {GRAY}Excluded (No one is too busy for ads){RESET}",
            f" {WHITE}• Recommended Gap  :{RESET} {AMBER}5-10 min break between quests{RESET}",
        ], 66, CYAN) + "\n"

    prompt = f"\n  {PINK}❯ Search Game Name (or type 'about'):{RESET} " + input_buffer
    return header + body + prompt


# ─── Input Handling ──────────────────────────────────────────────────────────

def get_input_live() -> str:
    """Capture non-blocking keyboard input with real-time screen redraws."""
    check_spoofer_status()

    if not HAS_MSVCRT or not active_spoofer_info:
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write(build_screen())
        sys.stdout.flush()
        return sys.stdin.readline().rstrip('\n')

    buffer = []
    last_second = -1

    def redraw():
        nonlocal last_second
        check_spoofer_status()
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.write(build_screen(''.join(buffer)))
        sys.stdout.flush()
        last_second = int(time.time())

    redraw()

    while True:
        check_spoofer_status()
        if active_spoofer_info is None:
            redraw()

        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char in ('\r', '\n'):
                sys.stdout.write('\n')
                sys.stdout.flush()
                return ''.join(buffer)
            if char == '\x03':
                raise KeyboardInterrupt
            if char == '\x08':
                if buffer:
                    buffer.pop()
                    redraw()
                continue
            if char in ('\x00', '\xe0'):
                msvcrt.getwch()
                continue
            if char.isprintable():
                buffer.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()
                continue

        current_second = int(time.time())
        if current_second != last_second:
            redraw()
        else:
            time.sleep(0.05)


# ─── About Screen ────────────────────────────────────────────────────────────

def show_about_screen():
    """Display about screen and disclaimer waiver."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(render_box([
        f" {PINK}{BOLD}✦  A B O U T   &   D I S C L A I M E R{RESET}",
        f" {GRAY}Developer : Kishore  •  github.com/MKishoreDev{RESET}",
    ], 66, PURPLE))

    print(render_box([
        f" {AMBER}{BOLD}[ MISSION STATEMENT ]{RESET}",
        f" {WHITE}• Data Preservation:{RESET}",
        f"   {GRAY}Saves bandwidth — no 50-100 GB downloads for a 15-min quest.{RESET}",
        "",
        f" {PINK}{BOLD}[ LEGAL & LIABILITY WAIVER ]{RESET}",
        f" {WHITE}• Zero Liability:{RESET}",
        f"   {RED}Author assumes NO liability for bans or account actions.{RESET}",
        f"   {GRAY}DisPlay does NOT promote TOS violations or illegal activity.{RESET}",
        f" {WHITE}• Personal Usage:{RESET}",
        f"   {MINT}Tested on main Discord account — 0 issues so far.{RESET}",
        f" {WHITE}• Video & Ad Quests:{RESET}",
        f"   {GRAY}Excluded: no one is too busy to watch a 30-second ad.{RESET}",
        "",
        f" {CYAN}{BOLD}[ OFFICIAL LINKS ]{RESET}",
        f" {GRAY}GitHub Repository :{RESET} {CYAN}{REPO_URL}{RESET}",
        f" {GRAY}Discord Profile   :{RESET} {CYAN}k4isszluv{RESET}",
        f" {GRAY}License           :{RESET} {PINK}MIT © 2026 Kishore{RESET}",
    ], 66, CYAN))

    print()
    play_chime()
    input(f"  {PURPLE}Press Enter to return...{RESET}")


# ─── Spoofer Deployment ──────────────────────────────────────────────────────

def deploy_game_spoof(game_name: str, exe_list: list):
    """Deploy process spoofing binaries and launch child window."""
    global active_spoofer_proc, active_spoofer_info

    try:
        safe_folder = re.sub(r'[<>:"/\\|?*]', '', game_name).strip()
        slot_folder = os.path.join(DISPLAY_HOME, "slot_0", safe_folder)
        os.makedirs(slot_folder, exist_ok=True)

        exe_name    = "game.exe"
        primary_exe = None

        if os.name == 'nt':
            src_exe = get_source_binary() # C:\Windows\System32\ping.exe

            # Terminate active spoofer process if running
            if active_spoofer_proc:
                try:
                    active_spoofer_proc.terminate()
                    active_spoofer_proc.kill()
                except Exception:
                    pass

            for item in exe_list:
                parts = item.replace("\\", "/").split("/")
                fname = parts[-1]
                tdir  = slot_folder
                if len(parts) > 1:
                    tdir = os.path.join(slot_folder, *parts[:-1])
                    os.makedirs(tdir, exist_ok=True)
                dst = os.path.join(tdir, fname)

                # Safe process termination without shell string interpolation
                subprocess.run(
                    ["taskkill", "/F", "/IM", fname],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                time.sleep(0.1)

                if os.path.exists(dst):
                    try:
                        os.remove(dst)
                    except Exception:
                        pass

                try:
                    shutil.copy(src_exe, dst)
                except Exception:
                    pass

                if os.path.exists(dst) and primary_exe is None:
                    primary_exe = dst
                    exe_name    = fname

            if primary_exe is None:
                fallback = os.path.join(slot_folder, "game.exe")
                if os.path.exists(fallback):
                    try:
                        os.remove(fallback)
                    except Exception:
                        pass
                try:
                    shutil.copy(src_exe, fallback)
                except Exception:
                    pass
                if os.path.exists(fallback):
                    primary_exe = fallback

            if primary_exe is None:
                print(f"\n  {RED}Error: Could not create process binary.{RESET}")
                input(f"\n  Press Enter..."); return

            # Launch standalone native PE binary with ping 127.0.0.1 -n 930
            active_spoofer_proc = subprocess.Popen(
                [primary_exe, '127.0.0.1', '-n', '930'],
                cwd=slot_folder,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

        else:
            # Unix / Linux / macOS
            bash        = "/bin/bash"
            primary_exe = None
            for item in exe_list:
                parts = item.replace("\\", "/").split("/")
                fname = parts[-1]
                tdir  = slot_folder
                if len(parts) > 1:
                    tdir = os.path.join(slot_folder, *parts[:-1])
                    os.makedirs(tdir, exist_ok=True)
                dst = os.path.join(tdir, fname)
                try:
                    shutil.copy(bash, dst)
                    os.chmod(dst, 0o755)
                    if primary_exe is None:
                        primary_exe = dst
                        exe_name    = fname
                except Exception:
                    pass

            if primary_exe is None:
                primary_exe = bash

            if active_spoofer_proc:
                try:
                    active_spoofer_proc.terminate()
                except Exception:
                    pass

            launched = False
            for tc in [["x-terminal-emulator", "-e"], ["gnome-terminal", "--"], ["xterm", "-e"]]:
                try:
                    active_spoofer_proc = subprocess.Popen(
                        tc + ["bash", "-c", "sleep 930"],
                        cwd=slot_folder
                    )
                    launched = True
                    break
                except FileNotFoundError:
                    continue

            if not launched:
                active_spoofer_proc = subprocess.Popen([bash, "-c", "sleep 930"], cwd=slot_folder)

        active_spoofer_info = {
            "game":       game_name,
            "exe":        exe_name,
            "start_time": time.time(),
        }

        print(f"\n  {MINT}✓ Process active: {exe_name}{RESET}")
        print(f"  {CYAN}🚀 Spoofer window opened! Leave it open as it is.{RESET}\n")
        play_chime()
        time.sleep(1.5)

    except Exception as exc:
        print(f"\n  {RED}Deployment error: {exc}{RESET}")
        input(f"\n  Press Enter...")


# ─── Search & Selection ──────────────────────────────────────────────────────

def get_executables(app: dict) -> list:
    """Filter Win32 executables from application record."""
    exes = [e["name"] for e in app.get("executables", [])
            if e.get("os") == "win32" and not e.get("is_launcher")]
    if not exes:
        exes = [e["name"] for e in app.get("executables", []) if e.get("os") == "win32"]
    return exes or ["game.exe"]


def process_search(query: str):
    """Execute fuzzy search across Discord detectable games database."""
    try:
        clean_query = query.strip().lower()
        if clean_query in {"about", "info", "help", "?", "credits", "disclaimer"}:
            show_about_screen()
            return

        show_spinner(f"Searching for '{query}'")

        games = get_detectable_games()
        if not games:
            print(f"  {AMBER}! Offline. Check internet connection.{RESET}")
            time.sleep(1.5)
            return

        name_map  = {app["name"]: app for app in games if app.get("name")}
        all_names = list(name_map)

        exact   = [name for name in all_names if name.lower() == clean_query]
        starts  = [name for name in all_names if name.lower().startswith(clean_query) and name not in exact]
        contains= [name for name in all_names if clean_query in name.lower() and name not in exact and name not in starts]
        rem     = [name for name in all_names if name not in exact and name not in starts and name not in contains]
        fuzzy   = difflib.get_close_matches(clean_query, rem, n=10, cutoff=0.4)
        matches = (exact + starts + contains + fuzzy)[:15]

        if not matches:
            print(f"  {AMBER}! No games found for '{query}'.{RESET}\n")
            time.sleep(1.2)
            return

        if len(matches) == 1:
            deploy_game_spoof(matches[0], get_executables(name_map[matches[0]]))
            return

        print(f"  {CYAN}Found {len(matches)} games:{RESET}\n")
        for i, name in enumerate(matches, 1):
            ex_preview = ", ".join(get_executables(name_map[name])[:2])
            print(f"  {PINK}❯ {i}.{RESET} {BOLD}{name:<34}{RESET} {GRAY}({ex_preview}){RESET}")

        selection = input(f"\n  {PURPLE}? Select 1-{len(matches)} (0=back):{RESET} ").strip()
        if not selection.isdigit():
            return
        idx = int(selection)
        if idx < 1 or idx > len(matches):
            return
        deploy_game_spoof(matches[idx-1], get_executables(name_map[matches[idx-1]]))

    except Exception as exc:
        print(f"\n  {RED}Search error: {exc}{RESET}")
        time.sleep(1.5)


# ─── Application Entry Point ─────────────────────────────────────────────────

def main():
    """Main interactive loop."""
    while True:
        try:
            check_spoofer_status()
            query = get_input_live().strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit", "0", "q"}:
                if active_spoofer_proc:
                    try:
                        active_spoofer_proc.terminate()
                    except Exception:
                        pass
                print(f"\n  {GRAY}Goodbye!{RESET}\n")
                sys.exit(0)
            process_search(query)
        except (KeyboardInterrupt, SystemExit):
            if active_spoofer_proc:
                try:
                    active_spoofer_proc.terminate()
                except Exception:
                    pass
            sys.exit(0)
        except Exception as exc:
            print(f"\n  {RED}Runtime error: {exc}{RESET}")
            time.sleep(1.5)


if __name__ == "__main__":
    main()
