from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
import datetime

budgets_bp = Blueprint('budgets_bp', __name__)

# Get MySQL from app
mysql = None
@budgets_bp.record
def record_mysql(setup_state):
    global mysql
    mysql = setup_state.app.extensions['mysql']

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to view this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@budgets_bp.route('/')
@login_required
def budgets():
    cur = mysql.connection.cursor()
    
    # Get current month and year budgets with spending data
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    cur.execute("""
        SELECT b.id, b.amount, b.month, b.year, c.name as category, c.color_code, c.id as category_id,
        (SELECT COALESCE(SUM(e.amount), 0) 
         FROM expenses e 
         WHERE e.category_id = b.category_id 
         AND e.user_id = %s 
         AND MONTH(e.date) = b.month 
         AND YEAR(e.date) = b.year) as spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = %s AND b.month = %s AND b.year = %s
        ORDER BY c.name
    """, (session['user_id'], session['user_id'], current_month, current_year))
    
    current_budgets = cur.fetchall()
    
    # Get all categories
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    
    # Get months with budgets for the dropdown
    cur.execute("""
        SELECT DISTINCT month, year 
        FROM budgets 
        WHERE user_id = %s 
        ORDER BY year DESC, month DESC
    """, [session['user_id']])
    budget_periods = cur.fetchall()
    
    cur.close()
    
    # Calculate totals
    total_budget = sum(budget[1] for budget in current_budgets)
    total_spent = sum(budget[7] for budget in current_budgets)
    
    return render_template('budgets/budgets.html',
                          budgets=current_budgets,
                          categories=categories,
                          budget_periods=budget_periods,
                          current_month=current_month,
                          current_year=current_year,
                          total_budget=total_budget,
                          total_spent=total_spent)

@budgets_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        # Get form data
        category_id = request.form['category']
        amount = request.form['amount']
        month = request.form['month']
        year = request.form['year']
        
        # Validate data
        if not category_id or not amount or not month or not year:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('budgets_bp.add_budget'))
        
        # Check if budget already exists for this category and month
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id FROM budgets 
            WHERE user_id = %s AND category_id = %s AND month = %s AND year = %s
        """, (session['user_id'], category_id, month, year))
        existing_budget = cur.fetchone()
        
        if existing_budget:
            flash('A budget for this category and month already exists!', 'danger')
            cur.close()
            return redirect(url_for('budgets_bp.add_budget'))
        
        # Insert budget
        cur.execute("""
            INSERT INTO budgets (user_id, category_id, amount, month, year)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], category_id, amount, month, year))
        mysql.connection.commit()
        cur.close()
        
        flash('Budget added successfully!', 'success')
        return redirect(url_for('budgets_bp.budgets'))
    
    # Get all categories for the form
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()
    
    # Set default month and year to current
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    return render_template('budgets/add_budget.html',
                           categories=categories,
                           current_month=current_month,
                           current_year=current_year)

@budgets_bp.route('/edit/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    # Get the budget
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT b.id, b.category_id, b.amount, b.month, b.year
        FROM budgets b
        WHERE b.id = %s AND b.user_id = %s
    """, (budget_id, session['user_id']))
    budget = cur.fetchone()
    
    if not budget:
        flash('Budget not found!', 'danger')
        return redirect(url_for('budgets_bp.budgets'))
    
    if request.method == 'POST':
        # Get form data
        amount = request.form['amount']
        
        # Validate data
        if not amount or float(amount) <= 0:
            flash('Please enter a valid amount', 'danger')
            return redirect(url_for('budgets_bp.edit_budget', budget_id=budget_id))
        
        # Update budget
        cur.execute("""
            UPDATE budgets
            SET amount = %s
            WHERE id = %s AND user_id = %s
        """, (amount, budget_id, session['user_id']))
        mysql.connection.commit()
        
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budgets_bp.budgets'))
    
    # Get category name
    cur.execute("SELECT name FROM categories WHERE id = %s", [budget[1]])
    category_name = cur.fetchone()[0]
    cur.close()
    
    return render_template('budgets/edit_budget.html',
                           budget=budget,
                           category_name=category_name)

@budgets_bp.route('/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    # Delete the budget
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM budgets
        WHERE id = %s AND user_id = %s
    """, (budget_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('budgets_bp.budgets'))

@budgets_bp.route('/view/<int:month>/<int:year>')
@login_required
def view_period(month, year):
    cur = mysql.connection.cursor()
    
    # Get budgets for specified month and year
    cur.execute("""
        SELECT b.id, b.amount, b.month, b.year, c.name as category, c.color_code, c.id as category_id,
        (SELECT COALESCE(SUM(e.amount), 0) 
         FROM expenses e 
         WHERE e.category_id = b.category_id 
         AND e.user_id = %s 
         AND MONTH(e.date) = b.month 
         AND YEAR(e.date) = b.year) as spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = %s AND b.month = %s AND b.year = %s
        ORDER BY c.name
    """, (session['user_id'], session['user_id'], month, year))
    
    period_budgets = cur.fetchall()
    
    # Get all categories
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    
    # Get months with budgets for the dropdown
    cur.execute("""
        SELECT DISTINCT month, year 
        FROM budgets 
        WHERE user_id = %s 
        ORDER BY year DESC, month DESC
    """, [session['user_id']])
    budget_periods = cur.fetchall()
    
    cur.close()
    
    # Calculate totals
    total_budget = sum(budget[1] for budget in period_budgets)
    total_spent = sum(budget[7] for budget in period_budgets)
    
    return render_template('budgets/budgets.html',
                          budgets=period_budgets,
                          categories=categories,
                          budget_periods=budget_periods,
                          current_month=month,
                          current_year=year,
                          total_budget=total_budget,
                          total_spent=total_spent)