from dotenv import load_dotenv
load_dotenv()

import os
import json
import queue
import atexit
import sqlite3
import threading
from contextlib import contextmanager
from flask import Flask, request, jsonify, session, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler

from backend.graph import build_graph

app = Flask(__name__, static_folder="frontend")

# Fix #1 — never hardcode the secret key
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Fix #2 — removed "null" from CORS origins
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

# Fix #4 — rate limiter to prevent brute-force on auth endpoints
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per day"],
    storage_uri="memory://"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "users.db")


# ----------------------------------
# DB context manager
# ----------------------------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()


# ----------------------------------
# Database Init
# ----------------------------------

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS portfolios(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT,
                profile     TEXT,
                allocation  TEXT,
                risk_score  REAL,
                stress_test TEXT,
                explanation TEXT,
                compliance  TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


init_db()

try:
    graph = build_graph()
except Exception as e:
    print(f"[FATAL] Failed to build graph: {e}")
    raise


# ----------------------------------
# APScheduler — Auto Rebalance
# ----------------------------------

def rebalance_all_users():
    print("[Scheduler] Starting monthly rebalance for all users...")

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT username, profile FROM portfolios
            WHERE id IN (SELECT MAX(id) FROM portfolios GROUP BY username)
        """)
        rows = c.fetchall()

    if not rows:
        print("[Scheduler] No users found.")
        return

    with get_db() as conn:
        c = conn.cursor()
        for username, profile_json in rows:
            try:
                profile = json.loads(profile_json)
                result = graph.invoke({
                    "profile": profile, "logs": [], "retry": False, "retry_count": 0
                })
                c.execute("""
                    INSERT INTO portfolios
                        (username, profile, allocation, risk_score, stress_test,
                         explanation, compliance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    username, profile_json,
                    json.dumps(result.get("allocation")),
                    result.get("risk_score"),
                    json.dumps(result.get("stress_test")),
                    result.get("explanation", ""),
                    result.get("compliance_review", "")
                ))
                print(f"[Scheduler] Rebalanced: {username}")
            except Exception as e:
                print(f"[Scheduler] Failed for {username}: {e}")
        conn.commit()

    print("[Scheduler] Monthly rebalance complete.")


scheduler = BackgroundScheduler()
scheduler.add_job(rebalance_all_users, 'interval', days=30)
scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))


# ----------------------------------
# Frontend
# ----------------------------------

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)


# ----------------------------------
# Auth APIs
# ----------------------------------

