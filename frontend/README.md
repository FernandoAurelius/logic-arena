# Frontend do Logic Arena

Esta pasta contém a interface principal do produto em `Vue 3 + TypeScript`.

## Papel desta camada

O frontend é responsável por três superfícies distintas:

- landing pública;
- página de ajuda/tutorial;
- arena autenticada de prática.

Ele conversa com o backend tipado via `OpenAPI` + `Zodios`, renderiza a shell visual do produto, controla a sessão do usuário e organiza o fluxo de prática entre escolha de exercício, edição de código, execução, feedback e revisão com IA.

## Arquivos e áreas principais

- `src/views/LandingView.vue`: entrada pública do produto
- `src/views/TutorialView.vue`: ajuda guiada e onboarding leve
- `src/views/ArenaView.vue`: estação autenticada de prática
- `src/components/editor/MonacoEditor.vue`: editor de código protagonista da arena
- `src/components/ui/`: primitives visuais no estilo técnico/brutalista do projeto
- `src/lib/api/`: client tipado gerado a partir do `OpenAPI`
- `src/lib/session.ts`: sessão local e cabeçalhos de autenticação
- `src/lib/theme.ts`: persistência e troca de tema

## Rodando localmente

```bash
cd "/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/frontend"
npm install
npm run generate:api
npm run dev
```

Se o backend estiver em outro host:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Build

```bash
npm run build
```

## Observações importantes

- o frontend depende da exportação de `backend/openapi.json` para manter o client coerente;
- o login é mínimo por `nickname + senha`, mas a arena só carrega conteúdo após sessão válida;
- o editor deve continuar sendo o centro da experiência, então mudanças visuais que reduzam seu protagonismo precisam ser tratadas com cuidado.

## Leitura aprofundada

Para entendimento didático e arquitetural desta camada, use a KB do projeto:

- [`kb/02_Bounded_Contexts/Arena Frontend e Experiência.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Arena%20Frontend%20e%20Experi%C3%AAncia.md)
- [`kb/02_Bounded_Contexts/Progressão, History e Gamificação.md`](/home/miguelbarreto/estudos/logica-de-programacao/avaliacao-pratica-app/kb/02_Bounded_Contexts/Progress%C3%A3o,%20History%20e%20Gamifica%C3%A7%C3%A3o.md)
