# On part d'une version légère de Python
FROM python:3.10-slim

# On définit le dossier de travail dans le conteneur
WORKDIR /app

# On installe les dépendances système pour psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# On copie les fichiers de dépendances et on installe
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie tout le reste du code
COPY . .

# On lance le bot
CMD ["python", "main.py"]