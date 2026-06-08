# Base stable avec KiCad et KiBot
FROM ghcr.io/inti-cmnb/kicad8_auto:latest

WORKDIR /app

# On force la mise à jour et l'installation de pip3 au niveau du système
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# On copie et installe les dépendances de ton API FastAPI
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
