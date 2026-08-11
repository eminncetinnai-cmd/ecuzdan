"""ReportingApplicationService skeleton.

Thin orchestration only; no business rules here.
"""

from typing import Optional

from application.base import ApplicationService


class ReportingApplicationService(ApplicationService):
    def __init__(
        self,
        reporting_service: Optional[object] = None,
        export_service: Optional[object] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.reporting_service = reporting_service
        self.export_service = export_service

    def generate_report(self, report_id, **kwargs):
        pass

    def export_pdf(self, report_id, **kwargs):
        pass
