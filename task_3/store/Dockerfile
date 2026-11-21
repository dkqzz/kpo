FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common/ common/
COPY store/ store/

CMD ["python", "-m", "flask", "--app", "store.app", "run", "--host=0.0.0.0", "--port=8001"]
