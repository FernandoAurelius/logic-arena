import json

import pytest

from apps.arena.models import ArenaUser, AuthSession


pytestmark = pytest.mark.django_db


def test_login_creates_user_and_session(client):
    response = client.post(
        '/api/auth/login',
        data=json.dumps({'nickname': 'miguel.barreto', 'password': 'senha-secreta'}),
        content_type='application/json',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['created'] is True
    assert payload['token']
    assert payload['user']['nickname'] == 'miguel.barreto'
    assert payload['user']['xp_total'] == 0
    assert ArenaUser.objects.filter(nickname='miguel.barreto').count() == 1
    assert AuthSession.objects.count() == 1
