import cors from 'cors'
import express from 'express'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawn } from 'node:child_process'
import { challengeGroups } from './src/challenges.js'

const app = express()
const port = 4175

app.use(cors())
app.use(express.json({ limit: '2mb' }))

function findChallenge(challengeId) {
  for (const group of challengeGroups) {
    const found = group.rounds.find((round) => round.id === challengeId)
    if (found) return found
  }
  return null
}

function runPython(code, stdin) {
  return new Promise((resolve) => {
    const tmpFile = path.join(
      os.tmpdir(),
      `logic-exam-${Date.now()}-${Math.random().toString(36).slice(2)}.py`
    )

    fs.writeFileSync(tmpFile, code, 'utf8')

    const child = spawn('python3', [tmpFile], { stdio: 'pipe' })
    let stdout = ''
    let stderr = ''
    let settled = false

    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true
        child.kill('SIGKILL')
        fs.unlink(tmpFile, () => {})
        resolve({
          ok: false,
          stdout,
          stderr: stderr || 'Execução interrompida por timeout.'
        })
      }
    }, 5000)

    child.stdout.on('data', (data) => {
      stdout += data.toString()
    })

    child.stderr.on('data', (data) => {
      stderr += data.toString()
    })

    child.on('close', (codeValue) => {
      if (settled) return
      settled = true
      clearTimeout(timeout)
      fs.unlink(tmpFile, () => {})
      resolve({
        ok: codeValue === 0,
        stdout,
        stderr
      })
    })

    child.stdin.write(stdin)
    child.stdin.end()
  })
}

function normalize(text) {
  return String(text).replace(/\r/g, '').trim()
}

function canonicalText(text) {
  return normalize(text)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .toLowerCase()
}

function extractNumericTokens(text) {
  return normalize(text)
    .match(/-?\d+(?:\.\d+)?/g)
    ?.map((token) => Number(token))
    .filter((value) => !Number.isNaN(value)) ?? []
}

function linesMatch(expectedLine, actualText) {
  const expectedNumber = Number(expectedLine)
  const actualNormalized = normalize(actualText)

  if (!Number.isNaN(expectedNumber)) {
    const actualNumbers = extractNumericTokens(actualNormalized)
    return actualNumbers.some((value) => Math.abs(value - expectedNumber) < 1e-9)
  }

  const expectedCanonical = canonicalText(expectedLine)
  const actualCanonical = canonicalText(actualNormalized)

  return actualCanonical.includes(expectedCanonical)
}

function compareOutputs(expected, actual) {
  const expectedNormalized = normalize(expected)
  const actualNormalized = normalize(actual)

  if (expectedNormalized === actualNormalized) {
    return true
  }

  const expectedLines = expectedNormalized.split('\n')
  return expectedLines.every((expectedLine) => linesMatch(expectedLine, actualNormalized))
}

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, port })
})

app.post('/api/run', async (req, res) => {
  const { challengeId, code } = req.body ?? {}
  const challenge = findChallenge(challengeId)

  if (!challenge || typeof code !== 'string') {
    return res.status(400).json({ error: 'Payload inválido.' })
  }

  if (!challenge.tests?.length) {
    return res.json({
      passed: false,
      summary: 'Este modo não possui correção automática.',
      console: 'Sem testes automáticos para esta rodada.',
      results: []
    })
  }

  const results = []

  for (const test of challenge.tests) {
    const execution = await runPython(code, test.input)
    const actual = normalize(execution.stdout)
    const expected = normalize(test.expected)
    const passed = execution.ok && compareOutputs(expected, actual)

    results.push({
      input: test.input,
      expected,
      actual,
      stderr: normalize(execution.stderr),
      passed
    })
  }

  const passed = results.every((result) => result.passed)
  const consoleLines = results.map((result, index) => {
    const lines = [
      `Teste ${index + 1}: ${result.passed ? 'PASSOU' : 'FALHOU'}`,
      `Entrada: ${JSON.stringify(result.input)}`,
      `Esperado: ${result.expected}`,
      `Obtido: ${result.actual || '(sem saída)'}`
    ]

    if (result.stderr) {
      lines.push(`Erro: ${result.stderr}`)
    }

    return lines.join('\n')
  })

  return res.json({
    passed,
    summary: passed ? 'Passou nos testes atuais.' : 'Ainda não passou em todos os testes.',
    console: consoleLines.join('\n\n'),
    results
  })
})

app.listen(port, () => {
  console.log(`Logic Exam API disponível em http://localhost:${port}`)
})
