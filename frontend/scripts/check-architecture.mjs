import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(new URL('.', import.meta.url).pathname, '..')

const checks = [
  {
    file: 'src/components/arena/surfaces/arenaSurfaceRegistry.ts',
    needle: 'http_contract_lab',
    label: 'registry de superfícies HTTP',
  },
  {
    file: 'src/components/arena/ArenaSurfaceHost.vue',
    needle: 'HttpContractLabSurface',
    label: 'host da arena renderizando a superfície HTTP',
  },
  {
    file: 'src/components/arena/surfaces/HttpContractLabSurface.vue',
    needle: 'Validar contrato',
    label: 'surface HTTP contract lab',
  },
  {
    file: 'src/views/ArenaView.vue',
    needle: 'ArenaSurfaceHost',
    label: 'ArenaView usando o host canônico',
  },
  {
    file: 'src/components/arena/ArenaResultsDialog.vue',
    needle: 'isHttpContractLab',
    label: 'central de resultados ciente da superfície HTTP',
  },
]

let failed = false

for (const check of checks) {
  const path = resolve(root, check.file)
  const source = await readFile(path, 'utf8')
  if (!source.includes(check.needle)) {
    failed = true
    console.error(`[architecture] missing ${check.label} in ${check.file}`)
  }
}

if (failed) {
  process.exit(1)
}

console.log('[architecture] frontend surface architecture looks consistent')
