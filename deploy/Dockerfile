FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM python:3.13.16-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY collector/pyproject.toml collector/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-managed-python

FROM python:3.13.16-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641
ARG SOURCE_REVISION
LABEL org.opencontainers.image.source="https://github.com/AgustinBanchio/ha-google-maps" \
      org.opencontainers.image.revision=$SOURCE_REVISION
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src" \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY collector/src /app/src
COPY collector/uv.lock /app/uv.lock
COPY LICENSE /app/LICENSE
USER 10001:10001
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD ["python", "-m", "google_maps_collector", "--healthcheck"]
CMD ["python", "-m", "google_maps_collector"]
