# syntax=docker/dockerfile:1
FROM debian:bookworm-slim@sha256:0000000000000000000000000000000000000000000000000000000000000000
RUN useradd --uid 10001 --create-home bench
WORKDIR /work
COPY src/ /work/src/
RUN apt-get update \
 && apt-get install --no-install-recommends -y gcc libc6-dev \
 && gcc -O0 -fno-stack-protector -z execstack -o /work/vuln /work/src/vuln.c \
 && apt-get purge -y gcc libc6-dev && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*
USER 10001:10001
HEALTHCHECK --interval=10s --timeout=2s CMD sh -c 'echo ping | /work/vuln --selftest'
CMD ["/work/vuln", "--listen", "31337"]
