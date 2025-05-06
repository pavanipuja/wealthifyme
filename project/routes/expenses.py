from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
import datetime

expenses_bp = Blueprint('expenses_bp', __name__)

# Get MySQL from app
mysql = None
@expenses_bp.record
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

@expenses_bp.route('/')
@login_required
def expenses():
    # Get all expenses for the current user
    cur = mysql.connection.cursor()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Get total count for pagination
    cur.execute("""
        SELECT COUNT(*) FROM expenses 
        WHERE user_id = %s
    """, [session['user_id']])
    total_count = cur.fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get expenses with pagination
    cur.execute("""
        SELECT e.id, e.amount, e.description, e.date, c.name as category, c.color_code 
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.date DESC
        LIMIT %s OFFSET %s
    """, (session['user_id'], per_page, offset))
    expenses = cur.fetchall()
    
    # Get all categories for the filter
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('expenses/expenses.html', 
                          expenses=expenses, 
                          categories=categories,
                          page=page,
                          total_pages=total_pages)

@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        # Get form data
        category_id = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']
        
        # Validate data
        if not category_id or not amount or not date:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('expenses_bp.add_expense'))
        
        # Insert expense
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO expenses (user_id, category_id, amount, description, date)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], category_id, amount, description, date))
        mysql.connection.commit()
        cur.close()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses_bp.expenses'))
    
    # Get all categories for the form
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()
    
    # Set default date to today
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    return render_template('expenses/add_expense.html', 
                           categories=categories,
                           today=today)

@expenses_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    # Get the expense
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.id, e.category_id, e.amount, e.description, e.date
        FROM expenses e
        WHERE e.id = %s AND e.user_id = %s
    """, (expense_id, session['user_id']))
    expense = cur.fetchone()
    
    if not expense:
        flash('Expense not found!', 'danger')
        return redirect(url_for('expenses_bp.expenses'))
    
    if request.method == 'POST':
        # Get form data
        category_id = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']
        
        # Validate data
        if not category_id or not amount or not date:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('expenses_bp.edit_expense', expense_id=expense_id))
        
        # Update expense
        cur.execute("""
            UPDATE expenses
            SET category_id = %s, amount = %s, description = %s, date = %s
            WHERE id = %s AND user_id = %s
        """, (category_id, amount, description, date, expense_id, session['user_id']))
        mysql.connection.commit()
        
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses_bp.expenses'))
    
    # Format date for the form
    formatted_date = expense[4].strftime('%Y-%m-%d')
    
    # Get all categories for the form
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    cur.close()
    
    return render_template('expenses/edit_expense.html', 
                           expense=expense, 
                           categories=categories,
                           formatted_date=formatted_date)

@expenses_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    # Delete the expense
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM expenses
        WHERE id = %s AND user_id = %s
    """, (expense_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses_bp.expenses'))

@expenses_bp.route('/filter', methods=['GET'])
@login_required
def filter_expenses():
    # Get filter parameters
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Build query dynamically
    query = """
        SELECT e.id, e.amount, e.description, e.date, c.name as category, c.color_code 
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
    """
    params = [session['user_id']]
    
    if category and category != 'all':
        query += " AND e.category_id = %s"
        params.append(category)
    
    if start_date:
        query += " AND e.date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND e.date <= %s"
        params.append(end_date)
    
    if min_amount:
        query += " AND e.amount >= %s"
        params.append(min_amount)
    
    if max_amount:
        query += " AND e.amount <= %s"
        params.append(max_amount)
    
    query += " ORDER BY e.date DESC"
    
    # Execute query
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    expenses = cur.fetchall()
    
    # Get all categories for the filter
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    
    cur.close()
    
    return render_template('expenses/expenses.html', 
                          expenses=expenses, 
                          categories=categories,
                          filters={
                              'category': category,
                              'start_date': start_date,
                              'end_date': end_date,
                              'min_amount': min_amount,
                              'max_amount': max_amount
                          })