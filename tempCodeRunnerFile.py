@app.route('/group_challenges')
def group_challenges():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email']
    today = datetime.now()
    challenges = list(mongo_challenges.find({'participants': email}).sort('end_date', 1))

    active_challenges = []
    past_challenges = []

    for challenge in challenges:
        participants = challenge['participants']
        challenge['user_progress'] = get_user_progress(email, challenge)
        leaderboard = []

        for participant in participants:
            progress = get_user_progress(participant, challenge)
            leaderboard.append({'email': participant, 'progress': progress})

        leaderboard.sort(
            key=lambda x: x['progress'],
            reverse=(challenge['type'] == 'savings')  # savings = more is better, spending = less is better
        )
        challenge['leaderboard'] = leaderboard
        challenge['leader'] = leaderboard[0]['email'] if leaderboard else None

        if challenge['end_date'] >= today.strftime('%Y-%m-%d'):
            active_challenges.append(challenge)
        else:
            challenge['user_result'] = 'won' if leaderboard and leaderboard[0]['email'] == email else 'lost'
            past_challenges.append(challenge)

    return render_template("group_challenges.html",
                           active_challenges=active_challenges,
                           past_challenges=past_challenges,
                           today=today)
