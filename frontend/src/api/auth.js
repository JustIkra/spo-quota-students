import api from './index'

export const authApi = {
  async login(login, password) {
    const response = await api.post('/auth/login', { login, password })
    return response.data
  },

  async me() {
    const response = await api.get('/auth/me')
    return response.data
  }
}
