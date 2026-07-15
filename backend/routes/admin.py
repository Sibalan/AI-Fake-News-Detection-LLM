from flask import Blueprint, request, jsonify, session as flask_session
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from backend.models.user import User, AdminLog, ContactMessage
from backend.models.news import NewsHistory, Dataset
from backend.models.prediction import PredictionLog
from backend.models import db
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def get_admin_id():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            decoded = decode_token(token)
            uid = int(decoded["sub"])
            user = User.query.get(uid)
            if user and user.is_admin:
                return uid
        except Exception:
            pass
    uid = flask_session.get("user_id")
    if uid:
        user = User.query.get(uid)
        if user and user.is_admin:
            return uid
    return None


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        admin_id = get_admin_id()
        if not admin_id:
            return jsonify({"error": "Admin access required"}), 403
        return f(admin_id, *args, **kwargs)

    return decorated


def log_admin_action(admin_id, action, details=None, ip=None, module=None):
    if not action or not str(action).strip():
        logger.warning("log_admin_action: action cannot be empty")
        return
    try:
        log = AdminLog(
            admin_id=admin_id,
            action=str(action).strip()[:255],
            details=details,
            module=module,
            ip_address=ip,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Admin log error: {e}")
        db.session.rollback()


@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users(admin_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        search = request.args.get("search", "")

        query = User.query
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%"),
                )
            )

        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "users": [u.to_dict() for u in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
            }
        ), 200
    except Exception as e:
        logger.error(f"Admin users error: {e}")
        return jsonify({"error": "Failed to load users"}), 500


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(admin_id, user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.is_admin:
            return jsonify({"error": "Cannot modify admin users"}), 403

        user.is_active = not user.is_active
        db.session.commit()

        action = "deactivated" if not user.is_active else "activated"
        log_admin_action(
            admin_id,
            f"User {action}: {user.username}",
            f"User ID: {user_id}",
            request.remote_addr,
        )

        return jsonify({"message": f"User {action}", "user": user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Toggle user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to toggle user"}), 500


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def get_dashboard(admin_id):
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_count = User.query.filter_by(is_admin=True).count()
        total_predictions = PredictionLog.query.count()
        total_history = NewsHistory.query.count()

        real_count = NewsHistory.query.filter_by(prediction="REAL").count()
        fake_count = NewsHistory.query.filter_by(prediction="FAKE").count()
        daily_scans = NewsHistory.query.filter(
            NewsHistory.created_at >= db.func.dateadd(db.text("day"), -1, db.func.now())
        ).count()

        recent_predictions = (
            PredictionLog.query.order_by(PredictionLog.created_at.desc())
            .limit(10)
            .all()
        )
        recent_history = (
            NewsHistory.query.order_by(NewsHistory.created_at.desc()).limit(8).all()
        )

        keyword_rows = (
            db.session.query(
                NewsHistory.keywords,
                db.func.count(NewsHistory.id).label("count"),
            )
            .filter(NewsHistory.keywords != None)
            .group_by(NewsHistory.keywords)
            .order_by(db.desc("count"))
            .limit(6)
            .all()
        )
        top_keywords = []
        for keywords, count in keyword_rows:
            if keywords:
                for term in keywords.split(","):
                    clean_term = term.strip().title()
                    if clean_term:
                        top_keywords.append({"term": clean_term, "count": count})
                        break

        source_type_breakdown = {}
        for source_type in NewsHistory.query.with_entities(NewsHistory.source_type).distinct():
            type_name = source_type[0] or "text"
            source_type_breakdown[type_name] = NewsHistory.query.filter_by(source_type=type_name).count()

        timeline = []
        for day in range(7):
            from datetime import datetime, timedelta
            current = (datetime.utcnow() - timedelta(days=day)).date().isoformat()
            day_count = NewsHistory.query.filter(db.func.date(NewsHistory.created_at) == current).count()
            day_real = NewsHistory.query.filter(
                db.func.date(NewsHistory.created_at) == current,
                NewsHistory.prediction == "REAL",
            ).count()
            day_fake = NewsHistory.query.filter(
                db.func.date(NewsHistory.created_at) == current,
                NewsHistory.prediction == "FAKE",
            ).count()
            timeline.append({"date": current, "total": day_count, "real": day_real, "fake": day_fake})

        accuracy = 0
        if total_history:
            accuracy = round((real_count / total_history) * 100, 1)

        return jsonify(
            {
                "total_users": total_users,
                "active_users": active_users,
                "admin_count": admin_count,
                "total_predictions": total_predictions,
                "total_history": total_history,
                "real_count": real_count,
                "fake_count": fake_count,
                "daily_scans": daily_scans,
                "detection_accuracy": accuracy,
                "top_keywords": top_keywords[:5],
                "most_common_source_type": max(source_type_breakdown.items(), key=lambda item: item[1], default=("text", 0))[0],
                "source_type_breakdown": source_type_breakdown,
                "recent_predictions": [p.to_dict() for p in recent_predictions],
                "recent_history": [h.to_dict() for h in recent_history],
                "timeline": list(reversed(timeline)),
            }
        ), 200
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({"error": "Failed to load dashboard"}), 500


@admin_bp.route("/history", methods=["GET"])
@admin_required
def get_all_history(admin_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        search = request.args.get("search", "")

        query = NewsHistory.query
        if search:
            query = query.filter(NewsHistory.news_text.ilike(f"%{search}%"))

        pagination = query.order_by(NewsHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "history": [item.to_dict() for item in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
            }
        ), 200
    except Exception as e:
        logger.error(f"Admin history error: {e}")
        return jsonify({"error": "Failed to load history"}), 500


@admin_bp.route("/datasets", methods=["GET"])
@admin_required
def get_datasets(admin_id):
    try:
        datasets = Dataset.query.order_by(Dataset.created_at.desc()).all()
        return jsonify({"datasets": [d.to_dict() for d in datasets]}), 200
    except Exception as e:
        logger.error(f"Datasets error: {e}")
        return jsonify({"error": "Failed to load datasets"}), 500


@admin_bp.route("/logs", methods=["GET"])
@admin_required
def get_admin_logs(admin_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        pagination = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        logs = []
        for log in pagination.items:
            l = log.to_dict()
            admin_user = User.query.get(log.admin_id)
            l["admin_name"] = (
                admin_user.full_name or admin_user.username if admin_user else "Unknown"
            )
            logs.append(l)

        return jsonify(
            {
                "logs": logs,
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
            }
        ), 200
    except Exception as e:
        logger.error(f"Admin logs error: {e}")
        return jsonify({"error": "Failed to load logs"}), 500


@admin_bp.route("/contact-messages", methods=["GET"])
@admin_required
def get_contact_messages(admin_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        unread_only = request.args.get("unread_only", 0, type=int)

        query = ContactMessage.query.order_by(ContactMessage.created_at.desc())
        if unread_only:
            query = query.filter_by(is_read=False)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify(
            {
                "messages": [m.to_dict() for m in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
                "total_unread": ContactMessage.query.filter_by(is_read=False).count(),
            }
        ), 200
    except Exception as e:
        logger.error(f"Contact messages error: {e}")
        return jsonify({"error": "Failed to load contact messages"}), 500


@admin_bp.route("/contact-messages/<int:message_id>/read", methods=["POST"])
@admin_required
def mark_contact_message_read(admin_id, message_id):
    try:
        message = ContactMessage.query.get(message_id)
        if not message:
            return jsonify({"error": "Message not found"}), 404

        message.is_read = True
        db.session.commit()
        log_admin_action(
            admin_id,
            f"Marked contact message #{message_id} as read",
            f"Contact from {message.name}",
            request.remote_addr,
            module="Contact",
        )
        return jsonify({"message": "Message marked as read", "contact": message.to_dict()}), 200
    except Exception as e:
        logger.error(f"Mark contact message error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update message"}), 500


@admin_bp.route("/users", methods=["POST"])
@admin_required
def create_user(admin_id):
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip() or username

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log_admin_action(
            admin_id,
            f"Created user: {username}",
            f"User created via admin panel",
            request.remote_addr,
        )
        return jsonify({"message": "User created", "user": user.to_dict()}), 201
    except Exception as e:
        logger.error(f"Create user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create user"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(admin_id, user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        if "full_name" in data:
            user.full_name = data["full_name"].strip() or user.full_name
        if "email" in data:
            new_email = data["email"].strip().lower()
            existing = User.query.filter(
                User.email == new_email, User.id != user_id
            ).first()
            if existing:
                return jsonify({"error": "Email already in use"}), 409
            user.email = new_email
        if "password" in data and data["password"]:
            user.set_password(data["password"])

        db.session.commit()
        log_admin_action(
            admin_id,
            f"Updated user: {user.username}",
            f"User ID: {user_id}",
            request.remote_addr,
        )
        return jsonify({"message": "User updated", "user": user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Update user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to update user"}), 500


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(admin_id, user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.is_admin:
            return jsonify({"error": "Cannot delete admin users"}), 403

        username = user.username
        db.session.delete(user)
        db.session.commit()

        log_admin_action(
            admin_id,
            f"Deleted user: {username}",
            f"User ID: {user_id}",
            request.remote_addr,
        )
        return jsonify({"message": f"User {username} deleted"}), 200
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete user"}), 500


@admin_bp.route("/history/<int:history_id>", methods=["DELETE"])
@admin_required
def delete_history(admin_id, history_id):
    try:
        item = NewsHistory.query.get(history_id)
        if not item:
            return jsonify({"error": "History entry not found"}), 404
        db.session.delete(item)
        db.session.commit()
        log_admin_action(
            admin_id, f"Deleted history entry #{history_id}", "", request.remote_addr
        )
        return jsonify({"message": "History entry deleted"}), 200
    except Exception as e:
        logger.error(f"Delete history error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete history entry"}), 500


@admin_bp.route("/history", methods=["DELETE"])
@admin_required
def clear_history(admin_id):
    try:
        count = NewsHistory.query.count()
        NewsHistory.query.delete()
        PredictionLog.query.delete()
        db.session.commit()
        log_admin_action(
            admin_id, f"Cleared all history ({count} entries)", "", request.remote_addr
        )
        return jsonify(
            {"message": f"All history cleared ({count} entries deleted)"}
        ), 200
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to clear history"}), 500


@admin_bp.route("/logs/<int:log_id>", methods=["DELETE"])
@admin_required
def delete_admin_log(admin_id, log_id):
    try:
        log = AdminLog.query.get(log_id)
        if not log:
            return jsonify({"error": "Log entry not found"}), 404
        db.session.delete(log)
        db.session.commit()
        return jsonify({"message": f"Log #{log_id} deleted"}), 200
    except Exception as e:
        logger.error(f"Delete admin log error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete log"}), 500


@admin_bp.route("/logs", methods=["POST"])
@admin_required
def create_admin_log(admin_id):
    data = request.get_json() or {}
    action = (data.get("action") or "").strip()
    if not action:
        return jsonify({"error": "Action is required"}), 400
    if len(action) < 3:
        return jsonify({"error": "Action must be at least 3 characters"}), 400
    log_admin_action(
        admin_id,
        action,
        details=data.get("details", ""),
        ip=request.remote_addr,
        module=data.get("module", ""),
    )
    return jsonify({"message": "Log entry created"}), 201


@admin_bp.route("/stats/methods", methods=["GET"])
@admin_required
def get_stats_methods(admin_id):
    try:
        records = (
            db.session.query(
                NewsHistory.method, db.func.count(NewsHistory.id).label("count")
            )
            .filter(NewsHistory.method != None)
            .group_by(NewsHistory.method)
            .all()
        )

        methods = {}
        for r in records:
            methods[r.method or "unknown"] = r.count
        return jsonify({"methods": methods}), 200
    except Exception as e:
        logger.error(f"Stats methods error: {e}")
        return jsonify({"error": "Failed to load method stats"}), 500


@admin_bp.route("/stats/top-users", methods=["GET"])
@admin_required
def get_top_users(admin_id):
    try:
        records = (
            db.session.query(
                NewsHistory.user_id, db.func.count(NewsHistory.id).label("count")
            )
            .filter(NewsHistory.user_id != None)
            .group_by(NewsHistory.user_id)
            .order_by(db.desc("count"))
            .limit(10)
            .all()
        )

        top = []
        for r in records:
            u = User.query.get(r.user_id)
            top.append(
                {
                    "user_id": r.user_id,
                    "name": u.full_name or u.username if u else "Deleted",
                    "count": r.count,
                }
            )
        return jsonify({"top_users": top}), 200
    except Exception as e:
        logger.error(f"Top users error: {e}")
        return jsonify({"error": "Failed to load top users"}), 500


@admin_bp.route("/stats/timeline", methods=["GET"])
@admin_required
def get_prediction_timeline(admin_id):
    try:
        from datetime import datetime, timedelta

        days = request.args.get("days", 30, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        records = (
            db.session.query(
                db.func.date(NewsHistory.created_at).label("date"),
                db.func.count(NewsHistory.id).label("count"),
                db.func.sum(
                    db.case((NewsHistory.prediction == "FAKE", 1), else_=0)
                ).label("fake_count"),
            )
            .filter(NewsHistory.created_at >= since)
            .group_by(db.func.date(NewsHistory.created_at))
            .order_by(db.func.date(NewsHistory.created_at))
            .all()
        )

        timeline = []
        for r in records:
            timeline.append(
                {
                    "date": str(r.date),
                    "total": r.count,
                    "fake": int(r.fake_count or 0),
                    "real": r.count - int(r.fake_count or 0),
                }
            )

        return jsonify({"timeline": timeline}), 200
    except Exception as e:
        logger.error(f"Timeline error: {e}")
        return jsonify({"error": "Failed to load timeline"}), 500