@app.route("/api/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        username = data.get("username") or data.get("email")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Missing fields"}), 400

        if len(password) < 8:
            return jsonify({"message": "Password must be at least 8 characters"}), 400

        hashed = generate_password_hash(password)

        with get_db() as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users(username,password) VALUES (?,?)", (username, hashed))
                conn.commit()
            except sqlite3.IntegrityError:
                return jsonify({"message": "Username already exists"}), 400

        return jsonify({"message": "Registered successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid JSON"}), 400

        username = data.get("username") or data.get("email")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Missing fields"}), 400

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username=?", (username,))
            user = c.fetchone()

        if not user:
            return jsonify({"message": "Invalid username"}), 401
        if not check_password_hash(user[0], password):
            return jsonify({"message": "Incorrect password"}), 401

        session["user"] = username
        return jsonify({"message": "Login successful"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out"})


@app.route("/api/login-check")
def login_check():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    return jsonify({"message": "Authorized"})


# ----------------------------------
# Portfolio Generation (standard)
# ----------------------------------

@app.route("/api/generate", methods=["POST"])
def generate():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        required_fields = {
            "age":    int,
            "income": float,
            "years":  int,
            "loss":   int,
            "amount": float
        }
        for field, ftype in required_fields.items():
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
            try:
                data[field] = ftype(data[field])
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid value for field: {field} (expected {ftype.__name__})"}), 400

        result = graph.invoke({
            "profile": data, "logs": [], "retry": False, "retry_count": 0
        })

        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO portfolios
                    (username, profile, allocation, risk_score, stress_test,
                     explanation, compliance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session["user"],
                json.dumps(data),
                json.dumps(result.get("allocation")),
                result.get("risk_score"),
                json.dumps(result.get("stress_test")),
                result.get("explanation", ""),
                result.get("compliance_review", "")
            ))
            conn.commit()

        return jsonify({
            "risk_score":  result.get("risk_score"),
            "allocation":  result.get("allocation"),
            "stress_test": result.get("stress_test"),
            "explanation": result.get("explanation"),
            "compliance":  result.get("compliance_review"),
            "logs":        result.get("logs", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------
# SSE — Real-time streaming generate
# Streams live agent progress events to the frontend
# while running the graph in a background thread.
# ----------------------------------

def _sse_event(event, data):
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.route("/api/generate/stream", methods=["POST"])
def generate_stream():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required_fields = {
        "age":    int,
        "income": float,
        "years":  int,
        "loss":   int,
        "amount": float
    }
    for field, ftype in required_fields.items():
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
        try:
            data[field] = ftype(data[field])
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid value for field: {field}"}), 400

    username = session["user"]
    q = queue.Queue()

    # Agent name → display label mapping
    AGENT_LABELS = {
        "profile":     "Profile Agent — calculating risk score",
        "tool_agent":  "Tool Agent — autonomous tool selection",
        "strategy":    "Strategy Agent — generating allocation",
        "live_data":   "Live Data Agent — fetching NIFTY 50",
        "simulation":  "Simulation Agent — running 1000 Monte Carlo iterations",
        "compliance":  "Compliance Agent — RAG regulatory validation",
        "critic":      "Critic Agent — reviewing allocation",
        "explanation": "Explanation Agent — generating AI summary",
    }

    def run_graph():
        """Run the full graph pipeline in a background thread,
        sending SSE progress events into the queue as each agent completes."""
        try:
            q.put(("progress", {"agent": "start", "message": "Pipeline starting..."}))

            # Patch state after each node using LangGraph's stream() API
            initial_state = {
                "profile": data, "logs": [], "retry": False, "retry_count": 0
            }

            for event in graph.stream(initial_state):
                for node_name in event:
                    label = AGENT_LABELS.get(node_name, node_name.replace("_", " ").title())
                    q.put(("progress", {
                        "agent":   node_name,
                        "message": f"✓ {label}"
                    }))

            # Final state is the last event value
            final_state = event[node_name] if event else {}

            # Save to DB
            with get_db() as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO portfolios
                        (username, profile, allocation, risk_score, stress_test,
                         explanation, compliance)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    json.dumps(data),
                    json.dumps(final_state.get("allocation")),
                    final_state.get("risk_score"),
                    json.dumps(final_state.get("stress_test")),
                    final_state.get("explanation", ""),
                    final_state.get("compliance_review", "")
                ))
                conn.commit()

            q.put(("result", {
                "risk_score":  final_state.get("risk_score"),
                "allocation":  final_state.get("allocation"),
                "stress_test": final_state.get("stress_test"),
                "explanation": final_state.get("explanation"),
                "compliance":  final_state.get("compliance_review"),
                "logs":        final_state.get("logs", [])
            }))

        except Exception as e:
            q.put(("error", {"message": str(e)}))
        finally:
            q.put(("done", {}))

    thread = threading.Thread(target=run_graph, daemon=True)
    thread.start()

    def event_stream():
        while True:
            try:
                event_type, payload = q.get(timeout=120)
                yield _sse_event(event_type, payload)
                if event_type in ("done", "error"):
                    break
            except queue.Empty:
                yield _sse_event("error", {"message": "Timeout — pipeline took too long."})
                break

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ----------------------------------
# Portfolio History API
# ----------------------------------

@app.route("/api/history", methods=["GET"])
def history():
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, profile, allocation, risk_score,
                       stress_test, explanation, compliance, created_at
                FROM portfolios
                WHERE username = ?
                ORDER BY created_at DESC
            """, (session["user"],))
            rows = c.fetchall()

        portfolios = []
        for row in rows:
            portfolios.append({
                "id":          row[0],
                "profile":     json.loads(row[1]) if row[1] else {},
                "allocation":  json.loads(row[2]) if row[2] else {},
                "risk_score":  row[3],
                "stress_test": json.loads(row[4]) if row[4] else {},
                "explanation": row[5] or "",
                "compliance":  row[6] or "",
                "created_at":  row[7]
            })

        return jsonify({"portfolios": portfolios, "count": len(portfolios)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<int:portfolio_id>", methods=["DELETE"])
def delete_portfolio(portfolio_id):
    if "user" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM portfolios WHERE id=? AND username=?",
                      (portfolio_id, session["user"]))
            conn.commit()
        return jsonify({"message": "Deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", threaded=True)