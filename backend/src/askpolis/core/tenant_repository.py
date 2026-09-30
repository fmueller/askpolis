import uuid_utils.compat as uuid

from askpolis.logging import get_logger

from .models import Tenant
from .repositories import ParliamentRepository

logger = get_logger(__name__)


class TenantRepository:
    def __init__(self, parliament_repository: ParliamentRepository):
        self._parliament_repository = parliament_repository
        self._tenants: dict[str, Tenant] | None = None

    def _load_default_tenants(self) -> dict[str, Tenant]:
        bundestag = self._parliament_repository.get_by_name("Bundestag")
        if bundestag is None:
            raise Exception("Parliament 'Bundestag' not found")

        tenant = Tenant(id=uuid.uuid7(), name="demo", supported_parliaments=[bundestag.id])
        logger.info_with_attrs(
            "Loaded default tenant", {"tenant": tenant.name, "supported_parliaments": tenant.supported_parliaments}
        )
        return {tenant.name: tenant}

    def _ensure_loaded(self) -> None:
        if self._tenants is None:
            self._tenants = self._load_default_tenants()

    def get(self, name: str) -> Tenant | None:
        self._ensure_loaded()
        return self._tenants.get(name) if self._tenants else None

    def get_default(self) -> Tenant:
        tenant = self.get("demo")
        if tenant is None:
            raise Exception("Default tenant not available")
        return tenant

    def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        self._ensure_loaded()
        if self._tenants is None:
            return None

        for tenant in self._tenants.values():
            if tenant.id == tenant_id:
                return tenant

        return None

    def all(self) -> list[Tenant]:
        self._ensure_loaded()
        return list(self._tenants.values()) if self._tenants else []
