"""Public errors, upload validation and synchronous service calls."""

from pathlib import PurePosixPath
from typing import Any

import httpx
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


MAX_ARTIFACT_BYTES = 5 * 1024 * 1024
SERVICE_NAMES = {"store": "Хранилище файлов", "analysis": "Анализ"}


class ApiError(Exception):
    def __init__(self, status: int, message: str, service: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.service = service
        self.submission_id: str | None = None


def configure_api(app: Flask) -> None:
    app.config.update(MAX_CONTENT_LENGTH=MAX_ARTIFACT_BYTES + 16 * 1024, MAX_FORM_PARTS=3)

    @app.errorhandler(ApiError)
    def api_error(error: ApiError):
        body = {"message": str(error)}
        if error.service is not None:
            body["service"] = error.service
        if error.submission_id is not None:
            body["submission_id"] = error.submission_id
        return jsonify(error=body), error.status

    @app.errorhandler(HTTPException)
    def framework_error(error: HTTPException):
        messages = {
            400: "Не удалось разобрать запрос.",
            404: "Запрошенный ресурс не найден.",
            405: "Метод не поддерживается для этого адреса.",
            413: "Размер файла превышает 5 МиБ или форма превышает лимиты.",
            500: "Внутренняя ошибка сервиса.",
        }
        response = error.get_response()
        message = messages.get(error.code, error.name)
        response.set_data(app.json.dumps({"error": {"message": message}}))
        response.content_type = "application/json"
        return response

    @app.get("/health")
    def health():
        return {"status": "ok"}


def required_id(value: str | None, field: str) -> str:
    identifier = (value or "").strip()
    if (
        not 1 <= len(identifier) <= 100
        or identifier in {".", ".."}
        or any(char in "/\\" or not char.isprintable() for char in identifier)
    ):
        raise ApiError(
            400,
            f"Укажите от 1 до 100 печатных символов для {field}. Символы / и \\ запрещены.",
        )
    return identifier


def read_upload() -> tuple[str, str, str, bytes]:
    if request.mimetype != "multipart/form-data":
        raise ApiError(400, "Отправьте сдачу как multipart/form-data.")
    student_id = required_id(request.form.get("student_id"), "student_id")
    assignment_id = required_id(request.form.get("assignment_id"), "assignment_id")
    file = request.files.get("file")
    if file is None:
        raise ApiError(400, "Приложите файл в поле file.")
    filename = PurePosixPath((file.filename or "").replace("\\", "/")).name.strip()
    if not 1 <= len(filename) <= 255 or filename in {".", ".."} or not filename.isprintable():
        raise ApiError(400, "Имя файла должно содержать от 1 до 255 печатных символов.")
    content = file.read(MAX_ARTIFACT_BYTES + 1)
    if len(content) > MAX_ARTIFACT_BYTES:
        raise ApiError(413, "Размер файла превышает 5 МиБ.")
    return student_id, assignment_id, filename, content


class ServiceClient:
    def __init__(self, service: str, base_url: str, client: httpx.Client) -> None:
        self._service = service
        self._base_url = base_url.rstrip("/")
        self._client = client

    def request(self, method: str, path: str, *, missing: str | None = None, **kwargs: Any) -> httpx.Response:
        name = SERVICE_NAMES[self._service]
        try:
            response = self._client.request(method, self._base_url + path, **kwargs)
        except httpx.TimeoutException as error:
            raise ApiError(504, f"Сервис «{name}» не ответил вовремя.", self._service) from error
        except httpx.NetworkError as error:
            raise ApiError(503, f"Сервис «{name}» недоступен.", self._service) from error
        except httpx.RequestError as error:
            raise ApiError(502, f"Не удалось получить ответ от сервиса «{name}».", self._service) from error

        if response.is_success:
            return response
        if response.status_code == 404 and missing is not None:
            raise ApiError(404, missing)
        if response.status_code in {502, 503, 504}:
            # analysis can report a failure of its own Store dependency
            try:
                error_body = response.json()["error"]
                service = error_body["service"]
                message = error_body["message"]
                if service in SERVICE_NAMES and isinstance(message, str):
                    raise ApiError(response.status_code, message, service)
            except (ValueError, KeyError, TypeError):
                pass
        raise ApiError(502, f"Сервис «{name}» вернул ошибку HTTP {response.status_code}.", self._service)

    def json(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as error:
            name = SERVICE_NAMES[self._service]
            raise ApiError(502, f"Сервис «{name}» вернул некорректный JSON.", self._service) from error
