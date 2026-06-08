import { useState } from 'react'
import { useDistillStream } from '../../../hooks/useDistillStream'
import { useSamples, useSample } from '../../../hooks/useDistiller'
import { Button } from '../../ui/Button'
import { Card } from '../../ui/Card'
import { LoadingSpinner } from '../../ui/LoadingSpinner'
import { DistillSamplePicker } from './DistillSamplePicker'
import { DistillResult } from './DistillResult'

export function DistillView() {
  const [input, setInput] = useState('')
  const { streaming, rawText, result, error, start, reset } = useDistillStream()
  const { data: samples, isLoading: samplesLoading } = useSamples()
  const [selectedSample, setSelectedSample] = useState<string | null>(null)
  const { data: sampleDetail } = useSample(selectedSample || '')

  const handleSelectSample = (key: string) => {
    setSelectedSample(key)
  }

  const handleLoadSample = () => {
    if (sampleDetail?.conversation) {
      setInput(sampleDetail.conversation)
      setSelectedSample(null)
    }
  }

  const handleDistill = () => {
    if (!input.trim()) return
    start(input)
  }

  return (
    <div className="space-y-4">
      {/* 示例场景 */}
      {samples && samples.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-zinc-300 mb-2">示例场景</h3>
          <DistillSamplePicker samples={samples} selected={selectedSample} onSelect={handleSelectSample} />
          {selectedSample && sampleDetail && (
            <div className="mt-2 flex items-center gap-2">
              <p className="text-xs text-zinc-500 flex-1">{sampleDetail.quote}</p>
              <Button size="sm" variant="secondary" onClick={handleLoadSample}>加载</Button>
            </div>
          )}
        </div>
      )}

      {/* 输入区域 */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">对话内容</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="粘贴用户与 AI 的对话内容..."
          rows={8}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 font-mono focus:outline-none focus:border-zinc-500 resize-y"
        />
        <div className="flex gap-2 mt-3">
          <Button onClick={handleDistill} disabled={!input.trim() || streaming}>
            {streaming ? '蒸馏中...' : '开始蒸馏'}
          </Button>
          {(rawText || result) && <Button variant="ghost" onClick={reset}>重置</Button>}
        </div>
      </div>

      {/* 错误 */}
      {error && (
        <Card className="border-rose-500/30 bg-rose-500/10">
          <p className="text-sm text-rose-400">{error}</p>
        </Card>
      )}

      {/* 流式原始输出 */}
      {streaming && rawText && (
        <Card>
          <h3 className="text-xs font-medium text-zinc-500 mb-2">生成中...</h3>
          <pre className="text-xs text-zinc-400 whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">{rawText}</pre>
        </Card>
      )}

      {/* 5幕结果 */}
      {result && <DistillResult result={result} />}

      {samplesLoading && <LoadingSpinner />}
    </div>
  )
}
