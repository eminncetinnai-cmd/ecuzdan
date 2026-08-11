from models import LogbookEntry, db


def test_logbook_crud_flow(authenticated_client, test_user):
    # 1. Create a logbook entry
    response = authenticated_client.post('/logbook/create', data={
        'title': 'Test Logbook Entry',
        'content': 'This is a test content for logbook.',
        'entry_date': '2026-06-19',
        'category': 'Finansal',
        'sentiment': 'Nötr'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # Verify in DB
    entry = LogbookEntry.query.filter_by(title='Test Logbook Entry', tenant_id=test_user.tenant_id).first()
    assert entry is not None
    assert entry.content == 'This is a test content for logbook.'

    # Test Detail - AJAX (returns JSON representation)
    response_detail_ajax = authenticated_client.get(f'/logbook/{entry.id}', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response_detail_ajax.status_code == 200
    data_detail = response_detail_ajax.get_json()
    assert data_detail['success'] is True
    assert data_detail['entry']['title'] == 'Test Logbook Entry'
    assert data_detail['entry']['content'] == 'This is a test content for logbook.'

    # Test Detail - Normal Request (redirects to /logbook/?open_edit=<id>)
    response_detail_normal = authenticated_client.get(f'/logbook/{entry.id}')
    assert response_detail_normal.status_code == 302
    assert f'/logbook/?open_edit={entry.id}' in response_detail_normal.headers['Location']

    # 2. Update the logbook entry
    response_update = authenticated_client.post(f'/logbook/{entry.id}/update', data={
        'title': 'Updated Test Logbook Entry',
        'content': 'Updated content.',
        'entry_date': '2026-06-20',
        'category': 'Yatırım',
        'sentiment': 'Boğa'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response_update.status_code == 200
    data_update = response_update.get_json()
    assert data_update['success'] is True

    # Verify update in DB
    entry = db.session.get(LogbookEntry, entry.id)
    assert entry is not None
    assert entry.title == 'Updated Test Logbook Entry'
    assert entry.content == 'Updated content.'
    assert str(entry.entry_date) == '2026-06-20'
    assert entry.category == 'Yatırım'
    assert entry.sentiment == 'Boğa'

    # 3. Delete the logbook entry
    response_delete = authenticated_client.post(f'/logbook/{entry.id}/delete', headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response_delete.status_code == 200
    data_delete = response_delete.get_json()
    assert data_delete['success'] is True

    # Verify deletion in DB
    deleted_entry = db.session.get(LogbookEntry, entry.id)
    assert deleted_entry is None
