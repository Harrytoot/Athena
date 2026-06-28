---
id: FRONTEND-001
title: Sprint 1 Frontend Technical Specification
status: Approved
version: 1.1.0
owner: Chief Architect
created: 2026-06-24
updated: 2026-06-28
depends:
  - ADR-001
  - RFC-001
  - API-001
---

# FRONTEND-001 Sprint 1 Frontend Technical Specification

## Status

Approved. Updated 2026-06-28 — 补齐 7 项缺失基础设施建设。

---

## 1. Technology Stack

| 层级 | 选型 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Next.js (App Router) | 14.2 | SSR/RSC + 客户端渲染 |
| UI 库 | React | 18.3 | 组件化 UI |
| 语言 | TypeScript | 5.4 | strict 模式，全量类型覆盖 |
| 样式 | Tailwind CSS + shadcn/ui | 3.4 / default | 原子化样式 + 组件基座 |
| 图表 | lightweight-charts | 5.2 | K 线 / 权益曲线 |
| 图表 | ECharts + echarts-for-react | 6.1 / 3.0 | 雷达图 / 复杂图表 |
| 流程图 | @xyflow/react (ReactFlow) | 12.11 | 可视化策略编辑器 |
| 状态管理 | Zustand | 5.0 | 策略图 / 执行面板 / 决策数据 |
| HTTP 客户端 | axios | 1.7 | 全局拦截器（Token 注入 / 401 处理） |
| 数据缓存 | @tanstack/react-query | 5.51 | 服务端状态缓存与同步 |
| 动画 | framer-motion | 12.42 | 组件进出动画 |
| 图标 | lucide-react | 0.378 | 全量 SVG 图标 |
| i18n | 自研 Provider + Context | — | 中/英双语，localStorage 持久化 |
| 测试 | Vitest + Testing Library | 1.6 / 16.0 | 单元测试 + 组件测试 |

### Dev Dependencies

| 工具 | 版本 | 用途 |
|------|------|------|
| ESLint | 8.57 (next/core-web-vitals) | 代码规范 |
| Prettier | 3.3 | 代码格式化 |
| Vitest | 1.6 | 测试运行器 |
| @testing-library/react | 16.0 | 组件渲染测试 |
| @testing-library/jest-dom | 6.4 | DOM 断言扩展 |
| jsdom | 24.0 | 浏览器环境模拟 |
| @vitejs/plugin-react | 4.3 | Vitest React 转译 |

---

## 2. Project Structure

