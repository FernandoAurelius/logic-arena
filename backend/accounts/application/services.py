import secrets

from django.contrib.auth.hashers import check_password, make_password

from arena.models import ArenaUser, AuthSession
from progress.application.services import build_user_progress_summary

from ..selectors import get_session_by_token


def build_user_schema_payload(user: ArenaUser) -> dict:
    return {
        'id': user.id,
        'nickname': user.nickname,
        'created_at': user.created_at,
        **build_user_progress_summary(user),
    }


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


def require_session(authorization: str | None) -> AuthSession:
    if not authorization or not authorization.startswith('Bearer '):
        raise PermissionError('Token ausente ou inválido.')
    token = authorization.replace('Bearer ', '', 1).strip()
    session = get_session_by_token(token)
    if session is None:
        raise PermissionError('Sessão não encontrada.')
    return session
