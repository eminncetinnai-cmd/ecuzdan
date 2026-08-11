
def test_settings_page_accessibility(authenticated_client):
    """Settings sayfasının 200 OK döndürdüğünü doğrular."""
    response = authenticated_client.get('/settings')
    assert response.status_code == 200
    assert b"Sistem Ayarlar" in response.data

def test_settings_requires_login(client):
    """Giriş yapmamış kullanıcının settings'e erişemediğini doğrular."""
    response = client.get('/settings')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_login_page_loads(client):
    """Login sayfasının yüklendiğini doğrular."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"E-C\xc3\xbczdan" in response.data
    assert b"Giri\xc5\x9f Yap" in response.data
