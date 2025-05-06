from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
import datetime

goals_bp = Blueprint('goals_bp', __name__)

# Get MySQL from app
mysql = None
@goals_bp.record
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

@goals_bp.route('/')
@login_required
def goals():
    # Get all goals for the current user
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT g.id, g.name, g.description, g.target_amount, g.current_amount, 
               g.deadline, g.created_at, 
               DATEDIFF(g.deadline, CURRENT_DATE()) as days_left,
               (g.current_amount / g.target_amount * 100) as progress
        FROM goals g
        WHERE g.user_id = %s
        ORDER BY g.deadline ASC
    """, [session['user_id']])
    goals = cur.fetchall()
    
    # Separate goals into categories
    active_goals = []
    completed_goals = []
    expired_goals = []
    
    for goal in goals:
        if goal[4] >= goal[3]:  # current >= target
            completed_goals.append(goal)
        elif goal[7] < 0:  # days_left < 0
            expired_goals.append(goal)
        else:
            active_goals.append(goal)
    
    cur.close()
    
    return render_template('goals/goals.html',
                          active_goals=active_goals,
                          completed_goals=completed_goals,
                          expired_goals=expired_goals)

@goals_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form.get('description', '')
        target_amount = request.form['target_amount']
        current_amount = request.form.get('current_amount', 0)
        deadline = request.form['deadline']
        
        # Validate data
        if not name or not target_amount or not deadline:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('goals_bp.add_goal'))
        
        if float(target_amount) <= 0:
            flash('Target amount must be greater than zero', 'danger')
            return redirect(url_for('goals_bp.add_goal'))
        
        # Ensure current_amount is not greater than target_amount
        if float(current_amount) > float(target_amount):
            flash('Current amount cannot be greater than target amount', 'danger')
            return redirect(url_for('goals_bp.add_goal'))
        
        # Insert goal
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO goals (user_id, name, description, target_amount, current_amount, deadline)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], name, description, target_amount, current_amount, deadline))
        mysql.connection.commit()
        cur.close()
        
        flash('Goal added successfully!', 'success')
        return redirect(url_for('goals_bp.goals'))
    
    # Set min date to today
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    return render_template('goals/add_goal.html', today=today)

@goals_bp.route('/update/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def update_goal(goal_id):
    # Get the goal
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT g.id, g.name, g.description, g.target_amount, g.current_amount, g.deadline
        FROM goals g
        WHERE g.id = %s AND g.user_id = %s
    """, (goal_id, session['user_id']))
    goal = cur.fetchone()
    
    if not goal:
        flash('Goal not found!', 'danger')
        return redirect(url_for('goals_bp.goals'))
    
    if request.method == 'POST':
        # Get form data
        current_amount = request.form['current_amount']
        
        # Validate data
        if not current_amount or float(current_amount) < 0:
            flash('Please enter a valid amount', 'danger')
            return redirect(url_for('goals_bp.update_goal', goal_id=goal_id))
        
        if float(current_amount) > goal[3]:
            flash('Current amount cannot be greater than target amount', 'danger')
            return redirect(url_for('goals_bp.update_goal', goal_id=goal_id))
        
        # Update goal
        cur.execute("""
            UPDATE goals
            SET current_amount = %s
            WHERE id = %s AND user_id = %s
        """, (current_amount, goal_id, session['user_id']))
        mysql.connection.commit()
        
        # Check if goal is completed
        if float(current_amount) == float(goal[3]):
            flash('Congratulations! You have completed your goal!', 'success')
        else:
            flash('Goal progress updated successfully!', 'success')
        
        return redirect(url_for('goals_bp.goals'))
    
    # Format deadline for display
    formatted_deadline = goal[5].strftime('%Y-%m-%d')
    
    # Calculate progress percentage
    progress = (goal[4] / goal[3]) * 100 if goal[3] > 0 else 0
    
    cur.close()
    
    return render_template('goals/update_goal.html',
                           goal=goal,
                           formatted_deadline=formatted_deadline,
                           progress=progress)

@goals_bp.route('/edit/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    # Get the goal
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT g.id, g.name, g.description, g.target_amount, g.current_amount, g.deadline
        FROM goals g
        WHERE g.id = %s AND g.user_id = %s
    """, (goal_id, session['user_id']))
    goal = cur.fetchone()
    
    if not goal:
        flash('Goal not found!', 'danger')
        return redirect(url_for('goals_bp.goals'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form.get('description', '')
        target_amount = request.form['target_amount']
        current_amount = request.form['current_amount']
        deadline = request.form['deadline']
        
        # Validate data
        if not name or not target_amount or not deadline:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('goals_bp.edit_goal', goal_id=goal_id))
        
        if float(target_amount) <= 0:
            flash('Target amount must be greater than zero', 'danger')
            return redirect(url_for('goals_bp.edit_goal', goal_id=goal_id))
        
        if float(current_amount) > float(target_amount):
            flash('Current amount cannot be greater than target amount', 'danger')
            return redirect(url_for('goals_bp.edit_goal', goal_id=goal_id))
        
        # Update goal
        cur.execute("""
            UPDATE goals
            SET name = %s, description = %s, target_amount = %s, current_amount = %s, deadline = %s
            WHERE id = %s AND user_id = %s
        """, (name, description, target_amount, current_amount, deadline, goal_id, session['user_id']))
        mysql.connection.commit()
        
        flash('Goal updated successfully!', 'success')
        return redirect(url_for('goals_bp.goals'))
    
    # Format deadline for the form
    formatted_deadline = goal[5].strftime('%Y-%m-%d')
    
    # Set min date to today
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    cur.close()
    
    return render_template('goals/edit_goal.html',
                           goal=goal,
                           formatted_deadline=formatted_deadline,
                           today=today)

@goals_bp.route('/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    # Delete the goal
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM goals
        WHERE id = %s AND user_id = %s
    """, (goal_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals_bp.goals'))