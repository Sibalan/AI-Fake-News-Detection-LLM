const categoryList = document.getElementById("category-list");
const newsGrid = document.getElementById("news-grid");
const feedTitle = document.getElementById("feed-title");
const messages = document.getElementById("messages");
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");
const bookmarkList = document.getElementById("bookmark-list");
const themeToggle = document.getElementById("theme-toggle");

let selectedCategory = "latest";
let currentArticles = [];
let autoRefreshTimer = null;

function init() {
  buildCategoryChips();
  loadArticles();
  loadBookmarks();
  attachEvents();
  startAutoRefresh();
  applySavedTheme();
}

function attachEvents() {
  searchButton.addEventListener("click", () => {
    selectedCategory = "";
    loadArticles(searchInput.value.trim());
  });

  searchInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      selectedCategory = "";
      loadArticles(searchInput.value.trim());
    }
  });

  themeToggle.addEventListener("click", toggleTheme);
}

function buildCategoryChips() {
  const categories = window.NEWS_CATEGORIES || {};
  categoryList.innerHTML = "";
  Object.entries(categories).forEach(([slug, label]) => {
    const chip = document.createElement("button");
    chip.className = "category-chip";
    chip.textContent = label;
    chip.dataset.slug = slug;
    chip.addEventListener("click", () => {
      searchInput.value = "";
      selectedCategory = slug;
      loadArticles();
      setActiveChip(slug);
    });
    categoryList.appendChild(chip);
  });
  setActiveChip(selectedCategory);
}

function setActiveChip(slug) {
  document.querySelectorAll(".category-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.slug === slug);
  });
}

function startAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
  }
  autoRefreshTimer = setInterval(() => loadArticles(), 10 * 60 * 1000);
}

function applySavedTheme() {
  const stored = localStorage.getItem("news-aggregator-theme");
  if (stored === "dark") {
    document.body.classList.add("dark-mode");
    themeToggle.textContent = "Light mode";
  }
}

function toggleTheme() {
  document.body.classList.toggle("dark-mode");
  const isDark = document.body.classList.contains("dark-mode");
  themeToggle.textContent = isDark ? "Light mode" : "Dark mode";
  localStorage.setItem("news-aggregator-theme", isDark ? "dark" : "light");
}

function loadArticles(searchQuery = "") {
  messages.textContent = "Loading news...";
  newsGrid.innerHTML = "";

  const endpoint = searchQuery
    ? `/news/search?q=${encodeURIComponent(searchQuery)}`
    : `/news/category/${selectedCategory}`;

  fetch(endpoint)
    .then((response) => response.json())
    .then((data) => {
      currentArticles = data.articles || [];
      feedTitle.textContent = searchQuery
        ? `Search results for \"${searchQuery}\"`
        : data.category || "Latest News";
      renderArticles(currentArticles);
    })
    .catch((error) => {
      messages.textContent = "Unable to load news right now.";
      console.error(error);
    });
}

function renderArticles(articles) {
  if (!articles.length) {
    messages.textContent = "No news available. Try another topic or refresh later.";
    return;
  }

  messages.textContent = "";
  newsGrid.innerHTML = "";

  articles.forEach((article, index) => {
    const card = document.createElement("article");
    card.className = "news-card";

    const image = article.image_url
      ? `<img src="${article.image_url}" alt="${escapeHtml(article.title)}" />`
      : "";

    const suspicious = article.suspicious_reason && article.credibility_score < 60;
    const credibilityLabel = article.credibility_score
      ? `${article.credibility_score.toFixed(0)}% credible`
      : "Credibility unknown";

    card.innerHTML = `
      ${image}
      <div class="news-meta">
        <span class="tag">${escapeHtml(article.category || "General Knowledge")}</span>
        <span class="tag">${escapeHtml(article.source || "Unknown")}</span>
        <span class="tag">${credibilityLabel}</span>
      </div>
      <h4>${escapeHtml(article.title)}</h4>
      <p>${escapeHtml(article.description || article.content)}</p>
      <div class="news-actions">
        <a class="btn btn-ghost" href="${article.url}" target="_blank" rel="noopener noreferrer">Read full story</a>
        <button class="btn btn-primary" data-index="${index}">Bookmark</button>
      </div>
      ${suspicious ? `<div class="badge badge-warning">Suspicious: ${escapeHtml(article.suspicious_reason)}</div>` : ""}
    `;

    const bookmarkButton = card.querySelector("button[data-index]");
    bookmarkButton.addEventListener("click", () => saveBookmark(article));
    newsGrid.appendChild(card);
  });
}

function saveBookmark(article) {
  fetch("/bookmarks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(article),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
      } else {
        loadBookmarks();
      }
    })
    .catch((error) => {
      console.error(error);
    });
}

function loadBookmarks() {
  fetch("/bookmarks")
    .then((response) => response.json())
    .then((data) => {
      const items = data.bookmarks || [];
      bookmarkList.innerHTML = items.length
        ? items
            .map(
              (bookmark) => `
          <div class="bookmark-card">
            <a href="${bookmark.url}" target="_blank" rel="noopener noreferrer"><strong>${escapeHtml(bookmark.title)}</strong></a>
            <p>${escapeHtml(bookmark.source || "Unknown source")}</p>
            <button class="btn btn-ghost" data-id="${bookmark.id}">Remove</button>
          </div>
        `
            )
            .join("")
        : "<p>No bookmarks yet. Save a story from the feed.</p>";

      bookmarkList.querySelectorAll("button[data-id]").forEach((button) => {
        button.addEventListener("click", () => deleteBookmark(button.dataset.id));
      });
    })
    .catch((error) => {
      console.error(error);
    });
}

function deleteBookmark(bookmarkId) {
  fetch(`/bookmarks/${bookmarkId}`, { method: "DELETE" })
    .then((response) => response.json())
    .then(() => loadBookmarks())
    .catch((error) => console.error(error));
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

init();
