# TPE Manager — Backend

Application de gestion pour TPE et auto-entrepreneurs marocains : devis, factures, trésorerie, scoring de crédit et notifications automatisées, via une API REST développée avec Django REST Framework.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Stack technique](#stack-technique)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Lancer le projet](#lancer-le-projet)
- [Tâches planifiées](#tâches-planifiées)
- [Structure du projet](#structure-du-projet)

## Fonctionnalités

- **Authentification** — Inscription, connexion, réinitialisation de mot de passe par code envoyé par email, JWT avec liste noire de tokens (logout sécurisé)
- **Devis & Factures** — Cycle de vie complet (Brouillon → Envoyé → Accepté/Refusé/Expiré), génération PDF via WeasyPrint
- **Trésorerie (Cashflow)** — Suivi des flux financiers de l'entreprise
- **Crédit** — Système de scoring d'éligibilité au crédit (statuts VERT / ORANGE / ROUGE)
- **Notifications multi-canal** — Envoi automatique par Email, SMS (Twilio) et Push (Firebase Cloud Messaging) :
  - Rappels de factures impayées
  - Rappels de devis arrivant à expiration
  - Rappels de déclaration fiscale (TVA)
  - Rappels de cotisation CNSS
- **Email personnalisé par vendeur** — Chaque utilisateur peut configurer sa propre adresse email SMTP pour que ses relances clients partent en son nom propre

## Stack technique

| Composant | Technologie |
|---|---|
| Framework API | Django REST Framework |
| Authentification | JWT (`rest_framework_simplejwt`) |
| Base de données | PostgreSQL |
| Broker / Cache | Redis |
| Tâches asynchrones | Celery + Celery Beat |
| Génération PDF | WeasyPrint |
| SMS | Twilio |
| Notifications Push | Firebase Cloud Messaging (FCM) |
| Documentation API | drf-spectacular (OpenAPI) |
| Conteneurisation | Docker / Docker Compose |

## Architecture

Le projet est organisé en applications Django modulaires :

```
apps/
├── users/           # Authentification, profils, configuration email
├── devis/           # Gestion des devis
├── billing/          # Gestion des factures
├── cashflow/        # Suivi de trésorerie
├── credit/          # Scoring et demandes de crédit
├── notifications/   # Notifications email / SMS / push + tâches Celery
└── clients/         # Gestion des clients des vendeurs
```

Les tâches planifiées (rappels automatiques) sont gérées par **Celery Beat** et exécutées par des workers **Celery**, avec **Redis** comme broker de messages.

## Installation

### Prérequis

- Docker et Docker Compose installés
- Un compte Twilio (pour les SMS)
- Un compte Firebase (pour les notifications push)
- Un compte Gmail avec mot de passe d'application (pour les emails système)

### Cloner le projet

```bash
git clone https://github.com/fatima-aitoulahyan/tpe-manager-backend.git
cd tpe-manager-backend
```

## Configuration

1. Copier le fichier d'exemple d'environnement :

```bash
cp .env.example .env
```

2. Remplir les variables dans `.env` :

```env
SECRET_KEY=
DEBUG=True

DB_NAME=tpe_db
DB_USER=tpe_admin
DB_PASSWORD=
DB_HOST=db
DB_PORT=5432

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_MESSAGING_SERVICE_SID=

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
```

3. Placer les identifiants Firebase (fichier de compte de service) dans :

```
config/firebase-credentials.json
```

## Lancer le projet

```bash
docker compose up --build
```

Cela démarre les services suivants :

| Service | Rôle | Port |
|---|---|---|
| `db` | Base de données PostgreSQL | 5432 |
| `redis` | Broker Celery | 6379 |
| `web` | API Django | 8000 |
| `celery_worker` | Traitement des tâches asynchrones | — |
| `celery_beat` | Planificateur de tâches périodiques | — |

Appliquer les migrations (première utilisation) :

```bash
docker compose exec web python manage.py migrate
```

Créer un superutilisateur (accès admin Django) :

```bash
docker compose exec web python manage.py createsuperuser
```

L'API est accessible sur `http://localhost:8000/`, et la documentation OpenAPI sur `http://localhost:8000/api/schema/swagger-ui/` (selon la configuration des URLs).

## Tâches planifiées

Les rappels automatiques sont exécutés quotidiennement (heure Maroc, `Africa/Casablanca`) :

| Tâche | Description |
|---|---|
| `rappel_factures_impayees` | Relance les factures arrivées à échéance |
| `rappel_devis_expirants` | Relance les devis proches de leur date de validité |
| `rappel_declaration_fiscale` | Rappel de déclaration TVA trimestrielle |
| `rappel_cotisation_cnss` | Rappel de cotisation CNSS mensuelle |

Chaque notification est envoyée selon les préférences de canal du vendeur (Email / SMS / Push / In-app), configurables via l'API `PreferencesNotification`.

## Structure du projet

```
tpe_backend/
├── apps/                  # Applications métier
├── config/                # Fichiers de configuration sensibles (Firebase, etc.)
├── core/                  # Settings Django, Celery, URLs racine
├── templates/             # Templates HTML 
├── media/                 # Fichiers médias uploadés
├── utils/                 # Utilitaires partagés (ex: génération PDF)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
```
