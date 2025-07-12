from flask import Blueprint, render_template, session, redirect, url_for, request
from database.models import db, User
from datetime import datetime

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

    return render_template(
        "dashboard.html",
        user=user,
        challenge=challenge
    )

@dashboard_bp.route("/submit_challenge", methods=["POST"])
def submit_challenge():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    selected = request.form.get("answer")

    # Hardcoded daily challenge (same as shown earlier)
    challenge_answer = "B. 0 1 2"

    if selected == challenge_answer:
        # Add points
        user.points += 50

        # Log activity
        today_str = datetime.now().strftime("%b %d")
        user.add_activity(f"✅ Completed Daily Challenge ({today_str})")
        user.add_activity("✅ Earned 50 points")
    else:
        user.add_activity("❌ Incorrect Daily Challenge")

    db.session.commit()

    return redirect(url_for("dashboard.dashboard"))
