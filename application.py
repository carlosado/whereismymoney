# Carlos Oliveira
# Sep - 2019
# CS50 Final Project - Personal Finance

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify, json
from flask_session import Session
from tempfile import mkdtemp
from datetime import datetime
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, euro, percent, decimal

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom jinja filters
app.jinja_env.filters["euro"] = euro
app.jinja_env.filters["percent"] = percent
app.jinja_env.filters["decimal"] = decimal

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///budget.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show current balance sheet"""

    # User reached route via POST (as by submitting a form via POST or clicking
    # on a chart bar)
    if request.method == "POST":

        # User selected variables (by clicking on a bar)
        selected_month = request.form['month'] # Ex: 'Aug'
        selected_bar = request.form['type'] # Ex: 'Income'

        # Current year
        selected_year = datetime.now().strftime('%Y') # Ex: '2019'

        if selected_bar == 'Income':
            # Get user income data
            income = db.execute("SELECT year, month, salary, subsidy, extra, salary+subsidy+extra as paycheck FROM income JOIN months ON income.month=months.month_name WHERE userid = :userid and year = :year ORDER BY month_number ASC",
                                userid=session["user_id"], year=selected_year)

            # Calculate income totals
            total_salary = 0
            total_subsidy = 0
            total_extra = 0
            grandtotal = 0
            for i in income:
                total_salary += i["salary"]
                total_subsidy += i["subsidy"]
                total_extra += i["extra"]
                grandtotal += i["paycheck"]

            return render_template("index_income.html", income=income, total_salary=total_salary,
                                   total_subsidy=total_subsidy, total_extra=total_extra,
                                   grandtotal=grandtotal, selected_year=selected_year)

        if selected_bar == 'Expenses':
            # Get user current expenses grouped by category
            exp_cat = db.execute("SELECT year, month, category, type, SUM(amount) as partial FROM expenses WHERE userid = :userid and year = :year and month = :month GROUP BY category",
                                 userid=session["user_id"], year=selected_year, month=selected_month)

            # Get user current expenses grouped by type
            exp_type = db.execute("SELECT year, month, category, type, SUM(amount) as partial FROM expenses WHERE userid = :userid and year = :year and month = :month GROUP BY type",
                                  userid=session["user_id"], year=selected_year, month=selected_month)

            # Calculate totals
            expenses_total = 0
            for expense in exp_type:
                expenses_total += expense["partial"]

            return render_template("index_expenses.html", selected_year=selected_year,
                                   selected_month=selected_month, exp_cat=exp_cat,
                                   exp_type=exp_type, expenses_total=expenses_total)


    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Get current month and year
        current_month = datetime.now().strftime('%h') # ex: Aug
        current_year = datetime.now().strftime('%Y') # ex: 2019

        # Get user income & expenses from current year grouped by month
        inc_exp_month = db.execute("SELECT year, month, salary+subsidy+extra as paycheck, (SELECT SUM(amount) FROM expenses WHERE userid=:userid and income.month=expenses.month) as partial FROM income JOIN months ON income.month=months.month_name WHERE userid = :userid and year = :year GROUP BY month ORDER BY month_number",
                               userid=session["user_id"], year=current_year)

        # Get the totals for income and expenses and accumulated cash remaining
        income_total = 0
        expense_total = 0
        accu_balance = []
        accu_diff= 0
        for totals in inc_exp_month:
            income_total += totals["paycheck"]
            expense_total += totals["partial"]
            accu_diff += (totals["paycheck"] - totals["partial"])
            accu_balance.append(accu_diff)

        # Savings section
        savings = db.execute("SELECT year, month, SUM(saving*(1+interest)) as partial FROM savings JOIN months ON savings.month=months.month_name WHERE userid = :userid GROUP by month ORDER by month_number ASC",
                             userid=session["user_id"])

        savings_total = 0
        savings_accu = []
        for saving in savings:
            savings_total += saving["partial"]
            savings_accu.append(savings_total)


        return render_template("index.html", savings=savings, savings_accu=savings_accu,
                               savings_total=savings_total, accu_balance=accu_balance,
                               current_year=current_year, inc_exp_month=inc_exp_month,
                               income_total=income_total, expense_total=expense_total)


