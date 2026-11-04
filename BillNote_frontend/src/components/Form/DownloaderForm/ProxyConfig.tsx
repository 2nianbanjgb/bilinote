import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { getProxyConfig, updateProxyConfig } from '@/services/proxy'

// 代理配置：
//   全局代理 —— 作用于 AI 模型接口、转写接口（Groq 等）和下载（兜底）；
//   YouTube 专用代理 —— 只作用于 YouTube 下载/字幕请求。YouTube 对机房 IP 的风控
//   远严于其它平台，建议单独给一条住宅/非机房线路；留空则跟随全局代理，
//   B 站 / 抖音 始终直连，不受这两项影响。
const ProxyConfig = () => {
  const [enabled, setEnabled] = useState(false)
  const [url, setUrl] = useState('')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [effective, setEffective] = useState('')
  const [youtubeEffective, setYoutubeEffective] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const cfg = await getProxyConfig()
        setEnabled(cfg.enabled)
        setUrl(cfg.url)
        setYoutubeUrl(cfg.youtube_url || '')
        setEffective(cfg.effective)
        setYoutubeEffective(cfg.youtube_effective || '')
      } catch {
        /* 拦截器已 toast */
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleSave = async () => {
    if (enabled && !url.trim()) {
      toast.error('请填写代理地址，或关闭代理开关')
      return
    }
    setSaving(true)
    try {
      const cfg = await updateProxyConfig({
        enabled,
        url: url.trim(),
        youtube_url: youtubeUrl.trim(),
      })
      setEnabled(cfg.enabled)
      setUrl(cfg.url)
      setYoutubeUrl(cfg.youtube_url || '')
      setEffective(cfg.effective)
      setYoutubeEffective(cfg.youtube_effective || '')
      toast.success('代理配置已保存')
    } catch {
      /* 拦截器已 toast */
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="text-xs text-gray-400">加载代理配置…</div>
  }

  // env 兜底：配置没开但 effective 有值，说明来自 HTTP_PROXY 环境变量
  const fromEnv = !enabled && !!effective

  return (
    <div className="flex flex-col gap-3 rounded border border-neutral-200 p-3">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">全局代理</span>
          <Switch checked={enabled} onCheckedChange={setEnabled} />
        </div>
        <p className="text-xs text-gray-400">
          作用于 AI 模型接口、转写接口（Groq 等）、下载兜底。
        </p>
        <Input
          placeholder="http://127.0.0.1:7890"
          value={url}
          disabled={!enabled}
          onChange={e => setUrl(e.target.value)}
          className="text-sm"
        />
        {fromEnv && (
          <p className="text-xs text-amber-600">
            当前生效（来自环境变量）：{effective}
          </p>
        )}
        {enabled && effective && (
          <p className="text-xs text-green-600">当前生效：{effective}</p>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t border-neutral-200 pt-3">
        <span className="text-sm font-medium">YouTube 专用代理（可选）</span>
        <p className="text-xs text-gray-400">
          仅 YouTube 下载 / 字幕请求使用，B 站、抖音直连。YouTube 对机房 IP
          风控很严，建议单独填住宅或非机房线路。
        </p>
        <Input
          placeholder="留空则跟随全局代理，如 http://127.0.0.1:7891"
          value={youtubeUrl}
          onChange={e => setYoutubeUrl(e.target.value)}
          className="text-sm"
        />
        {youtubeEffective && (
          <p className="text-xs text-green-600">
            YouTube 当前生效：{youtubeEffective}
            {!youtubeUrl.trim() ? '（跟随全局代理）' : ''}
          </p>
        )}
        {!youtubeEffective && (
          <p className="text-xs text-gray-400">
            未配置代理：YouTube 请求直接使用当前出口 IP。
          </p>
        )}
      </div>

      <Button size="sm" onClick={handleSave} disabled={saving}>
        {saving ? '保存中…' : '保存代理配置'}
      </Button>
    </div>
  )
}

export default ProxyConfig
