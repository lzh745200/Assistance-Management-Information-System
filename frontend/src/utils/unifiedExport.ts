import { exportUtil } from './exportUtil'
import { downloadBlobAsFile } from '@/api/helpers/blobDownload'
import request from '@/api/request'

// Re-export the client-side export utility so consumers can import everything
// export-related from a single "unified" module (also keeps the import in use).
export { exportUtil }

export interface ExportOptions {
  url: string
  params?: Record<string, any>
  fileName: string
  format?: 'xlsx' | 'csv' | 'pdf'
}

export async function unifiedExport(options: ExportOptions) {
  const { url, params, fileName, format = 'xlsx' } = options
  const ext = format === 'csv' ? 'csv' : format === 'pdf' ? 'pdf' : 'xlsx'
  await downloadBlobAsFile(
    () => request.get(url, { params: { ...params, format }, responseType: 'blob' }),
    { fallbackFileName: `${fileName}.${ext}` }
  )
}
