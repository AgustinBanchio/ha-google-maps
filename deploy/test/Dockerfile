FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM python:3.13.16-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /repo/collector
COPY collector/pyproject.toml collector/uv.lock ./
RUN uv sync --frozen --no-install-project --no-managed-python
COPY collector/src ./src
COPY collector/tests ./tests
COPY custom_components/google_maps/gm_loc_sharing.py /repo/custom_components/google_maps/gm_loc_sharing.py
COPY tools /repo/tools
COPY deploy /repo/deploy
ENV PYTHONPATH=/repo/collector/src
CMD ["/repo/collector/.venv/bin/python", "-m", "pytest", "-q"]
