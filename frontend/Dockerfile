# syntax=docker/dockerfile:1.7

# Component image: the built web interface served as static files, without the
# API. The published images serve the same files from the backend (root
# Dockerfile). Build from the repository root:
#
#   docker build -f frontend/Dockerfile -t acestream-scraper-frontend .
#
# It listens on 8080 as an unprivileged user. Put it behind a proxy that sends
# /api to the backend.
FROM node:20-slim AS build

WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
COPY version.txt /build/version.txt
RUN npm run build


FROM nginxinc/nginx-unprivileged:stable-alpine

# Client-side routes fall back to the application shell.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/frontend/dist/ /usr/share/nginx/html/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["wget", "--quiet", "--spider", "http://127.0.0.1:8080/"]

USER nginx

CMD ["nginx", "-g", "daemon off;"]
