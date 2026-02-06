import api from './index'

export const operatorApi = {
  // Специальности/профессии (только чтение)
  async getSpecialties() {
    const response = await api.get('/specialties')
    return response.data
  },

  // Студенты
  async getStudents(specialtyId = null) {
    const params = specialtyId ? { specialty_id: specialtyId } : {}
    const response = await api.get('/students', { params })
    return response.data
  },

  async createStudent(data) {
    const response = await api.post('/students', data)
    return response.data
  },

  async updateStudent(id, data) {
    const response = await api.put(`/students/${id}`, data)
    return response.data
  },

  async deleteStudent(id) {
    const response = await api.delete(`/students/${id}`)
    return response.data
  }
}
