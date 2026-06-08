import { postExport } from '../api/rest'

export function useExportDownload() {
  const download = async (skillName: string, target: string) => {
    const result = await postExport({ skill_name: skillName, target })
    const blob = new Blob([result.content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.filename
    a.click()
    URL.revokeObjectURL(url)
    return result
  }
  return { download }
}
