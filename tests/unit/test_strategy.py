
def test_strategy_page_access(authenticated_client):
    """Strateji sayfasına erişim testi"""
    # Giriş yaparak erişim
    response = authenticated_client.get('/strategy')
    assert response.status_code == 200
    assert b'Finansal Strateji' in response.data
    assert b'Monte Carlo' in response.data
    assert 'Alışılmadık'.encode('utf-8') in response.data

def test_strategy_data_logic(authenticated_client):
    """Strateji sayfasındaki veri mantığı testi"""
    response = authenticated_client.get('/strategy')
    assert response.status_code == 200
    assert b'Finansal Strateji' in response.data
    assert b'Fisher' in response.data or b'Monte Carlo' in response.data
