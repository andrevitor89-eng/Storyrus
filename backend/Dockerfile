FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org && \
    pip install --no-cache-dir . --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

COPY . .

# Fonte do ebook: Raleway Light 300 (Google Fonts) — gerada no build.
RUN pip install --no-cache-dir "fonttools>=4.38" --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org && \
    python scripts/fetch_fonts.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
