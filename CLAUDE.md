# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Система учёта квот СПО (Secondary Professional Education Quota Management System) — веб-приложение для контроля набора студентов по квотированным специальностям в учреждениях среднего профессионального образования.

**Ключевое ограничение:** номер аттестата глобально уникален — один человек может быть записан только в одно место во всей системе.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL, JWT auth
- **Frontend:** Vue 3 (Composition API), Vite, Pinia, Vue Router, Axios
- **Infrastructure:** Docker Compose, Nginx reverse proxy

## Commands

### Full Stack (Docker)
```bash
# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart specific service
docker-compose restart backend

# Stop all
docker-compose down
```

## Architecture

### Backend Structure (`backend/app/`)
```
main.py          # FastAPI app, lifespan events, CORS, routers
core/
  config.py      # Settings from environment variables
  database.py    # SQLAlchemy engine and session
  security.py    # JWT tokens, password hashing (bcrypt)
models/          # SQLAlchemy ORM models
  user.py        # User with UserRole enum (admin/operator)
  spo.py         # Educational institution
  specialty.py   # Specialty with quota
  student.py     # Student with globally unique attestat_number
  settings.py    # Key-value settings (base_quota)
schemas/         # Pydantic request/response schemas
services/
  user_service.py      # Operator creation, login generation, auth
  settings_service.py  # Base quota management
api/
  deps.py        # Dependencies: get_db, get_current_user, get_current_admin
  auth.py        # POST /api/auth/login, GET /api/auth/me
  admin.py       # CRUD for SPO, operators, quotas (admin only)
  operator.py    # CRUD for specialties, students (operator's SPO only)
  stats.py       # Statistics (admin sees all, operator sees own SPO)
```

### Frontend Structure (`frontend/src/`)
```
api/             # Axios API clients (auth, admin, operator, stats)
stores/auth.js   # Pinia store: user, token, login/logout
router/index.js  # Routes with role-based guards
views/
  admin/         # AdminDashboard, SpoList, OperatorList, QuotaSettings, AdminStats
  operator/      # OperatorDashboard, SpecialtyList, StudentList, OperatorStats
components/
  ui/            # Reusable: AppButton, AppInput, AppSelect, AppTable, AppModal
  forms/         # SpoForm, OperatorForm, SpecialtyForm, StudentForm
  AppLayout.vue  # Main layout with role-based navigation
```

### API Endpoints
| Endpoint | Role | Description |
|----------|------|-------------|
| `POST /api/auth/login` | Public | Returns JWT token |
| `GET /api/auth/me` | Auth | Current user info |
| `GET/POST /api/admin/spo` | Admin | List/create SPO |
| `GET/POST /api/admin/operators` | Admin | List/create operators (returns generated credentials) |
| `PUT /api/admin/specialties/{id}/quota` | Admin | Update specialty quota |
| `GET/PUT /api/admin/settings` | Admin | Base quota settings |
| `GET/POST /api/specialties` | Operator | Own SPO specialties |
| `GET/POST /api/students` | Operator | Own SPO students |
| `GET /api/stats` | Auth | Statistics (filtered by role) |


## Data Model Relationships

```
SPO (1) ──< Specialty (M) ──< Student (M)
SPO (1) ──< User/Operator (M)

User.role: admin | operator
User.spo_id: null for admin, required for operator
Student.attestat_number: UNIQUE globally
```

## Access Control

- **Admin:** Creates SPO, generates operator credentials (login auto-generated from SPO name), manages quotas, sees all statistics
- **Operator:** Works only with own SPO — adds specialties, records students, sees own statistics

## Port Configuration

- Nginx: `9010` (external access point)
- Backend: `8000` (internal)
- Frontend: `3000` (internal, Vite dev server)
- PostgreSQL: `5432` (internal)
