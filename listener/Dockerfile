FROM debian:latest

WORKDIR /tmp

RUN apt-get update && \
    apt-get install -y webhook curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/streamdal/plumber/releases/download/v2.9.0/plumber-linux --output /bin/plumber && chmod u+x /bin/plumber

RUN touch /hooks.json

COPY --chown root:root --chmod 500 plumber.sh /plumber.sh

EXPOSE 9000

CMD ["webhook", "-urlprefix", "", "-hooks", "/hooks.json", "-verbose", "-port", "9000"]
