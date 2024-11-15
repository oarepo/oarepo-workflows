from __future__ import annotations

from oarepo_runtime.services.entity.config import KeywordEntityServiceConfig
from oarepo_runtime.services.entity.service import KeywordEntityService


class AutoApproveEntityServiceConfig(KeywordEntityServiceConfig):
    service_id = "auto_approve"
    keyword = "auto_approve"


class AutoApproveEntityService(KeywordEntityService):
    pass
