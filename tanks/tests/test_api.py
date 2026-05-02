import pytest
from rest_framework.test import APIClient
from tanks.models import Location, Tank, TankVolume
from .conftest import make_reading


@pytest.fixture
def client():
    return APIClient()


# ---------------------------------------------------------------------------
# Location CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_create_location(client):
    response = client.post('/api/locations/', {'name': 'Austin, TX'}, format='json')
    assert response.status_code == 201
    assert response.data['name'] == 'Austin, TX'


@pytest.mark.django_db
def test_list_locations(client, location):
    response = client.get('/api/locations/')
    assert response.status_code == 200
    names = [l['name'] for l in response.data['results']]
    assert 'Austin, TX' in names


@pytest.mark.django_db
def test_retrieve_location(client, location):
    response = client.get(f'/api/locations/{location.id}/')
    assert response.status_code == 200
    assert response.data['name'] == 'Austin, TX'


@pytest.mark.django_db
def test_update_location(client, location):
    response = client.patch(f'/api/locations/{location.id}/', {'name': 'Dallas, TX'}, format='json')
    assert response.status_code == 200
    assert response.data['name'] == 'Dallas, TX'


@pytest.mark.django_db
def test_delete_location(client, location):
    response = client.delete(f'/api/locations/{location.id}/')
    assert response.status_code == 204
    location.refresh_from_db()
    assert location.is_archived is True


@pytest.mark.django_db
def test_delete_location_cascades_to_tanks(client, location, tank_a, tank_b):
    client.delete(f'/api/locations/{location.id}/')
    tank_a.refresh_from_db()
    tank_b.refresh_from_db()
    assert tank_a.is_archived is True
    assert tank_b.is_archived is True


