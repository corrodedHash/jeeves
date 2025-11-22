# Use the official Debian base image
FROM debian:latest

# Set the working directory
WORKDIR /tmp

# Install required tools (curl, tar, gzip)
RUN apt-get update && \
    apt-get install -y webhook curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/streamdal/plumber/releases/download/v2.9.0/plumber-linux --output /bin/plumber && chmod u+x /bin/plumber

# Create the hooks.json file (empty or with default content)
RUN touch /hooks.json

# Expose port 9000
EXPOSE 9000

# Run webhook with the specified hooks file
CMD ["webhook", "-urlprefix", "", "-hooks", "/hooks.json", "-verbose", "-port", "9000"]
