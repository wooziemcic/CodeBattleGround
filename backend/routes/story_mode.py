import io
import contextlib
import json
from flask import Blueprint, render_template, session, redirect, url_for, request
from database.models import db, User
from datetime import datetime

story_bp = Blueprint("story", __name__)

@story_bp.route("/story-mode/<int:level_id>")
def story_mode(level_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    # Load track data
    with open("backend/data/story_tracks.json") as f:
        story_data = json.load(f)

    # For now, assume DA track and level 1
    track = story_data["DA"]
    current_level = next((lvl for lvl in track["levels"] if lvl["id"] == level_id), track["levels"][0])

    completed = user.story_progress.get("DA", [])
    current = current_level["id"]

    level_states = []
    for i in range(1, 4):
        if i in completed:
            status = "completed"
            icon = "level_unlocked.png"
        elif i == current:
            status = "current"
            icon = "level_unlocked.png"
        elif i == 3:
            status = "locked"
            icon = "boss_locked.png"
        else:
            status = "locked"
            icon = "level_locked.png"

        level_states.append({
            "id": i,
            "status": status,
            "icon": icon
        })

    return render_template(
        "story_mode.html",
        track_name=track["track_name"],
        description=track["description"],
        level=current_level,
        user=user,
        level_states=level_states
    )

@story_bp.route("/submit-code/<int:level_id>", methods=["POST"])
def submit_code(level_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    # Load track
    with open("backend/data/story_tracks.json") as f:
        story_data = json.load(f)

    # For now, assume level 1
    track = story_data["DA"]
    current_level = next((lvl for lvl in track["levels"] if lvl["id"] == level_id), track["levels"][0])

    submitted_code = request.form["code_input"]

    # Capture output of exec
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(submitted_code, {"__builtins__": __builtins__}, {})
        output = output_buffer.getvalue().strip()
    except Exception as e:
        output = f"ERROR: {str(e)}"

    expected_output = current_level["expected_output"]
    passed = (output == expected_output) or (expected_output.startswith(">=") and float(output) >= float(expected_output[2:]))

    # Feedback
    # 1. Load user's current progress for the track
    track_id = "DA"  # (can later be dynamic)
    completed_levels = user.story_progress.get(track_id, [])

    # 2. Check for correctness
    if passed:
        if current_level["id"] in completed_levels:
            feedback = "✅ Challenge Already Completed. No additional points awarded."
        else:
            user.points += 100
            completed_levels.append(current_level["id"])
            user.story_progress[track_id] = completed_levels
            user.add_activity(f"✅ Completed Story Level {current_level['id']} ({datetime.now().strftime('%b %d')})")

        db.session.commit()

        # Redirect to next level
        next_level_id = current_level["id"] + 1
        if next_level_id <= 3:
            return redirect(url_for("story.story_mode", level_id=next_level_id))
        else:
            return redirect(url_for("story.story_mode", level_id=current_level["id"]))

    else:
        feedback = f"❌ Incorrect. Your output: {output}"
        user.add_activity(f"❌ Failed Story Level {current_level['id']} ({datetime.now().strftime('%b %d')})")
        db.session.commit()
    
    # Build level_states for re-rendering UI
    level_states = []
    for i in range(1, 4):
        if i in completed_levels:
            status = "completed"
            icon = "level_unlocked.png"
        elif i == current_level["id"]:
            status = "current"
            icon = "level_unlocked.png"
        elif i == 3:
            status = "locked"
            icon = "boss_locked.png"
        else:
            status = "locked"
            icon = "level_locked.png"

        level_states.append({
            "id": i,
            "status": status,
            "icon": icon
        })

    return render_template(
    "story_mode.html",
    track_name=track["track_name"],
    description=track["description"],
    level=current_level,
    user=user,
    feedback=feedback,
    passed=passed,
    level_states=level_states
)

@story_bp.route("/run-code/<int:level_id>", methods=["POST"])
def run_code(level_id):
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for("auth.login"))

    # Load track + current level (hardcoded for now)
    with open("backend/data/story_tracks.json") as f:
        story_data = json.load(f)

    track = story_data["DA"]
    current_level = next((lvl for lvl in track["levels"] if lvl["id"] == level_id), track["levels"][0])

    submitted_code = request.form.get("code_input")

    # Run user code safely and capture output
    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(submitted_code, {"__builtins__": __builtins__}, {})
        test_output = output_buffer.getvalue().strip()
    except Exception as e:
        test_output = f"ERROR: {str(e)}"

    completed = user.story_progress.get("DA", [])
    current = current_level["id"]

    level_states = []
    for i in range(1, 4):
        if i in completed:
            status = "completed"
            icon = "level_unlocked.png"
        elif i == current:
            status = "current"
            icon = "level_unlocked.png"
        elif i == 3:
            status = "locked"
            icon = "boss_locked.png"
        else:
            status = "locked"
            icon = "level_locked.png"

        level_states.append({
            "id": i,
            "status": status,
            "icon": icon
        })

    return render_template(
        "story_mode.html",
        track_name=track["track_name"],
        description=track["description"],
        level=current_level,
        user=user,
        test_output=test_output,
        level_states=level_states
    )
