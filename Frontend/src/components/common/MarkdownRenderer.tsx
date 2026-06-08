import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function MarkdownRenderer({ content }: { content: string }) {
  if (!content) return null
  return (
    <div className="prose prose-invert prose-sm max-w-none
      prose-headings:text-zinc-100 prose-headings:font-semibold
      prose-p:text-zinc-300 prose-p:leading-relaxed
      prose-li:text-zinc-300
      prose-strong:text-zinc-100
      prose-code:text-zinc-200 prose-code:bg-zinc-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-[''] prose-code:after:content-['']
      prose-pre:bg-zinc-800 prose-pre:border prose-pre:border-zinc-700 prose-pre:rounded-lg
      prose-blockquote:border-zinc-600 prose-blockquote:text-zinc-400
      prose-hr:border-zinc-700
      prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
      prose-table:text-xs prose-table:w-full
      prose-th:text-zinc-300 prose-th:border-zinc-700 prose-th:bg-zinc-800/50 prose-th:px-3 prose-th:py-2
      prose-td:text-zinc-400 prose-td:border-zinc-700 prose-td:px-3 prose-td:py-2
      prose-tr:border-zinc-700 hover:prose-tr:bg-zinc-800/30">
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  )
}
