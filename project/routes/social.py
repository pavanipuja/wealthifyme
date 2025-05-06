from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
import datetime

social_bp = Blueprint('social_bp', __name__)

# Get MySQL from app
mysql = None
@social_bp.record
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

@social_bp.route('/')
@login_required
def social():
    cur = mysql.connection.cursor()
    
    # Get user's groups
    cur.execute("""
        SELECT g.id, g.name, g.description, g.created_at, 
               (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY g.created_at DESC
    """, [session['user_id']])
    user_groups = cur.fetchall()
    
    # Get saving challenges the user is participating in
    cur.execute("""
        SELECT sc.id, sc.name, sc.description, sc.target_amount, sc.start_date, sc.end_date,
               cp.current_amount, 
               (SELECT COUNT(*) FROM challenge_participants WHERE challenge_id = sc.id) as participant_count
        FROM saving_challenges sc
        JOIN challenge_participants cp ON sc.id = cp.challenge_id
        WHERE cp.user_id = %s
        ORDER BY sc.end_date ASC
    """, [session['user_id']])
    user_challenges = cur.fetchall()
    
    # Get public saving challenges the user is not participating in
    cur.execute("""
        SELECT sc.id, sc.name, sc.description, sc.target_amount, sc.start_date, sc.end_date,
               (SELECT COUNT(*) FROM challenge_participants WHERE challenge_id = sc.id) as participant_count
        FROM saving_challenges sc
        WHERE sc.is_public = TRUE
        AND NOT EXISTS (
            SELECT 1 FROM challenge_participants 
            WHERE challenge_id = sc.id AND user_id = %s
        )
        AND sc.end_date >= CURRENT_DATE()
        ORDER BY sc.start_date ASC
        LIMIT 5
    """, [session['user_id']])
    public_challenges = cur.fetchall()
    
    # Get spending comparison data (anonymized)
    cur.execute("""
        SELECT c.name as category,
               (SELECT AVG(amount) FROM expenses 
                WHERE category_id = c.id 
                AND MONTH(date) = MONTH(CURRENT_DATE()) 
                AND YEAR(date) = YEAR(CURRENT_DATE())) as avg_spending,
               (SELECT SUM(amount) FROM expenses 
                WHERE category_id = c.id 
                AND user_id = %s 
                AND MONTH(date) = MONTH(CURRENT_DATE()) 
                AND YEAR(date) = YEAR(CURRENT_DATE())) as user_spending
        FROM categories c
        WHERE EXISTS (
            SELECT 1 FROM expenses 
            WHERE category_id = c.id 
            AND MONTH(date) = MONTH(CURRENT_DATE()) 
            AND YEAR(date) = YEAR(CURRENT_DATE())
        )
        ORDER BY c.name
    """, [session['user_id']])
    spending_comparison = cur.fetchall()
    
    cur.close()
    
    return render_template('social/social.html',
                          user_groups=user_groups,
                          user_challenges=user_challenges,
                          public_challenges=public_challenges,
                          spending_comparison=spending_comparison)

