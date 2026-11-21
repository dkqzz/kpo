"""HTTP routes for submitting and retrieving artifacts."""

import os
from pathlib import Path
from uuid import UUID

from flask import Flask, jsonify, request, send_file

from common.http import ApiError, configure_api, read_upload, required_id

from .repository import SubmissionRepository


def create_app(data_dir: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    configure_api(app)
    repository = SubmissionRepository(Path(data_dir or os.getenv("STORE_DATA_DIR", ".data/store")).resolve())

    @app.post("/submissions")
    def submit():
        return jsonify(repository.add(*read_upload())), 201

    @app.get("/submissions/<uuid:submission_id>")
    def get_submission(submission_id: UUID):
        submission = repository.get(str(submission_id))
        if submission is None:
            raise ApiError(404, "Сдача не найдена.")
        return submission

    @app.get("/submissions")
    def list_submissions():
        assignment_id = required_id(request.args.get("assignment_id"), "assignment_id")
        return jsonify(repository.for_assignment(assignment_id))

    @app.get("/artifacts/<uuid:submission_id>")
    def get_artifact(submission_id: UUID):
        if repository.get(str(submission_id)) is None:
            raise ApiError(404, "Артефакт не найден.")
        return send_file(
            repository.artifact_path(str(submission_id)),
            mimetype="application/octet-stream",
            conditional=False,
        )

    return app
