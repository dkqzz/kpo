"""HTTP routes to run a build check and retrieve its stored reports."""

import os
from pathlib import Path
from uuid import UUID

import httpx
from flask import Flask, jsonify, request

from common.http import ApiError, ServiceClient, configure_api, required_id

from .checker import check_artifact
from .repository import ReportRepository


def create_app(data_dir: str | Path | None = None, *, client: httpx.Client | None = None) -> Flask:
    app = Flask(__name__)
    configure_api(app)
    repository = ReportRepository(Path(data_dir or os.getenv("ANALYSIS_DATA_DIR", ".data/analysis")))
    store = ServiceClient(
        "store", os.getenv("STORE_URL", "http://127.0.0.1:8001"),
        client if client is not None else httpx.Client(timeout=3, trust_env=False),
    )

    @app.post("/reports/<uuid:submission_id>")
    def analyze(submission_id: UUID):
        identifier = str(submission_id)
        report = repository.get(identifier)
        if report is None:
            submission = store.json("GET", f"/submissions/{identifier}", missing="Сдача не найдена.")
            artifact = store.request("GET", f"/artifacts/{identifier}").content
            status, details = check_artifact(submission["filename"], artifact)
            report = repository.save(identifier, submission["assignment_id"], status, details)
        return report

    @app.get("/reports/<uuid:submission_id>")
    def get_report(submission_id: UUID):
        report = repository.get(str(submission_id))
        if report is None:
            raise ApiError(404, "Для этой сдачи пока нет отчёта.")
        return report

    @app.get("/reports")
    def list_reports():
        assignment_id = required_id(request.args.get("assignment_id"), "assignment_id")
        return jsonify(repository.for_assignment(assignment_id))

    return app
