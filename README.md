# Athena

AI-powered investment operating system — Sprint 1 (Foundation)

## Tech Stack

See [ADR-001](docs/adr/ADR-001-sprint-1-tech-stack-freeze.md).

## Principles

- Documentation First
- Plugin Architecture
- Domain-Driven Design
- Extensible
- Testable

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12 (for local dev)
- Node.js 20 (for local dev)

### Option 1: Docker Compose (Recommended)

```bash
docker compose up -d
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

### Option 2: Local Development

**Backend:**
```bash
cd src/backend
cp .env.example .env  # edit if needed
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd src/frontend
npm install
npm run dev
```

### Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

## Production Deployment

### Prerequisites

- Linux server with Docker & Docker Compose
- Existing Nginx reverse proxy
- Git

### Setup

```bash
git clone <repo-url> /opt/athena
cd /opt/athena

# Configure environment
cp .env.example .env.production
# Edit .env.production with secure passwords

# Deploy
./infra/scripts/deploy.sh
```

### Nginx Integration

Add to your existing Nginx config:

```nginx
location /athena/ {
    include /opt/athena/infra/nginx/athena.conf;
}
```

### Backup

```bash
./infra/scripts/backup.sh  # Daily cron
```

### Rollback

```bash
./infra/scripts/rollback.sh <commit-hash>
```

### Health Check

```bash
./infra/scripts/healthcheck.sh
```

See [RFC-003 Deployment Architecture](docs/rfc/RFC-003-deployment-architecture.md) for full details.

## Docs Index

| 目录 | 说明 |
|------|------|
| [AMS](docs/ams/) | Master Specification |
| [ADR](docs/adr/) | Architecture Decision Records |
| [RFC](docs/rfc/) | Request for Comments |
| [AES](docs/aes/) | Architecture Evolution Strategy |
| [PRD](docs/prd/) | Product Requirements |
| [API](docs/api/) | API Specifications |
| [Database](docs/database/) | Database Design |
| [Glossary](docs/glossary/) | Domain Glossary |
| [Engineering Standard](docs/engineering/) | Coding & Naming Standards |
| [Architecture Repository](docs/ARCHITECTURE_REPOSITORY.md) | Master Index |

## Sprint Status

See [SPRINT_STATUS.md](docs/roadmap/SPRINT_STATUS.md)
