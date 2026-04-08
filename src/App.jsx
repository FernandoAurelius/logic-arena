import React, { useEffect, useMemo, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { challengeGroups } from './challenges'

const EXAM_MINUTES = 40
const RUN_API_URL = 'http://localhost:4175/api/run'

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function App() {
  const [groupId, setGroupId] = useState(challengeGroups[0].id)
  const [roundIndex, setRoundIndex] = useState(0)
  const [timeLeft, setTimeLeft] = useState(EXAM_MINUTES * 60)
  const [running, setRunning] = useState(false)
  const [showProfessorLens, setShowProfessorLens] = useState(false)
  const [showRubric, setShowRubric] = useState(false)
  const [code, setCode] = useState(challengeGroups[0].rounds[0].starterCode ?? '')
  const [consoleOutput, setConsoleOutput] = useState('A execução do código aparecerá aqui.')
  const [runState, setRunState] = useState({ status: 'idle', passed: null, summary: '' })

  const activeGroup = useMemo(
    () => challengeGroups.find((group) => group.id === groupId) ?? challengeGroups[0],
    [groupId]
  )

  const activeRound = activeGroup.rounds[roundIndex] ?? activeGroup.rounds[0]
  const examProgress = ((EXAM_MINUTES * 60 - timeLeft) / (EXAM_MINUTES * 60)) * 100

  useEffect(() => {
    if (!running) return undefined

    const interval = window.setInterval(() => {
      setTimeLeft((current) => {
        if (current <= 1) {
          window.clearInterval(interval)
          return 0
        }
        return current - 1
      })
    }, 1000)

    return () => window.clearInterval(interval)
  }, [running])

  useEffect(() => {
    setRoundIndex(0)
    setShowProfessorLens(false)
    setShowRubric(false)
  }, [groupId])

  useEffect(() => {
    setCode(activeRound.starterCode ?? '')
    setConsoleOutput('A execução do código aparecerá aqui.')
    setRunState({ status: 'idle', passed: null, summary: '' })
  }, [activeRound])

  function nextRound() {
    if (roundIndex < activeGroup.rounds.length - 1) {
      setRoundIndex((current) => current + 1)
      setShowProfessorLens(false)
      setShowRubric(false)
    }
  }

  function previousRound() {
    if (roundIndex > 0) {
      setRoundIndex((current) => current - 1)
      setShowProfessorLens(false)
      setShowRubric(false)
    }
  }

  function resetExamClock() {
    setRunning(false)
    setTimeLeft(EXAM_MINUTES * 60)
  }

  function formatMultilineInput(text) {
    return String(text)
      .replace(/\r/g, '')
      .trimEnd()
      .split('\n')
      .map((line, index) => `${index + 1}. ${line === '' ? '(linha vazia)' : line}`)
      .join('\n')
  }

  async function runCode() {
    try {
      setRunState({ status: 'running', passed: null, summary: 'Executando testes...' })
      const response = await fetch(RUN_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          challengeId: activeRound.id,
          code
        })
      })

      if (!response.ok) {
        throw new Error(`Falha ${response.status}`)
      }

      const data = await response.json()
      setConsoleOutput(data.console)
      setRunState({
        status: 'done',
        passed: data.passed,
        summary: data.summary
      })
    } catch (error) {
      setConsoleOutput('Não foi possível executar o código. Verifique se a API local está rodando com npm run dev.')
      setRunState({
        status: 'error',
        passed: false,
        summary: 'Falha ao conectar com a execução local.'
      })
    }
  }

  return (
    <div className="exam-shell">
      <aside className="command-rail">
        <div className="rail-head">
          <p className="micro-label">Lógica de Programação</p>
          <h1>Exam Arena</h1>
          <p className="rail-copy">
            Simulador de avaliação prática com foco em Python básico, leitura de enunciado e execução sob pressão.
          </p>
        </div>

        <section className="rail-card">
          <p className="micro-label">Faixas de treino</p>
          <div className="group-stack">
            {challengeGroups.map((group) => (
              <button
                key={group.id}
                className={group.id === activeGroup.id ? 'group-button active' : 'group-button'}
                onClick={() => setGroupId(group.id)}
              >
                <strong>{group.label}</strong>
                <span>{group.description}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="rail-card rail-card-highlight">
          <p className="micro-label">Relógio de prova</p>
          <div className="clock-row">
            <div>
              <strong className="clock-value">{formatTime(timeLeft)}</strong>
              <p className="clock-caption">{running ? 'rodando agora' : 'pausado'}</p>
            </div>
            <div className="clock-actions">
              <button className="primary-btn" onClick={() => setRunning((current) => !current)}>
                {running ? 'Pausar' : 'Iniciar'}
              </button>
              <button className="ghost-btn" onClick={resetExamClock}>Reset</button>
            </div>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${examProgress}%` }} />
          </div>
        </section>
      </aside>

      <main className="exam-board">
        <header className="board-top">
          <div>
            <p className="micro-label">Rodada atual</p>
            <h2>{activeRound.title}</h2>
            <p className="board-copy">{activeRound.prompt}</p>
          </div>

          <div className="status-cluster">
            <div className="status-chip">
              <span className="chip-key">Skill</span>
              <strong>{activeRound.skill}</strong>
            </div>
            <div className="status-chip">
              <span className="chip-key">Bloco</span>
              <strong>{activeGroup.label}</strong>
            </div>
          </div>
        </header>

        <div className="board-scroll">
        <section className="board-grid">
          <div className="stack-column">
            <article className="panel panel-brief">
              <div className="panel-head">
                <p className="micro-label">Leitura operacional</p>
                <h3>O que você precisa entregar</h3>
              </div>

              <div className="brief-grid">
                <div className="brief-card">
                  <h4>Entradas</h4>
                  <ul>
                    {activeRound.inputs.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="brief-card">
                  <h4>Checklist mínimo</h4>
                  <ul>
                    {activeRound.checklist.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

              <div className="brief-card">
                <h4>Exemplo de I/O</h4>
                {activeRound.sampleIO.map((item, index) => (
                  <div className="io-case" key={`${activeRound.id}-${index}`}>
                    <p><strong>Entrada:</strong></p>
                    <pre className="io-block">{formatMultilineInput(item.input)}</pre>
                    <p><strong>Saída:</strong> {item.output}</p>
                  </div>
                ))}
              </div>
              </div>
            </article>

            <article className="panel panel-side">
              <div className="panel-head">
                <p className="micro-label">Leitura da banca</p>
                <h3>Como isso tende a ser cobrado</h3>
              </div>
              <p className="dense-copy">{activeRound.professorMode}</p>

              <div className="side-section">
                <h4>Erros que derrubam ponto</h4>
                <ul>
                  {activeRound.pitfalls.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              {showProfessorLens && (
                <div className="reveal-card">
                  <h4>Lente do professor</h4>
                  <p>
                    Nesta rodada, o que mais pesa não é “sofisticação”, e sim fidelidade ao enunciado,
                    escolha da estrutura correta e saída limpa.
                  </p>
                </div>
              )}

              {showRubric && (
                <div className="reveal-card reveal-card-orange">
                  <h4>Rubrica prática</h4>
                  <ul>
                    {activeRound.rubric.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          </div>

          <article className="panel panel-editor panel-editor-full">
            <div className="panel-head">
              <p className="micro-label">Execução prática</p>
              <h3>Editor Python</h3>
            </div>

            <div className="editor-shell">
              <CodeMirror
                value={code}
                height="100%"
                extensions={[python()]}
                theme={oneDark}
                basicSetup={{
                  autocompletion: false,
                  highlightActiveLine: true,
                  highlightActiveLineGutter: true,
                  foldGutter: true
                }}
                onChange={(value) => setCode(value)}
                className="code-editor"
                editable
                indentWithTab
                placeholder="# escreva sua solução aqui"
                style={{ height: '100%' }}
              />
            </div>

            <div className="console-shell">
              <div className="console-topbar">
                <strong>Console de execução</strong>
                <span
                  className={
                    runState.passed === true
                      ? 'verdict-chip verdict-pass'
                      : runState.passed === false
                        ? 'verdict-chip verdict-fail'
                        : 'verdict-chip'
                  }
                >
                  {runState.status === 'running'
                    ? 'executando'
                    : runState.passed === true
                      ? 'passou'
                      : runState.passed === false
                        ? 'não passou'
                        : 'aguardando'}
                </span>
              </div>
              <p className="console-summary">{runState.summary || 'Escreva sua solução e execute.'}</p>
              <pre className="console-output">{consoleOutput}</pre>
            </div>

            <div className="editor-actions">
              <button className="ghost-btn" onClick={() => setCode(activeRound.starterCode ?? '')}>
                Resetar código
              </button>
              <button className="ghost-btn" onClick={() => setShowProfessorLens((current) => !current)}>
                {showProfessorLens ? 'Ocultar lente do professor' : 'Mostrar lente do professor'}
              </button>
              <button className="primary-btn" onClick={() => setShowRubric((current) => !current)}>
                {showRubric ? 'Ocultar critérios' : 'Mostrar critérios'}
              </button>
              <button className="primary-btn" onClick={runCode}>
                Executar e validar
              </button>
            </div>
          </article>
        </section>
        </div>

        <footer className="board-footer">
          <button className="ghost-btn" onClick={previousRound} disabled={roundIndex === 0}>
            Rodada anterior
          </button>
          <div className="round-indicator">
            <span>{roundIndex + 1}</span>
            <small>/ {activeGroup.rounds.length}</small>
          </div>
          <button
            className="primary-btn"
            onClick={nextRound}
            disabled={roundIndex === activeGroup.rounds.length - 1}
          >
            Próxima rodada
          </button>
        </footer>
      </main>
    </div>
  )
}

export default App
