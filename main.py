import os 
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Chargement des variables du fichier .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Première phrase du bot au reveil
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut cobrasw3 ! Tracker activé et prêt à l'emploi !")

# Fonction de connexion à la database
def save_data(type_donnee, valeur):
    # 1. Connexion à la database
    conn = psycopg2.connect(
        host="db",
        database="calories_tracker",
        user="cobrasw3",
        password="my_password"
    )
    cur = conn.cursor()

    # 2. Execution des commandes SQL

    # 3. Fermeture de la database
    conn.commit()
    cur.close()
    conn.close()

# Fonction pour ajouter une valeur 
def insert_data(table, valeur):
    try:
        # On se connecte
        conn = psycopg2.connect(
            host="db",
            database="calories_tracker",
            user="cobrasw3",
            password="my_password"
        )
        cur = conn.cursor()
        
        # On prépare la commande SQL
        sql = f"INSERT INTO {table} (valeur) VALUES (%s)"
        
        cur.execute(sql, (valeur,))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur DB : {e}")
        return False
    
# Obtenir un bilan global
# Chercher les calories cumulées du jour
def get_calories_today():
    try:
        conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
        cur = conn.cursor()
        cur.execute("SELECT SUM(valeur) FROM suivi_calories WHERE date_enregistrement::date = CURRENT_DATE")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        return total
    except Exception as e:
        print(f"Erreur SQL Calories: {e}")
        return None

# Chercher le dernier poids enregistré aujourd'hui
def get_last_poids_today():
    try:
        conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
        cur = conn.cursor()
        cur.execute("SELECT valeur FROM suivi_poids WHERE date_enregistrement::date = CURRENT_DATE ORDER BY id DESC LIMIT 1")
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res[0] if res else None
    except Exception as e:
        print(f"Erreur SQL Poids: {e}")
        return None

# Chercher les pas cumulés du jour
def get_pas_today():
    try:
        conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
        cur = conn.cursor()
        cur.execute("SELECT SUM(valeur) FROM suivi_pas WHERE date_enregistrement::date = CURRENT_DATE")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        return total
    except Exception as e:
        print(f"Erreur SQL Pas: {e}")
        return None
    
async def bilan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cal = get_calories_today()
    poids_val = get_last_poids_today()
    pas_val = get_pas_today()
    
    # Construction dynamique du message
    message = "📊 **BILAN DU JOUR** 📊\n\n"
    
    # Section Calories
    if cal is not None and cal > 0:
        message += f"🔥 Calories : {cal} kcal\n"
    else:
        message += "🔥 Calories : _Pas encore saisi_\n"
        
    # Section Pas
    if pas_val is not None and pas_val > 0:
        message += f"👣 Pas : {pas_val} pas\n"
    else:
        message += "👣 Pas : _Pas encore saisi_\n"
        
    # Section Poids (Harmonisée avec les autres)
    if poids_val is not None:
        message += f"📉 Poids : {poids_val} kg\n"
    else:
        message += "📉 Poids : _Pas encore saisi_\n"

    # Vérification globale : si absolument rien n'a été saisi
    # On vérifie si cal et pas sont soit None soit 0, et si poids est None
    if (not cal) and (not pas_val) and (poids_val is None):
        message = "Aucune donnée enregistrée pour aujourd'hui. Bouge-toi ! 💪"

    await update.message.reply_text(message, parse_mode='Markdown')