```
src/frontend/
├── app/                          # Next.js App Router
│   ├── globals.css               # 全局样式 + Tailwind + CSS 变量
│   ├── layout.tsx                # 根布局（含 Providers 包裹）
│   ├── page.tsx                  # "/" → redirect("/dashboard")
│   │
│   ├── dashboard/page.tsx        # 市场概览仪表盘 [RSC]
│   ├── market/page.tsx           # 市场页 [同 dashboard]
│   ├── login/page.tsx            # 登录 [Client]
│   ├── register/page.tsx         # 注册 [Client]
│   ├── watchlist/page.tsx        # 自选股管理 [Client]
│   ├── portfolio/page.tsx        # 持仓管理 [Client]
│   ├── recommendation/page.tsx   # 投资建议 [Client]
│   ├── strategy/page.tsx         # 策略构建器 (ReactFlow) [Client]
│   ├── backtest/page.tsx         # 回测报告 [Client]
│   └── stocks/[symbol]/          # 个股详情 [RSC + Client Islands]
│       ├── page.tsx
│       ├── StockChartPanel.tsx
│       └── DetailDataPanel.tsx
│
├── components/
│   ├── Providers.tsx             # ErrorBoundary + Query + I18n 三层包裹
│   ├── ErrorBoundary.tsx         # 全局错误边界（Class Component）
│   ├── UserMenu.tsx              # 登录/登出（含 useAuth）
│   │
│   ├── charts/                   # 图表组件
│   │   ├── LightweightChart.tsx  # K 线图 (MA/MACD/买卖标记)
│   │   ├── EquityChart.tsx       # 权益曲线
│   │   └── BacktestMetricsCharts.tsx  # 雷达图
│   │
│   ├── decision/                 # 决策中心子组件
│   │   ├── DecisionCenter.tsx    # 编排器
│   │   ├── SignalConsensusPanel.tsx  # 置信度环 + 信号
│   │   ├── RiskSummaryPanel.tsx  # 共识与风险
│   │   ├── ScenarioPanel.tsx     # 牛/基/熊场景
│   │   └── ActionPanel.tsx       # APPROVE/HOLD/REJECT
│   │
│   ├── execution/
│   │   └── ExecutionSheet.tsx    # 纸交易侧滑面板
│   │
│   ├── strategy/                 # 策略构建器
│   │   ├── StrategyNode.tsx      # 自定义 ReactFlow 节点
│   │   ├── NodeLibrary.tsx       # 节点模板拖拽面板
│   │   ├── InspectorPanel.tsx    # 节点属性编辑面板
│   │   └── types.ts             # 节点类型 / 模板 / 兼容性验证
│   │
│   └── ui/                       # shadcn/ui + 业务组件
│       ├── button.tsx, card.tsx, dialog.tsx   # shadcn 基础
│       ├── drawer.tsx, sheet.tsx              # shadcn 面板
│       ├── slider.tsx, tabs.tsx               # shadcn 交互
│       ├── StockSearch.tsx       # 股票搜索自动补全
│       ├── GroupSidebar.tsx      # 自选股分组侧栏
│       ├── IndexCard.tsx         # 指数卡片
│       ├── MarketTemperatureGauge.tsx  # 市场温度 SVG 仪表盘
│       ├── MarketRegimeBadge.tsx # 牛/熊/震荡徽章
│       ├── MarketStatsRow.tsx    # 成交额/涨跌/北向统计
│       ├── HotSectorList.tsx     # 行业/概念排行
│       ├── AiMarketSummaryCard.tsx  # AI 市场摘要
│       ├── AiSummaryCard.tsx     # AI 个股分析
│       ├── MoneyFlowCard.tsx     # 资金流向
│       ├── TechnicalCard.tsx     # 技术指标网格
│       └── UpdateTimeLabel.tsx   # 数据更新标签
│
├── hooks/                        # 自定义 Hooks
│   ├── useAuth.ts               # 认证状态（login/register/logout/token）
│   ├── useDebounce.ts           # 通用防抖
│   ├── useLocalStorage.ts       # SSR-safe localStorage
│   ├── useStockSearch.ts        # 股票搜索（内置防抖）
│   └── useAsync.ts             # 通用异步操作封装
│
├── lib/                          # 工具与客户端
│   ├── utils.ts                 # cn() — clsx + tailwind-merge
│   ├── http-client.ts           # axios 实例（拦截器 + Token 管理）
│   ├── query-provider.tsx       # React Query 提供者
│   ├── auth.ts                  # 认证 API（login/register/getMe）
│   ├── api.ts                   # 核心 API（市场/股票/决策）
│   ├── watchlist-api.ts         # 自选股 CRUD
│   ├── portfolio-api.ts         # 持仓 CRUD
│   ├── recommendation-api.ts    # 投资建议 API
│   ├── execution-api.ts         # 执行预览/纸交易
│   ├── backtest-api.ts          # 回测 API
│   ├── mock-kline.ts            # Mock K 线生成器
│   └── i18n/
│       ├── translations.ts      # 中/英全量翻译字典
│       └── I18nProvider.tsx     # 语言切换 Context + Provider
│
├── stores/                      # Zustand 状态管理
│   ├── strategy-store.ts        # 策略图（nodes/edges/selection）
│   ├── execution-store.ts       # 执行面板（order/size/preview）
│   └── decision-store.ts        # 决策数据缓存
│
├── types/                       # TypeScript 类型定义
│   ├── auth.ts                  # TokenResponse, UserResponse
│   ├── backtest.ts             # BacktestResult, PeriodMetrics, EquityPoint
│   ├── decision.ts             # DecisionDTO, Signal, Action, ScenarioEntry
│   ├── execution.ts            # OrderType, TradeSide, ExecutionSheetContext
│   ├── market.ts               # IndexData, DashboardSummary, HotItem
│   ├── portfolio.ts            # PortfolioDTO, PositionDTO
│   ├── recommendation.ts       # RecommendationDTO
│   ├── stock.ts                # StockDetail, TechnicalIndicators, MoneyFlow
│   └── watchlist.ts            # Watchlist, WatchlistItem, StockSearchResult
│
├── __tests__/                   # 测试文件
│   ├── lib/utils.test.ts        # cn() 工具函数 (5 cases)
│   ├── hooks/useDebounce.test.ts  # 防抖 Hook (3 cases)
│   └── components/ErrorBoundary.test.tsx  # 错误边界 (4 cases)
│
├── public/                      # 静态资源
├── Dockerfile                   # 多阶段构建 (node:20-alpine)
├── next.config.mjs              # Next.js 配置
├── tsconfig.json                # TypeScript 配置
├── tailwind.config.ts           # Tailwind + CSS 变量 + 交易色
├── postcss.config.js            # PostCSS
├── vitest.config.ts             # Vitest 配置
├── vitest.setup.ts              # Vitest setup
├── components.json              # shadcn/ui 配置
├── .eslintrc.json               # ESLint 配置
├── .prettierrc                  # Prettier 配置
├── .prettierignore              # Prettier 排除
└── package.json                 # 依赖 + 脚本
```

