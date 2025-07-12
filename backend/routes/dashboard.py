from flask import Blueprint, render_template, session, redirect, url_for, request
from database.models import db, User
from datetime import datetime,date

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    # Load today’s challenge (for now: hardcoded)
    challenge = {
        "question": "What will be the output of this code?",
        "code": "for i in range(3): print(i)",
        "options": [
            "A. 1 2 3",
            "B. 0 1 2",
            "C. Error"
        ],
        "answer": "B. 0 1 2"  # used later in submission
    }

    today = date.today().isoformat()
    already_attempted = user.last_challenge_date == today
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
    challenge_answer = "B. 0 1 2"

    # Clear duplicated activity if needed (safety measure)
    if user.recent_activity is None:
        user.recent_activity = []

    # Check answer
    if selected == challenge_answer:
        user.points += 50
        user.last_challenge_result = "success"
        user.last_challenge_date = today
        user.add_activity(f"✅ Completed Daily Challenge ({today})")
        user.add_activity("✅ Earned 50 points")
    else:
        user.last_challenge_result = "fail"
        user.last_challenge_date = today
        user.add_activity(f"❌ Failed Daily Challenge ({today})")

    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))