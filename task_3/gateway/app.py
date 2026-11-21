"""Orchestrate submissions and expose reports over the public HTTP API."""

import os
from uuid import UUID

import httpx
from flask import Flask, jsonify, render_template

from common.http import ApiError, ServiceClient, configure_api, read_upload, required_id


def create_app(*, client: httpx.Client | None = None) -> Flask:
    app = Flask(__name__)
    configure_api(app)
    if client is None:
        client = httpx.Client(timeout=8, trust_env=False)
    store = ServiceClient("store", os.getenv("STORE_URL", "http://127.0.0.1:8001"), client)
    analysis = ServiceClient("analysis", os.getenv("ANALYSIS_URL", "http://127.0.0.1:8002"), client)

    def run_analysis(submission_id: str):
        try:
            return analysis.json("POST", f"/reports/{submission_id}", missing="Сдача не найдена.")
        except ApiError as error:
            error.submission_id = submission_id
            raise

    @app.post("/submissions")
    def submit():
        student_id, assignment_id, filename, content = read_upload()
        submission = store.json(
            "POST", "/submissions",
            data={"student_id": student_id, "assignment_id": assignment_id},
            files={"file": (filename, content)},
        )
        report = run_analysis(submission["submission_id"])
        return jsonify(submission=submission, report=report), 201

    @app.post("/submissions/<uuid:submission_id>/analysis")
    def retry_analysis(submission_id: UUID):
        return run_analysis(str(submission_id))

    @app.get("/submissions/<uuid:submission_id>/report")
    def get_report(submission_id: UUID):
        return analysis.json("GET", f"/reports/{submission_id}", missing="Для этой сдачи пока нет отчёта.")

    @app.get("/assignments/<assignment_id>/reports")
    def assignment_reports(assignment_id: str):
        assignment_id = required_id(assignment_id, "assignment_id")
        params = {"assignment_id": assignment_id}
        submissions = store.json("GET", "/submissions", params=params)
        reports = analysis.json("GET", "/reports", params=params)
        reports_by_id = {report["submission_id"]: report for report in reports}

        rows = []
        counts = {"passed": 0, "failed": 0, "no_report": 0}
        for submission in submissions:
            report = reports_by_id.get(submission["submission_id"])
            status = "no_report" if report is None else report["status"]
            rows.append({"submission": submission, "status": status, "report": report})
            counts[status] += 1
        return {"assignment_id": assignment_id, "summary": {"total": len(rows), **counts}, "submissions": rows}

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/docs")
    def swagger():
        return render_template("swagger.html")

    @app.get("/openapi.json")
    def openapi():
        return app.send_static_file("openapi.json")

    return app
