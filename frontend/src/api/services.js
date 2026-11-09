/**
 * Funciones de acceso a la API agrupadas por módulo.
 * Cada función devuelve directamente `response.data`.
 */
import api, { cleanParams } from './client'

const data = (promise) => promise.then((r) => r.data)

export const authApi = {
  login: (email, password) => data(api.post('/auth/login', { email, password })),
  register: (payload) => data(api.post('/auth/register', payload)),
  me: () => data(api.get('/auth/me')),
  updateMe: (payload) => data(api.put('/auth/me', payload)),
  changePassword: (payload) => data(api.post('/auth/change-password', payload)),
}

export const patientsApi = {
  list: (params) => data(api.get('/patients', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/patients/${id}`)),
  create: (payload) => data(api.post('/patients', payload)),
  update: (id, payload) => data(api.put(`/patients/${id}`, payload)),
  setStatus: (id, activo) => data(api.patch(`/patients/${id}/status`, { activo })),
}

export const doctorsApi = {
  list: (params) => data(api.get('/doctors', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/doctors/${id}`)),
  create: (payload) => data(api.post('/doctors', payload)),
  update: (id, payload) => data(api.put(`/doctors/${id}`, payload)),
  setStatus: (id, activo) => data(api.patch(`/doctors/${id}/status`, { activo })),
}

export const specialtiesApi = {
  list: (params) => data(api.get('/specialties', { params: cleanParams(params) })),
  create: (payload) => data(api.post('/specialties', payload)),
  update: (id, payload) => data(api.put(`/specialties/${id}`, payload)),
  setStatus: (id, activo) => data(api.patch(`/specialties/${id}/status`, { activo })),
}

export const servicesApi = {
  list: (params) => data(api.get('/services', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/services/${id}`)),
  doctors: (id) => data(api.get(`/services/${id}/doctors`)),
  create: (payload) => data(api.post('/services', payload)),
  update: (id, payload) => data(api.put(`/services/${id}`, payload)),
  setStatus: (id, activo) => data(api.patch(`/services/${id}/status`, { activo })),
}

export const schedulesApi = {
  list: (params) => data(api.get('/schedules', { params: cleanParams(params) })),
  create: (payload) => data(api.post('/schedules', payload)),
  update: (id, payload) => data(api.put(`/schedules/${id}`, payload)),
  remove: (id) => data(api.delete(`/schedules/${id}`)),
  slots: (params) => data(api.get('/schedules/available-slots', { params })),
}

export const appointmentsApi = {
  list: (params) => data(api.get('/appointments', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/appointments/${id}`)),
  create: (payload) => data(api.post('/appointments', payload)),
  update: (id, payload) => data(api.put(`/appointments/${id}`, payload)),
  setStatus: (id, estado) => data(api.patch(`/appointments/${id}/status`, { estado })),
  cancel: (id, motivo) => data(api.post(`/appointments/${id}/cancel`, { motivo: motivo || null })),
}

export const consultationsApi = {
  list: (params) => data(api.get('/consultations', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/consultations/${id}`)),
  create: (payload) => data(api.post('/consultations', payload)),
}

export const authorizationsApi = {
  list: (params) => data(api.get('/authorizations', { params: cleanParams(params) })),
  get: (id) => data(api.get(`/authorizations/${id}`)),
  history: (id) => data(api.get(`/authorizations/${id}/history`)),
  create: (payload) => data(api.post('/authorizations', payload)),
  setStatus: (id, estado, observaciones) =>
    data(api.patch(`/authorizations/${id}/status`, { estado, observaciones: observaciones || null })),
}

export const notificationsApi = {
  list: (params) => data(api.get('/notifications', { params: cleanParams(params) })),
  markRead: (id) => data(api.patch(`/notifications/${id}/read`)),
  markAllRead: () => data(api.patch('/notifications/read-all')),
}

export const dashboardApi = {
  stats: () => data(api.get('/dashboard/stats')),
}

export const usersApi = {
  list: (params) => data(api.get('/users', { params: cleanParams(params) })),
  setRole: (id, rol) => data(api.patch(`/users/${id}/role`, { rol })),
  setStatus: (id, activo) => data(api.patch(`/users/${id}/status`, { activo })),
}

export const auditApi = {
  list: (params) => data(api.get('/audit', { params: cleanParams(params) })),
}
