import pytest

from arena.selectors import get_active_exercise_by_slug, get_track_by_slug, list_active_exercises


pytestmark = pytest.mark.django_db


def test_selectors_return_active_exercises_and_track(catalog_graph):
    track = get_track_by_slug(catalog_graph['track'].slug)

    assert track is not None
    assert track.slug == catalog_graph['track'].slug
    assert list_active_exercises().filter(track=track).count() == 3
    assert get_active_exercise_by_slug(catalog_graph['exercises'][0].slug).slug == catalog_graph['exercises'][0].slug
