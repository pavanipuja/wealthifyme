from bson.objectid import ObjectId

@app.route('/groupChallenges', methods=["GET", "POST"])
def groupChallenges():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        creator_email = session["user_email"]

        challenge = {
            "name": request.form["challengeName"],
            "amount": float(request.form["targetAmount"]),
            "deadline": request.form["deadline"],
            "description": request.form["description"],
            "creator_email": creator_email,
            "joined_users": [creator_email]
        }

        print("Received form:", challenge)
        mongo_challenges.insert_one(challenge)
        return redirect(url_for("groupChallenges"))

    challenges = list(mongo_challenges.find())
    return render_template("groupChallenges.html", challenges=challenges)

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
