"""
Budget Tracker - Flask Web API
==============================
REST API backend that serves the Budget Tracker web UI.
Connects to the existing SQLite database used by budget_tracker.py.
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILENAME = "budget_tracker.db"
CATEGORIES = ["Food", "Rent", "Transport", "Entertainment", "Health", "Salary", "Other"]


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                type        TEXT NOT NULL,
                category    TEXT NOT NULL,
                description TEXT NOT NULL,
                amount      REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                month   TEXT NOT NULL UNIQUE,
                amount  REAL NOT NULL
            )
        """)
        conn.commit()


# ── SERVE FRONTEND ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE_DIR, "static"), "index.html")


# ── TRANSACTIONS API ──────────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    month = request.args.get("month")
    with get_connection() as conn:
        if month:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC, id DESC",
                (f"{month}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY date DESC, id DESC"
            ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.get_json()
    required = ["type", "category", "description", "amount"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    if data["type"] not in ("income", "expense"):
        return jsonify({"error": "Type must be income or expense"}), 400
    if data["category"] not in CATEGORIES:
        data["category"] = "Other"
    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Amount must be a positive number"}), 400

    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO transactions (date, type, category, description, amount) VALUES (?,?,?,?,?)",
            (date, data["type"], data["category"], data["description"], amount)
        )
        conn.commit()
        new_id = cursor.lastrowid

    return jsonify({"id": new_id, "message": "Transaction added"}), 201


@app.route("/api/transactions/<int:t_id>", methods=["PUT"])
def edit_transaction(t_id):
    data = request.get_json()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM transactions WHERE id=?", (t_id,)).fetchone()
        if not row:
            return jsonify({"error": "Transaction not found"}), 404

        t_type     = data.get("type", row["type"])
        category   = data.get("category", row["category"])
        description= data.get("description", row["description"])
        amount     = float(data.get("amount", row["amount"]))
        date       = data.get("date", row["date"])

        conn.execute(
            "UPDATE transactions SET type=?, category=?, description=?, amount=?, date=? WHERE id=?",
            (t_type, category, description, amount, date, t_id)
        )
        conn.commit()

    return jsonify({"message": "Transaction updated"})


@app.route("/api/transactions/<int:t_id>", methods=["DELETE"])
def delete_transaction(t_id):
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM transactions WHERE id=?", (t_id,)).fetchone()
        if not row:
            return jsonify({"error": "Transaction not found"}), 404
        conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))
        conn.commit()
    return jsonify({"message": "Transaction deleted"})


# ── SUMMARY API ───────────────────────────────────────────────────────────────

@app.route("/api/summary", methods=["GET"])
def get_summary():
    month = request.args.get("month")
    with get_connection() as conn:
        if month:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE date LIKE ?", (f"{month}%",)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM transactions").fetchall()

    transactions = [dict(r) for r in rows]
    total_income   = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")

    category_totals = {}
    for t in transactions:
        if t["type"] == "expense":
            category_totals[t["category"]] = category_totals.get(t["category"], 0) + t["amount"]

    return jsonify({
        "total_income":    total_income,
        "total_expenses":  total_expenses,
        "balance":         total_income - total_expenses,
        "category_totals": category_totals
    })


# ── BUDGET API ────────────────────────────────────────────────────────────────

@app.route("/api/budget/<month>", methods=["GET"])
def get_budget(month):
    with get_connection() as conn:
        row = conn.execute("SELECT amount FROM budgets WHERE month=?", (month,)).fetchone()
        spent_row = conn.execute(
            "SELECT SUM(amount) as spent FROM transactions WHERE type='expense' AND date LIKE ?",
            (f"{month}%",)
        ).fetchone()

    budget = row["amount"] if row else None
    spent  = spent_row["spent"] or 0.0

    return jsonify({
        "month":     month,
        "budget":    budget,
        "spent":     spent,
        "remaining": (budget - spent) if budget else None,
        "pct":       round((spent / budget * 100), 1) if budget else None
    })


@app.route("/api/budget/<month>", methods=["POST"])
def set_budget(month):
    data = request.get_json()
    try:
        amount = float(data["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Amount must be a positive number"}), 400

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO budgets (month, amount) VALUES (?, ?) "
            "ON CONFLICT(month) DO UPDATE SET amount=excluded.amount",
            (month, amount)
        )
        conn.commit()

    return jsonify({"message": f"Budget set for {month}", "amount": amount})


@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(CATEGORIES)


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 40)
    print("  Budget Tracker Web UI")
    print("  Open: http://localhost:5000")
    print("=" * 40)
    app.run(debug=True, port=8080)