def get_current_objectif(type_obj):
    try:
        conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
        cur = conn.cursor()
        cur.execute("SELECT valeur FROM objectifs WHERE type_objectif = %s", (type_obj,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res[0] if res else None
    except Exception as e:
        print(f"Erreur objectif : {e}")
        return None

def delete_by_date(table, date_str):
    try:
        conn = psycopg2.connect(
            host="db",
            database="calories_tracker",
            user="cobrasw3",
            password="my_password"
        )
        cur = conn.cursor()
        
        # On supprime les lignes où la date correspond à celle donnée (format AAAA-MM-JJ)
        sql = f"DELETE FROM {table} WHERE date_enregistrement::date = %s"
        
        cur.execute(sql, (date_str,))
        count = cur.rowcount # Nombre de lignes supprimées
        
        conn.commit()
        cur.close()
        conn.close()
        
        return count
    except Exception as e:
        print(f"Erreur suppression par date : {e}")
        return -1
    
# Fonction pour supprimer la dernière valeur saisie
def delete_data(table):
    try:
        # On se connecte
        conn = psycopg2.connect(
            host="db",
            database="calories_tracker",
            user="cobrasw3",
            password="my_password"
        )
        cur = conn.cursor()
        
        # On prépare la commande SQL
        sql = f"DELETE FROM {table} WHERE id = (SELECT MAX(id) FROM {table})"
        
        cur.execute(sql)
        count = cur.rowcount
        
        conn.commit()
        cur.close()
        conn.close()
        
        return count > 0
    except Exception as e:
        print(f"Erreur suppression : {e}")
        return False
    
# Fonction pour récupérer l'historique d'un paramètre sur les 7 derniers jours
def get_history(table, jours=7):
    try:
        conn = psycopg2.connect(
            host="db",
            database="calories_tracker",
            user="cobrasw3",
            password="my_password"
        )
        cur = conn.cursor()
        
        # Pour le poids, on prend la moyenne journalière, pour le reste la somme
        fonction_sql = "AVG" if table == "suivi_poids" else "SUM"
        
        sql = f"""
            SELECT date_enregistrement::date, {fonction_sql}(valeur)
            FROM {table}
            WHERE date_enregistrement >= CURRENT_DATE - INTERVAL '{jours} days'
            GROUP BY date_enregistrement::date
            ORDER BY date_enregistrement::date DESC
        """
        
        cur.execute(sql)
        lignes = cur.fetchall()
        cur.close()
        conn.close()
        return lignes
    except Exception as e:
        print(f"Erreur historique : {e}")
        return None
    
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage : /info [calories/pas/poids/objectifs]")
        return

    categorie = context.args[0].lower()

    # --- CAS PARTICULIER : OBJECTIFS ---
    if categorie == "objectifs":
        try:
            conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
            cur = conn.cursor()
            cur.execute("SELECT type_objectif, valeur FROM objectifs")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                await update.message.reply_text("Aucun objectif fixé pour le moment.")
                return

            msg = "🎯 **Tes Objectifs Actuels**\n\n"
            for t, v in rows:
                unite = "kcal" if t == "calories" else "pas"
                emoji = "🔥" if t == "calories" else "👣"
                msg += f"{emoji} {t.capitalize()} : **{v}** {unite}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        except Exception as e:
            await update.message.reply_text(f"Erreur : {e}")
            return

    # --- CAS CLASSIQUES : HISTORIQUE ---
    table_map = {
        "calories": ("suivi_calories", "kcal", "🔥"),
        "pas": ("suivi_pas", "pas", "👣"),
        "poids": ("suivi_poids", "kg", "📉")
    }

    if categorie in table_map:
        table, unite, emoji = table_map[categorie]
        historique = get_history(table)
        
        if not historique:
            await update.message.reply_text(f"Aucune donnée trouvée pour {categorie} sur les 7 derniers jours.")
            return

        message = f"{emoji} **Historique {categorie.capitalize()}** (7j)\n"
        message += "---------------------------\n"

        for date, valeur in historique:
            valeur_formatee = round(valeur, 1) if categorie == "poids" else int(valeur)
            message += f"📅 {date} : **{valeur_formatee}** {unite}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Catégorie inconnue. Utiliser : calories, pas, poids ou objectifs.")
    
async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # On vérifie qu'on a bien les 2 arguments (catégorie et date)
    if len(context.args) < 2:
        await update.message.reply_text("Usage : /clean [calories/pas/poids] [AAAA-MM-JJ]\nEx: /clean calories 2026-03-15")
        return

    categorie = context.args[0].lower()
    date_saisie = context.args[1]
    
    table_map = {
        "calories": "suivi_calories",
        "pas": "suivi_pas",
        "poids": "suivi_poids"
    }

    if categorie in table_map:
        table = table_map[categorie]
        nb_supprime = delete_by_date(table, date_saisie)
        
        if nb_supprime > 0:
            await update.message.reply_text(f"✅ {nb_supprime} entrée(s) de {categorie} supprimée(s) pour le {date_saisie}.")
        elif nb_supprime == 0:
            await update.message.reply_text(f"ℹ️ Aucune donnée trouvée pour {categorie} à la date du {date_saisie}.")
        else:
            await update.message.reply_text("❌ Erreur lors de la suppression. Vérifie le format de la date (AAAA-MM-JJ).")
    else:
        await update.message.reply_text("Catégorie inconnue. Utiliser : calories, pas ou poids.")
    
async def oups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage : /oups [calories/pas/poids]")
        return
    
    categorie = context.args[0].lower()
    table_map = {
        "calories": "suivi_calories",
        "pas": "suivi_pas",
        "poids": "suivi_poids"
    }

    if categorie in table_map:
        table = table_map[categorie]
        if delete_data(table):
            await update.message.reply_text(f"La dernière entrée de {categorie} a été supprimée.")
        else:
            await update.message.reply_text(f"Aucune donnée à supprimer dans {categorie}.")
    else:
        await update.message.reply_text("Catégorie inconnue. Utiliser : calories, pas ou poids.")

# Fonction pour ajouter mon nombre de calories consommé par jour 
async def calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        valeur = context.args[0]
        if insert_data("suivi_calories", int(valeur)):
            await update.message.reply_text(f"Calories enregistrées : {valeur} kcal !")
        else:
            await update.message.reply_text("Erreur lors de l'enregistrement.")
    else:
        await update.message.reply_text(f"Utiliser la commande comme ça : /cal [nombre] !")

# Fonction pour ajouter mon nombre de pas effectué par jour 
async def pas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        valeur = context.args[0]
        if insert_data("suivi_pas", int(valeur)):
            await update.message.reply_text(f"Pas enregistrés : {valeur} pas !")
        else:
            await update.message.reply_text("Erreur lors de l'enregistrement.")
    else:
        await update.message.reply_text(f"Utiliser la commande comme ça : /pas [nombre] !")

# Fonction pour ajouter mon nombre de calories consommé par jour 
async def poids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        valeur = context.args[0]
        if insert_data("suivi_poids", float(valeur)):
            await update.message.reply_text(f"Poids enregistré : {valeur} kg !")
        else:
                await update.message.reply_text("Erreur lors de l'enregistrement.")
    else:
        await update.message.reply_text(f"Utiliser la commande comme ça : /poids [nombre] !")

# Fonction pour fixer un objectif
async def set_objectif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage : /objectif [calories/pas] [nombre]")
        return

    type_obj = context.args[0].lower()
    valeur = context.args[1]

    if type_obj not in ['calories', 'pas']:
        await update.message.reply_text("Type inconnu. Utilise 'calories' ou 'pas'.")
        return

    try:
        conn = psycopg2.connect(host="db", database="calories_tracker", user="cobrasw3", password="my_password")
        cur = conn.cursor()
        cur.execute("UPDATE objectifs SET valeur = %s WHERE type_objectif = %s", (valeur, type_obj))
        conn.commit()
        cur.close()
        conn.close()
        await update.message.reply_text(f"✅ Objectif {type_obj} mis à jour : {valeur} !")
    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")

async def options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_texte = (
        "🛠 **MENU DES COMMANDES** 🛠\n\n"
        "📥 **Saisie de données :**\n"
        "🔥 `/cal [nombre]` : Enregistrer des calories\n"
        "👣 `/pas [nombre]` : Enregistrer tes pas\n"
        "📉 `/poids [nombre]` : Enregistrer ton poids\n\n"
        
        "🎯 **Objectifs :**\n"
        "🏆 `/objectif [type] [nombre]` : Fixer tes cibles\n"
        "📜 `/info objectifs` : Voir tes cibles actuelles\n\n"
        
        "📊 **Consultation :**\n"
        "📱 `/bilan` : Résumé complet de ta journée\n"
        "📜 `/info [type]` : Historique simple (7j)\n"
        "   _(ex: /info calories, /info pas, /info poids)_\n\n"
        
        "🧹 **Correction & Nettoyage :**\n"
        "🔙 `/oups [type]` : Supprime la toute dernière saisie\n"
        "📅 `/clean [type] [AAAA-MM-JJ]` : Vide une journée précise\n\n"
        
        "❓ `/options` : Afficher ce message"
    )
    
    await update.message.reply_text(menu_texte, parse_mode='Markdown')

if __name__ == '__main__':
    # Construction de l'application
    app = ApplicationBuilder().token(TOKEN).build()
    # Ecouteur pour la commande start
    app.add_handler(CommandHandler('start', start))

    # Ajout des différentes fonctions
    app.add_handler(CommandHandler('options', options))
    app.add_handler(CommandHandler('poids', poids))
    app.add_handler(CommandHandler('pas', pas))
    app.add_handler(CommandHandler('cal', calories))
    app.add_handler(CommandHandler('oups', oups))
    app.add_handler(CommandHandler('bilan', bilan))
    app.add_handler(CommandHandler('clean', clean))
    app.add_handler(CommandHandler('info', info))
    app.add_handler(CommandHandler('objectif', set_objectif))

    # Lancement du bot
    print("Lancement du bot en cours...")
    app.run_polling()
