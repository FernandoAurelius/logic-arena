import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const generatedPath = resolve(process.cwd(), 'src/lib/api/generated.ts')
let source = readFileSync(generatedPath, 'utf8')

source = source.replaceAll(/const (\w+Endpoints) = makeApi\(\[/g, 'export const $1 = makeApi([')

source = source.replace(
  /\nexport function createApiClient[\s\S]*?return new Zodios\(baseUrl, endpoints, options\);\n}\n?$/m,
  '\n',
)

writeFileSync(generatedPath, source)
