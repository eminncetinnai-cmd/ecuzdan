import pytest


@pytest.mark.unit
def test_background_worker_owner_prevents_duplicate_process_start(app, monkeypatch):
    from app import _background_workers_enabled

    app.config.update(
        TESTING=False,
        DISABLE_BACKGROUND_SERVICE=False,
        BACKGROUND_SERVICE_ENABLED=True,
        BACKGROUND_WORKER_OWNER="web",
    )
    monkeypatch.setenv("DISABLE_BACKGROUND_SERVICE", "false")

    assert _background_workers_enabled(owner="web") is True
    assert _background_workers_enabled(owner="worker") is False


@pytest.mark.unit
def test_background_worker_owner_allows_dedicated_worker_only_when_selected(app, monkeypatch):
    from app import _background_workers_enabled

    app.config.update(
        TESTING=False,
        DISABLE_BACKGROUND_SERVICE=False,
        BACKGROUND_SERVICE_ENABLED=True,
        BACKGROUND_WORKER_OWNER="worker",
    )
    monkeypatch.setenv("DISABLE_BACKGROUND_SERVICE", "false")

    assert _background_workers_enabled(owner="web") is False
    assert _background_workers_enabled(owner="worker") is True
