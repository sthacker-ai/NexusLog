import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Entries
export const getEntries = (params = {}) => api.get('/entries', { params });
export const getEntriesByDate = (params = {}) => api.get('/entries/by-date', { params });
export const getEntry = (id) => api.get(`/entries/${id}`);
export const createEntry = (data) => api.post('/entries', data);
export const deleteEntry = (id) => api.delete(`/entries/${id}`);

// Categories
export const getCategories = () => api.get('/categories');
export const createCategory = (data) => api.post('/categories', data);
export const updateCategory = (id, data) => api.put(`/categories/${id}`, data);
export const deleteCategory = (id) => api.delete(`/categories/${id}`);
export const getSubcategories = (parentId) => api.get(`/categories/${parentId}/subcategories`);

// Content Ideas
export const getContentIdeas = (params = {}) => api.get('/content-ideas', { params });
export const updateContentIdea = (id, data) => api.put(`/content-ideas/${id}`, data);

// Projects
export const getProjects = () => api.get('/projects');
export const createProject = (data) => api.post('/projects', data);

// Config
export const getConfig = () => api.get('/config');
export const updateConfig = (key, value) => api.put(`/config/${key}`, { value });

// Stats
export const getStats = () => api.get('/stats');
export const getAnalytics = () => api.get('/analytics');

export default api;
