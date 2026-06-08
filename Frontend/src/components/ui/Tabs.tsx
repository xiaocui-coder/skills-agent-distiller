import type { ReactNode } from 'react'

interface Tab {
  key: string
  label: string
}

interface TabsProps {
  tabs: Tab[]
  active: string
  onChange: (key: string) => void
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 border-b border-zinc-800 px-1">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-4 py-2.5 text-sm transition-colors relative ${
            active === tab.key
              ? 'text-zinc-100'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {tab.label}
          {active === tab.key && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />
          )}
        </button>
      ))}
    </div>
  )
}

export function TabPanel({ children, active, tab }: { children: ReactNode; active: string; tab: string }) {
  return <div className={`p-4 ${active !== tab ? 'hidden' : ''}`}>{children}</div>
}
