import subprocess
import json
import time
from datetime import datetime
import os

INTERVAL = 1800  # seconds (30 min)


def parse_who():
    result = subprocess.run(["who"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()

    sessions = []

    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue

        user = parts[0]
        tty = parts[1]

        ip = "-"
        if len(parts) >= 5:
            ip = parts[4].strip("()")

        sessions.append({
            "user": user,
            "tty": tty,
            "ip": ip
        })

    # Sort for stable output
    sessions.sort(key=lambda x: (x["user"], x["tty"]))

    return sessions


def detect_changes(prev, current):
    prev_set = {(s["user"], s["tty"], s["ip"]) for s in prev}
    curr_set = {(s["user"], s["tty"], s["ip"]) for s in current}

    login = curr_set - prev_set
    logout = prev_set - curr_set

    login_list = [
        {"user": x[0], "tty": x[1], "ip": x[2]}
        for x in login
    ]

    logout_list = [
        {"user": x[0], "tty": x[1], "ip": x[2]}
        for x in logout
    ]

    return login_list, logout_list


def detect_alerts(current, login_events):
    alerts = []

    hour = datetime.now().hour

    # Night login detection
    if login_events and (hour < 6 or hour > 22):
        alerts.append("night_login")

    # Too many sessions
    if len(current) > 5:
        alerts.append("too_many_sessions")

    return alerts


def format_log(time_str, users, login, logout, alerts):
    lines = []

    lines.append(f"[TIME]   {time_str}")
    #lines.append("")

    # Active sessions
    lines.append("[ACTIVE SESSIONS]")
    if users:
        for s in users:
            lines.append(
                f"  - user={s['user']:10} tty={s['tty']:8} ip={s['ip']}"
            )
    else:
        lines.append("  (none)")

    # Login events
    if login:
        #lines.append("")
        lines.append("[LOGIN]")
        for s in login:
            lines.append(
                f"  + user={s['user']:10} tty={s['tty']:8} ip={s['ip']}"
            )

    # Logout events
    if logout:
        #lines.append("")
        lines.append("[LOGOUT]")
        for s in logout:
            lines.append(
                f"  - user={s['user']:10} tty={s['tty']:8} ip={s['ip']}"
            )

    # Alerts
    if alerts:
        #lines.append("")
        lines.append("[ALERT]")
        for a in alerts:
            lines.append(f"  ! {a}")

    lines.append("\n" + "-" * 60)

    return "\n".join(lines)


def ask_log_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    default_text = "who.log"
    default_json = "who.jsonl"

    print(f"Default log files:")
    print(f"  Text : {base_dir}/{default_text}")
    print(f"  JSON : {base_dir}/{default_json}")

    path = input("Enter base filename (without extension) or press Enter: ").strip()

    if path == "":
        text_path = os.path.join(base_dir, default_text)
        json_path = os.path.join(base_dir, default_json)
    else:
        text_path = path + ".log"
        json_path = path + ".jsonl"

    return text_path, json_path


def main():
    text_log_file, json_log_file = ask_log_path()

    print(f"\nText log : {text_log_file}")
    print(f"JSON log : {json_log_file}")
    print("Monitoring started...\n")

    prev_sessions = []

    while True:
        current_sessions = parse_who()
        login, logout = detect_changes(prev_sessions, current_sessions)
        alerts = detect_alerts(current_sessions, login)

        # Time formats
        now = datetime.now()
        time_iso = now.isoformat()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        # time_iso = datetime.utcnow().isoformat() + "Z"
        # time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # -------- Human-readable log --------
        log_text = format_log(
            time_str,
            current_sessions,
            login,
            logout,
            alerts
        )

        with open(text_log_file, "a") as f:
            f.write(log_text + "\n")

        # -------- JSONL log (machine use) --------
        log_entry = {
            "time": time_iso,
            "users": current_sessions,
            "login": login,
            "logout": logout,
            "alert": alerts
        }

        with open(json_log_file, "a") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")

        prev_sessions = current_sessions

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()


