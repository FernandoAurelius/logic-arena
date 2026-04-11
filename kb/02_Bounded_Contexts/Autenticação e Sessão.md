# Autenticação e Sessão

## Objetivo do módulo

Este contexto existe para resolver a pergunta mais simples do sistema: quem é o operador atual e como a arena sabe que ele pode listar exercícios, submeter código e abrir histórico?

## Arquivos principais

- `backend/arena/models.py`
- `backend/arena/api.py`
- `backend/arena/services.py`
- `frontend/src/lib/session.ts`
- `frontend/src/components/auth/LoginModal.vue`

## Modelo atual

O backend usa dois objetos principais:

```python
class ArenaUser(TimestampedModel):
    nickname = models.CharField(max_length=40, unique=True)
    password_hash = models.CharField(max_length=255)


class AuthSession(TimestampedModel):
    user = models.ForeignKey(ArenaUser, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=64, unique=True)
```

Esse desenho é simples, mas coerente com o recorte atual: não há perfis complexos, reset de senha, permissões granulares ou múltiplos papéis. O que existe é apenas o mínimo necessário para separar histórico e progresso por operador.

## Fluxo observado

1. o usuário informa `nickname + senha`;
2. `get_or_create_session()` procura o nickname;
3. se o usuário não existir, ele é criado automaticamente;
4. se existir, a senha é verificada;
5. uma nova sessão tokenizada é criada;
6. o frontend persiste token e usuário localmente e passa a enviar `Authorization: Bearer`.

Trecho central:

```python
def get_or_create_session(nickname: str, password: str) -> tuple[AuthSession, bool]:
    user = ArenaUser.objects.filter(nickname=nickname).first()
    created = False

    if user is None:
        user = ArenaUser.objects.create(nickname=nickname, password_hash=make_password(password))
        created = True
    elif not check_password(password, user.password_hash):
        raise ValueError('Nickname já existe, mas a senha não confere.')

    session = AuthSession.objects.create(user=user, token=secrets.token_hex(32))
    return session, created
```

## Leitura didática

Esta solução foi escolhida porque o produto ainda é interno e pequeno. Há um tradeoff claro aqui:

- ganha-se velocidade e zero atrito de cadastro;
- perde-se robustez típica de autenticação pública.

Para o estágio atual, isso é aceitável. Para um produto mais amplo, não seria suficiente.

## Tensões abertas

- não existe expiração explícita de sessão no modelo de domínio;
- não existe limite de sessões simultâneas;
- a progressão do usuário ainda está local no frontend, não acoplada à conta no backend.

## Por onde continuar

- [[Catálogo de Exercícios]]
- [[../04_Milestones/M1 - Integridade da Progressão]]
