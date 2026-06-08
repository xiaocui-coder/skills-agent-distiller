import { useAppStore } from '../stores/appStore'
import { Tabs, TabPanel } from '../components/ui/Tabs'
import { DistillView } from '../components/distiller/distill/DistillView'
import { AutoGenerateView } from '../components/distiller/auto-generate/AutoGenerateView'
import { LintView } from '../components/distiller/lint/LintView'
import { DiffView } from '../components/distiller/diff/DiffView'
import { ExportView } from '../components/distiller/export/ExportView'
import { StoreView } from '../components/distiller/store/StoreView'

const tabs = [
  { key: 'distill', label: '蒸馏' },
  { key: 'auto-generate', label: '自动生成' },
  { key: 'lint', label: '校验' },
  { key: 'diff', label: '对比' },
  { key: 'export', label: '导出' },
  { key: 'store', label: '存储库' },
]

export function DistillerPage() {
  const activeTab = useAppStore((s) => s.activeDistillerTab)
  const setDistillerTab = useAppStore((s) => s.setDistillerTab)

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-full">
      <Tabs tabs={tabs} active={activeTab} onChange={setDistillerTab} />
      <div className="flex-1 overflow-y-auto">
        <TabPanel active={activeTab} tab="distill"><DistillView /></TabPanel>
        <TabPanel active={activeTab} tab="auto-generate"><AutoGenerateView /></TabPanel>
        <TabPanel active={activeTab} tab="lint"><LintView /></TabPanel>
        <TabPanel active={activeTab} tab="diff"><DiffView /></TabPanel>
        <TabPanel active={activeTab} tab="export"><ExportView /></TabPanel>
        <TabPanel active={activeTab} tab="store"><StoreView /></TabPanel>
      </div>
    </div>
  )
}
