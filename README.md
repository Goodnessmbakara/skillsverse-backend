# SkillsVerse Backend 🧠💼

A smart job marketplace powered by AI and blockchain. This backend service enables secure job matching, automated job fetching, CV parsing, skill-based recommendations, and verified credential handling.

---

## 🚀 Features

- 🔐 Wallet-based authentication
- 🧾 CV parsing with machine learning
- 🤖 AI-powered job recommendations
- 💼 Job fetching from external APIs
- 🔗 Blockchain-integrated credential verification
- 📧 Optional email verification and job alerts
- 📊 Admin dashboard and job management
- 📝 User activity tracking for smarter suggestions

---

## 🧱 Tech Stack

- **Python 3.11+**
- **Django & Django REST Framework**
- **PostgreSQL**
- **Celery + Redis** for background tasks
- **Docker & Docker Compose**

---

## 🐳 Getting Started with Docker

### 📦 Build the project

```bash
docker-compose build
```

### ▶️ Run the project

```bash
docker-compose up
```

### 🚪 Access the app

- **API Base URL**: `http://localhost:8000/api/`
- **Admin Panel**: `http://localhost:8000/admin/`

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and update with your config:

```bash
cp .env.example .env
```

Update with your DB credentials, secret keys, etc.

---

## ⚙️ Common Commands

### 📚 Run Migrations

```bash
docker-compose exec web python manage.py migrate
```

### 🧪 Run Tests

```bash
docker-compose exec web pytest
```

### 🧑‍💻 Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

---

## 🔧 Services Overview

| Service  | URL                            | Description                     |
|----------|--------------------------------|---------------------------------|
| API      | `http://localhost:8000/api/`   | Core backend REST API           |
| Admin    | `http://localhost:8000/admin/` | Django Admin Panel              |
| Redis    | Internal service               | Message broker for Celery       |
| Celery   | Internal worker                | Background job handling         |

---

## 📁 Project Structure

```
skillsverse-backend/
├── jobs/              # Job models, APIs, and fetchers
├── users/             # Custom user model and logic
├── cv_parser/         # CV processing and ML integration
├── recommendations/   # AI/ML recommendation engine
├── credentials/       # Blockchain verification module
├── config/            # Django settings and routing
├── docker/            # Docker and entrypoint configs
├── manage.py
└── requirements.txt
```

---

## 📩 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## 📜 License

MIT License © 2025 Ui-ubak Engineering Services Ltd.
