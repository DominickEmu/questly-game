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

  // Shop
  getShopItems: () => request('/shop'),
  buyItem: (id, currency = 'coins') => request(`/shop/buy/${id}?currency=${currency}`, { method: 'POST' }),
  getPurchases: () => request('/shop/purchases'),
};
