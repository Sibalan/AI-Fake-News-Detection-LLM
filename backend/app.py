import os
import logging
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session as flask_session,
)
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import inspect, text

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        static_url_path="/static",
        template_folder="../templates",
    )

    app.config.from_object("config.Config")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    from models import db, bcrypt, jwt

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from routes.auth import auth_bp
    from routes.predict import predict_bp
    from routes.history import history_bp
    from routes.admin import admin_bp
    from routes.news import news_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(news_bp)

    def login_required(f):
        from functools import wraps

        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in flask_session:
                flash("Please sign in to access this page", "error")
                return redirect(url_for("login_page"))
            return f(*args, **kwargs)

        return decorated

    def admin_required(f):
        from functools import wraps

        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in flask_session:
                flash("Please sign in to access this page", "error")
                return redirect(url_for("login_page"))
            if not flask_session.get("is_admin"):
                flash("Admin access required", "error")
                return redirect(url_for("dashboard_page"))
            return f(*args, **kwargs)

        return decorated

    # ========== Template Routes ==========

    @app.route("/")
    def home_page():
        return render_template("index.html")

    @app.route("/about")
    def about_page():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact_page():
        if request.method == "POST":
            name = request.form.get("name", "")
            email = request.form.get("email", "")
            message = request.form.get("message", "")
            logger.info(
                f"Contact form submission from {name} ({email}): {message[:50]}..."
            )
            flash("Message sent! We will get back to you.", "success")
            return redirect(url_for("contact_page"))
        return render_template("contact.html")

    from models.user import User

    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        if "user_id" in flask_session:
            return redirect(url_for("dashboard_page"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter(
                (User.username == username) | (User.email == username.lower())
            ).first()

            if user and user.check_password(password):
                if not user.is_active:
                    flash("Account is deactivated. Contact admin.", "error")
                    return render_template("login.html")

                from flask_jwt_extended import create_access_token

                token = create_access_token(identity=str(user.id))

                flask_session["user_id"] = user.id
                flask_session["username"] = user.username
                flask_session["email"] = user.email
                flask_session["full_name"] = user.full_name or user.username
                flask_session["is_admin"] = user.is_admin
                flask_session["jwt_token"] = token

                if user.is_admin:
                    from routes.admin import log_admin_action
                    log_admin_action(
                        user.id, f"Admin login: {user.username}",
                        details="Session started", ip=request.remote_addr, module="Auth"
                    )

                flash("Welcome back!", "success")
                return redirect(url_for("dashboard_page"))
            else:
                flash("Invalid credentials", "error")
                return render_template("login.html", form_data=request.form)

        return render_template("login.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup_page():
        if "user_id" in flask_session:
            return redirect(url_for("dashboard_page"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            full_name = request.form.get("full_name", "").strip()

            if not username or not email or not password:
                flash("All required fields must be filled", "error")
                return render_template("signup.html")

            if password != confirm:
                flash("Passwords do not match", "error")
                return render_template("signup.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters", "error")
                return render_template("signup.html")

            if User.query.filter_by(username=username).first():
                flash("Username already exists", "error")
                return render_template("signup.html")

            if User.query.filter_by(email=email).first():
                flash("Email already registered", "error")
                return render_template("signup.html")

            user = User(username=username, email=email, full_name=full_name or username)
            user.set_password(password)
            from models import db

            db.session.add(user)
            db.session.commit()

            from flask_jwt_extended import create_access_token

            token = create_access_token(identity=str(user.id))

            flask_session["user_id"] = user.id
            flask_session["username"] = user.username
            flask_session["email"] = user.email
            flask_session["full_name"] = user.full_name or user.username
            flask_session["is_admin"] = user.is_admin
            flask_session["jwt_token"] = token

            flash("Account created successfully!", "success")
            return redirect(url_for("dashboard_page"))

        return render_template("signup.html")

    @app.route("/logout")
    def logout():
        if flask_session.get("is_admin") and flask_session.get("user_id"):
            from routes.admin import log_admin_action
            log_admin_action(
                flask_session["user_id"], f"Admin logout: {flask_session.get('username', '')}",
                details="Session ended", ip=request.remote_addr, module="Auth"
            )
        flask_session.clear()
        flash("Signed out successfully", "success")
        return redirect(url_for("home_page"))

    @app.route("/dashboard")
    @login_required
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/detect")
    @login_required
    def detect_page():
        return render_template("detect.html")

    @app.route("/history")
    @login_required
    def history_page():
        return render_template("history.html")

    @app.route("/news")
    @login_required
    def news_page():
        return render_template("news.html")

    @app.route("/admin-logs")
    @admin_required
    def admin_logs_page():
        return render_template("admin_logs.html")

    @app.route("/change-password", methods=["GET", "POST"])
    @login_required
    def change_password_page():
        if request.method == "POST":
            current = request.form.get("current_password", "")
            new_pass = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")

            user = User.query.get(flask_session["user_id"])
            if not user or not user.check_password(current):
                flash("Current password is incorrect", "error")
                return render_template("change_password.html")

            if len(new_pass) < 6:
                flash("New password must be at least 6 characters", "error")
                return render_template("change_password.html")

            if new_pass != confirm:
                flash("Passwords do not match", "error")
                return render_template("change_password.html")

            user.set_password(new_pass)
            from models import db

            db.session.commit()
            flash("Password changed successfully", "success")
            return redirect(url_for("dashboard_page"))

        return render_template("change_password.html")

    @app.route("/admin")
    @admin_required
    def admin_page():
        return redirect("/admin-panel")

    @app.route("/admin-panel")
    @app.route("/admin-pannel")
    @login_required
    def admin_panel_page():
        return render_template("admin_panel.html")

    @app.route("/admin-login", methods=["GET", "POST"])
    def admin_login_page():
        if flask_session.get("is_admin"):
            return redirect(url_for("admin_panel_page"))

        # Clear any existing non-admin session so login form shows
        if "user_id" in flask_session and not flask_session.get("is_admin"):
            flask_session.clear()

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = User.query.filter(
                (User.username == username) | (User.email == username.lower())
            ).first()

            if user and user.check_password(password) and user.is_admin:
                if not user.is_active:
                    flash("Admin account is deactivated. Contact system administrator.", "error")
                    return render_template("admin_login.html")

                from flask_jwt_extended import create_access_token
                token = create_access_token(identity=str(user.id))

                flask_session["user_id"] = user.id
                flask_session["username"] = user.username
                flask_session["email"] = user.email
                flask_session["full_name"] = user.full_name or user.username
                flask_session["is_admin"] = True
                flask_session["jwt_token"] = token

                from routes.admin import log_admin_action
                log_admin_action(
                    user.id, f"Admin login: {user.username}",
                    details="Admin panel access via admin login page",
                    ip=request.remote_addr, module="Auth"
                )

                flash("Welcome to the Admin Panel!", "success")
                return redirect(url_for("admin_panel_page"))
            elif user and user.check_password(password) and not user.is_admin:
                flash("This account does not have administrator privileges.", "error")
            else:
                flash("Invalid admin credentials. Please try again.", "error")

            return render_template("admin_login.html", form_data=request.form)

        return render_template("admin_login.html")

    # ========== API Routes ==========

    @app.route("/api/health", methods=["GET"])
    def health_check():
        from ollama_client import check_ollama_status

        ollama_status = check_ollama_status()
        return jsonify(
            {
                "status": "healthy",
                "ollama": ollama_status,
                "version": "1.0.0",
                "project": "AI-Based Fake News Detection System",
                "institution": "AI Innovation Lab, Bengaluru",
            }
        )

    @app.route("/api/ollama/status", methods=["GET"])
    def ollama_status():
        from ollama_client import check_ollama_status

        return jsonify(check_ollama_status())

    @app.route("/api/predict/test", methods=["GET", "POST"])
    def predict_test():
        from ollama_client import analyze_with_phi3

        text = "Scientists discover a new species of frog in the Amazon rainforest."
        if request.method == "POST":
            text = request.get_json().get("text", text)
        result = analyze_with_phi3(text)
        return jsonify(
            {
                "status": "ok",
                "input_text": text[:100],
                "prediction": result.get("prediction"),
                "confidence": result.get("confidence"),
                "method": result.get("method"),
                "llm_source": result.get("llm_source"),
                "explanation": result.get("explanation", "")[:200],
            }
        )

    # Inject session into all templates
    @app.context_processor
    def inject_session():
        return dict(session=flask_session)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")

            try:
                inspector = inspect(db.engine)
                if "news_history" in inspector.get_table_names():
                    columns = [col["name"] for col in inspector.get_columns("news_history")]
                    if "source_type" not in columns:
                        logger.info("Adding missing source_type column to news_history")
                        db.session.execute(
                            text(
                                "ALTER TABLE news_history ADD COLUMN source_type VARCHAR(20) DEFAULT 'text'"
                            )
                        )
                        db.session.commit()
                    else:
                        db.session.execute(
                            text(
                                "UPDATE news_history SET source_type='text' WHERE source_type IS NULL"
                            )
                        )
                        db.session.commit()

                if "admin_logs" in inspector.get_table_names():
                    log_cols = [c["name"] for c in inspector.get_columns("admin_logs")]
                    if "module" not in log_cols:
                        logger.info("Adding missing module column to admin_logs")
                        db.session.execute(
                            text("ALTER TABLE admin_logs ADD COLUMN module VARCHAR(100)")
                        )
                        db.session.commit()
            except Exception as migration_err:
                logger.warning(f"Database schema check failed: {migration_err}")

            admin = User.query.filter_by(username="admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    email="admin@rvce.edu.in",
                    full_name="Admin RVCE",
                    is_admin=True,
                    is_active=True,
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created: admin / admin123")

            demo = User.query.filter_by(username="demo").first()
            if not demo:
                demo = User(
                    username="demo",
                    email="demo@rvce.edu.in",
                    full_name="Demo User",
                    is_admin=False,
                    is_active=True,
                )
                demo.set_password("demo123")
                db.session.add(demo)
                db.session.commit()
                logger.info("Demo user created: demo / demo123")
        except Exception as e:
            logger.error(f"Database init error: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
