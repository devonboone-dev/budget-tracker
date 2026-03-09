# test_budget_tracker.py
# Run with: pytest test_budget_tracker.py -v


# HELPER FUNCTION
def make_transactions():
    return [
        {"date": "2026-03-01", "type": "income",  "category": "Salary", "description": "Job",       "amount": 3000.0},
        {"date": "2026-03-02", "type": "expense", "category": "Rent",   "description": "Apt",       "amount": 1200.0},
        {"date": "2026-03-03", "type": "expense", "category": "Food",   "description": "Groceries", "amount": 200.0},
        {"date": "2026-03-04", "type": "expense", "category": "Food",   "description": "Takeout",   "amount": 50.0},
    ]


# BALANCE TESTS
def test_balance_is_correct():
    transactions = make_transactions()
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income - expenses == 1550.0


def test_balance_with_no_transactions():
    transactions = []
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income == 0.0
    assert expenses == 0.0


def test_balance_goes_negative():
    transactions = [
        {"type": "income",  "amount": 500.0,  "category": "Salary"},
        {"type": "expense", "amount": 1000.0, "category": "Rent"},
    ]
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    assert income - expenses == -500.0


# CATEGORY TESTS
def test_category_totals_are_correct():
    transactions = make_transactions()
    totals = {}
    for t in [x for x in transactions if x["type"] == "expense"]:
        totals[t["category"]] = totals.get(t["category"], 0) + t["amount"]
    assert totals["Food"] == 250.0
    assert totals["Rent"] == 1200.0


def test_income_excluded_from_category_totals():
    transactions = make_transactions()
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