import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex items-center justify-center h-full p-8">
          <div className="text-center max-w-md space-y-4">
            <div className="text-4xl">⚠</div>
            <h2 className="text-sm font-semibold text-zinc-200">渲染出错</h2>
            <pre className="text-xs text-zinc-400 bg-zinc-900 rounded-lg p-4 overflow-auto max-h-40 text-left whitespace-pre-wrap">
              {this.state.error?.message}
            </pre>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              重试
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
