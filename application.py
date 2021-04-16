# import frameworks
import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, lookup, usd
import pytz
import datetime

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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


# index route
@app.route("/")
@login_required
def index():

    # query for info in stocks table
    user_stocks = db.execute("SELECT symbol, amount, bought_at FROM stocks WHERE users_id = :id", id = session["user_id"])

    # if user doesn't have any shares, render placeholder message
    if not user_stocks:
        message = "You don't have any shares yet. Start buying right now!"
        return render_template("apology.html", message = message)

    # query for cash amount in users table
    cash_dict = list(db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"]))
    cash = cash_dict[0]["cash"]

    # create empty list for index info display
    portfolio = []

    # add info to portfolio list
    for i in range(len(user_stocks)):

        # create temp list
        list_tmp = []

        # add symbols and shares amount to tmp list
        list_tmp.append(user_stocks[i]["symbol"])
        list_tmp.append(user_stocks[i]["amount"])

        # call lookup and add current price and company name
        quote = lookup(user_stocks[i]["symbol"])
        list_tmp.append(quote["name"])
        list_tmp.append(quote["price"])

        # calculate revenue and add it
        bought_at = user_stocks[i]["bought_at"]
        revenue = {"revenue": ((quote["price"] - bought_at) / bought_at ) * 100}
        list_tmp.append(revenue["revenue"])

        # calculate and add subtotal (total without cash)
        sub = {"subtotal": quote["price"] * int(user_stocks[i]["amount"])}
        list_tmp.append(sub["subtotal"])

        # add price paid when shares were bought
        list_tmp.append(user_stocks[i]["bought_at"])

        # pass temp list data to portfolio list
        portfolio.append(list_tmp)

    # calculate total (shares income + cash)
    total = 0
    for i in range(len(user_stocks)):
        total += portfolio[i][5]
    total += cash


    # create empty list and looper
    looper = len(user_stocks)
    symbol = []
    shares = []
    company = []
    price = []
    revenue = []
    subtotal = []
    paid = []

    # fill in arranged lists with portfolio info
    for i in range(looper):
        symbol.append(portfolio[i][0])
        shares.append(portfolio[i][1])
        company.append(portfolio[i][2])
        price.append(portfolio[i][3])
        revenue.append(portfolio[i][4])
        subtotal.append(portfolio[i][5])
        paid.append(portfolio[i][6])

    # return index
    for i in range(0, looper):
        return render_template("index.html", looper = looper, total = usd(total), cash = usd(cash), symbol = symbol, company = company, shares = shares, price = price, paid = paid, revenue = revenue, subtotal = subtotal)

# buy route
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    # return if GET request
    if request.method == "GET":
        return render_template("buy.html")

    # if POST request
    else:

        # import current user
        query_user = db.execute("SELECT * FROM users WHERE id = :query_user", query_user = session["user_id"])
        current_user = query_user[0]

        # check every field is completed
        if not request.form.get("symbol_buy") or not request.form.get("shares_buy"):
            return render_template("buy.html")


        # create variables for requested symbol, amount and buyment request
        shares = int(request.form.get("shares_buy"))
        symbol = request.form.get("symbol_buy").upper()
        quote = lookup(symbol)
        print(quote)

        # ensure a correct amount input
        if shares < 1:
            return render_template("buy.html")

        # ensure the symbol exist
        if quote == None:
            alerter = 40
            return render_template("buy.html", alerter = alerter)

        # ensure the user can afford the shares
        final_price = quote["price"] * shares

        if final_price > current_user["cash"]:
            alerter = 41
            return render_template("buy.html", alerter = alerter)

        # do the transaction
        else:

            # sustract stocks value from cash and update users table
            current_user["cash"] = current_user["cash"] - final_price
            db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash = current_user["cash"], id = current_user["id"])


            # query database to know if current user already have at least one of the requested shares
            share_holder = db.execute("SELECT * FROM stocks WHERE owner = :owner AND symbol = :symbol", owner = current_user["username"], symbol = symbol)

            # if user doesn't have any of this particular shares
            if not share_holder:
                db.execute("INSERT INTO stocks (symbol, owner, amount, users_id, bought_at) VALUES (:symbol, :owner, :amount, :users_id, :bought_at)", symbol = symbol, owner = current_user["username"], amount = shares, users_id = current_user["id"], bought_at = quote["price"])
                db.execute("INSERT INTO transactions (holder, symbol, shares, price, users_id, type, date) VALUES (:holder, :symbol, :shares, :price, :users_id, :type, :date)", holder = current_user["username"], symbol = symbol, shares = shares, price = quote["price"], users_id = session["user_id"], type = "Bought", date = datetime.datetime.now(pytz.timezone('America/Buenos_Aires')))
                share_holder.clear()
                return render_template("bought.html", number = shares, company = quote["name"], symbol = quote["symbol"], paid = final_price)

            # if user have at least one share already
            else:
                new_shares_amount = int(share_holder[0]["amount"]) + shares
                db.execute("UPDATE stocks SET amount = :amount, bought_at = :bought_at WHERE id = :id", amount = new_shares_amount, id = share_holder[0]["id"], bought_at = quote["price"] )
                db.execute("INSERT INTO transactions (holder, symbol, shares, price, users_id, type, date) VALUES (:holder, :symbol, :shares, :price, :users_id, :type, :date)", holder = current_user["username"], symbol = symbol, shares = shares, price = quote["price"], users_id = session["user_id"], type = "Bought", date = datetime.datetime.now(pytz.timezone('America/Buenos_Aires')))
                return render_template("bought.html", number = shares, company = quote["name"], symbol = quote["symbol"], paid = final_price)

