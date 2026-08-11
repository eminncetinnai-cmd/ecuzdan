Repository Layer

- Repositories expose a clear contract (BaseRepository / *RepositoryContract) used by Domain services.
- Repositories are the only components that perform direct DB operations (session.add / commit etc.).
- Prefer small focused repository methods (get_by_id, list_for_tenant, add, delete).
- Do not embed business rules in repositories; return entities or raise persistence errors.
