import api from './index'

export const statsApi = {
  async getStats() {
    const response = await api.get('/stats')
    return response.data
  }
}
