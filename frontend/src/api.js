const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed");
  }

  return response.json();
}

export function fetchFeed(userId, category = "") {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  if (category) params.set("category", category);
  return request(`/news?${params.toString()}`);
}

export function fetchCategories() {
  return request("/categories");
}

export function fetchUser(userId) {
  return request(`/users/${userId}`);
}

export function updatePreferences(userId, categoryIds) {
  return request(`/users/${userId}/preferences`, {
    method: "PUT",
    body: JSON.stringify({ category_ids: categoryIds }),
  });
}

export function searchArticles(userId, query) {
  const params = new URLSearchParams({ q: query });
  if (userId) params.set("user_id", userId);
  return request(`/search?${params.toString()}`);
}

export function fetchBookmarks(userId) {
  return request(`/bookmarks?user_id=${userId}`);
}

export function saveBookmark(userId, articleId) {
  return request("/bookmarks", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, article_id: articleId }),
  });
}

export function deleteBookmark(userId, articleId) {
  return request(`/bookmarks/${articleId}?user_id=${userId}`, {
    method: "DELETE",
  });
}

export function refreshNews() {
  return request("/admin/refresh", {
    method: "POST",
  });
}