---

## 3. Routing Design

| Route | Render Mode | Page Component | Description |
|-------|------------|----------------|-------------|
| `/` | RSC | `app/page.tsx` | redirect("/dashboard") |
| `/dashboard` | RSC | `app/dashboard/page.tsx` | 市场概览仪表盘 |
| `/market` | RSC | `app/market/page.tsx` | 市场页（与 dashboard 相同） |
| `/stocks/[symbol]` | RSC + Client Island | `app/stocks/[symbol]/page.tsx` | 个股详情（含图表 + 决策中心） |
| `/watchlist` | Client | `app/watchlist/page.tsx` | 自选股分组管理 |
| `/portfolio` | Client | `app/portfolio/page.tsx` | 持仓组合管理 |
| `/recommendation` | Client | `app/recommendation/page.tsx` | 投资建议列表 |
| `/strategy` | Client | `app/strategy/page.tsx` | 可视化策略构建器 |
| `/backtest` | Client | `app/backtest/page.tsx` | 回测报告 |
| `/login` | Client | `app/login/page.tsx` | 登录表单 |
| `/register` | Client | `app/register/page.tsx` | 注册表单 |

### 渲染策略

- **RSC (Server Components)**: 数据密集型页面（dashboard/market/stocks），async 函数直接 fetch，零 JS 传输
- **Client Components**: 交互密集型页面（watchlist/portfolio/strategy/backtest/login），`"use client"` 标记
- **Client Islands**: 个股详情页的图表和决策面板是客户端"岛屿"，嵌入 RSC 页面

### 路由守卫

当前无 middleware 路由守卫。所有页面可直接访问。认证仅通过 API 层 Token 校验，未登录时 API 调用返回 401 并自动重定向到 `/login`（由 axios 拦截器处理）。

---

## 4. Component Architecture

### 4.1 Provider Hierarchy

```
<html lang="zh-CN" class="dark">
  <body>
    <Providers>                    ← components/Providers.tsx
      ├── ErrorBoundary            ← 全局错误捕获
      │   ├── QueryProvider        ← react-query 缓存层
      │   │   └── I18nProvider     ← 国际化上下文
      │   │       ├── Sidebar      ← 侧边导航 + UserMenu
      │   │       └── <main>children</main>
```

### 4.2 Sidebar Navigation

