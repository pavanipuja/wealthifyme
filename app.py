from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory
from forms import LoginForm, RegistrationForm, ForgotPasswordForm,ResetPasswordForm,HintAnswerForm
from config import Config
from werkzeug.utils import secure_filename
from db import mysql
from services import check_user, registration
from pymongo import MongoClient
from datetime import datetime, timedelta
from flask_mysqldb import MySQL
from bson.objectid import ObjectId
import re
from twilio.rest import Client
import random
import os



app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = '1234 this is my secret key'

mysql = MySQL(app)

# MongoDB setup
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client["wealthyfyme2"]
mongo_transactions = mongo_db["transactions"]
mongo_budgets = mongo_db["budgets"]
mongo_challenges=mongo_db["group_challenges"]
split_expenses_col = mongo_db["split_expenses"]

CATEGORIES = ["Salary","Food", "Housing", "Transportation", "Entertainment", "Shopping", "Healthcare", "Education","Others"]


@app.route('/')
def home():
    return render_template("index.html")


# Twilio config
TWILIO_ACCOUNT_SID = 'AC3dd54a862fc10fcf2208cb56a24'
TWILIO_AUTH_TOKEN = '7299e981e7d7a6f367ac982e80c3'
TWILIO_PHONE_NUMBER = '+16814413892'

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/login', methods=["GET", "POST"])
def login():
    msg = session.get('msg', '')
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        res = check_user(email, password)

        if res:
            session['user_email'] = email  # Save user for session scope
            return redirect(url_for('dashboard_home'))
        else:
            session['msg'] = "unsuccessful"
            return redirect(url_for('login'))

    session.pop('msg', None)
    return render_template("login.html", form=form, msg=msg)


