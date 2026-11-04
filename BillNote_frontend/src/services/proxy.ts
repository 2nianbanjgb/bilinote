import request from '@/utils/request'

export interface ProxyConfig {
  enabled: boolean
  url: string
  /** YouTube 专用代理：留空则跟随全局代理，B 站 / 抖音始终直连 */
  youtube_url: string
  /** 后端实际生效的全局代理（可能来自配置，也可能来自 HTTP_PROXY 环境变量兜底） */
  effective: string
  /** YouTube 实际生效的代理（youtube_url 为空时等于 effective） */
  youtube_effective: string
}

export const getProxyConfig = async (): Promise<ProxyConfig> => {
  return await request.get('/proxy_config')
}

export const updateProxyConfig = async (data: {
  enabled: boolean
  url?: string
  youtube_url?: string
}): Promise<ProxyConfig> => {
  return await request.post('/proxy_config', data)
}
