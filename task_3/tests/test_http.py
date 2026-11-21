import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import httpx

from analysis.app import create_app as create_analysis
from common.http import MAX_ARTIFACT_BYTES
from gateway.app import create_app as create_gateway
from store.app import create_app as create_store
from tests.test_checker import zip_project


class VyshBuildHttpTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data = Path(directory.name)
        environment = patch.dict("os.environ", {"STORE_URL": "http://store", "ANALYSIS_URL": "http://analysis"})
        environment.start()
        self.addCleanup(environment.stop)
        self.failures = {}
        self.calls = []
        self.transport = httpx.Client(transport=httpx.MockTransport(self.route_request))
        self.addCleanup(self.transport.close)
        self.restart_services()

    def restart_services(self):
        self.store = create_store(self.data / "store")
        self.analysis = create_analysis(self.data / "analysis", client=self.transport)
        self.upstreams = {
            "store": httpx.WSGITransport(self.store),
            "analysis": httpx.WSGITransport(self.analysis),
        }
        gateway = create_gateway(client=self.transport)
        gateway.testing = True
        self.gateway = gateway.test_client()

    def route_request(self, request):
        host = request.url.host
        self.calls.append((host, request.method, request.url.path))
        if failure := self.failures.get(host):
            raise failure("simulated upstream failure", request=request)
        return self.upstreams[host].handle_request(request)

    def upload(self, content=b"print(1)\n", filename="main.py", assignment="hw-3", student="s-1"):
        upload = httpx.Request(
            "POST", "http://gateway/submissions",
            data={"assignment_id": assignment, "student_id": student},
            files={"file": (filename, content)},
        )
        return self.gateway.post("/submissions", headers=upload.headers, data=upload.read())

    def test_submission_is_stored_and_analyzed_in_one_request(self):
        created = self.upload(assignment="ДЗ 3", student="  s-1 ")
        self.assertEqual(created.status_code, 201, created.get_data(as_text=True))
        result = created.json
        submission_id = result["submission"]["submission_id"]
        self.assertEqual(result["submission"]["student_id"], "s-1")
        self.assertEqual(result["report"]["submission_id"], submission_id)
        self.assertTrue(result["report"]["success"])
        self.assertEqual(self.calls, [
            ("store", "POST", "/submissions"),
            ("analysis", "POST", f"/reports/{submission_id}"),
            ("store", "GET", f"/submissions/{submission_id}"),
            ("store", "GET", f"/artifacts/{submission_id}"),
        ])
        with self.store.test_client().get(f"/artifacts/{submission_id}") as artifact:
            self.assertEqual(artifact.data, b"print(1)\n")
        self.assertEqual(self.gateway.get(f"/submissions/{submission_id}/report").json, result["report"])
        self.assertEqual(self.gateway.get("/assignments/ДЗ%203/reports").json["summary"]["passed"], 1)

    def test_assignment_summary_contains_both_results_and_filters_other_assignments(self):
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload(assignment="hw-4").status_code, 201)
        failed = self.upload(zip_project({"README.md": b"# project"}), "project.zip")
        self.assertEqual(failed.status_code, 201)
        self.assertFalse(failed.json["report"]["success"])
        self.assertIn("main.py", failed.json["report"]["details"])
        response = self.gateway.get("/assignments/hw-3/reports")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["summary"], {"total": 2, "passed": 1, "failed": 1, "no_report": 0})
        self.assertEqual([row["status"] for row in response.json["submissions"]], ["failed", "passed"])
        self.assertEqual(self.gateway.get("/assignments/unknown/reports").json["submissions"], [])

    def test_empty_file_is_a_stored_failed_report(self):
        response = self.upload(b"")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["submission"]["size_bytes"], 0)
        self.assertEqual(response.json["report"]["status"], "failed")

    def test_invalid_form_and_oversized_upload_are_rejected_before_store(self):
        self.assertEqual(self.gateway.post("/submissions", json={}).status_code, 400)
        self.assertEqual(self.upload(student="  ").status_code, 400)
        self.assertEqual(self.upload(assignment="bad/id").status_code, 400)
        self.assertEqual(self.upload(b"a" * (MAX_ARTIFACT_BYTES + 1)).status_code, 413)
        self.assertEqual(self.calls, [])

    def test_store_unavailable_stops_workflow_before_analysis(self):
        self.failures["store"] = httpx.ConnectError
        response = self.upload()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"]["service"], "store")
        self.assertNotIn("submission_id", response.json["error"])
        self.assertEqual(self.calls, [("store", "POST", "/submissions")])

    def test_analysis_failure_retains_submission_and_allows_idempotent_recovery(self):
        self.failures["analysis"] = httpx.ConnectError
        failed = self.upload()
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.json["error"]["service"], "analysis")
        submission_id = failed.json["error"]["submission_id"]
        self.assertEqual(self.gateway.get("/assignments/hw-3/reports").status_code, 503)
        del self.failures["analysis"]

        self.assertEqual(self.gateway.get(f"/submissions/{submission_id}/report").status_code, 404)
        row, = self.gateway.get("/assignments/hw-3/reports").json["submissions"]
        self.assertEqual(row["status"], "no_report")
        self.assertIsNone(row["report"])
        self.assertEqual(row["submission"]["submission_id"], submission_id)

        first = self.gateway.post(f"/submissions/{submission_id}/analysis")
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json["success"])
        self.assertEqual(self.gateway.post(f"/submissions/{submission_id}/analysis").json, first.json)
        self.assertEqual(self.gateway.get("/assignments/hw-3/reports").json["summary"]["total"], 1)

    def test_analysis_timeout_returns_504_with_submission_id(self):
        self.failures["analysis"] = httpx.ReadTimeout
        response = self.upload()
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json["error"]["service"], "analysis")
        self.assertIn("submission_id", response.json["error"])

    def test_store_failure_during_analysis_identifies_store(self):
        self.failures["analysis"] = httpx.ConnectError
        submission_id = self.upload().json["error"]["submission_id"]
        del self.failures["analysis"]
        self.failures["store"] = httpx.ConnectError
        response = self.gateway.post(f"/submissions/{submission_id}/analysis")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"]["service"], "store")
        self.assertEqual(response.json["error"]["submission_id"], submission_id)

    def test_missing_submission_has_a_json_404(self):
        for method, path in [
            ("GET", f"/submissions/{uuid4()}/report"),
            ("GET", "/submissions/invalid-id/report"),
            ("POST", f"/submissions/{uuid4()}/analysis"),
        ]:
            with self.subTest(method=method, path=path):
                response = self.gateway.open(path, method=method)
                self.assertEqual(response.status_code, 404)
                self.assertIn("message", response.json["error"])

    def test_data_survives_service_recreation(self):
        created = self.upload()
        self.assertEqual(created.status_code, 201)
        submission_id = created.json["submission"]["submission_id"]
        self.restart_services()
        self.assertEqual(self.gateway.get(f"/submissions/{submission_id}/report").json, created.json["report"])
        self.assertEqual(self.gateway.get("/assignments/hw-3/reports").json["summary"]["passed"], 1)
        with self.store.test_client().get(f"/artifacts/{submission_id}") as artifact:
            self.assertEqual(artifact.data, b"print(1)\n")

    def test_dashboard_and_swagger_are_served_by_gateway(self):
        self.assertIn("Отчёты по заданию", self.gateway.get("/").get_data(as_text=True))
        self.assertIn("/openapi.json", self.gateway.get("/docs").get_data(as_text=True))
        with self.gateway.get("/openapi.json") as schema:
            self.assertEqual(set(schema.json["paths"]), {
                "/submissions", "/submissions/{submission_id}/analysis", "/submissions/{submission_id}/report",
                "/assignments/{assignment_id}/reports", "/health",
            })