from MySQLdb.cursors import DictCursor  # You already imported this, so use it

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    forgot_form = ForgotPasswordForm()
    hint_form = HintAnswerForm()

    if 'step' not in session:
        session['step'] = 'email'

    if session['step'] == 'email':
        if forgot_form.validate_on_submit():
            email = forgot_form.email.data.strip()

            cur = mysql.connection.cursor(DictCursor)
            cur.execute("SELECT * FROM login WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()

            if user and 'hint_question' in user:
                session['reset_email'] = email
                session['hint_question'] = user['hint_question']
                session['step'] = 'hint'
                return redirect(url_for('forgot_password'))
            else:
                flash("No user found with that email or missing hint question.", "danger")

        return render_template("forgot_password.html", forgot_form=forgot_form, hint_form=None, step="email")

    elif session['step'] == 'hint':
        if hint_form.validate_on_submit():
            answer = hint_form.hint_answer.data.strip().lower()
            new_password = hint_form.password.data.strip()

            cur = mysql.connection.cursor(DictCursor)
            cur.execute("SELECT hint_answer FROM login WHERE email = %s", (session['reset_email'],))
            user = cur.fetchone()
            cur.close()

            if user and user['hint_answer'].strip().lower() == answer:
                cur = mysql.connection.cursor()
                cur.execute("UPDATE login SET password = %s WHERE email = %s", (new_password, session['reset_email']))
                mysql.connection.commit()
                cur.close()

                session.pop('step', None)
                session.pop('reset_email', None)
                session.pop('hint_question', None)

                
                return redirect(url_for('login'))
            else:
                flash("Incorrect hint answer. Please try again.", "danger")

        return render_template("forgot_password.html", forgot_form=None, hint_form=hint_form,
                               hint_question=session.get('hint_question'), step="hint")

    # Fallback if session state breaks
    session.pop('step', None)
    flash("Something went wrong. Please try again.", "danger")
    return redirect(url_for('forgot_password'))



def get_user_by_email(email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM login WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    if user:
        user['phone'] = '+917876134701'
    return user



def send_otp_sms(phone_number, otp):
    message = client.messages.create(
        body=f'Your OTP for password reset is: {otp}',
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    return message.sid


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        session_otp = session.get('reset_otp')

        if user_otp == session_otp:
            # OTP matched — redirect to password reset page
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP. Please try again.")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')




@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        flash("Session expired. Please start password reset again.")
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.password.data
        email = session['reset_email']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE login SET password = %s WHERE email = %s", (new_password, email))
        mysql.connection.commit()
        cur.close()

        session.pop('reset_email', None)
        session.pop('reset_otp', None)

        flash("Password reset successfully. Please log in.")
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)






@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if request.method == "POST":
        if form.validate_on_submit():
            name = form.name.data
            email = form.email.data
            password = form.password.data
            confirm_password = form.confirm_password.data
            hint_question = form.hint_question.data
            hint_answer = form.hint_answer.data
            res = registration(name, email, password, confirm_password,hint_question,hint_answer)
            if res:
                flash('Account created successfully!', 'success')
                return redirect(url_for('login'))
            else:
                session['msg'] = "Please, Enter a Valid Email !!!"
                return redirect(url_for('register'))
        else:
            # Store errors in session and redirect
            session['form_errors'] = form.errors
            return redirect(url_for('register'))

    # GET request, render form with any stored errors or msg
    msg = session.pop('msg', '')
    form_errors = session.pop('form_errors', {})
    return render_template("registration.html", form=form, msg=msg, form_errors=form_errors)



@app.route('/dashboard_home')
def dashboard_home():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    email = session['user_email']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM login WHERE email = %s", (email,))
    user_row = cursor.fetchone()
    user_name = user_row['name'] if user_row else 'User'

   
    current_date = datetime.now()
    start_date = current_date.replace(day=1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)

    monthly_income = 0
    monthly_expenses = 0
    total_balance = 0
    category_expenses = {}

    transactions = mongo_transactions.find({
        'email': email,
        'date': {'$gte': start_date.strftime('%Y-%m-%d'), '$lt': end_date.strftime('%Y-%m-%d')}
    })

    for txn in transactions:
        txn_type = txn.get('type', '').lower()
        amount = txn.get('amount', 0)
        if txn_type == 'income':
            monthly_income += amount
        elif txn_type == 'expense':
            monthly_expenses += amount
            category = txn.get('category', 'Uncategorized')
            category_expenses[category] = category_expenses.get(category, 0) + amount

    total_balance = monthly_income - monthly_expenses
    sorted_categories = sorted([(cat, abs(amt)) for cat, amt in category_expenses.items()], key=lambda x: x[1], reverse=True)

    monthly_summary = []
    for i in range(6, 0, -1):
        month_start = (current_date - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        month_txns = mongo_transactions.find({
            'email': email,
            'date': {'$gte': month_start.strftime('%Y-%m-%d'), '$lt': month_end.strftime('%Y-%m-%d')}
        })

        month_income, month_expenses = 0, 0
        for txn in month_txns:
            amount = txn.get('amount', 0)
            if txn.get('type', '').lower() == 'income':
                month_income += amount
            else:
                month_expenses += amount

        monthly_summary.append({
            'month': month_start.strftime('%b %Y'),
            'income': month_income,
            'expenses': abs(month_expenses),
            'savings': month_income - abs(month_expenses)
        })

    recent_transactions = mongo_transactions.find({'email': email}).sort('date', -1).limit(5)
    formatted_recent = [{
        'date': datetime.strptime(txn.get('date', ''), '%Y-%m-%d'),
        'category': txn.get('category', ''),
        'description': txn.get('description', ''),
        'amount': txn.get('amount', 0),
        'type': txn.get('type', '')
    } for txn in recent_transactions]

    return render_template("dashboard_home.html",
                           total_balance=total_balance,
                           monthly_income=monthly_income,
                           monthly_expenses=monthly_expenses,
                           recent_transactions=formatted_recent,
                           sorted_categories=sorted_categories,
                           monthly_data={
                               'labels': [m['month'] for m in monthly_summary],
                               'income': [m['income'] for m in monthly_summary],
                               'expenses': [m['expenses'] for m in monthly_summary],
                               'savings': [m['savings'] for m in monthly_summary]
                           },
                           category_data={
                               'labels': [cat[0] for cat in sorted_categories],
                               'data': [cat[1] for cat in sorted_categories]
                           },user_name=user_name.upper())


@app.route('/transactions', methods=["GET", "POST"])
def transactions():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']

    if request.method == "POST":
        txn = {
            "amount": float(request.form["amount"]),
            "category": request.form["category"],
            "description": request.form["description"],
            "date": request.form["date"],
            "type": request.form.get("type", "expense"),
            "email": email
        }
        mongo_transactions.insert_one(txn)
        return redirect(url_for('transactions'))

    transactions = mongo_transactions.find({'email': email}).sort("date", -1)
    formatted_txns = [{
    "id": str(txn.get("_id")),
    "date": datetime.strptime(txn.get("date", ""), "%Y-%m-%d").date(),
    "category": txn.get("category", "No Category"),
    "description": txn.get("description", "No description"),
    "amount": txn.get("amount", 0.0),
    "type": txn.get("type", "expense")
    } for txn in transactions]


    return render_template("transactions.html", transactions=formatted_txns,CATEGORIES=CATEGORIES)


@app.route('/transactions/delete/<txn_id>')
def delete_transaction(txn_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    mongo_transactions.delete_one({'_id': ObjectId(txn_id)})
    return redirect(url_for('transactions'))



@app.route('/transactions/edit/<txn_id>', methods=['GET', 'POST'])
def edit_transaction(txn_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))

    txn = mongo_transactions.find_one({'_id': ObjectId(txn_id)})
    if not txn:
        return redirect(url_for('transactions'))

    if request.method == 'POST':
        updated_txn = {
            "amount": float(request.form["amount"]),
            "category": request.form["category"],
            "description": request.form["description"],
            "date": request.form["date"],
            "type": request.form["type"],
            "email": txn['email']  # Retain the original user
        }
        mongo_transactions.update_one({'_id': ObjectId(txn_id)}, {'$set': updated_txn})
        return redirect(url_for('transactions'))

    return render_template("edit_transaction.html", txn=txn, CATEGORIES=CATEGORIES)




from datetime import datetime

@app.route('/budgets')
def budgets():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']
    budgets_data = list(mongo_budgets.find({'email': email}))

    # Get current year and month strings
    now = datetime.now()
    current_year = str(now.year)
    current_month = f"{now.month:02d}"  # zero-padded

    # Aggregate and filter using string matching (e.g., "2025-06")
    pipeline = [
        {
            "$match": {
                "email": email,
                "type": "expense",
                "$expr": {
                    "$eq": [
                        {"$substr": ["$date", 0, 7]},  # Extract "YYYY-MM"
                        f"{current_year}-{current_month}"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$category",
                "total_spent": {"$sum": "$amount"}
            }
        }
    ]

    expense_sums = list(mongo_transactions.aggregate(pipeline))
    spent_map = {e['_id']: e['total_spent'] for e in expense_sums}

    for b in budgets_data:
        cat = b['category']
        limit = b.get('limit', 0)
        spent = spent_map.get(cat, 0)
        b['spent'] = spent
        b['progress'] = round((spent / limit) * 100, 2) if limit > 0 else 0

    return render_template('budgets.html', budgets=budgets_data)



@app.route('/add-budget', methods=['POST'])
def add_budget():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']
    category = request.form.get('category')
    category=category.capitalize()
    limit = float(request.form.get('limit'))

    if not category or limit <= 0:
        flash("Invalid budget input!", "danger")
        return redirect(url_for('budgets'))

    existing = mongo_budgets.find_one({"email": email, "category": category})
    if existing:
        flash(f"Budget for '{category}' already exists.", "warning")
        return redirect(url_for('budgets'))

    mongo_budgets.insert_one({
        "category": category,
        "limit": limit,
        "email": email
    })

    flash(f"Budget for '{category}' added!", "success")
    return redirect(url_for('budgets'))


@app.route('/edit-budget/<budget_id>', methods=['POST'])
def edit_budget(budget_id):
    category = request.form.get('category')
    category=category.capitalize()
    limit = float(request.form.get('limit'))
    mongo_budgets.update_one(
        {"_id": ObjectId(budget_id)},
        {"$set": {"category": category, "limit": limit}}
    )
    flash("Budget updated.", "success")
    return redirect(url_for('budgets'))


@app.route('/delete-budget/<budget_id>', methods=['POST'])
def delete_budget(budget_id):
    mongo_budgets.delete_one({"_id": ObjectId(budget_id)})
    flash("Budget deleted.", "info")
    return redirect(url_for('budgets'))




@app.route('/peer_comparison')
def peer_comparison():
    # Get distinct user emails from transactions
    user_emails = mongo_transactions.distinct("email")

    user_savings = []

    for email in user_emails:
        # Get income total
        income_result = mongo_transactions.aggregate([
            {"$match": {"email": email, "type": "income"}},
            {"$group": {"_id": None, "total_income": {"$sum": "$amount"}}}
        ])
        income = next(income_result, {}).get("total_income", 0)

        # Get expense total
        expense_result = mongo_transactions.aggregate([
            {"$match": {"email": email, "type": "expense"}},
            {"$group": {"_id": None, "total_expense": {"$sum": "$amount"}}}
        ])
        expense = next(expense_result, {}).get("total_expense", 0)

        saved_amount = income - expense
        saving_percentage = (saved_amount / income * 100) if income > 0 else 0

        # Optionally fetch user's name
        user_info = mongo_db["users"].find_one({"email": email})
        raw_name = user_info.get("name") if user_info else email.split("@")[0]
        name = re.sub(r'\d+', '', raw_name)

        user_savings.append({
            "name": name,
            "email": email,
            "saved_amount": saved_amount,
            "saving_percentage": saving_percentage
        })

    # Sort users by saving percentage descending
    sorted_users = sorted(user_savings, key=lambda x: x["saving_percentage"], reverse=True)

    top3 = sorted_users[:3]
    next5 = sorted_users[3:8]

    return render_template("peer_comparison.html", top3=top3, next5=next5)




@app.route('/alerts')
def alerts():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']
    budgets_data = list(mongo_budgets.find({'email': email}))

    pipeline = [
        {"$match": {"email": email, "type": "expense"}},
        {"$group": {"_id": "$category", "total_spent": {"$sum": "$amount"}}}
    ]
    expense_sums = list(mongo_transactions.aggregate(pipeline))
    spent_map = {e['_id']: e['total_spent'] for e in expense_sums}

    alerts = []
    for b in budgets_data:
        cat = b['category']
        limit = b.get('limit', 0)
        spent = spent_map.get(cat, 0)
        percentage = (spent / limit) * 100 if limit > 0 else 0

        if percentage >= 90:
            alerts.append({
                'category': cat,
                'limit': limit,
                'spent': spent,
                'percentage': round(percentage, 2)
            })

    # Store alert count in session for use in sidebar
    session['alert_count'] = len(alerts)

    return render_template('alerts.html', alerts=alerts)




from datetime import datetime
from collections import defaultdict
from bson.objectid import ObjectId

@app.route('/groupChallenges', methods=["GET", "POST"])
def groupChallenges():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']

    if request.method == "POST":
        # Create new challenge
        challenge = {
            "name": request.form["challengeName"],
            "amount": float(request.form["targetAmount"]),
            "deadline": request.form["deadline"],
            "description": request.form["description"],
            "creator_email": user_email,
            "joined_users": [user_email]
        }
        mongo_challenges.insert_one(challenge)
        return redirect(url_for("groupChallenges"))

    challenges = list(mongo_challenges.find())
    contributions = list(mongo_db.challenge_contributions.find())

    from collections import defaultdict
    from datetime import datetime

    user_contributions = defaultdict(lambda: defaultdict(float))
    total_contributions = defaultdict(float)

    for c in contributions:
        cid = str(c['challenge_id'])
        user = c['user_email']
        amount = c['amount']
        user_contributions[cid][user] += amount
        total_contributions[cid] += amount

    joined_active = []
    not_joined = []
    completed = []
    now = datetime.utcnow()

    for c in challenges:
        cid = str(c['_id'])
        total = total_contributions.get(cid, 0)
        has_joined = user_email in c.get("joined_users", [])

        try:
            deadline = datetime.strptime(c['deadline'], "%Y-%m-%d")
        except:
            deadline = None

        is_completed = False
        status = None

        # ✅ Mark as WON immediately if goal is met
        if total >= c['amount']:
            status = "won"
            is_completed = True

        # ✅ Mark as LOST if deadline passed and goal not met
        elif deadline and now > deadline:
            status = "lost"
            is_completed = True

        if is_completed and has_joined:
            c['total'] = total
            c['status'] = status
            completed.append(c)
        elif has_joined:
            c['your_amount'] = user_contributions[cid].get(user_email, 0)
            c['total_amount'] = total
            joined_active.append(c)
        else:
            not_joined.append(c)

    return render_template(
        "groupChallenges.html",
        joined_challenges=joined_active,
        available_challenges=not_joined,
        completed_challenges=completed,
        user_contributions=user_contributions,
        total_contributions=total_contributions,
        user_email=user_email
    )



@app.route('/joinChallenge/<challenge_id>', methods=["POST"])
def join_challenge(challenge_id):
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for('login'))

    mongo_challenges.update_one(
        {"_id": ObjectId(challenge_id)},
        {"$addToSet": {"joined_users": user_email}}  # prevents duplicates
    )

    return redirect(url_for('groupChallenges'))



@app.route('/contribute', methods=['POST'])
def contribute():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']
    challenge_id = request.form.get('challenge_id')
    amount = request.form.get('amount')

    if not challenge_id or not amount:
        return "Missing data", 400

    try:
        amount = float(amount)
    except ValueError:
        return "Invalid amount", 400

    challenge = mongo_challenges.find_one({"_id": ObjectId(challenge_id)})
    if not challenge:
        return "Challenge not found", 404

    if user_email not in challenge.get('joined_users', []):
        return "You must join the challenge before contributing", 403

    mongo_db.challenge_contributions.insert_one({
        "challenge_id": ObjectId(challenge_id),
        "user_email": user_email,
        "amount": amount,
        "timestamp": datetime.utcnow()
    })

    return redirect(url_for('groupChallenges'))



if __name__ == '__main__':
    app.run(debug=True)
