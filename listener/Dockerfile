FROM debian:latest

WORKDIR /tmp

RUN apt-get update && \
    apt-get install -y webhook redis-tools && \
    rm -rf /var/lib/apt/lists/*

RUN touch /hooks.json

COPY --chown=root:root --chmod=500 plumber.sh /plumber.sh

EXPOSE 9000

CMD ["webhook", "-urlprefix", "", "-hooks", "/hooks.json", "-verbose", "-port", "9000"]
