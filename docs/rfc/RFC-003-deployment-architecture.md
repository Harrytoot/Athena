---
id: RFC-003
title: Athena Deployment Architecture
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
depends:
  - ADR-001
  - ADR-009
---

# RFC-003 Deployment Architecture

## Background

Founder 已拥有一台腾讯云 Linux 服务器，服务器当前已有一个生产服务正在运行。

Athena 必须与现有服务长期共存，不允许影响现有业务。

---

# Deployment Principle

Athena 必须采用 Docker Compose 独立部署，不得直接安装运行环境。

所有服务均运行于 Docker Network。

---

# Reverse Proxy

统一由 Nginx 管理，Athena 不直接监听公网。

```
Nginx → Athena Frontend (3000)
      → Athena Backend (8000)
```

---

# URL Strategy

第一阶段采用路径区分：

| 路径 | 目标 |
|------|------|
| `https://example.com/` | 现有系统 |
| `https://example.com/athena/` | Athena 前端 |
| `https://example.com/athena/api/` | Athena API |
| `https://example.com/athena/docs` | Swagger |
| `https://example.com/athena/health` | Health Check |

第二阶段可选切换 `https://athena.example.com`，无需修改业务代码。

---

# Docker

Athena 使用独立 Compose，不与现有 Compose 冲突。

内部端口：Frontend 3000, Backend 8000, PostgreSQL 5432 (容器), Redis 6379 (容器), MinIO 9000 (容器)。

所有容器除 Frontend、Backend 外默认不暴露公网端口。

---

# Environment

- `.env.production` — 生产环境
- `.env.staging` — 预发布环境
- 所有敏感配置必须来自环境变量
- 禁止提交真实密钥

---

# Deployment Scripts

`infra/scripts/`:
- `deploy.sh` — 一键部署
- `rollback.sh` — 回滚
- `backup.sh` — 数据库 + MinIO 备份
- `healthcheck.sh` — 健康检查

---

# Backup

- PostgreSQL: 每日自动备份，保留 30 天
- MinIO: 每日同步备份，保留 30 天

---

# Security

生产环境必须：HTTPS, Security Headers, Gzip/Brotli, Rate Limit (API), CORS 白名单, 非 Root 运行容器。

---

# CI/CD

保持 GitHub Actions。新增 Production Deploy Workflow，支持人工审批后部署，禁止自动推送生产。

---

# Acceptance

Athena 能够与现有服务长期共存。部署、升级、回滚互不影响。

Note: auto-renumbered to RFC-003 to avoid conflict with existing RFC-002 (12-Repository Architecture).
