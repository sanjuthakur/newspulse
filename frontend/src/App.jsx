import { useEffect, useState } from "react";
import {
  deleteBookmark,
  fetchBookmarks,
  fetchCategories,
  fetchFeed,
  fetchUser,
  refreshNews,
  saveBookmark,
  searchArticles,
  updatePreferences,
} from "./api";

const DEMO_USER_ID = 1;

function formatDate(value) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatRefreshTimestamp(value) {
  if (!value) {
    return "Not refreshed yet";
  }
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getArticleLink(article) {
  if (article.url.includes("example.com")) {
    return article.source.homepage_url;
  }
  return article.url;
}

function CategoryPicker({ categories, selectedIds, onToggle, onSave, busy }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Personalization</p>
          <h2>Follow your topics</h2>
        </div>
        <button className="secondary-button" onClick={onSave} disabled={busy}>
          {busy ? "Saving..." : "Save interests"}
        </button>
      </div>
      <div className="chip-row">
        {categories.map((category) => {
          const active = selectedIds.includes(category.id);
          return (
            <button
              key={category.id}
              className={`chip ${active ? "chip-active" : ""}`}
              onClick={() => onToggle(category.id)}
            >
              {category.name}
            </button>
          );
        })}
      </div>
    </section>
  );
}

function ArticleCard({ article, onBookmarkToggle }) {
  const articleLink = getArticleLink(article);

  return (
    <article className="article-card">
      <div className="article-meta">
        <span>{article.category.name}</span>
        <span>{article.source.name}</span>
        <span>{formatDate(article.published_at)}</span>
      </div>
      <div className="article-body">
        <div>
          <h3>{article.title}</h3>
          <p className="summary">{article.summary}</p>
          <p className="snippet">{article.content_snippet}</p>
        </div>
        <div className="article-actions">
          <button
            className={`bookmark-button ${article.is_bookmarked ? "active" : ""}`}
            onClick={() => onBookmarkToggle(article)}
          >
            {article.is_bookmarked ? "Bookmarked" : "Bookmark"}
          </button>
          <a href={articleLink} target="_blank" rel="noreferrer">
            Visit publisher
          </a>
        </div>
      </div>
    </article>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [activeFilter, setActiveFilter] = useState("");
  const [feed, setFeed] = useState([]);
  const [bookmarks, setBookmarks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [refreshingNews, setRefreshingNews] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [lastRefreshedAt, setLastRefreshedAt] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [userData, categoryData, feedData, bookmarkData] = await Promise.all([
          fetchUser(DEMO_USER_ID),
          fetchCategories(),
          fetchFeed(DEMO_USER_ID),
          fetchBookmarks(DEMO_USER_ID),
        ]);
        setUser(userData);
        setCategories(categoryData);
        setSelectedCategoryIds(userData.preferences.map((item) => item.id));
        setFeed(feedData.items);
        setBookmarks(bookmarkData);
        setLastRefreshedAt(new Date().toISOString());
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();
  }, []);

  useEffect(() => {
    async function refreshFeed() {
      try {
        const feedData = await fetchFeed(DEMO_USER_ID, activeFilter);
        setFeed(feedData.items);
        setLastRefreshedAt(new Date().toISOString());
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    refreshFeed();
  }, [activeFilter]);

  async function handleSavePreferences() {
    try {
      setError("");
      setStatusMessage("");
      setSavingPreferences(true);
      const userData = await updatePreferences(DEMO_USER_ID, selectedCategoryIds);
      setUser(userData);
      const feedData = await fetchFeed(DEMO_USER_ID, activeFilter);
      setFeed(feedData.items);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSavingPreferences(false);
    }
  }

  function toggleCategory(categoryId) {
    setSelectedCategoryIds((current) =>
      current.includes(categoryId)
        ? current.filter((id) => id !== categoryId)
        : [...current, categoryId]
    );
  }

  async function handleSearch(event) {
    event.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      setError("");
      const results = await searchArticles(DEMO_USER_ID, searchQuery.trim());
      setSearchResults(results);
    } catch (searchError) {
      setError(searchError.message);
    }
  }

  async function handleBookmarkToggle(article) {
    try {
      setError("");
      setStatusMessage("");
      if (article.is_bookmarked) {
        await deleteBookmark(DEMO_USER_ID, article.id);
      } else {
        await saveBookmark(DEMO_USER_ID, article.id);
      }
      const [feedData, bookmarkData] = await Promise.all([
        fetchFeed(DEMO_USER_ID, activeFilter),
        fetchBookmarks(DEMO_USER_ID),
      ]);
      setFeed(feedData.items);
      setBookmarks(bookmarkData);
      if (searchResults.length) {
        const results = await searchArticles(DEMO_USER_ID, searchQuery.trim());
        setSearchResults(results);
      }
    } catch (bookmarkError) {
      setError(bookmarkError.message);
    }
  }

  async function handleManualRefresh() {
    try {
      setRefreshingNews(true);
      setError("");
      const refreshResult = await refreshNews();
      const [feedData, bookmarkData] = await Promise.all([
        fetchFeed(DEMO_USER_ID, activeFilter),
        fetchBookmarks(DEMO_USER_ID),
      ]);
      setFeed(feedData.items);
      setBookmarks(bookmarkData);
      setStatusMessage(refreshResult.message);
      setLastRefreshedAt(new Date().toISOString());
    } catch (refreshError) {
      setError(refreshError.message);
    } finally {
      setRefreshingNews(false);
    }
  }

  if (loading) {
    return <div className="state-screen">Loading NewsPulse...</div>;
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <h1>The stories that matter.</h1>
          <p className="hero-copy">
            Personalized headlines, compact summaries, category filters, and saved reading.
          </p>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}
      {statusMessage ? <div className="success-banner">{statusMessage}</div> : null}

      <main className="layout">
        <section className="main-column">
          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Search</p>
                <h2>Find stories fast</h2>
              </div>
            </div>
            <form className="search-form" onSubmit={handleSearch}>
              <input
                type="text"
                value={searchQuery}
                placeholder="Search OpenAI, finance, Reuters..."
                onChange={(event) => setSearchQuery(event.target.value)}
              />
              <button type="submit">Search</button>
            </form>
            {searchResults.length > 0 ? (
              <div className="compact-list search-results">
                {searchResults.map((article) => (
                  <ArticleCard
                    key={`search-${article.id}`}
                    article={article}
                    onBookmarkToggle={handleBookmarkToggle}
                  />
                ))}
              </div>
            ) : null}
          </section>

          <CategoryPicker
            categories={categories}
            selectedIds={selectedCategoryIds}
            onToggle={toggleCategory}
            onSave={handleSavePreferences}
            busy={savingPreferences}
          />

          <section className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Feed</p>
                <h2>Top stories</h2>
                <p className="refresh-note">Last refreshed: {formatRefreshTimestamp(lastRefreshedAt)}</p>
              </div>
              <div className="feed-actions">
                <button
                  className="secondary-button"
                  onClick={handleManualRefresh}
                  disabled={refreshingNews}
                >
                  {refreshingNews ? "Refreshing..." : "Refresh news"}
                </button>
                <div className="chip-row">
                <button
                  className={`chip ${activeFilter === "" ? "chip-active" : ""}`}
                  onClick={() => setActiveFilter("")}
                >
                  All
                </button>
                {categories.map((category) => (
                  <button
                    key={category.id}
                    className={`chip ${activeFilter === category.name ? "chip-active" : ""}`}
                    onClick={() => setActiveFilter(category.name)}
                  >
                    {category.name}
                  </button>
                ))}
                </div>
              </div>
            </div>
            <div className="article-list">
              {feed.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onBookmarkToggle={handleBookmarkToggle}
                />
              ))}
            </div>
          </section>
        </section>

        <aside className="sidebar">
          <section className="panel">
            <p className="eyebrow">Bookmarks</p>
            <h2>Reading list</h2>
            <div className="compact-list">
              {bookmarks.length === 0 ? (
                <p className="empty-state">No saved articles yet.</p>
              ) : (
                bookmarks.map((article) => (
                  <ArticleCard
                    key={`bookmark-${article.id}`}
                    article={article}
                    onBookmarkToggle={handleBookmarkToggle}
                  />
                ))
              )}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
