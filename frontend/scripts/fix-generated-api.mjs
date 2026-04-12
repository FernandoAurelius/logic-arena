import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const generatedPath = resolve(process.cwd(), 'src/lib/api/generated.ts')
let source = readFileSync(generatedPath, 'utf8')

const endpointNames = [
  'authEndpoints',
  'exercisesEndpoints',
  'submissionsEndpoints',
  'catalogEndpoints',
  'catalog_adminEndpoints',
  'systemEndpoints',
]

for (const endpointName of endpointNames) {
  source = source.replace(`const ${endpointName} = makeApi([`, `export const ${endpointName} = makeApi([`)
}

source = source.replace(
  /\nexport function createApiClient[\s\S]*?return new Zodios\(baseUrl, endpoints, options\);\n}\n?$/m,
  '\n',
)

writeFileSync(generatedPath, source)
