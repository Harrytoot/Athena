# Athena Brain

> 项目唯一的长期知识操作系统。

## Overview

Athena Brain 是 Athena 项目的长期知识载体。任何 AI、任何开发者，都应通过 Athena Brain 恢复项目上下文，而不是依赖聊天记录或个人记忆。

治理文档：[BRAIN-001 Athena Brain Governance](./BRAIN-001-athena-brain-governance.md)

## Directory Map

| 目录 | 层级 | 说明 |
|------|------|------|
| [00-constitution/](./00-constitution/) | Layer 0 | 长期稳定原则 |
| [01-knowledge/](./01-knowledge/) | Layer 1 | 已验证知识 |
| [02-research/](./02-research/) | Layer 2 | 研究课题 |
| [03-experiments/](./03-experiments/) | Layer 3 | 可复现实验 |
| [04-failures/](./04-failures/) | Layer 4 | 失败记录 |
| [05-playbooks/](./05-playbooks/) | Layer 5 | 投资行动方案 |
| [06-evidence/](./06-evidence/) | — | 原始证据 |
| [07-decisions/](./07-decisions/) | — | 决策记录 |
| [08-glossary/](./08-glossary/) | — | 领域术语 |

## Knowledge State Machine

```
Idea → Hypothesis → Experiment → Validated → Knowledge → Playbook → Decision Engine
```

## Governance Rules (from BRAIN-001)

1. 任何长期投资结论不得直接进入代码
2. 任何长期投资结论必须先形成 Research
3. Research 必须有 Evidence
4. Evidence 必须可追溯
5. Playbook 必须引用 Knowledge
6. Decision Engine 必须引用 Playbook
7. 每条 Knowledge 必须记录 Confidence（0~100）

## Onboarding

新成员加入项目时，必须按顺序阅读：

1. Constitution (00-constitution/)
2. ADR (../adr/)
3. Athena Brain (本目录)
4. Research (02-research/)
5. Playbooks (05-playbooks/)
