// API helper with auth
function apiFetch(url, options) {
  options = options || {};
  options.headers = options.headers || {};
  options.headers['Content-Type'] = 'application/json';
  options.headers['Authorization'] = 'Bearer ' + AUTH_TOKEN;
  options.credentials = 'same-origin';
  return fetch(url, options);
}

function apiGet(url) {
  return apiFetch(url, { method: 'GET' });
}

function apiPost(url, data) {
  return apiFetch(url, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

function apiDelete(url) {
  return apiFetch(url, { method: 'DELETE' });
}
