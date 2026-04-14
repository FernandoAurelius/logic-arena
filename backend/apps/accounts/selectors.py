from apps.arena.models import AuthSession


def get_session_by_token(token: str):
    return AuthSession.objects.select_related('user').filter(token=token).first()
