from flask import Blueprint, render_template, session, redirect, url_for, request
from database.models import User, db
from backend.one_v_one.challenge_pool import challenges
import io
import contextlib

one_v_one_bp = Blueprint("onevone", __name__)

@one_v_one_bp.route("/one-v-one")
def start_match():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))
    
    # Initialize session match state
    session["1v1"] = {
        "player_points": 5000,
        "opponent_points": 5000,
        "round": 1,
        "match_active": True,
        "last_result": None,
        "challenge": challenges[0]
    }   
    return render_template(
        "onevone.html",
        user=user,
        challenge=challenges[0],
        match=session["1v1"],
        player_hp_percent=session["1v1"]["player_points"] / 5000 * 100,
        opponent_hp_percent=session["1v1"]["opponent_points"] / 5000 * 100
    )

@one_v_one_bp.route("/submit-round", methods=["POST"])
def submit_round():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    match = session.get("1v1")
    if not match or not match.get("match_active"):
        return redirect(url_for("onevone.start_match"))

    round_num = match["round"]
    challenge = match["challenge"]
    submitted_code = request.form.get("code_input")

    # Safe execution
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(submitted_code, {"__builtins__": __builtins__}, {})
        output = output_buffer.getvalue().strip()
    except Exception as e:
        output = f"ERROR: {str(e)}"

    correct = (output == challenge["answer"])

    result_message = ""
    if correct:
        # Predefined damage values
        damage_values = {1: 1000, 2: 2000, 3: 3000, 4: 4000, 5: 5000}
        current_round = match["round"]

        damage = damage_values.get(current_round, 5000) 
        match["opponent_points"] = max(0, match["opponent_points"] - damage)
        result_message = f"✅ Correct! You dealt {damage} damage."

        # Check for win
        if match["opponent_points"] <= 0:
            match["match_active"] = False
            result_message += " 🎉 You won the match!"
            user.points += 200
            user.add_activity("🏆 Won a 1v1 match!")
    else:
        result_message = "❌ Incorrect output. No damage dealt."

    # Advance to next round
    if correct and match["match_active"]:
        match["round"] += 1
        next_index = (match["round"] - 1) % len(challenges)
        match["challenge"] = challenges[next_index]

    db.session.commit()

    session["1v1"] = match

    return render_template(
        "onevone.html",
        user=user,
        challenge=match["challenge"],
        match=match,
        result_message=result_message,
        player_hp_percent = session["1v1"]["player_points"] / 5000 * 100,
        opponent_hp_percent = session["1v1"]["opponent_points"] / 5000 * 100
    )

@one_v_one_bp.route("/timeout-round", methods=["POST"])
def timeout_round():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    match = session.get("1v1")

    if not match or not match.get("match_active"):
        return redirect(url_for("onevone.start_match"))

    # No damage dealt, just advance round
    match["round"] += 1
    next_index = (match["round"] - 1) % len(challenges)
    match["challenge"] = challenges[next_index]

    session["1v1"] = match

    return render_template(
        "onevone.html",
        user=user,
        challenge=match["challenge"],
        match=match,
        result_message="⏳ Time's up! Moving to next round.",
        player_hp_percent=match["player_points"] / 5000 * 100,
        opponent_hp_percent=match["opponent_points"] / 5000 * 100
    )


