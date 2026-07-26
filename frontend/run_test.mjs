import { execSync } from 'child_process'
import { writeFileSync } from 'fs'

const cwd = 'c:\\military-Rural Revitalization-system\\frontend'
writeFileSync(cwd + '\\test_marker.txt', 'STARTED')

try {
  const out = execSync('npx vitest run --coverage', {
    cwd,
    timeout: 600000,
    encoding: 'utf8',
    maxBuffer: 50 * 1024 * 1024
  })
  writeFileSync(cwd + '\\test_marker.txt', 'SUCCESS\n' + out.slice(-5000))
} catch (e) {
  writeFileSync(cwd + '\\test_marker.txt', 'FAILED\n' + ((e.stdout || e.stderr || e.message || '').slice(-5000)))
}
