import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, session, redirect, url_for
from database.models import db
from backend.auth.auth_routes import auth
from backend.routes.dashboard import dashboard_bp
from backend.routes.story_mode import story_bp


app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")
app.secret_key = "supersecretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
app.register_blueprint(story_bp)
app.register_blueprint(auth)
app.register_blueprint(dashboard_bp)

@app.route("/")
def index():
    if "user_email" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
