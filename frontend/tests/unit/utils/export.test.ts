import { describe, it, expect } from 'vitest'
import { exportUtil } from '@/utils/exportUtil'
import _defaultExportUtil, { exportToExcel, exportToCSV, exportToPDF } from '@/utils/export'

describe('utils/export', () => {
  it('exports exportUtil', () => {
    expect(_defaultExportUtil).toBe(exportUtil)
  })
  it('exportToExcel', () => {
    expect(exportToExcel).toBe(exportUtil.exportToExcel)
  })
  it('exportToCSV', () => {
    expect(exportToCSV).toBe(exportUtil.exportToCSV)
  })
  it('exportToPDF', () => {
    expect(exportToPDF).toBe(exportUtil.exportToPDF)
  })
})
