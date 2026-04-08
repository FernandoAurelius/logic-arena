# Logic Exam Arena

App React/Vite para simular avaliação prática de lógica de programação em Python.

## Ideia

O app usa os tokens e a direção visual da referência `stitch_ai_learning_platform_home.zip`, mas com outro propósito:

- menos "plataforma de learning"
- mais "estação de prova prática"
- foco em enunciado, checklist, armadilhas e ritmo de execução
- editor Python com highlight leve
- execução local via `python3`
- console com veredito de `passou` ou `não passou`

## Como rodar

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app"
npm install
npm run dev
```

O `npm run dev` agora sobe:

- frontend Vite
- API local de execução em `http://localhost:4175`

## Estrutura

- `src/challenges.js`: desafios calibrados a partir dos exercícios e provas já existentes
- `src/App.jsx`: interface principal da arena
- `src/styles.css`: implementação visual baseada nos tokens da referência
- `server.mjs`: API local para executar o código Python e validar os testes
