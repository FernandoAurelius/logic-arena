import pytest

from accounts.application.services import build_user_schema_payload, get_or_create_session
from arena.models import ArenaUser, AuthSession


pytestmark = pytest.mark.django_db


def test_login_endpoint_creates_user_and_session(client):
    response = client.post(
        '/api/auth/login',
        data='{"nickname":"miguel.barreto","password":"senha-secreta"}',
        content_type='application/json',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['created'] is True
    assert payload['token']
    assert payload['user']['nickname'] == 'miguel.barreto'
    assert ArenaUser.objects.filter(nickname='miguel.barreto').count() == 1
    assert AuthSession.objects.count() == 1


def test_accounts_application_service_returns_user_schema_payload(arena_user):
    payload = build_user_schema_payload(arena_user)

    assert payload['nickname'] == arena_user.nickname
    assert payload['xp_total'] == 0
    assert payload['level'] == 1


def test_get_or_create_session_reuses_password_and_validates_mismatch(arena_user):
    session, created = get_or_create_session(arena_user.nickname, 'senha-secreta')
    assert created is False
    assert session.user_id == arena_user.id
