let csrf;
export async function api(path, body) {
  if (!csrf && body !== undefined) {
    const response = await fetch('/api/session/', {credentials: 'same-origin'});
    if (!response.ok) throw new Error('Could not establish a secure session. Refresh and try again.');
    csrf = (await response.json()).csrf;
  }
  const response = await fetch('/api/' + path, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: body === undefined ? {} : {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}). Please retry.`);
  return data;
}
