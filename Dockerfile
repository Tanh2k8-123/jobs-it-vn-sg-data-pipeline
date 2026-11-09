FROM ghcr.io/astral-sh/uv:0.11.19 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra cloud --no-install-project
COPY src ./src
COPY config ./config
COPY dbt ./dbt
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit
RUN uv sync --frozen --extra cloud
ENTRYPOINT ["sea-it-jobs"]
CMD ["--help"]