固定在 `w-56` 侧栏，含 9 个导航项：
- 7 个启用：Dashboard(📊), Market(📈), Watchlist(⭐), Portfolio(💼), Recommend(💡), Strategy(⚙️), Backtest(⏪)
- 2 个禁用占位：AI Center(🤖), Settings(⚡)

底部含 UserMenu，根据登录状态显示"退出"或"登录"按钮。

### 4.3 Decision Center (个股详情子组件)

5 个子组件组成的编排面板：
1. **SignalConsensusPanel** — SVG 置信度环 + STRONG_BUY~STRONG_SELL 信号 + 股票代码
2. **RiskSummaryPanel** — 共识摘要 + 风险项列表（带严重度颜色）
3. **ScenarioPanel** — 牛/基/熊三种情景柱状对比图
4. **ActionPanel** — APPROVE/HOLD/REJECT 按钮，点击打开 ExecutionSheet
5. **DecisionCenter** — 编排器，组合上述 4 个子组件

### 4.4 Strategy Builder (ReactFlow)

- **NodeLibrary**: 可折叠拖拽面板，8 种节点模板（数据源/选股/择时/风控/组合/信号/执行/回测）
- **StrategyNode**: 自定义 ReactFlow 节点渲染器（颜色编码 + Handle 端口）
- **InspectorPanel**: 侧滑属性编辑器（framer-motion 动画）
- **Handle 兼容性验证**: 输入/输出端口类型匹配检查

### 4.5 Execution Sheet

纸交易侧滑面板（Radix Dialog 实现）：
- 订单类型：MARKET / LIMIT / TWAP / VWAP
- 交易方向：BUY / SELL
- 智能委托参数（TWAP 时间片 / VWAP 参与率）
- 异步执行预览（费用/滑点/填充率估算）
- 提交状态流（preview → submit → loading → result）

---

## 5. State Management

采用 **Zustand v5** 管理 3 个独立 Store，无 Context 冗余：

### 5.1 useStrategyStore

```typescript
interface StrategyStore {
  nodes: Node<StrategyNodeData>[];     // ReactFlow 节点列表
  edges: Edge[];                       // 连接边列表
  selectedNodeId: string | null;       // 当前选中节点

  onNodesChange, onEdgesChange;        // ReactFlow 内置变化处理
  onConnect(connection);               // 边连接 + Handle 验证
  addNode(category, type, ...);        // 新增节点（自动位置偏移）
  updateNodeProperties(id, props);     // Inspector 面板属性更新
  removeNode(id);                      // 节点 + 关联边删除
}
```

### 5.2 useExecutionStore

```typescript
interface ExecutionStore {
  isSheetOpen: boolean;
  sheetContext: ExecutionSheetContext;  // { symbol, name, price, action }
  orderType: "MARKET" | "LIMIT" | "TWAP" | "VWAP";
  size: number;                        // 委托数量
  algoParams: AlgoParams;
  preview: ExecutionPreviewResponse | null;
  previewLoading: boolean;
  submitting: boolean;
  submitResult: PaperTradeResponse | null;

  openSheet(ctx), closeSheet();
  setOrderType(t), setSize(n), setAlgoParams(p);
  fetchPreview(): Promise;             // 异步获取预估
  submit(): Promise;                   // 异步提交纸交易
  reset();
}
```

### 5.3 useDecisionStore

```typescript
interface DecisionStore {
  decision: DecisionDTO | null;
  loading: boolean;

  fetchDecision(symbol): Promise;      // API 失败时自动降级 Mock
  setDecision(d), clearDecision();
}
```

---

## 6. API Communication Layer

### 6.1 axios 实例 (`lib/http-client.ts`)

```typescript
const httpClient = axios.create({
  baseURL: NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
});

// 请求拦截器 — 自动注入 Bearer Token
httpClient.interceptors.request.use(config => {
  const token = localStorage.getItem("athena_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 响应拦截器 — 401 自动清除 Token + 跳转登录
httpClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem("athena_token");
      window.location.href = "/login";
    }
    return Promise.reject(new Error(error.response?.data?.detail || "请求失败"));
  }
);
```

