# syntax=docker/dockerfile:1
FROM python:3.11-slim@sha256:0000000000000000000000000000000000000000000000000000000000000000
RUN useradd --uid 10001 --create-home bench
WORKDIR /work
COPY app.py /work/app.py
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=2s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health')"
CMD ["python", "/work/app.py"]
