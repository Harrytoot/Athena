---
id: ADR-010
title: Athena Brain Introduction
status: Approved
version: 1.0.0
owner: Chief Architect
reviewer: Founder
created: 2026-06-24
depends:
  - ADR-002
  - ADR-003
---

# ADR-010 Athena Brain Introduction

## Status

Approved

---

# Context

Athena 是一个 AI 驱动的投资操作系统。随着 AI Agent 和人类开发者持续加入，项目面临核心挑战：

**上下文丢失。**

每次新 AI 会话启动时，ChatGPT / Claude 等 AI 的记忆是空的。每个新开发者加入时，对项目的理解依赖口头传递。每次决策后的推理链，往往只留在当时的聊天记录里。

这导致：

1. AI 每次都要重新理解项目
2. 开发者入职成本高昂
3. 关键决策的推理链无法追溯
4. 知识资产无法积累
5. 项目完全依赖人的记忆

这些问题通过建立正式的长期知识操作系统来解决。

---

# Decision

引入 **Athena Brain** 作为项目唯一的长期知识载体。

---

## Why Athena Brain Exists

Athena Brain 的存在基于以下原则：

### 1. 项目知识不应依赖 AI 对话记忆

AI 的每一次会话都是无状态的。聊天记录虽然是持久的，但：

- 难以结构化检索
- 推理链分散在多个会话中
- 无法按域分类
- 无法建立引用关系

Athena Brain 提供结构化、可检索、可引用的知识存储。

### 2. AI 和人类需要共享同一套知识体系

如果 AI 读取聊天记录，人类读取文档，两者无法对齐。Athena Brain 是 AI 和人类的共同上下文。

### 3. 知识需要生命周期管理

聊天记录中的"结论"一旦形成就静止了。但市场会变，知识会过期。Athena Brain 提供完整生命周期：

```
Idea → Hypothesis → Experiment → Validated → Knowledge → Playbook → Decision Engine
```

每一步都有明确的进入和退出标准。

---

## Why Knowledge, Research, and Code Are Separated

Athena 强制分离三个层次：

| 层级 | 载体 | 变更速度 | 可信度要求 | 决策引用 |
|------|------|----------|------------|----------|
| Code | Git Repository | 高频 | 通过 CI/审查即可 | — |
| Research | docs/brain/02-research/ | 中频 | 需要 Peer Review | 否 |
| Knowledge | docs/brain/01-knowledge/ | 低频 | 需要 Approval | 是（通过 Playbook） |

### 分离的理由

1. **防止"代码即策略"反模式**

   如果投资结论直接写入代码（例如 `if rsi < 30: buy()`），则：
   - 无法追溯该结论的来源
   - 无法评估置信度
   - 无法对比替代方案
   - 修改只能靠改代码，失去治理

2. **不同的审查标准**

   - Code 审查：逻辑正确 + 风格一致 + 测试通过
   - Research 审查：方法论正确 + 证据充分 + 结论合理
   - Knowledge 审查：多研究交叉验证 + 置信度高 + 长期有效

   三者需要的 Reviewer 和审批流程完全不同。

3. **不同生命周期**

   - Code 每次 Sprint 都在变化
   - Research 可能持续数月
   - Knowledge 可能持续数年

4. **可追溯性**

   任何决策都可以通过以下链路追溯：

   ```
   Decision Engine (执行决策)
     → Playbook (行动方案)
       → Knowledge (已验证结论)
         → Research (研究过程)
           → Evidence (原始数据)
   ```

### 治理规则（来自 BRAIN-001）

1. 任何长期投资结论不得直接进入代码
2. 任何长期投资结论必须先形成 Research
3. Research 必须有 Evidence
4. Evidence 必须可追溯
5. Playbook 必须引用 Knowledge
6. Decision Engine 必须引用 Playbook

---

## Athena Brain 目录结构

```
docs/brain/
├── README.md                        # Brain 总览
├── BRAIN-001-*.md                   # Brain 治理文档
├── 00-constitution/                 # Layer 0: 长期原则
├── 01-knowledge/                    # Layer 1: 已验证知识
│   ├── market/
│   ├── macro/
│   ├── industry/
│   ├── factor/
│   ├── policy/
│   ├── sentiment/
│   ├── execution/
│   └── ontology/
├── 02-research/                     # Layer 2: 研究课题
├── 03-experiments/                  # Layer 3: 可复现实验
├── 04-failures/                     # Layer 4: 失败记录
├── 05-playbooks/                    # Layer 5: 投资行动方案
├── 06-evidence/                     # 原始证据
├── 07-decisions/                    # 决策记录
└── 08-glossary/                     # 领域术语
```

---

## AI Onboarding

任何 AI Agent 或开发者加入项目时，按顺序阅读：

1. Constitution（00-constitution/）
2. ADR（../adr/）
3. Athena Brain（docs/brain/README.md）
4. Research（02-research/）
5. Playbooks（05-playbooks/）

完成后方可参与开发或决策。

---

## Future Migration Plan

### 当前阶段（Sprint 1）

Athena Brain 作为 `docs/brain/` 子目录存在，随主仓库版本控制。

### 中期（未来）

如果知识资产增长到影响主仓库性能：

- 可能将 `docs/brain/` 拆分为独立 Git 仓库
- 通过 Git Submodule 或专用工具（如 ATLAS）集成
- 维持相同的治理规则和引用链路

迁移决策需要单独的 ADR。

### 长期（未来）

可能建立 Athena Brain 专用服务：

- API 接口用于知识检索
- 知识图谱可视化
- 自动过期提醒
- AI Agent 集成接口

---

# Consequences

## 正面

- 知识资产可积累、可追溯、可审查
- 新成员（AI 和人类）可快速恢复完整上下文
- 决策推理链完整可查
- 代码不承载策略结论，降低耦合

## 负面

- 引入额外的文档编写和维护成本
- 知识流程增加了决策延迟
- 需要建立 Review 流程（Research → Knowledge → Playbook）

## 缓解措施

- 不是所有想法都需要走完整流程：只有"长期有效的投资结论"才需要
- 快速探索可以在 Research (Draft) 级别进行，不强制审批
- 文档模板和 Checklist 降低编写成本

---

# Acceptance

Athena Brain 正式引入，作为项目长期知识操作系统。

`docs/brain/` 目录结构冻结，新增子目录需 ADR。
