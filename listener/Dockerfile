# FROM python:3.11-alpine
# FROM python:3.11
FROM python:3.11-slim

ADD listener.py /workspace/listener.py
WORKDIR /workspace
RUN pip install Flask "uvicorn[standard]"
EXPOSE 8000/tcp
CMD ["uvicorn", "--interface", "wsgi", "--host", "0.0.0.0", "listener:app"]

