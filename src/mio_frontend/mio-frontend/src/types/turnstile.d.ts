// Cloudflare Turnstile TypeScript 类型定义

interface TurnstileOptions {
  sitekey: string
  theme?: 'light' | 'dark' | 'auto'
  size?: 'normal' | 'compact'
  callback?: (token: string) => void
  'error-callback'?: () => void
  'expired-callback'?: () => void
}

interface Turnstile {
  render(container: string | HTMLElement, options: TurnstileOptions): string
  remove(widgetId: string): void
  reset(widgetId: string): void
  getResponse(widgetId: string): string | null
}

declare global {
  interface Window {
    turnstile?: Turnstile
  }
}

export {}
