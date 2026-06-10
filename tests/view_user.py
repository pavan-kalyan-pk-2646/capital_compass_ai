"""
view_users.py — Capital Compass AI · Admin Utility
Run: python tests/view_users.py          (from the paradise/ directory)
Shows all registered members + their portfolio status.
"""

import sqlite3
import os
import sys
from datetime import datetime

# ── DB path: works when run from paradise/ or tests/ ──────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "users.db")

# ── Terminal colours (no external deps) ───────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
MAGENTA= "\033[95m"

def clr(text, *codes):
    return "".join(codes) + str(text) + RESET

def banner():
    print()
    print(clr("╔══════════════════════════════════════════════════════════╗", CYAN, BOLD))
    print(clr("║        Capital Compass AI  ·  Registered Members         ║", CYAN, BOLD))
    print(clr("╚══════════════════════════════════════════════════════════╝", CYAN, BOLD))
    print()

def divider():
    print(clr("─" * 62, DIM))

def format_date(dt_str):
    if not dt_str:
        return clr("—", DIM)
    try:
        dt = datetime.fromisoformat(str(dt_str))
        return dt.strftime("%d %b %Y  %H:%M")
    except Exception:
        return str(dt_str)

def main():
    if not os.path.exists(DB_PATH):
        print(clr(f"[ERROR] Database not found at: {DB_PATH}", RED, BOLD))
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── Fetch all users ──────────────────────────────────────────────────────
    cur.execute("SELECT id, username FROM users ORDER BY id")
    users = cur.fetchall()

    # ── Fetch portfolios keyed by username ───────────────────────────────────
    cur.execute(
        "SELECT username, risk_score, allocation, created_at, profile "
        "FROM portfolios ORDER BY created_at DESC"
    )
    port_rows = cur.fetchall()
    # keep only the latest portfolio per user
    portfolios = {}
    for p in port_rows:
        uname = p["username"]
        if uname not in portfolios:
            portfolios[uname] = dict(p)

    conn.close()

    banner()
    print(clr(f"  Total registered members: {len(users)}", BOLD))
    print()

    if not users:
        print(clr("  No users found in the database.", YELLOW))
        return

    # ── Header row ───────────────────────────────────────────────────────────
    print(
        clr(f"  {'#':<4}", BOLD) +
        clr(f"{'Username':<20}", BOLD, CYAN) +
        clr(f"{'Portfolio':<14}", BOLD) +
        clr(f"{'Risk Score':<16}", BOLD) +
        clr(f"{'Last Updated':<22}", BOLD)
    )
    divider()

    for user in users:
        uid      = user["id"]
        uname    = user["username"]
        port     = portfolios.get(uname)

        if port:
            port_status = clr("✔  Active", GREEN)
            risk_raw    = port["risk_score"]
            risk_label  = f"{risk_raw:.1f}" if risk_raw is not None else "—"

            # colour-code risk score
            if risk_raw is not None:
                if risk_raw <= 3:
                    risk_disp = clr(risk_label + "  (Low)", GREEN)
                elif risk_raw <= 6:
                    risk_disp = clr(risk_label + "  (Med)", YELLOW)
                else:
                    risk_disp = clr(risk_label + "  (High)", RED)
            else:
                risk_disp = clr("—", DIM)

            updated = format_date(port["created_at"])
        else:
            port_status = clr("✘  None", DIM)
            risk_disp   = clr("—", DIM)
            updated     = clr("—", DIM)

        print(
            f"  {str(uid)+'.':<4}"
            f"  {clr(uname, MAGENTA, BOLD):<28}"
            f"{port_status:<22}"
            f"{risk_disp:<32}"
            f"{updated}"
        )

        # ── Show allocation breakdown if available ───────────────────────────
        if port and port.get("allocation"):
            import json
            try:
                alloc = json.loads(port["allocation"])
                parts = [f"{k}: {v}%" for k, v in alloc.items()]
                alloc_str = " · ".join(parts)
                if len(alloc_str) > 65:
                    alloc_str = alloc_str[:62] + "..."
                print(clr(f"       └─ Allocation → {alloc_str}", DIM))
            except Exception:
                pass

    divider()
    print()
    has_port = sum(1 for u in users if u["username"] in portfolios)
    print(
        clr(f"  Portfolios generated : {has_port}/{len(users)}", BOLD) +
        "   " +
        clr(f"Pending setup : {len(users)-has_port}", YELLOW if len(users)-has_port else DIM)
    )
    print()

if __name__ == "__main__":
    main()