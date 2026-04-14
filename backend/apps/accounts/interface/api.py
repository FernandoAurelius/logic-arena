from ninja import Header, Router

from apps.accounts.application.services import build_user_schema_payload, get_or_create_session, require_session
from apps.accounts.schemas import ErrorSchema, LoginInputSchema, LoginResponseSchema, UserSchema


router = Router(tags=['auth'])


@router.post('/login', response={200: LoginResponseSchema, 401: ErrorSchema}, summary='Faz login ou cria o usuário automaticamente.')
def login(request, payload: LoginInputSchema):
    try:
        session, created = get_or_create_session(payload.nickname.strip(), payload.password)
    except ValueError as error:
        return 401, {'message': str(error)}

    return 200, {
        'token': session.token,
        'created': created,
        'user': build_user_schema_payload(session.user),
    }


@router.get('/me', response={200: UserSchema, 401: ErrorSchema}, summary='Retorna o usuário autenticado.')
def me(request, authorization: str | None = Header(default=None)):
    try:
        session = require_session(authorization)
    except PermissionError as error:
        return 401, {'message': str(error)}
    return 200, build_user_schema_payload(session.user)
