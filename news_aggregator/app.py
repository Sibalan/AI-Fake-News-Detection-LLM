from flask import Flask, jsonify, request, render_template
from config import Config
from models import db, Bookmark
from news_fetcher import NewsFetcher
from llm_client import GroqClient
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

llm_client = GroqClient(
    api_key=app.config["GROQ_API_KEY"],
    model=app.config["GROQ_MODEL"],
    base_url=app.config["GROQ_API_URL"],
)
fetcher = NewsFetcher(Config, llm_client=llm_client)

CATEGORY_SLUGS = [
    "latest",
    "sports",
    "international-relations",
    "general-knowledge",
    "science-technology",
    "indian-polity",
    "finance-economy",
    "business",
    "entertainment",
]

CATEGORY_LABELS = {
    "latest": "Latest News",
    "sports": "Sports",
    "international-relations": "International Relations",
    "general-knowledge": "General Knowledge",
    "science-technology": "Science & Technology",
    "indian-polity": "Indian Polity",
    "finance-economy": "Finance & Economy",
    "business": "Business",
    "entertainment": "Entertainment",
}

@app.route("/")
def home():
    return render_template("index.html", categories=CATEGORY_LABELS)

@app.route("/news/latest", methods=["GET"])
def latest_news():
    articles = fetcher.fetch_latest(trusted_only=True)
    return jsonify({"articles": articles, "category": CATEGORY_LABELS.get("latest")})

@app.route("/news/trusted", methods=["GET"])
def trusted_news():
    articles = fetcher.fetch_trusted()
    return jsonify({"articles": articles, "category": "Trusted Sources"})

@app.route("/news/category/<category_slug>", methods=["GET"])
def news_by_category(category_slug):
    if category_slug not in CATEGORY_SLUGS:
        return jsonify({"error": "Unknown category"}), 404
    if category_slug == "latest":
        articles = fetcher.fetch_latest(trusted_only=True)
    else:
        articles = fetcher.fetch_by_category(category_slug)
    return jsonify({"articles": articles, "category": CATEGORY_LABELS.get(category_slug, "Latest News")})

@app.route("/news/search", methods=["GET"])
def news_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"articles": []})
    articles = fetcher.search(query)
    return jsonify({"articles": articles, "query": query})

@app.route("/bookmarks", methods=["GET"])
def list_bookmarks():
    bookmarks = Bookmark.query.order_by(Bookmark.created_at.desc()).all()
    return jsonify({"bookmarks": [bookmark.to_dict() for bookmark in bookmarks]})

@app.route("/bookmarks", methods=["POST"])
def save_bookmark():
    payload = request.get_json() or {}
    url = payload.get("url")
    if not url:
        return jsonify({"error": "Bookmark URL is required"}), 400

    bookmark = Bookmark.query.filter_by(url=url).first()
    if bookmark:
        return jsonify({"message": "Already bookmarked", "bookmark": bookmark.to_dict()})

    bookmark = Bookmark(
        title=payload.get("title", "Untitled"),
        url=url,
        image_url=payload.get("image_url"),
        source=payload.get("source"),
        category=payload.get("category"),
        summary=payload.get("summary"),
        credibility_score=payload.get("credibility_score"),
        suspicious_reason=payload.get("suspicious_reason", ""),
    )
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({"message": "Bookmark saved", "bookmark": bookmark.to_dict()})

@app.route("/bookmarks/<int:bookmark_id>", methods=["DELETE"])
def delete_bookmark(bookmark_id):
    bookmark = Bookmark.query.get(bookmark_id)
    if not bookmark:
        return jsonify({"error": "Bookmark not found"}), 404
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"message": "Bookmark removed"})

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
