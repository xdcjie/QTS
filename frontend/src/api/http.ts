import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

export class ApiClient {
  private readonly axiosInstance: AxiosInstance

  constructor(baseUrl: string = '/api') {
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.axiosInstance.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message
        console.error('API Error:', message)
        return Promise.reject(error)
      }
    )
  }

  async get<T = JsonValue>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.get<T>(url, config)
    return response.data
  }

  async post<T = JsonValue>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.axiosInstance.post<T>(url, data, config)
    return response.data
  }

  async put<T = JsonValue>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.put<T>(url, data, config)
    return response.data
  }

  async delete<T = JsonValue>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.axiosInstance.delete<T>(url, config)
    return response.data
  }
}

export const apiClient = new ApiClient()
