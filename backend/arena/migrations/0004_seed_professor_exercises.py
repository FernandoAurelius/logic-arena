from django.db import migrations


EXERCISES = [
    {
        'slug': 'soma-dois-inteiros',
        'title': 'Soma de Dois Inteiros',
        'statement': 'Leia dois valores inteiros, calcule a soma e exiba o resultado final.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'valor1 = int(input())\nvalor2 = int(input())\nprint(valor1 + valor2)\n',
        'sample_input': '10\n20\n',
        'sample_output': '30',
        'professor_note': 'Baseado em l02e01soma.py. Cobra leitura, conversão para inteiro e soma direta.',
        'test_cases': [
            {'input_data': '10\n20\n', 'expected_output': '30', 'is_hidden': False},
            {'input_data': '-5\n12\n', 'expected_output': '7', 'is_hidden': True},
        ],
    },
    {
        'slug': 'area-triangulo',
        'title': 'Área do Triângulo',
        'statement': 'Leia a base e a altura de um triângulo, calcule a área e exiba o resultado.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'base = float(input())\naltura = float(input())\narea = base * altura / 2\nprint(area)\n',
        'sample_input': '1.5\n2.6\n',
        'sample_output': '1.95',
        'professor_note': 'Baseado em l02e02area_triangulo.py. Questão clássica de fórmula direta com float.',
        'test_cases': [
            {'input_data': '1.5\n2.6\n', 'expected_output': '1.95', 'is_hidden': False},
            {'input_data': '10\n5\n', 'expected_output': '25.0', 'is_hidden': True},
        ],
    },
    {
        'slug': 'media-duas-notas',
        'title': 'Média de Duas Notas',
        'statement': 'Leia duas notas, calcule a média aritmética e informe se o aluno foi aprovado ou reprovado. Considere aprovado com média maior ou igual a 5.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'nota1 = float(input())\nnota2 = float(input())\nmedia = (nota1 + nota2) / 2\nprint(media)\nprint("Aluno aprovado." if media >= 5 else "Aluno reprovado.")\n',
        'sample_input': '5\n2\n',
        'sample_output': '3.5\nAluno reprovado.',
        'professor_note': 'Baseado em l03e02calcula_media_aula.py. Muito próximo do padrão de sala e de prova.',
        'test_cases': [
            {'input_data': '5\n2\n', 'expected_output': '3.5\nAluno reprovado.', 'is_hidden': False},
            {'input_data': '7\n8\n', 'expected_output': '7.5\nAluno aprovado.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'fahrenheit-celsius',
        'title': 'Conversão Fahrenheit para Celsius',
        'statement': 'Leia uma temperatura em graus Fahrenheit, converta para Celsius usando a fórmula correta e exiba o resultado.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'fahrenheit = float(input())\ncelsius = 5 * (fahrenheit - 32) / 9\nprint(celsius)\n',
        'sample_input': '32\n',
        'sample_output': '0.0',
        'professor_note': 'Baseado em l02e05fahrenheit_celsius.py. Cobra fórmula, parênteses e float.',
        'test_cases': [
            {'input_data': '32\n', 'expected_output': '0.0', 'is_hidden': False},
            {'input_data': '70\n', 'expected_output': '21.11111111111111', 'is_hidden': True},
        ],
    },
    {
        'slug': 'maior-ou-igual-cem',
        'title': 'Maior ou Igual a Cem',
        'statement': 'Leia um valor numérico e mostre "Valor maior ou igual a cem." se ele for maior ou igual a 100. Caso contrário, mostre "Valor menor que cem.".',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'valor = int(input())\nif valor >= 100:\n    print("Valor maior ou igual a cem.")\nelse:\n    print("Valor menor que cem.")\n',
        'sample_input': '20\n',
        'sample_output': 'Valor menor que cem.',
        'professor_note': 'Baseado em l03e01maior_cem_aula.py. Questão de if/else puro.',
        'test_cases': [
            {'input_data': '20\n', 'expected_output': 'Valor menor que cem.', 'is_hidden': False},
            {'input_data': '100\n', 'expected_output': 'Valor maior ou igual a cem.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'calculadora-somar-subtrair',
        'title': 'Calculadora Somar ou Subtrair',
        'statement': 'Leia dois números e uma opção de operação. Se a opção for 1, mostre a soma. Caso contrário, mostre a subtração do primeiro valor pelo segundo.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'valor1 = float(input())\nvalor2 = float(input())\nopcao = int(input())\nif opcao == 1:\n    print(valor1 + valor2)\nelse:\n    print(valor1 - valor2)\n',
        'sample_input': '8\n3\n1\n',
        'sample_output': '11.0',
        'professor_note': 'Baseado em l03e03a_somar_subtrair_aula(1).py. Menu simples com if/else.',
        'test_cases': [
            {'input_data': '8\n3\n1\n', 'expected_output': '11.0', 'is_hidden': False},
            {'input_data': '8\n3\n2\n', 'expected_output': '5.0', 'is_hidden': True},
        ],
    },
    {
        'slug': 'par-ou-impar',
        'title': 'Par ou Ímpar',
        'statement': 'Leia um valor inteiro e informe se ele é par ou ímpar.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'valor = int(input())\nif valor % 2 == 0:\n    print("Número par.")\nelse:\n    print("Número ímpar.")\n',
        'sample_input': '7\n',
        'sample_output': 'Número ímpar.',
        'professor_note': 'Baseado em l03e03b_par_impar(1).py. Usa operador módulo.',
        'test_cases': [
            {'input_data': '7\n', 'expected_output': 'Número ímpar.', 'is_hidden': False},
            {'input_data': '8\n', 'expected_output': 'Número par.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'maior-de-dois',
        'title': 'Maior de Dois Valores',
        'statement': 'Leia dois valores e mostre o maior deles. Se forem iguais, mostre "Os valores são iguais.".',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'valor1 = float(input())\nvalor2 = float(input())\nif valor1 > valor2:\n    print(valor1)\nelif valor2 > valor1:\n    print(valor2)\nelse:\n    print("Os valores são iguais.")\n',
        'sample_input': '5\n10\n',
        'sample_output': '10.0',
        'professor_note': 'Baseado em l03e07maior2(1).py. Cobra if/elif/else corretamente.',
        'test_cases': [
            {'input_data': '5\n10\n', 'expected_output': '10.0', 'is_hidden': False},
            {'input_data': '4\n4\n', 'expected_output': 'Os valores são iguais.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'positivo-nulo-negativo',
        'title': 'Positivo, Nulo ou Negativo',
        'statement': 'Leia um número e informe se ele é positivo, negativo ou nulo.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'numero = float(input())\nif numero > 0:\n    print("Número positivo.")\nelif numero < 0:\n    print("Número negativo.")\nelse:\n    print("Número nulo.")\n',
        'sample_input': '0\n',
        'sample_output': 'Número nulo.',
        'professor_note': 'Baseado em l03e06positivo_nulo_negativo(1).py. Exercício de classificação simples.',
        'test_cases': [
            {'input_data': '0\n', 'expected_output': 'Número nulo.', 'is_hidden': False},
            {'input_data': '-4\n', 'expected_output': 'Número negativo.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'lucro-ou-prejuizo',
        'title': 'Lucro ou Prejuízo',
        'statement': 'Leia o preço de compra e o preço de venda de um produto e informe se teve lucro, prejuízo ou se os valores são iguais.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'compra = float(input())\nvenda = float(input())\nif venda > compra:\n    print("Teve lucro.")\nelif compra > venda:\n    print("Teve prejuízo.")\nelse:\n    print("Os valores são iguais.")\n',
        'sample_input': '1000\n1200\n',
        'sample_output': 'Teve lucro.',
        'professor_note': 'Baseado em l03e08lucro_prejuizo_msg(1).py. Comparação de dois valores com três cenários.',
        'test_cases': [
            {'input_data': '1000\n1200\n', 'expected_output': 'Teve lucro.', 'is_hidden': False},
            {'input_data': '1000\n1000\n', 'expected_output': 'Os valores são iguais.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'idade-para-votar',
        'title': 'Idade para Votar',
        'statement': 'Leia o ano de nascimento, calcule a idade considerando o ano atual como 2026 e informe se a pessoa pode votar. Pode votar com 16 anos ou mais.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'ano_nascimento = int(input())\nidade = 2026 - ano_nascimento\nprint(idade)\nprint("Pode votar." if idade >= 16 else "Não pode votar.")\n',
        'sample_input': '2011\n',
        'sample_output': '15\nNão pode votar.',
        'professor_note': 'Baseado em l03e12a_idade_votar_aula(1).py. Mistura cálculo simples com condição.',
        'test_cases': [
            {'input_data': '2011\n', 'expected_output': '15\nNão pode votar.', 'is_hidden': False},
            {'input_data': '2000\n', 'expected_output': '26\nPode votar.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'contar-numeros-flag',
        'title': 'Contar Números com Flag',
        'statement': 'Leia vários números inteiros até que o usuário digite -1. Mostre ao final a quantidade de números digitados, sem contar o -1.',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'ct = 0\nwhile True:\n    numero = int(input())\n    if numero == -1:\n        break\n    ct += 1\nprint(ct)\n',
        'sample_input': '5\n6\n7\n-1\n',
        'sample_output': '3',
        'professor_note': 'Baseado em l04e04a_conta(1).py. Introduz flag e while com break.',
        'test_cases': [
            {'input_data': '5\n6\n7\n-1\n', 'expected_output': '3', 'is_hidden': False},
            {'input_data': '-1\n', 'expected_output': '0', 'is_hidden': True},
        ],
    },
    {
        'slug': 'media-turma-flag',
        'title': 'Média da Turma com Flag',
        'statement': 'Leia notas de uma turma até que o usuário digite -1. Mostre a média aritmética da turma e a quantidade de alunos lidos.',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'ct = 0\nsoma = 0\nwhile True:\n    nota = float(input())\n    if nota == -1:\n        break\n    ct += 1\n    soma += nota\nprint(soma / ct)\nprint(ct)\n',
        'sample_input': '5\n6\n7\n-1\n',
        'sample_output': '6.0\n3',
        'professor_note': 'Baseado em l04e04b_media_turma_com_flag_aula.py. Muito importante para prova prática.',
        'test_cases': [
            {'input_data': '5\n6\n7\n-1\n', 'expected_output': '6.0\n3', 'is_hidden': False},
            {'input_data': '5\n6\n6\n-1\n', 'expected_output': '5.666666666666667\n3', 'is_hidden': True},
        ],
    },
    {
        'slug': 'media-dos-pares',
        'title': 'Média dos Números Pares',
        'statement': 'Leia números inteiros até que o usuário digite 0. Considere apenas os valores pares, calcule a média deles e, se nenhum número par for digitado, mostre "Não foi digitado número par.".',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'ct = 0\nsoma = 0\nwhile True:\n    valor = int(input())\n    if valor == 0:\n        break\n    if valor % 2 == 0:\n        soma += valor\n        ct += 1\nif ct > 0:\n    print(soma / ct)\nelse:\n    print("Não foi digitado número par.")\n',
        'sample_input': '1\n2\n3\n4\n0\n',
        'sample_output': '3.0',
        'professor_note': 'Baseado em l04e05_media_pares.py. Mistura flag, módulo, somador e contador.',
        'test_cases': [
            {'input_data': '1\n2\n3\n4\n0\n', 'expected_output': '3.0', 'is_hidden': False},
            {'input_data': '1\n3\n5\n0\n', 'expected_output': 'Não foi digitado número par.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'menor-valor-flag',
        'title': 'Menor Valor com Flag',
        'statement': 'Leia números inteiros até que o usuário digite 0. Mostre o menor valor digitado. Se nenhum valor for digitado antes do 0, mostre "Não foi digitado nenhum valor.".',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'menor = None\nwhile True:\n    valor = int(input())\n    if valor == 0:\n        break\n    if menor is None or valor < menor:\n        menor = valor\nif menor is None:\n    print("Não foi digitado nenhum valor.")\nelse:\n    print(menor)\n',
        'sample_input': '2\n3\n1\n0\n',
        'sample_output': '1',
        'professor_note': 'Baseado em l04e07_menor_valor.py. Cobra atualização de acumulador mínimo.',
        'test_cases': [
            {'input_data': '2\n3\n1\n0\n', 'expected_output': '1', 'is_hidden': False},
            {'input_data': '0\n', 'expected_output': 'Não foi digitado nenhum valor.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'menor-e-maior-valor',
        'title': 'Menor e Maior Valor',
        'statement': 'Leia números inteiros até que o usuário digite 0. Mostre o menor valor e o maior valor digitados. Se nenhum valor for digitado, mostre "Não foi digitado nenhum valor.".',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'menor = None\nmaior = None\nwhile True:\n    valor = int(input())\n    if valor == 0:\n        break\n    if menor is None or valor < menor:\n        menor = valor\n    if maior is None or valor > maior:\n        maior = valor\nif menor is None:\n    print("Não foi digitado nenhum valor.")\nelse:\n    print(menor)\n    print(maior)\n',
        'sample_input': '2\n4\n3\n1\n0\n',
        'sample_output': '1\n4',
        'professor_note': 'Baseado em l04e08_menor_maior_valor.py. Sequência típica de prova com dois acumuladores.',
        'test_cases': [
            {'input_data': '2\n4\n3\n1\n0\n', 'expected_output': '1\n4', 'is_hidden': False},
            {'input_data': '0\n', 'expected_output': 'Não foi digitado nenhum valor.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'altura-e-genero',
        'title': 'Altura e Gênero do Grupo',
        'statement': 'Leia altura e gênero de várias pessoas. Use altura 0 como condição de saída. Ao final, mostre a maior altura, a menor altura, a quantidade de homens e a quantidade de mulheres. Considere gênero "m" e "f".',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'maior = None\nmenor = None\nct_m = 0\nct_f = 0\nwhile True:\n    altura = float(input())\n    if altura == 0:\n        break\n    genero = input().strip().lower()\n    if maior is None or altura > maior:\n        maior = altura\n    if menor is None or altura < menor:\n        menor = altura\n    if genero == "m":\n        ct_m += 1\n    elif genero == "f":\n        ct_f += 1\nif maior is None:\n    print("Não foi digitado nenhum dado.")\nelse:\n    print(maior)\n    print(menor)\n    print(ct_m)\n    print(ct_f)\n',
        'sample_input': '1.8\nm\n1.6\nf\n0\n',
        'sample_output': '1.8\n1.6\n1\n1',
        'professor_note': 'Baseado em l04e09altura_genero.py. Excelente para praticar while + múltiplos acumuladores.',
        'test_cases': [
            {'input_data': '1.8\nm\n1.6\nf\n0\n', 'expected_output': '1.8\n1.6\n1\n1', 'is_hidden': False},
            {'input_data': '0\n', 'expected_output': 'Não foi digitado nenhum dado.', 'is_hidden': True},
        ],
    },
    {
        'slug': 'naturais-vertical-ate-10',
        'title': 'Naturais até 10 na Vertical',
        'statement': 'Gere e mostre os números naturais de 0 até 10, um por linha.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'for numero in range(0, 11):\n    print(numero)\n',
        'sample_input': '',
        'sample_output': '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10',
        'professor_note': 'Baseado em l06e01naturais_vertical.py. Questão de for básico.',
        'test_cases': [
            {'input_data': '', 'expected_output': '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10', 'is_hidden': False},
            {'input_data': '', 'expected_output': '0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10', 'is_hidden': True},
        ],
    },
    {
        'slug': 'naturais-pares-ate-12',
        'title': 'Naturais Pares até 12',
        'statement': 'Gere e mostre os números naturais pares até 12, um por linha.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'for par in range(0, 13, 2):\n    print(par)\n',
        'sample_input': '',
        'sample_output': '0\n2\n4\n6\n8\n10\n12',
        'professor_note': 'Baseado em l06e04naturais_pares_ate_12.py. Cobra range com passo.',
        'test_cases': [
            {'input_data': '', 'expected_output': '0\n2\n4\n6\n8\n10\n12', 'is_hidden': False},
            {'input_data': '', 'expected_output': '0\n2\n4\n6\n8\n10\n12', 'is_hidden': True},
        ],
    },
    {
        'slug': 'naturais-impares-ate-13',
        'title': 'Naturais Ímpares até 13',
        'statement': 'Gere e mostre os números naturais ímpares até 13, um por linha.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'for impar in range(1, 14, 2):\n    print(impar)\n',
        'sample_input': '',
        'sample_output': '1\n3\n5\n7\n9\n11\n13',
        'professor_note': 'Baseado em l06e05naturais_impares_ate_13.py. Complementa o exercício dos pares.',
        'test_cases': [
            {'input_data': '', 'expected_output': '1\n3\n5\n7\n9\n11\n13', 'is_hidden': False},
            {'input_data': '', 'expected_output': '1\n3\n5\n7\n9\n11\n13', 'is_hidden': True},
        ],
    },
    {
        'slug': 'multiplos-de-tres-ate-21',
        'title': 'Múltiplos de 3 até 21',
        'statement': 'Gere e mostre os números múltiplos de 3 até 21, um por linha.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'for multiplo in range(0, 22, 3):\n    print(multiplo)\n',
        'sample_input': '',
        'sample_output': '0\n3\n6\n9\n12\n15\n18\n21',
        'professor_note': 'Baseado em l06e06naturais_multiplos_3.py. Bom treino de passo e sequência.',
        'test_cases': [
            {'input_data': '', 'expected_output': '0\n3\n6\n9\n12\n15\n18\n21', 'is_hidden': False},
            {'input_data': '', 'expected_output': '0\n3\n6\n9\n12\n15\n18\n21', 'is_hidden': True},
        ],
    },
    {
        'slug': 'ordem-decrescente-7-1',
        'title': 'Ordem Decrescente de 7 até 1',
        'statement': 'Gere e mostre a sequência dos números inteiros na ordem decrescente de 7 até 1.',
        'difficulty': 'iniciante',
        'language': 'python',
        'starter_code': 'for numero in range(7, 0, -1):\n    print(numero)\n',
        'sample_input': '',
        'sample_output': '7\n6\n5\n4\n3\n2\n1',
        'professor_note': 'Baseado em l06e07a_naturais_decrescente.py. Cobra passo negativo.',
        'test_cases': [
            {'input_data': '', 'expected_output': '7\n6\n5\n4\n3\n2\n1', 'is_hidden': False},
            {'input_data': '', 'expected_output': '7\n6\n5\n4\n3\n2\n1', 'is_hidden': True},
        ],
    },
    {
        'slug': 'sequencia-inteiros-intervalo',
        'title': 'Sequência de Inteiros por Intervalo',
        'statement': 'Leia o valor inicial e o valor final de uma sequência e mostre todos os inteiros do primeiro até o último, em ordem crescente.',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'primeiro = int(input())\nultimo = int(input())\nfor numero in range(primeiro, ultimo + 1):\n    print(numero)\n',
        'sample_input': '2\n6\n',
        'sample_output': '2\n3\n4\n5\n6',
        'professor_note': 'Baseado em l06e08sequencia_leia.py. Range com limites fornecidos pelo usuário.',
        'test_cases': [
            {'input_data': '2\n6\n', 'expected_output': '2\n3\n4\n5\n6', 'is_hidden': False},
            {'input_data': '5\n5\n', 'expected_output': '5', 'is_hidden': True},
        ],
    },
    {
        'slug': 'sequencia-crescente-ou-decrescente',
        'title': 'Sequência Crescente ou Decrescente',
        'statement': 'Leia o primeiro e o último valor. Se o primeiro for menor ou igual ao último, mostre a sequência em ordem crescente. Se o primeiro for maior, mostre a sequência em ordem decrescente.',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'primeiro = int(input())\nultimo = int(input())\nif primeiro <= ultimo:\n    for numero in range(primeiro, ultimo + 1):\n        print(numero)\nelse:\n    for numero in range(primeiro, ultimo - 1, -1):\n        print(numero)\n',
        'sample_input': '5\n1\n',
        'sample_output': '5\n4\n3\n2\n1',
        'professor_note': 'Baseado em l06e09sequencia_ordem_aula.py. Muito útil para treinar lógica condicional com for.',
        'test_cases': [
            {'input_data': '5\n1\n', 'expected_output': '5\n4\n3\n2\n1', 'is_hidden': False},
            {'input_data': '1\n5\n', 'expected_output': '1\n2\n3\n4\n5', 'is_hidden': True},
        ],
    },
    {
        'slug': 'media-turma-for',
        'title': 'Média da Turma com For',
        'statement': 'Leia 5 notas de alunos usando uma estrutura de repetição for e mostre a média da turma.',
        'difficulty': 'intermediario',
        'language': 'python',
        'starter_code': 'soma = 0\nfor _ in range(5):\n    soma += float(input())\nprint(soma / 5)\n',
        'sample_input': '2\n4\n6\n8\n10\n',
        'sample_output': '6.0',
        'professor_note': 'Baseado em l06e10media_turma_aula.py. Repetição controlada por for.',
        'test_cases': [
            {'input_data': '2\n4\n6\n8\n10\n', 'expected_output': '6.0', 'is_hidden': False},
            {'input_data': '3\n4\n6\n8\n10\n', 'expected_output': '6.2', 'is_hidden': True},
        ],
    },
]


SEEDED_SLUGS = [exercise['slug'] for exercise in EXERCISES]


def seed_exercises(apps, schema_editor):
    Exercise = apps.get_model('arena', 'Exercise')
    ExerciseTestCase = apps.get_model('arena', 'ExerciseTestCase')

    for payload in EXERCISES:
        exercise, _ = Exercise.objects.update_or_create(
            slug=payload['slug'],
            defaults={
                'title': payload['title'],
                'statement': payload['statement'],
                'difficulty': payload['difficulty'],
                'language': payload['language'],
                'starter_code': payload['starter_code'],
                'sample_input': payload['sample_input'],
                'sample_output': payload['sample_output'],
                'professor_note': payload['professor_note'],
                'is_active': True,
            },
        )

        ExerciseTestCase.objects.filter(exercise=exercise).delete()
        for test_case in payload['test_cases']:
            ExerciseTestCase.objects.create(
                exercise=exercise,
                input_data=test_case['input_data'],
                expected_output=test_case['expected_output'],
                is_hidden=test_case['is_hidden'],
            )


def unseed_exercises(apps, schema_editor):
    Exercise = apps.get_model('arena', 'Exercise')
    Exercise.objects.filter(slug__in=SEEDED_SLUGS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('arena', '0003_submission_feedback_status'),
    ]

    operations = [
        migrations.RunPython(seed_exercises, unseed_exercises),
    ]
