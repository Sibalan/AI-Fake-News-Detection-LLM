from flask import Blueprint, request, jsonify, session as flask_session
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from sqlalchemy import inspect
from backend.models.news import NewsHistory
from backend.models import db
import logging

logger = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__, url_prefix="/api/history")


def get_user_id():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        try:
            decoded = decode_token(token)
            return int(decoded["sub"])
        except Exception:
            pass
    return flask_session.get("user_id")


def auth_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        uid = get_user_id()
        if not uid:
            return jsonify({"error": "Authentication required"}), 401
        return f(uid, *args, **kwargs)

    return decorated


@history_bp.route("/", methods=["GET"])
@auth_required
def get_history(user_id):
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "").strip()
        prediction_filter = request.args.get("prediction", "").strip()
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")

        query = NewsHistory.query.filter_by(user_id=user_id)

        if search:
            query = query.filter(NewsHistory.news_text.ilike(f"%{search}%"))

        if prediction_filter in ["REAL", "FAKE"]:
            query = query.filter_by(prediction=prediction_filter)

        if sort_by == "confidence":
            order_col = NewsHistory.confidence
        elif sort_by == "prediction":
            order_col = NewsHistory.prediction
        else:
            order_col = NewsHistory.created_at

        query = query.order_by(
            order_col.desc() if sort_order == "desc" else order_col.asc()
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify(
            {
                "history": [item.to_dict() for item in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page,
                "per_page": per_page,
            }
        ), 200

    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({"error": "Failed to load history"}), 500


@history_bp.route("/<int:history_id>", methods=["GET"])
@auth_required
def get_history_detail(user_id, history_id):
    try:
        item = NewsHistory.query.filter_by(id=history_id, user_id=user_id).first()
        if not item:
            return jsonify({"error": "History item not found"}), 404
        return jsonify(item.to_dict()), 200
    except Exception as e:
        logger.error(f"History detail error: {e}")
        return jsonify({"error": "Failed to load item"}), 500


@history_bp.route("/<int:history_id>", methods=["DELETE"])
@auth_required
def delete_history(user_id, history_id):
    try:
        item = NewsHistory.query.filter_by(id=history_id, user_id=user_id).first()
        if not item:
            return jsonify({"error": "History item not found"}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "History item deleted"}), 200
    except Exception as e:
        logger.error(f"History delete error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete"}), 500


@history_bp.route("/clear", methods=["DELETE"])
@auth_required
def clear_history(user_id):
    try:
        NewsHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"message": "History cleared"}), 200
    except Exception as e:
        logger.error(f"History clear error: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to clear history"}), 500


@history_bp.route("/stats", methods=["GET"])
@auth_required
def get_stats(user_id):
    try:
        total = NewsHistory.query.filter_by(user_id=user_id).count()
        real_count = NewsHistory.query.filter_by(
            user_id=user_id, prediction="REAL"
        ).count()
        fake_count = NewsHistory.query.filter_by(
            user_id=user_id, prediction="FAKE"
        ).count()
        avg_confidence = (
            db.session.query(db.func.avg(NewsHistory.confidence))
            .filter_by(user_id=user_id)
            .scalar()
            or 0
        )
        active_users = (
            db.session.query(db.func.count(db.distinct(NewsHistory.user_id)))
            .filter(NewsHistory.user_id.isnot(None))
            .scalar()
            or 0
        )

        source_type_column_exists = False
        try:
            columns = inspect(db.engine).get_columns("news_history")
            source_type_column_exists = any(col["name"] == "source_type" for col in columns)
        except Exception:
            source_type_column_exists = False

        if source_type_column_exists:
            text_total = NewsHistory.query.filter_by(
                user_id=user_id, source_type="text"
            ).count()
            text_real_count = NewsHistory.query.filter_by(
                user_id=user_id,
                source_type="text",
                prediction="REAL",
            ).count()
            text_fake_count = NewsHistory.query.filter_by(
                user_id=user_id,
                source_type="text",
                prediction="FAKE",
            ).count()
            image_total = NewsHistory.query.filter_by(
                user_id=user_id, source_type="image"
            ).count()
            image_real_count = NewsHistory.query.filter_by(
                user_id=user_id,
                source_type="image",
                prediction="REAL",
            ).count()
            image_fake_count = NewsHistory.query.filter_by(
                user_id=user_id,
                source_type="image",
                prediction="FAKE",
            ).count()
        else:
            text_total = text_real_count = text_fake_count = 0
            image_total = image_real_count = image_fake_count = 0

        return jsonify(
            {
                "total": total,
                "real_count": real_count,
                "fake_count": fake_count,
                "avg_confidence": round(float(avg_confidence), 2),
                "active_users": int(active_users),
                "text_total": text_total,
                "text_real_count": text_real_count,
                "text_fake_count": text_fake_count,
                "image_total": image_total,
                "image_real_count": image_real_count,
                "image_fake_count": image_fake_count,
            }
        ), 200
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Failed to load stats"}), 500
