Composition Root / DI scaffold (Phase 7)

Purpose
-------
This folder contains a minimal, non-invasive composition root intended to prepare the codebase for incremental Dependency Injection and test-friendly wiring.

How it works
------------
- bootstrap.get_container() returns an object with .repositories and .applications providers.
- Repositories and application services are created lazily and cached.
- Tests can call get_container().repositories.set_override('catalog', fake_repo) before requesting applications.
- Nothing is wired automatically; routes must opt-in to use providers to avoid behavioral changes.

Files
-----
- container.py: main RepositoryProvider and ApplicationProvider implementations and a top-level container.
- __init__.py: exposes container helpers.

Recommended next steps
----------------------
- Replace creation sites in one route (single endpoint) to get providers from bootstrap.get_container() and use the provided application instance.
- Add small unit tests that override repository providers to verify composition behavior.

Notes
-----
This is intentionally small and dependency-free. If a richer container is desired later, it can be introduced behind the same API shape to limit migration scope.