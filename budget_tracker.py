"""
Budget Tracker
==============
A beginner Python project that tracks
income and expenses using a SQLite database.
"""

import sqlite3
import os
from datetime import datetime

# DATA STORAGE SETUP
DB_FILENAME = "budget_tracker.db"
CATEGORIES = ["Food", "Rent", "Transport", "Entertainment", "Health", "Salary", "Other"]


# DATABASE SETUP
def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_FILENAME)


def init_db():
    """Create the transactions table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                category    TEXT    NOT NULL,
                description TEXT    NOT NULL,
                amount      REAL    NOT NULL
            )
        """)
        conn.commit()


# LOAD AND SAVE FUNCTIONS
def load_transactions():
    """Load all transactions from the database."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM transactions ORDER BY date ASC, id ASC"
        )
        return [dict(row) for row in cursor.fetchall()]


def save_transaction(transaction):
    """Insert a single transaction into the database."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO transactions (date, type, category, description, amount) "
            "VALUES (:date, :type, :category, :description, :amount)",
            transaction
        )
        conn.commit()


# MIGRATE FROM CSV
def migrate_from_csv(csv_filename="transactions.csv"):
    """One-time migration: import existing CSV data into SQLite."""
    import csv

    if not os.path.exists(csv_filename):
        print(f"  No CSV file found at '{csv_filename}'. Skipping migration.")
        return

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if count > 0:
            print("  Database already has data. Skipping CSV migration.")
            return

    migrated = 0
    with open(csv_filename, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["amount"] = float(row["amount"])
            save_transaction(row)
            migrated += 1

    print(f"  Migrated {migrated} transaction(s) from '{csv_filename}' to SQLite.")


# ADD TRANSACTION
def add_transaction():
    """Prompt the user to add a new income or expense."""
    print("\n-- Add Transaction --")

    t_type = input("Type (income/expense): ").strip().lower()
    if t_type not in ("income", "expense"):
        print("Invalid type. Please enter 'income' or 'expense'.")
        return

    print("Categories:", ", ".join(CATEGORIES))
    category = input("Category: ").strip().capitalize()
    if category not in CATEGORIES:
        print(f"'{category}' not in list. Saving as 'Other'.")
        category = "Other"

    description = input("Description: ").strip()

    try:
        amount = float(input("Amount ($): "))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Please enter a valid positive number.")
        return

    transaction = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": t_type,
        "category": category,
        "description": description,
        "amount": amount,
    }

    save_transaction(transaction)
    print(f"{t_type.capitalize()} of ${amount:.2f} added!")


# VIEW TRANSACTIONS
def view_transactions(transactions=None):
    """Display all transactions in a formatted table."""
    if transactions is None:
        transactions = load_transactions()

    if not transactions:
        print("\n  No transactions found.")
        return

    print("\n-- All Transactions --")
    print(f"{'Date':<12} {'Type':<10} {'Category':<15} {'Description':<20} {'Amount':>10}")
    print("-" * 70)

    for t in transactions:
        sign = "+" if t["type"] == "income" else "-"
        print(
            f"{t['date']:<12} {t['type']:<10} {t['category']:<15} "
            f"{t['description']:<20} {sign}${t['amount']:>9.2f}"
        )


# SUMMARY
def get_summary(transactions=None):
    """Calculate and display income, expenses, and balance."""
    if transactions is None:
        transactions = load_transactions()

    if not transactions:
        print("\n  No data to summarize.")
        return

    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expenses

    print("\n-- Summary --")
    print(f"  Total Income:    ${total_income:,.2f}")
    print(f"  Total Expenses:  ${total_expenses:,.2f}")
    print(f"  Balance:         ${balance:,.2f}")

    if balance >= 0:
        print("  Status:          On track!")
    else:
        print("  Status:          Overspent!")


# EXPENSES BY CATEGORY
def expenses_by_category(transactions=None):
    """Show a breakdown of spending per category."""
    if transactions is None:
        transactions = load_transactions()

    expenses = [t for t in transactions if t["type"] == "expense"]
    if not expenses:
        print("\n  No expenses found.")
        return

    category_totals = {}
    for t in expenses:
        cat = t["category"]
        category_totals[cat] = category_totals.get(cat, 0) + t["amount"]

    total = sum(category_totals.values())

    print("\n-- Expenses by Category --")
    for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        bar = "=" * int((amount / total) * 30)
        pct = (amount / total) * 100
        print(f"  {cat:<15} ${amount:>8.2f} {pct:>5.1f}% {bar}")