# history route
@app.route("/history")
@login_required
def history():

    # query transactions db
    historial = list(db.execute("SELECT type, symbol, shares, price, date FROM transactions WHERE users_id = :id", id = session["user_id"]))
    looper = len(historial)

    # if historial is still empty, render placeholder message
    if not historial:
        message = "You haven't realized any transactions yet. Start investing now!"
        return render_template("apology.html", message = message)

    type = []
    symbol = []
    shares = []
    price = []
    date = []

    for i in range(looper):
        type.append(historial[i]["type"])
        symbol.append(historial[i]["symbol"])
        shares.append(historial[i]["shares"])
        price.append(historial[i]["price"])
        date.append(historial[i]["date"])

    for i in range(looper):
        return render_template("history.html", looper = looper, type = type, symbol = symbol, shares = shares, price = price, date = date)

# login route
@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            alerter = 22
            return render_template("login.html", alerter = alerter)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# logout route
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# quote route
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    # if GET requested
    if request.method == "GET":
        return render_template("quote.html")

    # if POST requested
    else:

        # check input is not empty
        if not request.form.get("symbol"):
            return render_template("quote.html")

        # look for symbol in API
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        # ensure it exist
        if quote == None:
            alerter = 90
            return render_template("quote.html", alerter = alerter)

        # output result in screen
        else:
            return render_template ("quoted.html", name = quote["name"], symbol = quote["symbol"], price = quote["price"])

# register route
@app.route("/register", methods=["GET", "POST"])
def register():

    # if a new user is submited
    if request.method == "POST":

        # max and min characters for username and password
        MAX = 15
        MIN = 5

        # Ensure password and confirmation are the same
        if request.form.get("password") != request.form.get("confirm"):
            alerter = 20
            return render_template("register.html", alerter = alerter)

        # create username variable
        username = request.form.get("username")

        # Ensure the username is not being used
        users_list = db.execute("SELECT username FROM users")

        # Ensure username is not taken already
        for i in range(len(users_list)):
            if username == users_list[i]["username"]:
                alerter = 21
                return render_template("register.html", alerter = alerter)
                
        # hash the password and create variable
        password = request.form.get("password")
        hash_pass = generate_password_hash(password)

        # insert username and hashed password to the .db table and redirect to login menu
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username = username,  password = hash_pass)
        alerter = 9
        return render_template("/login.html", alerter = alerter)

    # send clean .html sheet
    else:
        return render_template("register.html")


# sell route
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
     # return if GET request
    if request.method == "GET":
        symbols = list(db.execute("SELECT symbol FROM stocks WHERE users_id = :id", id = session["user_id"]))
        looper = len(symbols)
        return render_template("sell.html", symbols = symbols, looper = looper)

    # if POST request
    else:
        # import current user
        query_user = db.execute("SELECT * FROM users WHERE id = :query_user", query_user = session["user_id"])
        current_user = query_user[0]

        # check every field is completed
        if not request.form.get("symbol_sell") or not request.form.get("shares_sell"):
            return render_template("sell.html")

        # create variables for requested symbol, amount and sale request
        shares = int(request.form.get("shares_sell"))
        symbol = request.form.get("symbol_sell").upper()
        quote = lookup(symbol)

        # ensure the symbol exist
        if quote == None:
            alerter = 30
            return render_template("sell.html", alerter = alerter)

        # query thru table to get user's shares
        portfolio = db.execute("SELECT symbol, amount FROM stocks WHERE users_id = :id", id = session["user_id"])

        # create lists and fill it with user's shares symbols
        tags = []
        for i in range(len(portfolio)):
            tags.append(portfolio[i]["symbol"])


        # ensure user has at least requested amount of shares
        for i in range(len(portfolio)):
            if portfolio[i]["symbol"] == symbol:
                amount_owned = int(portfolio[i]["amount"])
                break
        if amount_owned < shares:
            symbols = list(db.execute("SELECT symbol FROM stocks WHERE users_id = :id", id = session["user_id"]))
            looper = len(symbols)
            alerter = 31
            return render_template("sell.html", alerter = alerter, symbols = symbols, looper = looper)

        # pay profit to user
        profit = shares * quote["price"]
        user_cash = list(db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"]))
        income = user_cash[0]["cash"] + profit
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash = income, id = session["user_id"])

        # if user sold all shares, remove row from stocks table
        if amount_owned == shares:
            db.execute("DELETE FROM stocks WHERE symbol = :symbol AND users_id = :id", symbol = symbol, id = session["user_id"])
            db.execute("INSERT INTO transactions (holder, symbol, shares, price, users_id, type, date) VALUES (:holder, :symbol, :shares, :price, :users_id, :type, :date)", holder = current_user["username"], symbol = symbol, shares = shares, price = quote["price"], users_id = session["user_id"], type = "Sold", date = datetime.datetime.now(pytz.timezone('America/Buenos_Aires')))
            return render_template("sold.html", number = shares, company = quote["name"], symbol = symbol, profit = profit)

        # if user only sold a part, update amount from stocks table
        else:
            amount_owned -= shares
            db.execute("UPDATE stocks SET amount = :amount WHERE symbol = :symbol AND users_id = :id", amount = amount_owned, symbol = symbol, id = session["user_id"])
            db.execute("INSERT INTO transactions (holder, symbol, shares, price, users_id, type, date) VALUES (:holder, :symbol, :shares, :price, :users_id, :type, :date)", holder = current_user["username"], symbol = symbol, shares = shares, price = quote["price"], users_id = session["user_id"], type = "Sold", date = datetime.datetime.now(pytz.timezone('America/Buenos_Aires')))
            return render_template("sold.html", number = shares, company = quote["name"], symbol = symbol, profit = profit)

