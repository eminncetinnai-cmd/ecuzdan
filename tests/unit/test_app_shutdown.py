from app import _cleanup_database_resources


def test_cleanup_database_resources_callable():
    # Running the cleanup callback should not raise even if the database session
    # is already cleaned up or the engine has been disposed.
    _cleanup_database_resources()