### 6.2 React Query Provider (`lib/query-provider.tsx`)

```typescript
defaultOptions: {
  queries: {
    staleTime: 60 * 1000,       // 1 分钟内不重新请求
    retry: 1,                    // 失败重试 1 次
    refetchOnWindowFocus: false, // 窗口聚焦不刷新
  },
  mutations: { retry: 0 },
}
```

Singleton 模式：SSR 时每次新建，浏览器端复用同一实例。

### 6.3 API Module Pattern

所有 API 模块遵循统一模式：

```typescript
// lib/auth.ts — 认证模块（使用原生 fetch）
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "...";

async function request<T>(path, options?) {
  // 自动附加 Authorization header
  // 非 2xx 抛出 Error
}

export async function login(username, password): Promise<TokenResponse>
export async function register(...): Promise<TokenResponse>
export async function getMe(): Promise<UserResponse>
export function getToken(): string | null
export function setToken(token)
export function clearToken()
export function isLoggedIn(): boolean
```

### 6.4 API Endpoint Reference

| Module | Method | Endpoint | Types |
|--------|--------|----------|-------|
| Core | GET | `/market/overview` | `DashboardSummary` |
| Core | GET | `/market/score` | `MarketScore` |
| Core | GET | `/stocks/:symbol` | `StockDetail` |
| Core | GET | `/decision/:symbol` | `DecisionDTO` |
| Auth | POST | `/auth/login` | `TokenResponse` |
| Auth | POST | `/auth/register` | `TokenResponse` |
| Auth | GET | `/auth/me` | `UserResponse` |
| Watchlist | CRUD | `/watchlists` | `Watchlist` |
| Watchlist | CRUD | `/watchlists/:id/items` | `WatchlistItem` |
| Watchlist | GET | `/watchlists/stock/search?q=` | `StockSearchResult[]` |
| Portfolio | CRUD | `/portfolio` | `PortfolioDTO` |
| Portfolio | CRUD | `/portfolio/positions` | `PositionDTO` |
| Recommendation | GET | `/recommendations` | `RecommendationDTO` |
| Execution | POST | `/execution/preview` | `ExecutionPreviewResponse` |
| Execution | POST | `/execution/paper-trade` | `PaperTradeResponse` |
| Backtest | POST | `/backtest/run` | `BacktestResult` |

---

## 7. Custom Hooks

### 7.1 useAuth
```typescript
const { user, token, loggedIn, loading, loginAction, registerAction, logout } = useAuth()
```
- 页面挂载时从 localStorage 恢复 token 并获取用户信息
- loginAction/registerAction 成功后自动跳转 `/dashboard`
- logout 清除 token 并跳转 `/login`

### 7.2 useDebounce\<T\>
```typescript
const debouncedValue = useDebounce(searchQuery, 300)
```
- 通用防抖，支持泛型

### 7.3 useLocalStorage\<T\>
```typescript
const [value, setValue, removeValue] = useLocalStorage<Theme>("theme", "dark")
```
- SSR 安全的 localStorage 封装
- 支持函数式更新 `setValue(prev => ...)`
- 返回 removeValue 清除函数

### 7.4 useStockSearch
```typescript
const { query, results, loading, setQuery, clearSearch } = useStockSearch()
```
- 内置 300ms 防抖
- 自动调用 `/watchlists/stock/search` API

### 7.5 useAsync\<T\>
```typescript
const { data, loading, error, execute, reset } = useAsync(fetchFn, immediate?)
```
- 通用异步状态封装（loading/error/data）
- execute 返回 Promise，支持链式调用
- reset 清除状态

---

## 8. i18n System

### Architecture

```
I18nProvider (React Context)
  ├── translations.ts        — 类型安全的翻译字典 (zh-CN + en)
  └── useTranslation() hook  — 返回 { locale, setLocale, t }
```

