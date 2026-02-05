import api from './index'

export const adminApi = {
  // Учреждения
  async getSpoList() {
    const response = await api.get('/admin/spo')
    return response.data
  },

  async getSpo(id) {
    const response = await api.get(`/admin/spo/${id}`)
    return response.data
  },

  async createSpo(data) {
    const response = await api.post('/admin/spo', data)
    return response.data
  },

  async updateSpo(id, data) {
    const response = await api.put(`/admin/spo/${id}`, data)
    return response.data
  },

  async deleteSpo(id) {
    const response = await api.delete(`/admin/spo/${id}`)
    return response.data
  },

  // Операторы
  async getOperators() {
    const response = await api.get('/admin/operators')
    return response.data
  },

  async createOperator(data) {
    const response = await api.post('/admin/operators', data)
    return response.data
  },

  async deleteOperator(id) {
    const response = await api.delete(`/admin/operators/${id}`)
    return response.data
  },

  async resetOperatorPassword(id) {
    const response = await api.post(`/admin/operators/${id}/reset-password`)
    return response.data
  },

  // Справочник специальностей/профессий
  async getSpecialtyTemplates() {
    const response = await api.get('/admin/specialty-templates')
    return response.data
  },

  async createSpecialtyTemplate(data) {
    const response = await api.post('/admin/specialty-templates', data)
    return response.data
  },

  async updateSpecialtyTemplate(id, data) {
    const response = await api.put(`/admin/specialty-templates/${id}`, data)
    return response.data
  },

  async deleteSpecialtyTemplate(id) {
    const response = await api.delete(`/admin/specialty-templates/${id}`)
    return response.data
  },

  // Специальности/профессии (привязка к учреждениям)
  async getSpecialties(spoId = null) {
    const params = spoId ? { spo_id: spoId } : {}
    const response = await api.get('/admin/specialties', { params })
    return response.data
  },

  async assignSpecialtyToSpo(data) {
    const response = await api.post('/admin/specialties', data)
    return response.data
  },

  async deleteSpecialty(id) {
    const response = await api.delete(`/admin/specialties/${id}`)
    return response.data
  },

  async updateSpecialtyQuota(specialtyId, quota) {
    const response = await api.put(`/admin/specialties/${specialtyId}/quota`, { quota })
    return response.data
  },

  // Настройки квот
  async getSettings() {
    const response = await api.get('/admin/settings')
    return response.data
  },

  async updateSettings(data) {
    const response = await api.put('/admin/settings', data)
    return response.data
  }
}
