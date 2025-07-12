from flask import Blueprint, render_template, session, redirect, url_for, request
from database.models import db, User
from datetime import datetime,date
import json

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    # Load challenge pool
    with open("backend/data/daily_challenges.json") as f:
        all_challenges = json.load(f)

    # Deterministically pick one challenge per day
    today_index = hash(date.today().isoformat()) % len(all_challenges)
    challenge = all_challenges[today_index]

    already_attempted = user.last_challenge_date == date.today().isoformat()
    result = user.last_challenge_result if already_attempted else None

    return render_template(
        "dashboard.html",
        user=user,
        challenge=challenge,
        already_attempted=already_attempted,
        result=result
    )

@dashboard_bp.route("/submit_challenge", methods=["POST"])
def submit_challenge():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    today = date.today().isoformat()

    # ⛔ Prevent re-submission if already completed today
    if user.last_challenge_date == today:
        return redirect(url_for("dashboard.dashboard"))

    selected = request.form.get("answer")

    # Load challenge of the day from JSON
    with open("backend/data/daily_challenges.json") as f:
        all_challenges = json.load(f)
    today_index = hash(today) % len(all_challenges)
    challenge_answer = all_challenges[today_index]["answer"]

    # Activity safety init
    if user.recent_activity is None:
        user.recent_activity = []

    # Check answer
    if selected == challenge_answer:
        user.points += 50
        user.last_challenge_result = "success"
        user.add_activity(f"✅ Completed Daily Challenge ({today})")
        user.add_activity("✅ Earned 50 points")
    else:
        user.last_challenge_result = "fail"
        user.add_activity(f"❌ Failed Daily Challenge ({today})")

    # Set submission lock
    user.last_challenge_date = today

    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))