### Features
- **无第三方依赖**：纯 React Context 实现，零外部依赖
- **类型安全**：`TranslationDict` interface 约束所有 key，编译期校验
- **持久化**：locale 存储于 `localStorage("athena_locale")`
- **降级策略**：默认 `zh-CN`，浏览器语言非中文时仍默认中文
- **无需路由变更**：不依赖 `[locale]` 路由重写

### Translation Scope
覆盖 6 个命名空间：`common`、`nav`、`dashboard`、`watchlist`、`portfolio`、`errorBoundary`、`stock`

### Usage
```tsx
const { t } = useTranslation();
<h1>{t.dashboard.title}</h1>
```

---

## 9. Error Handling

### 9.1 ErrorBoundary (Class Component)

全局错误边界，捕获渲染树中所有未处理的 React 错误：
- **降级 UI**：居中的错误卡片（AlertTriangle 图标 + 错误信息 + 重试按钮）
- **reset 机制**：`handleReset()` 清除错误状态后重新挂载子树
- **fallback prop**：支持自定义降级 UI
- **日志**：`componentDidCatch` 输出错误 + 组件堆栈

### 9.2 API 层错误处理

- **axios 拦截器**：统一处理 HTTP 错误（401→跳转登录，其他→toast 待实现）
- **React Query**：自动重试 + stale 判定
- **RSC 页面**：try/catch 后渲染"无法连接到后端服务"降级提示

---

## 10. Testing

### Configuration (`vitest.config.ts`)
- **环境**: jsdom
- **Setup**: `@testing-library/jest-dom/vitest` 扩展断言
- **别名**: `@/*` → `./*`
- **排除**: `node_modules`, `.next`

### Test Cases (12 total)

| File | Cases | Coverage |
|------|-------|----------|
| `lib/utils.test.ts` | 5 | cn() 合并/过滤/条件/Tailwind 冲突/空输入 |
| `hooks/useDebounce.test.ts` | 3 | 初始值/延迟后更新/默认 300ms |
| `components/ErrorBoundary.test.tsx` | 4 | 正常渲染/错误捕获/自定义 fallback/错误信息展示 |

### Scripts
```json
"test": "vitest run",
"test:watch": "vitest"
```

---

## 11. Build & Deployment

### Dockerfile (Multi-stage)
```dockerfile
# Stage 1: builder
FROM node:20-alpine
COPY . .
RUN npm ci && npm run build

# Stage 2: runner
FROM node:20-alpine
COPY --from=builder .next .next
COPY --from=builder node_modules node_modules
COPY --from=builder package.json next.config.mjs .
EXPOSE 3000
CMD ["npx", "next", "start"]
```

### docker-compose.prod.yml
- Frontend 通过 Nginx 代理
- 环境变量：`NEXT_PUBLIC_API_URL=/athena/api/v1`
- 网络：`athena` bridge

### Scripts
```json
"dev": "next dev",       // 开发模式（HMR）
"build": "next build",   // 生产构建
"start": "next start",   // 生产启动
"lint": "next lint",     // ESLint 检查
"format": "prettier --write .",     // 格式化
"format:check": "prettier --check .", // 格式化检查
"test": "vitest run",              // 运行测试
"test:watch": "vitest"            // 监视模式
```

---

## 12. Design Conventions

### 12.1 Theme
- **强制深色模式**: `<html class="dark">`
- **基础色板**: shadcn slate（CSS 变量体系）
- **交易专用色**:
  - 涨/买入: `#00B8D9` (cyan, CSS `--up`)
  - 跌/卖出: `#FF5630` (red, CSS `--down`)
  - 中性/警告: 系统 `--warning` / `--destructive`

### 12.2 Typography
- **字体**: JetBrains Mono（next/font/google, CSS var `--font-mono`）
- **数字**: `tabular-nums` 等宽数字对齐

### 12.3 Language
- **默认语言**: `zh-CN`
- **国际化支持**: 中/英双语切换（`I18nProvider`）
- **数字格式化**: `Number.toLocaleString("zh-CN")` / `Intl.NumberFormat`

