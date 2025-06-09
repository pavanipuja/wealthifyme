app.py
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




 
