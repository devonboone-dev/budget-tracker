"""
Budget Tracker
==============
A beginner Python project that tracks
income and expenses and saves them to a CSV file.
"""

import csv
import os
from datetime import datetime

# DATA STORAGE SETUP
FILENAME = "transactions.csv"
CATEGORIES = ["Food", "Rent", "Transport", "Entertainment", "Health", "Salary", "Other"]


# LOAD AND SAVE FUNCTIONS
def load_transactions():
    """Load all transactions from the CSV file."""
    transactions = []
    if not os.path.exists(FILENAME):
        return transactions

    with open(FILENAME, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["amount"] = float(row["amount"])
            transactions.append(row)

    return transactions


def save_transactions(transactions):
    """Save all transactions to the CSV file."""
    fieldnames = ["date", "type", "category", "description", "amount"]

    with open(FILENAME, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)


# ADD TRANSACTION
def add_transaction(transactions):
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

    transactions.append(transaction)
    save_transactions(transactions)
    print(f"{t_type.capitalize()} of ${amount:.2f} added!")


# VIEW TRANSACTIONS
def view_transactions(transactions):
    """Display all transactions in a formatted table."""
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
def get_summary(transactions):
    """Calculate and display income, expenses, and balance."""
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
def expenses_by_category(transactions):
    """Show a breakdown of spending per category."""
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



# FILTER BY MONTH
def filter_by_month(transactions):
    """Filter and display transactions for a specific month."""
    month_input = input("\nEnter month (YYYY-MM): ").strip()
    filtered = [t for t in transactions if t["date"].startswith(month_input)]

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
    """Main program loop - displays menu and routes user inpurt."""
    print("=" * 40)
    print("         Budget Tracker")
    print("=" * 40)

    transactions = load_transactions()

    while True:
        print("\n-- Menu --")
        print("  1. Add Transaction")
        print("  2. View All Transactions")
        print("  3. Summary (Income vs Expenses)")
        print("  4. Expenses by Category")
        print("  5. Filter by Month")
        print("  6. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            add_transaction(transactions)
        elif choice == "2":
            view_transactions(transactions)
        elif choice == "3":
            get_summary(transactions)
        elif choice == "4":
            expenses_by_category(transactions)
        elif choice == "5":
            filter_by_month(transactions)
        elif choice == "6":
            print("\nGoodbye! Stay on budget!")
            break
        else:
            print("Invalid option. Please choose 1 through 6.")


if __name__ == "__main__":
    main()
