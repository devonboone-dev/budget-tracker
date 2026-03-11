# test_budget_tracker.py
# Run with: pytest test_budget_tracker.py -v

import sqlite3
import os
import pytest
import budget_tracker as bt


# FIXTURES
@pytest.fixture(autouse=True)
def use_test_db(tmp_path, monkeypatch):
    """Point the app at a temporary test database for every test."""
    test_db = str(tmp_path / "test_budget.db")
    monkeypatch.setattr(bt, "DB_FILENAME", test_db)
    bt.init_db()
    yield


def seed_transactions():
    """Insert sample transactions directly into the test DB."""
    transactions = [
        {"date": "2026-03-01", "type": "income",  "category": "Salary", "description": "Job",       "amount": 3000.0},
        {"date": "2026-03-02", "type": "expense", "category": "Rent",   "description": "Apt",       "amount": 1200.0},
        {"date": "2026-03-03", "type": "expense", "category": "Food",   "description": "Groceries", "amount": 200.0},
        {"date": "2026-03-04", "type": "expense", "category": "Food",   "description": "Takeout",   "amount": 50.0},
    ]
    for t in transactions:
        bt.save_transaction(t)


# DATABASE TESTS
def test_init_db_creates_table():
    """init_db should create the transactions table."""
    with bt.get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
        )
        assert cursor.fetchone() is not None


def test_save_and_load_transaction():
    """A saved transaction should be retrievable via load_transactions."""
    bt.save_transaction({
        "date": "2026-03-01", "type": "income",
        "category": "Salary", "description": "Test pay", "amount": 1000.0
    })
    transactions = bt.load_transactions()
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 1000.0
    assert transactions[0]["description"] == "Test pay"


def test_transaction_has_auto_id():
    """Each saved transaction should receive an auto-incremented id."""
    bt.save_transaction({
        "date": "2026-03-01", "type": "expense",
        "category": "Food", "description": "Lunch", "amount": 12.0
    })
    transactions = bt.load_transactions()
    assert "id" in transactions[0]
    assert transactions[0]["id"] == 1


# BALANCE TESTS
def test_balance_is_correct():
    seed_transactions()
    transactions = bt.load_transactions()
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income - expenses == 1550.0


def test_balance_with_no_transactions():
    transactions = bt.load_transactions()
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income == 0.0
    assert expenses == 0.0


def test_balance_goes_negative():
    bt.save_transaction({"date": "2026-03-01", "type": "income",  "category": "Salary", "description": "Pay",  "amount": 500.0})
    bt.save_transaction({"date": "2026-03-01", "type": "expense", "category": "Rent",   "description": "Rent", "amount": 1000.0})
    transactions = bt.load_transactions()
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income - expenses == -500.0


# CATEGORY TESTS
def test_category_totals_are_correct():
    seed_transactions()
    transactions = bt.load_transactions()
    totals = {}
    for t in [x for x in transactions if x["type"] == "expense"]:
        totals[t["category"]] = totals.get(t["category"], 0) + t["amount"]
    assert totals["Food"] == 250.0
    assert totals["Rent"] == 1200.0


def test_income_excluded_from_category_totals():
    seed_transactions()
    transactions = bt.load_transactions()
    totals = {}
    for t in [x for x in transactions if x["type"] == "expense"]:
        totals[t["category"]] = totals.get(t["category"], 0) + t["amount"]
    assert "Salary" not in totals


# INPUT VALIDATION TESTS
def test_amount_must_be_positive():
    amount_input = "-50"
    try:
        amount = float(amount_input)
        valid = amount > 0
    except ValueError:
        valid = False
    assert valid == False


def test_invalid_amount_string():
    amount_input = "abc"
    try:
        float(amount_input)
        valid = True
    except ValueError:
        valid = False
    assert valid == False


def test_valid_amount():
    amount_input = "85.50"
    try:
        amount = float(amount_input)
        valid = amount > 0
    except ValueError:
        valid = False
    assert valid == True


# MIGRATION TEST
def test_migrate_from_csv(tmp_path, monkeypatch):
    """migrate_from_csv should import rows from a CSV into the DB."""
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text(
        "date,type,category,description,amount\n"
        "2026-01-01,income,Salary,Pay,2000.0\n"
        "2026-01-02,expense,Food,Groceries,100.0\n"
    )
    bt.migrate_from_csv(str(csv_file))
    transactions = bt.load_transactions()
    assert len(transactions) == 2
    assert transactions[0]["amount"] == 2000.0


def test_migrate_skips_if_data_exists(tmp_path):
    """migrate_from_csv should not re-import if DB already has rows."""
    bt.save_transaction({
        "date": "2026-01-01", "type": "income",
        "category": "Salary", "description": "Existing", "amount": 999.0
    })
    csv_file = tmp_path / "transactions.csv"
    csv_file.write_text(
        "date,type,category,description,amount\n"
        "2026-01-02,expense,Food,Should not import,50.0\n"
    )
    bt.migrate_from_csv(str(csv_file))
    transactions = bt.load_transactions()
    assert len(transactions) == 1  # Only the pre-existing row


# EDIT & DELETE TESTS
def test_edit_transaction():
    """Editing a transaction should update the correct fields in the DB."""
    seed_transactions()
    transactions = bt.load_transactions()
    t_id = transactions[1]["id"]  # Rent transaction

    with bt.get_connection() as conn:
        conn.execute(
            "UPDATE transactions SET description=?, amount=? WHERE id=?",
            ("New Rent", 1300.0, t_id)
        )
        conn.commit()

    updated = bt.load_transactions()
    assert updated[1]["description"] == "New Rent"
    assert updated[1]["amount"] == 1300.0


def test_edit_does_not_affect_other_transactions():
    """Editing one transaction should leave all others unchanged."""
    seed_transactions()
    transactions = bt.load_transactions()
    t_id = transactions[1]["id"]

    with bt.get_connection() as conn:
        conn.execute("UPDATE transactions SET amount=? WHERE id=?", (999.0, t_id))
        conn.commit()

    updated = bt.load_transactions()
    assert updated[0]["amount"] == 3000.0  # Salary unchanged
    assert updated[2]["amount"] == 200.0   # Food unchanged


def test_delete_transaction():
    """Deleting a transaction should remove it from the DB."""
    seed_transactions()
    transactions = bt.load_transactions()
    t_id = transactions[2]["id"]  # Food transaction

    with bt.get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))
        conn.commit()

    after_delete = bt.load_transactions()
    assert len(after_delete) == 3
    descriptions = [t["description"] for t in after_delete]
    assert "Groceries" not in descriptions


def test_delete_does_not_affect_other_transactions():
    """Deleting one transaction should leave all others intact."""
    seed_transactions()
    transactions = bt.load_transactions()
    t_id = transactions[2]["id"]  # Delete Food/Groceries

    with bt.get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (t_id,))
        conn.commit()

    remaining = bt.load_transactions()
    descriptions = [t["description"] for t in remaining]
    assert "Job" in descriptions
    assert "Apt" in descriptions