# profile route
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # if requested via GET
    if request.method == "GET":

        # get user profile data (username, amount of tansactions, cash and shares)
        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        transactions = db.execute("SELECT COUNT(*) FROM transactions WHERE users_id = :id", id = session["user_id"])
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        shares = db.execute("SELECT symbol, amount FROM stocks WHERE users_id = :id", id = session["user_id"])

        # calculate shares values
        total = 0
        for i in range(len(shares)):
            quote = lookup(shares[i]["symbol"])
            subtotal = quote["price"] * shares[i]["amount"]
            total += subtotal

        # return data
        return render_template("profile.html", user = username[0]["username"], transactions = transactions[0]["COUNT(*)"], cash = cash[0]["cash"], subtotal = usd(total))

    #if requested via POST
    else:

        #delete account and update db
        db.execute("DELETE FROM users WHERE id = :id", id = session["user_id"])
        return redirect("/logout")


# change username route
@app.route("/change_username", methods=["GET", "POST"])
@login_required
def change_username():

    # if requested via GET
    if request.method == "GET":
        return render_template("change_username.html")

     # if requested via POST
    else:

        # ensure new username and its repeat match
        new_username = request.form.get("username")
        repeat_username = request.form.get("repeat_username")
        if new_username != repeat_username:
            alerter = 0
            return render_template("change_username.html", alerter = alerter)

        # ensure password is ok
        requested_password = request.form.get("password")
        db_password = db.execute("SELECT hash FROM users WHERE id = :id", id = session["user_id"])
        if check_password_hash(db_password[0]["hash"], requested_password) is False:
            alerter = 1
            return render_template("change_username.html", alerter = alerter)

        #replace former username for new one
        db.execute("UPDATE users SET username = :username WHERE id = :id", username = new_username, id = session["user_id"])

        # add info for profile template
        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        transactions = db.execute("SELECT COUNT(*) FROM transactions WHERE users_id = :id", id = session["user_id"])
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        shares = db.execute("SELECT symbol, amount FROM stocks WHERE users_id = :id", id = session["user_id"])

        # calculate shares values
        total = 0
        for i in range(len(shares)):
            quote = lookup(shares[i]["symbol"])
            subtotal = quote["price"] * shares[i]["amount"]
            total += subtotal

        alerter = 2
        return render_template("profile.html", alerter = alerter, user = username[0]["username"], subtotal = usd(total), cash = cash[0]["cash"], transactions = transactions[0]["COUNT(*)"])

# change password route
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    # if requested via get
    if request.method == "GET":
        return render_template("change_password.html")

     # if requested via post
    else:

        # ensure new password and its repeat match
        new_password = request.form.get("new_password")
        password_repeat = request.form.get("new_password_repeat")
        if new_password != password_repeat:
            alerter = 70
            return render_template("change_password.html", alerter = alerter)

        #hash new password and submit it to db
        hash_password = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash = hash_password, id = session["user_id"])
        alerter = 71

        # add info for profile template
        username = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])
        transactions = db.execute("SELECT COUNT(*) FROM transactions WHERE users_id = :id", id = session["user_id"])
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        shares = db.execute("SELECT symbol, amount FROM stocks WHERE users_id = :id", id = session["user_id"])

        # calculate shares values
        total = 0
        for i in range(len(shares)):
            quote = lookup(shares[i]["symbol"])
            subtotal = quote["price"] * shares[i]["amount"]
            total += subtotal

        return render_template("profile.html", alerter = alerter, user = username[0]["username"], subtotal = usd(total), cash = cash[0]["cash"], transactions = transactions[0]["COUNT(*)"])


# error handler
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("apology.html")


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
