import api from './client';

export const productsApi = {
  getAll: () => api.get('/products').then(res => res.data),
  get: (id) => api.get(`/products/${id}`).then(res => res.data),
  create: (data) => api.post('/products', data).then(res => res.data),
  update: (id, data) => api.put(`/products/${id}`, data).then(res => res.data),
  delete: (id) => api.delete(`/products/${id}`).then(res => res.data),
};

export const customersApi = {
  getAll: () => api.get('/customers').then(res => res.data),
  get: (id) => api.get(`/customers/${id}`).then(res => res.data),
  create: (data) => api.post('/customers', data).then(res => res.data),
  delete: (id) => api.delete(`/customers/${id}`).then(res => res.data),
};

export const ordersApi = {
  getAll: () => api.get('/orders').then(res => res.data),
  get: (id) => api.get(`/orders/${id}`).then(res => res.data),
  create: (data) => api.post('/orders', data).then(res => res.data),
  delete: (id) => api.delete(`/orders/${id}`).then(res => res.data),
};

export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary').then(res => res.data),
};
