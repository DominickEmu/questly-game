const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (options.method === 'DELETE' && res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Tasks
  getTasks: (params) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.due_date) qs.set('due_date', params.due_date);
    const q = qs.toString();
    return request(`/tasks${q ? `?${q}` : ''}`);
  },
  createTask: (data) => request('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (id, data) => request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),
  completeTask: (id) => request(`/tasks/${id}/complete`, { method: 'POST' }),

  // Profile
  getProfile: () => request('/profile'),
  updateProfile: (data) => request('/profile', { method: 'PUT', body: JSON.stringify(data) }),
  devAddCurrency: () => request('/profile/dev', { method: 'POST' }),

  // Shop
  getShopItems: () => request('/shop'),
  buyItem: (id, currency = 'coins') => request(`/shop/buy/${id}?currency=${currency}`, { method: 'POST' }),
  equipItem: (id) => request(`/shop/equip/${id}`, { method: 'POST' }),
  unequipSlot: (slot) => request('/profile', { method: 'PUT', body: JSON.stringify({ [`equipped_${slot}`]: null }) }),
  getPurchases: () => request('/shop/purchases'),

  // Google Calendar
  gcalStatus: () => request('/gcal/status'),
  gcalAuthUrl: () => request('/gcal/auth-url'),
  gcalSync: () => request('/gcal/sync', { method: 'POST' }),
  gcalDisconnect: () => request('/gcal/disconnect', { method: 'DELETE' }),
  gcalGetKeywords: () => request('/gcal/keywords'),
  gcalUpdateKeywords: (data) => request('/gcal/keywords', { method: 'PUT', body: JSON.stringify(data) }),

  // Gmail
  gmailStatus: () => request('/gmail/status'),
  gmailSync: () => request('/gmail/sync', { method: 'POST' }),

  // Story
  getStory: () => request('/story'),
  resetStory: () => request('/story/reset', { method: 'POST' }),
  getArchives: () => request('/story/archives'),
  archiveStory: (title) => request('/story/archive', { method: 'POST', body: JSON.stringify({ title }) }),
  renameArchive: (id, title) => request(`/story/archives/${id}`, { method: 'PUT', body: JSON.stringify({ title }) }),
  deleteArchive: (id) => request(`/story/archives/${id}`, { method: 'DELETE' }),
  rateSegment: (id, rating, feedback) =>
    request(`/story/segments/${id}/rate`, { method: 'PUT', body: JSON.stringify({ rating, feedback: feedback || null }) }),
  narrateArchive: async (id) => {
    const res = await fetch(`${BASE}/story/archives/${id}/narrate`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Narration failed');
    }
    return res.blob();
  },
};
