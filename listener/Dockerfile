# FROM python:3.11-alpine
# FROM python:3.11
FROM python:3-slim

WORKDIR /workspace
RUN pip install Flask "uvicorn[standard]"

ADD listener.py /workspace/listener.py

EXPOSE 8000/tcp

CMD ["uvicorn", "--interface", "wsgi", "--host", "0.0.0.0", "--port", "8000", "listener:app"]

