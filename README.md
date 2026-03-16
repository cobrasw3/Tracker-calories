# 🥗 Tracker Calories & Pas - Bot Telegram

Système complet de suivi de santé avec monitoring en temps réel.

## 🚀 Stack Technique
- **Bot :** Python (python-telegram-bot)
- **Base de données :** PostgreSQL 15
- **Visualisation :** Grafana
- **Infrastructure :** Docker & Docker Compose

## 🛠 Installation
1. Remplir le fichier `.env` avec votre `TELEGRAM_TOKEN` et vos accès DB.
2. Lancer l'infrastructure :
   ```bash
   docker compose up --build -d
3. Accéder au Dashboard sur localhost:3000
### ✅ Mission accomplie !
Une fois que c'est push, ton projet est immortel. Si tu changes de PC ou si tu veux l'installer sur un serveur (VPS) pour qu'il tourne 24h/24 sans que ton PC reste allumé, tu n'auras qu'à faire un `git clone` et un `docker compose up`.