# Visão Geral do Produto

## O que é o Logic Arena

`Logic Arena` é uma plataforma de treino prático de programação orientada a avaliação. Ela foi desenhada para aproximar o estudante de um cenário de prova prática: o exercício vem com enunciado, exemplos, testes visíveis, código vazio por padrão, execução real, feedback objetivo e revisão posterior.

O recorte do produto é intencionalmente enxuto. Ele não tenta competir com plataformas gigantes nem cobrir todos os formatos de aprendizagem. A aposta é outra: ser pequeno, útil, rápido e didático exatamente no momento em que o aluno precisa praticar.

## Problema que o produto resolve

O treinamento tradicional de lógica costuma ter dois extremos ruins:

- listas estáticas e descontextualizadas, que não simulam o ambiente de avaliação;
- judge online genérico, que corrige mas não explica, e não preserva o contexto pedagógico.

O `Logic Arena` tenta ocupar um meio-termo melhor:

- simular a dinâmica de execução e correção;
- preservar contexto de sala e de prova;
- permitir releitura posterior da sessão;
- usar IA como apoio explicativo, não como muleta central.

## Recorte atual

Hoje o produto está focado em:

- login mínimo por `nickname + senha`;
- catálogo interno de exercícios inspirados nas aulas do professor;
- linguagem principal: `Python`;
- fluxo único de treino: escolher, codar, executar, revisar e repetir;
- revisão com IA sempre ligada no backend.

## O que já existe

- landing pública;
- página de ajuda/tutorial;
- arena autenticada com sidebar, especificação, editor, console, hints, histórico e revisão com IA;
- runner isolado para execução;
- histórico restaurável com código, console e conversa da revisão;
- deploy contínuo em produção.

## O que ainda está em aberto

As principais tensões do produto hoje não são “falta de funcionalidade básica”. Elas são tensões de maturidade:

- o XP ainda não representa progresso real, porque pode ser farmado;
- a navegação ainda não tem taxonomia robusta para um catálogo grande;
- a gamificação ainda é mais ornamental do que sistêmica;
- o catálogo ainda é forte em fundamentos, mas fraco em desafios realmente integradores.

## Tese de evolução

O projeto parece mais promissor se seguir esta ordem:

1. corrigir integridade da progressão;
2. organizar catálogo e navegação;
3. justificar a gamificação com ranking e domínio;
4. expandir o conteúdo para problemas mais ambiciosos.

## Leituras seguintes

- [[../03_Arquitetura/Visão Arquitetural]]
- [[../04_Milestones/Mapa de Milestones]]