### 12.4 Code Conventions
- **无注释原则**: 代码自文档化（遵循 AGENTS.md）
- **命名**: camelCase 变量/函数，PascalCase 组件/类型
- **文件命名**: kebab-case 文件名（`watchlist-api.ts`）或 PascalCase 组件（`UserMenu.tsx`）
- **导出**: named export 用于工具函数，default export 用于页面组件

### 12.5 Mock / Fallback Strategy
- **回测页面**: API 失败时自动生成 Mock 数据（随机游走 K 线 + MA/MACD 交叉信号）
- **决策中心**: `fetchDecision()` 失败时生成 fallback 信号数据
- **市场仪表盘**: RSC 中 try/catch，渲染"无法连接到后端服务"降级 UI

---

## 13. Type System

### 13.1 API Response Types

```typescript
// Auth
TokenResponse { accessToken, tokenType, userId, username, displayName }
UserResponse { id, username, email, displayName, isActive }

// Market
DashboardSummary { indices, hotSectors, hotConcepts, marketStats, regime, temperature, aiSummary }
IndexData { name, code, price, change, changePct }
MarketStats { turnover, upCount, downCount, northBoundNet, turnoverRate }

// Stock
StockDetail { symbol, name, price, change, changePct, technicalIndicators, moneyFlow, aiAnalysis }
TechnicalIndicators { ma5, ma10, ma20, ma60, macd, rsi, kdj, boll }

// Decision
DecisionDTO { symbol, name, signals: Signal[], riskSummary, scenarios: ScenarioEntry[] }
Signal: "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL"
Action: "APPROVE" | "HOLD" | "REJECT"

// Execution
OrderType: "MARKET" | "LIMIT" | "TWAP" | "VWAP"
TradeSide: "BUY" | "SELL"
ExecutionPreviewResponse { estimatedCost, estimatedSlippage, estimatedFillPct, fee, totalCost, notes }

// Backtest
BacktestResult { periods, equityCurve, tradeMarks, drawdowns, summary }
PeriodMetrics { period, ic, rankIc, sharpe, winRate, annualReturn, maxDrawdown }
```

### 13.2 Utility Types

```typescript
// lib/mock-kline.ts
KlineItem { time, open, high, low, close, volume }
TradeMark { time, position, color, shape, text }
KlineData { klines, tradeMarks, ma5, ma10, ma20, macd }

// components/strategy/types.ts
NodeCategory: "data" | "signal" | "risk" | "execution" | "indicator" | "alpha" | "portfolio" | "sentiment"
NodeTemplate { category, type, label, sublabel, defaultData, handles: {input, output} }
NODE_TEMPLATES: NodeTemplate[]  // 8 种预定义模板
HANDLE_COMPATIBILITY: Record<HandleType, HandleType[]>  // 端口兼容矩阵
```

---

## 14. Authentication Flow

```
1. User visits /login or /register
2. Submits credentials → POST /auth/login or /auth/register
3. Backend returns { accessToken, ... }
4. Frontend stores token in localStorage("athena_token")
5. Redirects to /dashboard
6. All subsequent API requests: axios interceptor adds "Authorization: Bearer <token>"
7. On 401 response: axios interceptor clears token, redirects to /login
8. On app mount: useAuth() reads token → GET /auth/me → sets user state
9. Logout: clearToken(), clear user state, redirect to /login
```

No refresh token mechanism. No remember-me. No OAuth2.

---

## 15. Cross-references

- **ADR-001**: Sprint 1 Tech Stack Freeze
- **ADR-002**: Development Principles
- **RFC-001**: Sprint 1 Foundation Development Plan
- **API-001**: Sprint 1 API Baseline
- **PRD-002**: Watchlist PRD
- **AES-001**: Four-Layer Architecture

---

## 16. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-24 | Initial specification |
| 1.1.0 | 2026-06-28 | 补齐 7 项基础设施：Prettier, ESLint custom rules, ErrorBoundary, Hooks (useAuth/useDebounce/useLocalStorage/useStockSearch/useAsync), axios + react-query, i18n, Vitest + Testing Library |
