import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { resolve, relative } from 'node:path'

const root = resolve(process.cwd())
const srcRoot = resolve(root, 'src')
const forbiddenDirectories = ['views', 'components'].map((directory) => resolve(srcRoot, directory))
const forbiddenImportPatterns = [
  {
    pattern: '@/lib/api/generated',
    message: 'Importe schemas e endpoints via `@/shared/api` em vez de acessar o gerado cru.',
  },
  {
    pattern: '@/views',
    message: 'A camada `views/` não faz mais parte do contrato. Use `pages/`.',
  },
  {
    pattern: '@/components',
    message: 'A camada `components/` não faz mais parte do contrato. Use `shared/ui`, `widgets`, `features` ou `entities`.',
  },
]
const architectureFileAllowlist = new Set([
  resolve(srcRoot, 'shared/api/generated.ts'),
])
const allowedExtensions = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.vue', '.json'])
const layerOrder = ['shared', 'entities', 'features', 'widgets', 'pages']
const allowedLayerImports = {
  shared: new Set(['shared']),
  entities: new Set(['entities', 'shared']),
  features: new Set(['features', 'entities', 'shared']),
  widgets: new Set(['widgets', 'features', 'entities', 'shared']),
  pages: new Set(['pages', 'widgets', 'features', 'entities', 'shared']),
}

function walk(directory) {
  const entries = readdirSync(directory, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const fullPath = resolve(directory, entry.name)
    if (entry.isDirectory()) {
      files.push(...walk(fullPath))
      continue
    }
    if (entry.isFile()) {
      files.push(fullPath)
    }
  }

  return files
}

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'))
}

function detectLayer(filePath) {
  const relativePath = relative(srcRoot, filePath)
  const layer = relativePath.split('/')[0]
  return layerOrder.includes(layer) ? layer : null
}

function detectImportedLayer(importPath) {
  if (!importPath.startsWith('@/')) {
    return null
  }

  const layer = importPath.replace(/^@\//, '').split('/')[0]
  return layerOrder.includes(layer) ? layer : null
}

function isEntityApiFile(filePath) {
  const relativePath = relative(srcRoot, filePath)
  return /^entities\/[^/]+\/api\/.+\.(ts|tsx)$/.test(relativePath)
}

const failures = []

for (const directory of forbiddenDirectories) {
  if (existsSync(directory)) {
    failures.push(`Diretório proibido encontrado: ${relative(root, directory)}`)
  }
}

for (const filePath of walk(srcRoot)) {
  if (!allowedExtensions.has(filePath.slice(filePath.lastIndexOf('.')))) {
    continue
  }

  if (architectureFileAllowlist.has(filePath)) {
    continue
  }

  const content = readFileSync(filePath, 'utf8')
  const currentLayer = detectLayer(filePath)

  for (const { pattern, message } of forbiddenImportPatterns) {
    if (content.includes(pattern)) {
      failures.push(`${relative(root, filePath)}: ${message}`)
    }
  }

  if (content.includes("@/shared/api/zodios") && !isEntityApiFile(filePath)) {
    failures.push(
      `${relative(root, filePath)}: use o facade de \`@/shared/api\` em vez de importar \`zodios\` diretamente.`,
    )
  }

  const importMatches = content.matchAll(/from\s+['"](@\/[^'"]+)['"]/g)
  for (const [, importPath] of importMatches) {
    const importedLayer = detectImportedLayer(importPath)
    if (!currentLayer || !importedLayer) {
      continue
    }
    if (!allowedLayerImports[currentLayer]?.has(importedLayer)) {
      failures.push(`${relative(root, filePath)}: a camada \`${currentLayer}\` não pode importar \`${importPath}\`.`)
    }
  }
}

const componentsConfigPath = resolve(root, 'components.json')
if (existsSync(componentsConfigPath)) {
  const componentsConfig = readJson(componentsConfigPath)
  const aliases = componentsConfig.aliases ?? {}
  const invalidAliasTargets = ['components', 'ui'].filter((key) => typeof aliases[key] === 'string' && aliases[key].includes('@/components'))

  if (invalidAliasTargets.length > 0) {
    failures.push(
      `components.json ainda aponta para @/components em: ${invalidAliasTargets.join(', ')}`,
    )
  }
}

if (failures.length > 0) {
  console.error('Falha no check de arquitetura do frontend:')
  for (const failure of failures) {
    console.error(`- ${failure}`)
  }
  process.exit(1)
}

console.log('Check de arquitetura do frontend passou.')
