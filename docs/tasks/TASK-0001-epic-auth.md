---
id: TASK-0001
title: Epic-001 Authentication
epic: Authentication
status: Pending
priority: High
dependencies:
  - ADR-001
  - RFC-001
---

# TASK-0001 Epic-001 Authentication

## Goal

完成基础认证能力：Login / Logout / JWT / Refresh Token（预留）/ User Profile。

## Domain

User

## Tasks

### Backend

- [ ] 创建 User 实体 (domain/entities/user.py)
- [ ] 创建 UserRepository 接口 (domain/repositories/user_repository.py)
- [ ] 创建 SQLAlchemy User Model (infrastructure/persistence/models/user.py)
- [ ] 创建 UserRepositoryImpl (infrastructure/persistence/repositories/user_repository_impl.py)
- [ ] 创建 AuthService (application/services/auth_service.py)
- [ ] 创建 JWT 工具类 (infrastructure/auth/jwt.py)
- [ ] 创建 POST /api/v1/auth/login 接口
- [ ] 创建 GET /api/v1/auth/me (User Profile) 接口
- [ ] 创建 Refresh Token 端点（预留）
- [ ] 数据库迁移：users 表
- [ ] 单元测试

### Frontend

- [ ] 创建 Login 页面
- [ ] 创建全局 AuthProvider / AuthContext
- [ ] 创建登录/登出逻辑
- [ ] 创建 JWT 存储与自动附带
- [ ] 创建路由守卫（未登录跳转登录页）
- [ ] 创建 User Profile 展示组件

## Acceptance Criteria

- POST /api/v1/auth/login 返回 JWT
- JWT 过期后拒绝访问
- 登录后可以获取 User Profile
- 前端未登录自动跳转 /login
- 前端登录后持久化 Token

## References

- [RFC-001](../rfc/RFC-001-sprint-1-foundation-development-plan.md)
- [ADR-001](../adr/ADR-001-sprint-1-tech-stack-freeze.md)
