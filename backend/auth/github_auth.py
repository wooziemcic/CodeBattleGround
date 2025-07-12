from flask import url_for

def init_github_auth(app):
    from flask_dance.contrib.github import make_github_blueprint

    blueprint = make_github_blueprint(
        client_id="Ov23liie97WXLTfvL629",
        client_secret="d49d006b41f8a4f6dcc02c4f10c7a42aa9aa5d07",
        scope="read:user"
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    # Debug the actual redirect URL Flask is building
    @app.route("/debug-real-redirect")
    def debug_real_redirect():
        return f"Real redirect URI used: {url_for('github.login', _external=True)}"
