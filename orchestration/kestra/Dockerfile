FROM ghcr.io/astral-sh/uv:0.11.19 AS uv
FROM kestra/kestra:v1.1.6
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/sea-jobs-venv UV_LINK_MODE=copy \
    PATH="/opt/sea-jobs-venv/bin:$PATH"
WORKDIR /opt/tech-jobs
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY config ./config
COPY dbt ./dbt
RUN uv sync --frozen --extra cloud --python /usr/bin/python3
WORKDIR /app
