FROM python:3.12-slim-bookworm

ENV APP_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LTP_PATH=/opt/language-tool \
    NLTK_DATA=/opt/nltk_data

WORKDIR /app

# LanguageTool 6.6+ requires Java 17. Include it in the Render runtime image,
# then cache the wrapper's default LanguageTool distribution during the build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -c "import nltk; assert nltk.download('punkt_tab', download_dir='/opt/nltk_data', quiet=True)" \
    && python -c "from language_tool_python.download_lt import download_lt; download_lt('latest')"

COPY . .

RUN useradd --create-home --uid 10001 writewise \
    && chown -R writewise:writewise /app
USER writewise

EXPOSE 10000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 120 run:app"]