@pytest.mark.django_db
def test_delete_location_cascades_to_volumes(client, location, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    client.delete(f'/api/locations/{location.id}/')
    reading.refresh_from_db()
    assert reading.is_archived is True


@pytest.mark.django_db
def test_archive_location_via_patch_is_ignored(client, location, tank_a):
    response = client.patch(f'/api/locations/{location.id}/', {'is_archived': True}, format='json')
    assert response.status_code == 200
    tank_a.refresh_from_db()
    assert tank_a.is_archived is False


@pytest.mark.django_db
def test_archived_location_not_in_list(client, location):
    client.delete(f'/api/locations/{location.id}/')
    response = client.get('/api/locations/')
    names = [l['name'] for l in response.data['results']]
    assert 'Austin, TX' not in names


# ---------------------------------------------------------------------------
# Tank CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_create_tank(client, location):
    response = client.post('/api/tanks/', {'name': 'Tank A', 'location': location.id}, format='json')
    assert response.status_code == 201


@pytest.mark.django_db
def test_list_tanks(client, tank_a):
    response = client.get('/api/tanks/')
    assert response.status_code == 200
    names = [t['name'] for t in response.data['results']]
    assert 'Tank A' in names


@pytest.mark.django_db
def test_retrieve_tank(client, tank_a):
    response = client.get(f'/api/tanks/{tank_a.id}/')
    assert response.status_code == 200
    assert response.data['name'] == 'Tank A'


@pytest.mark.django_db
def test_update_tank(client, tank_a):
    response = client.patch(f'/api/tanks/{tank_a.id}/', {'name': 'Tank Z'}, format='json')
    assert response.status_code == 200
    assert response.data['name'] == 'Tank Z'


@pytest.mark.django_db
def test_delete_tank(client, tank_a):
    response = client.delete(f'/api/tanks/{tank_a.id}/')
    assert response.status_code == 204
    tank_a.refresh_from_db()
    assert tank_a.is_archived is True


@pytest.mark.django_db
def test_delete_tank_cascades_to_volumes(client, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    client.delete(f'/api/tanks/{tank_a.id}/')
    reading.refresh_from_db()
    assert reading.is_archived is True


@pytest.mark.django_db
def test_archived_volume_not_in_list(client, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    client.delete(f'/api/tanks/{tank_a.id}/')
    response = client.get('/api/tank-volumes/')
    ids = [r['id'] for r in response.data['results']]
    assert reading.id not in ids


@pytest.mark.django_db
def test_archived_tank_not_in_list(client, tank_a):
    client.delete(f'/api/tanks/{tank_a.id}/')
    response = client.get('/api/tanks/')
    names = [t['name'] for t in response.data['results']]
    assert 'Tank A' not in names


# ---------------------------------------------------------------------------
# Tanks by location
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tanks_by_location(client, location, tank_a, tank_b):
    other_location = Location.objects.create(name="Houston, TX")
    other_tank = Tank.objects.create(name="Tank X", location=other_location)

    response = client.get(f'/api/locations/{location.id}/tanks/')
    assert response.status_code == 200
    ids = [t['id'] for t in response.data]
    assert tank_a.id in ids
    assert tank_b.id in ids
    assert other_tank.id not in ids


# ---------------------------------------------------------------------------
# TankVolume CRUD + validation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_create_tank_volume(client, tank_a):
    response = client.post('/api/tank-volumes/', {
        'tank': tank_a.id,
        'volume': '50.00',
        'created_at': '2023-01-02T10:00:00Z'
    }, format='json')
    assert response.status_code == 201


@pytest.mark.django_db
def test_retrieve_tank_volume(client, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    response = client.get(f'/api/tank-volumes/{reading.id}/')
    assert response.status_code == 200
    assert response.data['volume'] == '50.00'


@pytest.mark.django_db
def test_update_tank_volume(client, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    response = client.patch(f'/api/tank-volumes/{reading.id}/', {'volume': '35.00'}, format='json')
    assert response.status_code == 200
    assert response.data['volume'] == '35.00'


@pytest.mark.django_db
def test_delete_tank_volume(client, tank_a):
    reading = make_reading(tank_a, 50, "2023-01-02 10:00")
    response = client.delete(f'/api/tank-volumes/{reading.id}/')
    assert response.status_code == 204


@pytest.mark.django_db
def test_filter_tank_volumes_by_tank(client, tank_a, tank_b):
    make_reading(tank_a, 50, "2023-01-02 10:00")
    make_reading(tank_b, 30, "2023-01-02 10:00")

    response = client.get(f'/api/tank-volumes/?tank_id={tank_a.id}')
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['tank'] == tank_a.id


@pytest.mark.django_db
def test_filter_tank_volumes_by_date(client, tank_a):
    make_reading(tank_a, 50, "2023-01-02 10:00")
    make_reading(tank_a, 40, "2023-01-03 10:00")

    response = client.get('/api/tank-volumes/?date=2023-01-02')
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['volume'] == '50.00'


@pytest.mark.django_db
def test_create_tank_volume_negative_volume_returns_400(client, tank_a):
    response = client.post('/api/tank-volumes/', {
        'tank': tank_a.id,
        'volume': '-5.00',
        'created_at': '2023-01-02T10:00:00Z'
    }, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tank_volume_zero_volume_is_valid(client, tank_a):
    response = client.post('/api/tank-volumes/', {
        'tank': tank_a.id,
        'volume': '0.00',
        'created_at': '2023-01-02T10:00:00Z'
    }, format='json')
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_tank_volume_missing_volume_returns_400(client, tank_a):
    response = client.post('/api/tank-volumes/', {
        'tank': tank_a.id,
        'created_at': '2023-01-02T10:00:00Z'
    }, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tank_volume_missing_created_at_returns_400(client, tank_a):
    response = client.post('/api/tank-volumes/', {
        'tank': tank_a.id,
        'volume': '50.00',
    }, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tank_volume_invalid_tank_returns_400(client):
    response = client.post('/api/tank-volumes/', {
        'tank': 99999,
        'volume': '50.00',
        'created_at': '2023-01-02T10:00:00Z'
    }, format='json')
    assert response.status_code == 400