@social_bp.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form.get('description', '')
        
        # Validate data
        if not name:
            flash('Please enter a group name', 'danger')
            return redirect(url_for('social_bp.create_group'))
        
        # Create group
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO groups (name, description, created_by)
            VALUES (%s, %s, %s)
        """, (name, description, session['user_id']))
        mysql.connection.commit()
        
        # Get the new group id
        group_id = cur.lastrowid
        
        # Add creator as a member
        cur.execute("""
            INSERT INTO group_members (group_id, user_id)
            VALUES (%s, %s)
        """, (group_id, session['user_id']))
        mysql.connection.commit()
        cur.close()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('social_bp.view_group', group_id=group_id))
    
    return render_template('social/create_group.html')

@social_bp.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    # Check if user is a member of the group
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 1 FROM group_members
        WHERE group_id = %s AND user_id = %s
    """, (group_id, session['user_id']))
    is_member = cur.fetchone() is not None
    
    if not is_member:
        flash('You are not a member of this group', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # Get group details
    cur.execute("""
        SELECT g.id, g.name, g.description, g.created_at, u.name as created_by_name,
               (g.created_by = %s) as is_owner
        FROM groups g
        JOIN users u ON g.created_by = u.id
        WHERE g.id = %s
    """, (session['user_id'], group_id))
    group = cur.fetchone()
    
    if not group:
        flash('Group not found!', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # Get group members
    cur.execute("""
        SELECT u.id, u.name, gm.joined_at
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = %s
        ORDER BY gm.joined_at
    """, [group_id])
    members = cur.fetchall()
    
    # Get group expenses
    cur.execute("""
        SELECT ge.id, ge.amount, ge.description, ge.date, u.name as paid_by_name,
               (ge.paid_by = %s) as is_payer
        FROM group_expenses ge
        JOIN users u ON ge.paid_by = u.id
        WHERE ge.group_id = %s
        ORDER BY ge.date DESC
    """, (session['user_id'], group_id))
    expenses = cur.fetchall()
    
    # Get user's expense shares
    cur.execute("""
        SELECT es.group_expense_id, es.amount, es.is_paid
        FROM expense_shares es
        JOIN group_expenses ge ON es.group_expense_id = ge.id
        WHERE es.user_id = %s AND ge.group_id = %s
    """, (session['user_id'], group_id))
    user_shares = {row[0]: (row[1], row[2]) for row in cur.fetchall()}
    
    cur.close()
    
    return render_template('social/view_group.html',
                          group=group,
                          members=members,
                          expenses=expenses,
                          user_shares=user_shares)

@social_bp.route('/groups/<int:group_id>/add-expense', methods=['GET', 'POST'])
@login_required
def add_group_expense(group_id):
    # Check if user is a member of the group
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 1 FROM group_members
        WHERE group_id = %s AND user_id = %s
    """, (group_id, session['user_id']))
    is_member = cur.fetchone() is not None
    
    if not is_member:
        flash('You are not a member of this group', 'danger')
        return redirect(url_for('social_bp.social'))
    
    if request.method == 'POST':
        # Get form data
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']
        split_type = request.form['split_type']
        
        # Validate data
        if not amount or not description or not date:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('social_bp.add_group_expense', group_id=group_id))
        
        # Begin transaction
        cur.execute("START TRANSACTION")
        
        try:
            # Add group expense
            cur.execute("""
                INSERT INTO group_expenses (group_id, paid_by, amount, description, date)
                VALUES (%s, %s, %s, %s, %s)
            """, (group_id, session['user_id'], amount, description, date))
            
            expense_id = cur.lastrowid
            
            # Get group members
            cur.execute("""
                SELECT user_id FROM group_members
                WHERE group_id = %s
            """, [group_id])
            members = [row[0] for row in cur.fetchall()]
            
            # Split expense based on split type
            if split_type == 'equal':
                share_amount = float(amount) / len(members)
                
                for member_id in members:
                    # Skip the payer
                    is_paid = member_id == session['user_id']
                    
                    cur.execute("""
                        INSERT INTO expense_shares (group_expense_id, user_id, amount, is_paid)
                        VALUES (%s, %s, %s, %s)
                    """, (expense_id, member_id, share_amount, is_paid))
            
            # Commit transaction
            mysql.connection.commit()
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('social_bp.view_group', group_id=group_id))
            
        except Exception as e:
            # Rollback in case of error
            mysql.connection.rollback()
            flash(f'Error adding expense: {str(e)}', 'danger')
            return redirect(url_for('social_bp.add_group_expense', group_id=group_id))
        finally:
            cur.close()
    
    # Get group details
    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM groups WHERE id = %s", [group_id])
    group_name = cur.fetchone()[0]
    cur.close()
    
    # Set default date to today
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    return render_template('social/add_group_expense.html',
                           group_id=group_id,
                           group_name=group_name,
                           today=today)

@social_bp.route('/challenges/create', methods=['GET', 'POST'])
@login_required
def create_challenge():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form.get('description', '')
        target_amount = request.form['target_amount']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        is_public = 'is_public' in request.form
        
        # Validate data
        if not name or not target_amount or not start_date or not end_date:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('social_bp.create_challenge'))
        
        if float(target_amount) <= 0:
            flash('Target amount must be greater than zero', 'danger')
            return redirect(url_for('social_bp.create_challenge'))
        
        if start_date > end_date:
            flash('Start date cannot be after end date', 'danger')
            return redirect(url_for('social_bp.create_challenge'))
        
        # Create challenge
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO saving_challenges (name, description, target_amount, start_date, end_date, created_by, is_public)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, description, target_amount, start_date, end_date, session['user_id'], is_public))
        mysql.connection.commit()
        
        # Get the new challenge id
        challenge_id = cur.lastrowid
        
        # Add creator as a participant
        cur.execute("""
            INSERT INTO challenge_participants (challenge_id, user_id)
            VALUES (%s, %s)
        """, (challenge_id, session['user_id']))
        mysql.connection.commit()
        cur.close()
        
        flash('Saving challenge created successfully!', 'success')
        return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))
    
    # Set min date to today
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    return render_template('social/create_challenge.html', today=today)

@social_bp.route('/challenges/<int:challenge_id>')
@login_required
def view_challenge(challenge_id):
    # Check if user is a participant
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 1 FROM challenge_participants
        WHERE challenge_id = %s AND user_id = %s
    """, (challenge_id, session['user_id']))
    is_participant = cur.fetchone() is not None
    
    # Get challenge details
    cur.execute("""
        SELECT sc.id, sc.name, sc.description, sc.target_amount, sc.start_date, sc.end_date,
               sc.is_public, u.name as created_by_name, (sc.created_by = %s) as is_creator
        FROM saving_challenges sc
        JOIN users u ON sc.created_by = u.id
        WHERE sc.id = %s
    """, (session['user_id'], challenge_id))
    challenge = cur.fetchone()
    
    if not challenge:
        flash('Challenge not found!', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # If not participant and not public, deny access
    if not is_participant and not challenge[6]:
        flash('This is a private challenge. You are not a participant.', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # Get challenge participants
    cur.execute("""
        SELECT u.id, u.name, cp.current_amount, cp.joined_at
        FROM challenge_participants cp
        JOIN users u ON cp.user_id = u.id
        WHERE cp.challenge_id = %s
        ORDER BY cp.current_amount DESC
    """, [challenge_id])
    participants = cur.fetchall()
    
    # Calculate days left
    days_left = (challenge[5] - datetime.date.today()).days
    
    # Calculate user's progress if participant
    user_progress = 0
    if is_participant:
        for participant in participants:
            if participant[0] == session['user_id']:
                user_progress = (participant[2] / challenge[3]) * 100 if challenge[3] > 0 else 0
                break
    
    cur.close()
    
    return render_template('social/view_challenge.html',
                          challenge=challenge,
                          participants=participants,
                          is_participant=is_participant,
                          days_left=days_left,
                          user_progress=user_progress)

@social_bp.route('/challenges/<int:challenge_id>/join', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    # Check if challenge exists and is public
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT is_public FROM saving_challenges
        WHERE id = %s
    """, [challenge_id])
    result = cur.fetchone()
    
    if not result:
        flash('Challenge not found!', 'danger')
        return redirect(url_for('social_bp.social'))
    
    is_public = result[0]
    
    if not is_public:
        flash('This is a private challenge. You cannot join.', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # Check if user is already a participant
    cur.execute("""
        SELECT 1 FROM challenge_participants
        WHERE challenge_id = %s AND user_id = %s
    """, (challenge_id, session['user_id']))
    is_participant = cur.fetchone() is not None
    
    if is_participant:
        flash('You are already participating in this challenge!', 'warning')
        return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))
    
    # Add user as participant
    cur.execute("""
        INSERT INTO challenge_participants (challenge_id, user_id)
        VALUES (%s, %s)
    """, (challenge_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('You have successfully joined the challenge!', 'success')
    return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))

@social_bp.route('/challenges/<int:challenge_id>/update', methods=['POST'])
@login_required
def update_challenge_progress(challenge_id):
    # Check if user is a participant
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 1 FROM challenge_participants
        WHERE challenge_id = %s AND user_id = %s
    """, (challenge_id, session['user_id']))
    is_participant = cur.fetchone() is not None
    
    if not is_participant:
        flash('You are not a participant in this challenge!', 'danger')
        return redirect(url_for('social_bp.social'))
    
    # Get form data
    current_amount = request.form['current_amount']
    
    if not current_amount or float(current_amount) < 0:
        flash('Please enter a valid amount', 'danger')
        return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))
    
    # Get challenge target amount
    cur.execute("""
        SELECT target_amount FROM saving_challenges
        WHERE id = %s
    """, [challenge_id])
    target_amount = cur.fetchone()[0]
    
    if float(current_amount) > target_amount:
        flash('Current amount cannot be greater than target amount', 'danger')
        return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))
    
    # Update progress
    cur.execute("""
        UPDATE challenge_participants
        SET current_amount = %s
        WHERE challenge_id = %s AND user_id = %s
    """, (current_amount, challenge_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    
    flash('Your progress has been updated!', 'success')
    return redirect(url_for('social_bp.view_challenge', challenge_id=challenge_id))