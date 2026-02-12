export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase as string

  async function get<T>(path: string): Promise<T> {
    return await $fetch<T>(`${base}${path}`)
  }

  async function post<T>(path: string, body?: any): Promise<T> {
    return await $fetch<T>(`${base}${path}`, { method: 'POST', body })
  }

  async function put<T>(path: string, body?: any): Promise<T> {
    return await $fetch<T>(`${base}${path}`, { method: 'PUT', body })
  }

  async function del<T>(path: string): Promise<T> {
    return await $fetch<T>(`${base}${path}`, { method: 'DELETE' })
  }

  return { get, post, put, del }
}
