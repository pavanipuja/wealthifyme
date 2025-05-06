from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os
from datetime import datetime, timedelta
import json
from functools import wraps

app = Flask(__name__)

# Configure MySQL from config file
if os.path.exists('db.yaml'):
    with open('db.yaml') as f:
        db_config = yaml.safe_load(f)
        app.config['MYSQL_HOST'] = db_config['mysql_host']
        app.config['MYSQL_USER'] = db_config['mysql_user']
        app.config['MYSQL_PASSWORD'] = db_config['mysql_password']
        app.config['MYSQL_DB'] = db_config['mysql_db']
else:
    # Default configuration for development
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'wealthifyme'

app.config['SECRET_KEY'] = os.urandom(24)
mysql = MySQL(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to view this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        userDetails = request.form
        name = userDetails['name']
        email = userDetails['email']
        password = userDetails['password']
        confirm_password = userDetails['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
            
        # Check if user already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        
        if user:
            flash('Email already registered', 'danger')
            cur.close()
            return redirect(url_for('register'))
            
        # Hash password and insert user
        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", 
                    (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists and password is correct
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user[3], password):
            # Set session
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['email'] = user[2]
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    
    # Get user's expenses
    cur.execute("""
        SELECT e.id, e.amount, e.description, e.date, c.name as category, c.color_code 
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.date DESC LIMIT 10
    """, [session['user_id']])
    recent_expenses = cur.fetchall()
    
    # Get user's budget info
    cur.execute("""
        SELECT b.id, b.amount, b.month, b.year, c.name as category, c.color_code,
        (SELECT COALESCE(SUM(e.amount), 0) 
         FROM expenses e 
         WHERE e.category_id = b.category_id 
         AND e.user_id = %s 
         AND MONTH(e.date) = b.month 
         AND YEAR(e.date) = b.year) as spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = %s AND b.month = MONTH(CURRENT_DATE()) AND b.year = YEAR(CURRENT_DATE())
    """, (session['user_id'], session['user_id']))
    budgets = cur.fetchall()
    
    # Get user's goals
    cur.execute("""
        SELECT g.id, g.name, g.target_amount, g.current_amount, g.deadline, g.created_at
        FROM goals g
        WHERE g.user_id = %s
        ORDER BY g.deadline ASC
    """, [session['user_id']])
    goals = cur.fetchall()
    
    # Get monthly spending data for chart
    current_month = datetime.now().month
    current_year = datetime.now().year
    months_data = []
    
    for i in range(6):
        month = (current_month - i) if (current_month - i) > 0 else (current_month - i + 12)
        year = current_year if (current_month - i) > 0 else current_year - 1
        
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE user_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
        """, (session['user_id'], month, year))
        result = cur.fetchone()
        
        month_name = datetime(year, month, 1).strftime('%b')
        months_data.append({'month': month_name, 'total': result[0]})
    
    months_data.reverse()
    
    # Get spending by category for the current month
    cur.execute("""
        SELECT c.name, c.color_code, COALESCE(SUM(e.amount), 0) as total
        FROM categories c
        LEFT JOIN expenses e ON c.id = e.category_id 
            AND e.user_id = %s 
            AND MONTH(e.date) = MONTH(CURRENT_DATE())
            AND YEAR(e.date) = YEAR(CURRENT_DATE())
        GROUP BY c.id
        ORDER BY total DESC
    """, [session['user_id']])
    category_data = cur.fetchall()
    
    cur.close()
    
    return render_template('dashboard.html', 
                          recent_expenses=recent_expenses, 
                          budgets=budgets, 
                          goals=goals,
                          months_data=json.dumps(months_data),
                          category_data=category_data)

# Import and register blueprints
from routes.expenses import expenses_bp
from routes.budgets import budgets_bp
from routes.goals import goals_bp
from routes.social import social_bp

app.register_blueprint(expenses_bp, url_prefix='/expenses')
app.register_blueprint(budgets_bp, url_prefix='/budgets')
app.register_blueprint(goals_bp, url_prefix='/goals')
app.register_blueprint(social_bp, url_prefix='/social')

if __name__ == '__main__':
    app.run(debug=True)