@app.route("/modal", methods=["GET"])
def modal():
    """Create a modal chart"""
    # User clicked on item in category chart
    chart_category = request.args.get("category")

    # User clicked on item in type chart
    chart_type = request.args.get("type")

    if chart_category:
        # Extract from database all 'category' data and return it to user
        cat_data = db.execute("SELECT month, SUM(amount) as partial FROM expenses JOIN months ON expenses.month=months.month_name WHERE userid=:userid and category=:category GROUP by month ORDER BY month_number ASC",
                               userid=session["user_id"], category=chart_category)
        return jsonify(cat_data)

    else:
        # Extract from database all 'type' data and return it to user
        typ_data = db.execute("SELECT month, SUM(amount) as partial FROM expenses JOIN months ON expenses.month=months.month_name WHERE userid=:userid and type=:type Group by month ORDER BY month_number ASC",
                                userid=session["user_id"], type=chart_type)
        return jsonify(typ_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/income")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password was re-submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Store confirmed password as a hash using werkzeug.security
        pwhash = generate_password_hash(request.form.get("confirmation"))

        # Insert user in the database
        result = db.execute("INSERT INTO users(username, hash) VALUES(:username, :hash)",
                            username=request.form.get("username"), hash=pwhash)

        # If username already exists
        if not result:
            return apology("username already in database", 400)

        # Login this user automatically
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        flash("Registered!")

        # Redirect user to home page
        return redirect("/income")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # Take username as argument
    username = request.args.get("username")

    # Check database for username
    user = db.execute("SELECT username FROM users WHERE username = :username", username=username)
    if not user:
        # Username is available
        return jsonify(True)
    else:
        # Username already in database
        return jsonify(False)


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    """Declare monthly income"""

    # User reached route via POST (as by submiting a form via POST)
    if request.method == "POST":

        # Check if user already declared that months income
        row = db.execute("SELECT year, month FROM income WHERE userid = :userid AND year = :year AND month = :month",
                         userid=session["user_id"], year=request.form.get("year"),
                         month=request.form.get("month"))

        # There is no income record yet
        if len(row) == 0:
            db.execute("INSERT INTO income (userid, year, month, salary, subsidy, extra) VALUES(:userid, :year, :month, :salary, :subsidy, :extra)",
                       userid=session["user_id"], year=request.form.get("year"), month=request.form.get("month"),
                       salary=request.form.get("salary"), subsidy=request.form.get("subsidy"), extra=request.form.get("extra"))
        # There is already a record for that year and month
        elif row.year == request.form.get("year") and row.month == request.form.get("month"):
            db.execute("UPDATE income SET year = :year, month = :month, salary = :salary, subsidy = :subsidy, extra = :extra WHERE userid = :userid",
                       userid=session["user_id"], year=request.form.get("year"), month=request.form.get("month"),
                       salary=request.form.get("salary"), subsidy=request.form.get("subsidy"), extra=request.form.get("extra"))

        flash("Your monthly income was registered!")

        # Redirect user to expenses page
        return redirect("/expenses")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("income.html")


@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    """Insert monthly expenses"""
    # User reached route via POST (as by submiting a form via POST)
    if request.method == "POST":

        # Insert expense in database
        db.execute("INSERT INTO 'expenses' (userid, year, month, category, type, amount) VALUES(:userid, :year, :month, :category, :type, :amount)",
                   userid=session["user_id"], year=int(request.form.get("year")),
                   month=request.form.get("month"), category=request.form.get("category"),
                   type=request.form.get("type"), amount=float(request.form.get("amount")))

        # Check if user marks it as last expense
        last_expense = request.form.get("last_expense")
        if last_expense:
            # Yes? Go to homepage
            return redirect("/")
        else:
            # No? Reload page
            flash("Expense inserted in database.")
            return redirect("/expenses")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("expenses.html")


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    """Manage month and anual savings"""

    # User reached route via POST (as by submiting a form via POST)
    if request.method == "POST":

        # Insert saving in database
        db.execute("INSERT INTO savings (userid, year, month, type, saving, interest, withdraw) VALUES(:userid, :year, :month, :type, :saving, :interest, :withdraw)",
                   userid=session["user_id"], year=int(request.form.get("year")),
                   month=request.form.get("month"), type=request.form.get("type"), 
                   saving=request.form.get("saving"), interest=request.form.get("interest"),
                   withdraw=request.form.get("withdraw"))

        #flash("Saving inserted in database.")

        # Automatically insert saving as an expense in database
        db.execute("INSERT INTO expenses (userid, year, month, category, type, amount) VALUES(:userid, :year, :month, :category, :type, :amount)",
                   userid=session["user_id"], year=int(request.form.get("year")),
                   month=request.form.get("month"), category="Miscellaneous",
                   type="Savings", amount=float(request.form.get("saving")))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Retrive savings data from database
        rows = db.execute("SELECT year, type, SUM(saving) as invest, interest, SUM(saving*(interest+1)) as total FROM savings WHERE userid = :userid GROUP BY type",
                          userid=session["user_id"])

        # Calculate useful info for tables and charts
        # Labels for chart (type of saving)
        label = []
        # Data for chart (investment in savings plus interest)
        data = []
        savings_total = 0
        for item in rows:
            label.append(item["type"])
            data.append(item["total"])
            savings_total += item["total"]

        return render_template("savings.html", rows=rows, savings_total=savings_total, label=label, data=data)


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    """"Insert Monthly Budget """

    if request.method == "POST":

        return redirect("/")

    else:

        return render_template("budget.html")


@app.route("/history", methods=["GET"])
def history():
    """"Show monthly balances"""

    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