# EDIT TRANSACTION
def edit_transaction():
    """Let the user edit an existing transaction."""
    transactions = load_transactions()
    if not transactions:
        print("\n  No transactions to edit.")
        return

    print("\n-- Edit Transaction --")
    print(f"{'#':<4} {'Date':<12} {'Type':<10} {'Category':<15} {'Description':<20} {'Amount':>10}")
    print("-" * 74)
    for i, t in enumerate(transactions, 1):
        sign = "+" if t["type"] == "income" else "-"
        print(f"{i:<4} {t['date']:<12} {t['type']:<10} {t['category']:<15} "
              f"{t['description']:<20} {sign}${t['amount']:>9.2f}")

    try:
        choice = int(input("\nEnter the # of the transaction to edit: "))
        if not 1 <= choice <= len(transactions):
            print("Invalid number.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    t = transactions[choice - 1]
    t_id = t["id"]

    print(f"\nEditing: {t['date']} | {t['type']} | {t['category']} | {t['description']} | ${t['amount']:.2f}")
    print("Press Enter to keep the current value.\n")

    # Type
    new_type = input(f"Type (income/expense) [{t['type']}]: ").strip().lower()
    if new_type == "":
        new_type = t["type"]
    elif new_type not in ("income", "expense"):
        print("Invalid type. Keeping original.")
        new_type = t["type"]

    # Category
    print("Categories:", ", ".join(CATEGORIES))
    new_category = input(f"Category [{t['category']}]: ").strip().capitalize()
    if new_category == "":
        new_category = t["category"]
    elif new_category not in CATEGORIES:
        print(f"'{new_category}' not in list. Keeping original.")
        new_category = t["category"]

    # Description
    new_description = input(f"Description [{t['description']}]: ").strip()
    if new_description == "":
        new_description = t["description"]

    # Amount
    new_amount_input = input(f"Amount (${t['amount']:.2f}): ").strip()
    if new_amount_input == "":
        new_amount = t["amount"]
    else:
        try:
            new_amount = float(new_amount_input)
            if new_amount <= 0:
                raise ValueError
        except ValueError:
            print("Invalid amount. Keeping original.")
            new_amount = t["amount"]

    with get_connection() as conn:
        conn.execute(
            "UPDATE transactions SET type=?, category=?, description=?, amount=? WHERE id=?",
            (new_type, new_category, new_description, new_amount, t_id)
        )
        conn.commit()

    print("✓ Transaction updated successfully!")


# DELETE TRANSACTION
def delete_transaction():
    """Let the user delete an existing transaction."""
    transactions = load_transactions()
    if not transactions:
        print("\n  No transactions to delete.")
        return

    print("\n-- Delete Transaction --")
    print(f"{'#':<4} {'Date':<12} {'Type':<10} {'Category':<15} {'Description':<20} {'Amount':>10}")
    print("-" * 74)
    for i, t in enumerate(transactions, 1):
        sign = "+" if t["type"] == "income" else "-"
        print(f"{i:<4} {t['date']:<12} {t['type']:<10} {t['category']:<15} "
              f"{t['description']:<20} {sign}${t['amount']:>9.2f}")

    try:
        choice = int(input("\nEnter the # of the transaction to delete: "))
        if not 1 <= choice <= len(transactions):
            print("Invalid number.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    t = transactions[choice - 1]
    confirm = input(f"\nAre you sure you want to delete '{t['description']}' (${t['amount']:.2f})? (yes/no): ").strip().lower()

    if confirm != "yes":
        print("Deletion cancelled.")
        return

    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (t["id"],))
        conn.commit()

    print("✓ Transaction deleted successfully!")


# FILTER BY MONTH
def filter_by_month():
    """Filter and display transactions for a specific month."""
    month_input = input("\nEnter month (YYYY-MM): ").strip()

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date ASC",
            (f"{month_input}%",)
        )
        filtered = [dict(row) for row in cursor.fetchall()]

    if not filtered:
        print("No transactions found for " + month_input)
        return

    print("\n-- Transactions for " + month_input + " --")
    view_transactions(filtered)

    income = sum(t["amount"] for t in filtered if t["type"] == "income")
    expenses = sum(t["amount"] for t in filtered if t["type"] == "expense")
    net = income - expenses

    print("\n-- Monthly Summary --")
    print(f" Month Income:    ${income:,.2f}")
    print(f" Month Expenses:  ${expenses:,.2f}")
    print(f" Net:             ${net:,.2f}")


# MAIN MENU
def main():
    """Main program loop - displays menu and routes user input."""
    print("=" * 40)
    print("         Budget Tracker")
    print("=" * 40)

    init_db()
    migrate_from_csv()

    while True:
        print("\n-- Menu --")
        print("  1. Add Transaction")
        print("  2. View All Transactions")
        print("  3. Summary (Income vs Expenses)")
        print("  4. Expenses by Category")
        print("  5. Filter by Month")
        print("  6. Edit Transaction")
        print("  7. Delete Transaction")
        print("  8. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            get_summary()
        elif choice == "4":
            expenses_by_category()
        elif choice == "5":
            filter_by_month()
        elif choice == "6":
            edit_transaction()
        elif choice == "7":
            delete_transaction()
        elif choice == "8":
            print("\nGoodbye! Stay on budget!")
            break
        else:
            print("Invalid option. Please choose 1 through 8.")


if __name__ == "__main__":
    main()
