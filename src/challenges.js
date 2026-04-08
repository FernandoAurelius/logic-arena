export const challengeGroups = [
  {
    id: 'fundamentos',
    label: 'Fundamentos',
    description: 'Entrada, processamento e saída com fórmulas simples.',
    rounds: [
      {
        id: 'area-triangulo',
        title: 'Área do Triângulo',
        skill: 'input + float + fórmula',
        professorMode: 'Questão curta, direta, cobrando leitura de valores e cálculo sem enfeite.',
        prompt:
          'Leia a base e a altura de um triângulo, calcule a área e exiba o resultado.',
        inputs: ['base', 'altura'],
        checklist: [
          'Ler dois valores reais',
          'Aplicar a fórmula area = base * altura / 2',
          'Exibir apenas o resultado solicitado'
        ],
        pitfalls: [
          'Usar divisão inteira sem perceber',
          'Trocar a ordem do cálculo',
          'Não converter a entrada para float'
        ],
        sampleIO: [
          { input: 'Base = 1.5 | Altura = 2.6', output: 'Área do triângulo = 1.95' }
        ],
        rubric: [
          'Correto uso de entrada e saída',
          'Fórmula aplicada sem erro',
          'Código simples e legível'
        ],
        starterCode: `base = float(input())
altura = float(input())

# escreva sua solução abaixo
area = 0

print(area)
`,
        tests: [
          { input: '1.5\n2.6\n', expected: '1.95' },
          { input: '10\n5\n', expected: '25.0' }
        ]
      },
      {
        id: 'fahrenheit-celsius',
        title: 'Conversão de Temperatura',
        skill: 'fórmula + precisão',
        professorMode: 'Exercício típico de transformação aritmética com entrada única.',
        prompt:
          'Leia uma temperatura em Fahrenheit e converta para Celsius usando a fórmula adequada.',
        inputs: ['fahrenheit'],
        checklist: [
          'Ler um valor real',
          'Aplicar celsius = 5 * (fahrenheit - 32) / 9',
          'Exibir o valor convertido'
        ],
        pitfalls: [
          'Esquecer os parênteses',
          'Misturar a ordem da fórmula',
          'Tratar Fahrenheit como inteiro sem necessidade'
        ],
        sampleIO: [
          { input: 'Fahrenheit = 55', output: 'Celsius = 12.777...' }
        ],
        rubric: [
          'Fórmula correta',
          'Entrada tratada como número',
          'Saída coerente com o enunciado'
        ],
        starterCode: `fahrenheit = float(input())

# escreva sua solução abaixo
celsius = 0

print(celsius)
`,
        tests: [
          { input: '32\n', expected: '0.0' },
          { input: '55\n', expected: '12.777777777777779' }
        ]
      }
    ]
  },
  {
    id: 'decisao',
    label: 'Decisão',
    description: 'If, else, classificação e mensagens condicionais.',
    rounds: [
      {
        id: 'media-aprovacao',
        title: 'Média com Aprovação',
        skill: 'if/else + média',
        professorMode: 'Questão clássica para verificar lógica condicional simples.',
        prompt:
          'Leia duas notas, calcule a média aritmética e informe se o aluno foi aprovado ou reprovado. A aprovação ocorre com média maior ou igual a 5.',
        inputs: ['nota 1', 'nota 2'],
        checklist: [
          'Calcular média corretamente',
          'Usar condição media >= 5',
          'Exibir média e situação'
        ],
        pitfalls: [
          'Usar > 5 em vez de >= 5',
          'Errar a fórmula da média',
          'Imprimir mensagem incompatível com a condição'
        ],
        sampleIO: [
          { input: '5 e 2', output: 'Média = 3.5 | Aluno reprovado.' }
        ],
        rubric: [
          'Condição correta',
          'Resultado consistente',
          'Leitura fiel do enunciado'
        ],
        starterCode: `nota1 = float(input())
nota2 = float(input())

media = 0

print(media)
if False:
    print("Aluno aprovado.")
else:
    print("Aluno reprovado.")
`,
        tests: [
          { input: '5\n2\n', expected: '3.5\nAluno reprovado.' },
          { input: '5.5\n6.5\n', expected: '6.0\nAluno aprovado.' }
        ]
      },
      {
        id: 'classificador-inteiros',
        title: 'Classificador de Inteiros',
        skill: 'comparação + ordenação simples',
        professorMode: 'Pode aparecer como “leia dois valores e mostre em ordem crescente”.',
        prompt:
          'Leia dois números inteiros e exiba-os em ordem crescente. Se forem iguais, informe que são equivalentes.',
        inputs: ['inteiro 1', 'inteiro 2'],
        checklist: [
          'Comparar os dois valores',
          'Exibir em ordem crescente',
          'Tratar igualdade'
        ],
        pitfalls: [
          'Não tratar o caso de valores iguais',
          'Inverter a lógica de maior e menor',
          'Mostrar ordem errada'
        ],
        sampleIO: [
          { input: '10 e 2', output: 'Inteiros classificados: 2, 10' }
        ],
        rubric: [
          'Ordenação correta',
          'Uso adequado de condição',
          'Saída completa'
        ],
        starterCode: `a = int(input())
b = int(input())

# escreva sua solução abaixo
`,
        tests: [
          { input: '10\n2\n', expected: '2, 10' },
          { input: '7\n7\n', expected: 'Os inteiros são equivalentes' }
        ]
      }
    ]
  },
  {
    id: 'repeticao',
    label: 'Repetição',
    description: 'While, acumuladores e estatísticas de múltiplos valores.',
    rounds: [
      {
        id: 'stats-valores',
        title: 'Estatísticas de Valores',
        skill: 'while + soma + média + contagem',
        professorMode: 'Muito cara de prova prática com entrada repetida até sentinela.',
        prompt:
          'Leia vários valores até o usuário digitar "sair". Ao final, informe quantidade, soma, média e quantidade de valores maiores que 20.',
        inputs: ['valor repetido até sentinela'],
        checklist: [
          'Controlar laço com sentinela',
          'Acumular soma',
          'Calcular média ao final',
          'Contar valores maiores que 20'
        ],
        pitfalls: [
          'Tentar calcular média sem ter valores',
          'Não converter a entrada antes de acumular',
          'Confundir sentinela com valor válido'
        ],
        sampleIO: [
          { input: '10, 25, 30, sair', output: 'Qtd = 3 | Soma = 65 | Média = 21.66... | >20 = 2' }
        ],
        rubric: [
          'Controle de repetição correto',
          'Acumuladores consistentes',
          'Encerramento limpo do programa'
        ],
        starterCode: `valores = []

while True:
    entrada = input().strip()
    if entrada.lower() == "sair":
        break
    valores.append(float(entrada))

# escreva sua solução abaixo
`,
        tests: [
          { input: '10\n25\n30\nsair\n', expected: '3\n65.0\n21.666666666666668\n2' },
          { input: '5\n18\n22\nsair\n', expected: '3\n45.0\n15.0\n1' }
        ]
      },
      {
        id: 'pares-impares',
        title: 'Média de Pares e Ímpares',
        skill: 'while + classificação + acumuladores',
        professorMode: 'Questão que mistura repetição com classificação numérica.',
        prompt:
          'Leia números até o usuário digitar 0. Ao final, mostre a média dos pares, a média dos ímpares, a quantidade de números digitados e a soma total.',
        inputs: ['números até 0'],
        checklist: [
          'Parar no sentinela 0',
          'Separar pares e ímpares',
          'Manter acumuladores e contadores separados',
          'Exibir estatísticas finais'
        ],
        pitfalls: [
          'Incluir o 0 nos cálculos',
          'Dividir por zero se não houver pares ou ímpares',
          'Confundir média com soma'
        ],
        sampleIO: [
          { input: '2, 3, 8, 0', output: 'Média pares = 5 | Média ímpares = 3 | Qtd = 3 | Soma = 13' }
        ],
        rubric: [
          'Sentinela correta',
          'Separação correta das categorias',
          'Cálculo final consistente'
        ],
        starterCode: `numeros = []

while True:
    numero = float(input())
    if numero == 0:
        break
    numeros.append(numero)

# escreva sua solução abaixo
`,
        tests: [
          { input: '2\n3\n8\n0\n', expected: '5.0\n3.0\n3\n13.0' },
          { input: '4\n6\n9\n0\n', expected: '5.0\n9.0\n3\n19.0' }
        ]
      }
    ]
  },
  {
    id: 'avaliacao',
    label: 'Simulação',
    description: 'Modo de prova com ritmo, checklist e postura de execução.',
    rounds: [
      {
        id: 'full-practical',
        title: 'Rodada de Avaliação Prática',
        skill: 'execução sob pressão',
        professorMode: 'Simula o que costuma ser cobrado: ler, processar, decidir, repetir e exibir corretamente.',
        prompt:
          'Escolha um desafio real da lista, escreva a solução em Python, teste com um exemplo e valide a saída final sem enfeitar o programa.',
        inputs: ['variável conforme exercício escolhido'],
        checklist: [
          'Ler o enunciado inteiro antes de codar',
          'Identificar entradas, processamento e saída',
          'Escolher a estrutura correta (sequência, decisão ou repetição)',
          'Testar pelo menos um caso manualmente'
        ],
        pitfalls: [
          'Codar antes de entender o enunciado',
          'Esquecer o formato de saída',
          'Misturar validação extra onde o professor não pediu'
        ],
        sampleIO: [
          { input: 'depende do desafio escolhido', output: 'saída fiel ao enunciado, sem excesso de interface' }
        ],
        rubric: [
          'Leitura correta do problema',
          'Estrutura de controle adequada',
          'Saída compatível com o que foi pedido',
          'Postura prática de prova'
        ],
        starterCode: `# escolha um dos desafios reais e escreva aqui sua solução em Python
`,
        tests: []
      }
    ]
  }
]
