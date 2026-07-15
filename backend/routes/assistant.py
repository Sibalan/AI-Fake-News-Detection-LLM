import logging
import re
from flask import Blueprint, jsonify, request, session as flask_session
from backend.ollama_client import analyze_with_phi3

logger = logging.getLogger(__name__)
assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


def _get_context():
    ctx = flask_session.get("assistant_context") or {}
    return ctx if isinstance(ctx, dict) else {}


def _get_history():
    history = flask_session.get("assistant_history") or []
    return history if isinstance(history, list) else []


def _save_history(history):
    flask_session["assistant_history"] = history


def _confidence_pct(value):
    if value is None:
        return 0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if numeric <= 1:
        numeric *= 100
    return round(max(0, min(99, numeric)))


def _build_reply(message, context, history):
    article_text = (context.get("article_text") or "").strip()
    user_text = (message or "").strip()
    lower_user_text = user_text.lower()
    follow_up_terms = ["why", "explain", "summarize", "this", "that", "it", "article", "claim", "context", "trust", "reliable", "verify", "check"]
    is_follow_up = bool(article_text) and len(user_text.split()) <= 12 and any(term in lower_user_text for term in follow_up_terms)
    analysis_text = article_text if is_follow_up else (user_text or article_text)

    if not user_text and not article_text:
        reply = (
            "I’m your verification assistant. Paste a headline, claim, or article snippet and I’ll analyze it in a chat-style response."
        )
        return reply, "NEEDS VERIFICATION", 0

    if len(user_text.split()) <= 3 and user_text.lower() in {"yes", "no", "ok", "okay", "sure", "thanks", "thank you"} and not article_text:
        reply = (
            "I’m ready to verify headlines and claims, but I need a specific statement or headline to analyze. Paste it here and I’ll respond like a news verification assistant."
        )
        return reply, "NEEDS VERIFICATION", 0

    if any(term in lower_user_text for term in ["generate", "write", "create", "compose", "make news", "news story", "tell me news"]):
        reply = (
            "I’m designed to verify headlines, claims, and news statements in a conversational way. "
            "Paste a claim or headline, and I’ll assess whether it appears real and what evidence supports that conclusion."
        )
        return reply, "NEEDS VERIFICATION", 0

    try:
        result = analyze_with_phi3(analysis_text, display_policy="conservative", source_type="text")
        verdict = (result.get("display_prediction") or result.get("prediction") or "NEEDS VERIFICATION").upper()
        confidence_score = _confidence_pct(result.get("confidence", 0))
        explanation = (result.get("explanation") or "The claim was analyzed using the evidence pipeline.").strip()

        evidence = []
        for fact in (result.get("fact_checks") or [])[:4]:
            rating = fact.get("rating") or "Evidence"
            source = fact.get("source") or "Source"
            evidence.append(f"- **{source}**: {rating}")
        if not evidence:
            evidence = ["- I used available news and trusted-source signals to assess the claim."]

        suspicious = []
        lower_text = analysis_text.lower()
        if any(term in lower_text for term in ["breaking", "shocking", "you won’t believe", "you won't believe", "100%", "guaranteed"]):
            suspicious.append("Sensational or absolute wording")
        if any(term in lower_text for term in ["urgent", "share now", "must see", "everyone knows", "secret"]):
            suspicious.append("Urgency or clickbait phrasing")
        if not suspicious:
            suspicious = ["No major warning signs were detected in the current analysis."]

    except Exception as exc:
        logger.warning(f"Assistant analysis failed: {exc}")
        verdict = "NEEDS VERIFICATION"
        confidence_score = 0
        explanation = "I could not complete the verification. Please try again with a clear headline or claim."
        evidence = ["- The assistant could not gather enough evidence from the current input."]
        suspicious = ["The assistant was unable to inspect the text reliably."]

    source_line = (
        "I used the current article context and your latest request." if is_follow_up and article_text else "I analyzed the headline or claim you provided directly."
    )
    claim_line = f"\n\n**Claim reviewed:** \"{user_text}\"" if user_text and len(user_text) > 20 else ""

    reply_parts = [
        f"{source_line}",
        f"**Verdict:** {verdict}",
        f"**Confidence:** {confidence_score}%",
        "",
        f"**What this means:** {('The statement looks supported by evidence.' if verdict == 'REAL' else 'The statement appears misleading or unverified.')}",
        "",
        f"**Key reasoning:** {explanation}",
        "",
        "**Evidence:**",
        *evidence,
        "",
        "**What to watch for:**",
        *[f"- {item}" for item in suspicious],
    ]

    if claim_line:
        reply_parts.insert(1, claim_line)

    reply_parts.append("")
    reply_parts.append("If you want, I can explain this in simpler language, summarize it, compare sources, or check another headline.")
    reply = "\n".join(reply_parts).strip()
    return reply, verdict, confidence_score


@assistant_bp.route("/chat", methods=["POST"])
def chat_with_assistant():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    context = _get_context()
    history = _get_history()

    history.append({"role": "user", "content": message})
    reply, verdict, confidence = _build_reply(message, context, history)
    history.append({"role": "assistant", "content": reply})
    _save_history(history)

    return jsonify(
        {
            "reply": reply,
            "verdict": verdict,
            "confidence": confidence,
            "history": history,
            "used_context": bool(context.get("article_text")),
        }
    ), 200


@assistant_bp.route("/history", methods=["GET"])
def get_assistant_history():
    history = _get_history()
    return jsonify({"history": history}), 200


@assistant_bp.route("/reset", methods=["POST"])
def reset_assistant():
    flask_session.pop("assistant_history", None)
    return jsonify({"message": "Conversation cleared."}), 200
