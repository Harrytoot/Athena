export type Locale = "zh-CN" | "en";

export interface TranslationDict {
  common: {
    login: string;
    logout: string;
    register: string;
    retry: string;
    loading: string;
    error: string;
    noData: string;
    save: string;
    cancel: string;
    delete: string;
    confirm: string;
    search: string;
    back: string;
    close: string;
  };
  nav: {
    dashboard: string;
    market: string;
    watchlist: string;
    portfolio: string;
    recommend: string;
    strategy: string;
    backtest: string;
    aiCenter: string;
    settings: string;
    branding: string;
  };
  dashboard: {
    title: string;
    backendError: string;
    backendErrorHint: string;
    hotIndustry: string;
    hotConcept: string;
    marketScore: string;
  };
  watchlist: {
    title: string;
    groupPlaceholder: string;
    noStocks: string;
    selectGroup: string;
    code: string;
    name: string;
    price: string;
    change: string;
    tags: string;
    note: string;
    deleteGroup: string;
  };
  portfolio: {
    title: string;
    totalValue: string;
    cash: string;
    pnl: string;
  };
  errorBoundary: {
    title: string;
    unknownError: string;
    retry: string;
  };
  stock: {
    detail: string;
    technicalIndicators: string;
    moneyFlow: string;
    aiAnalysis: string;
    decision: string;
  };
}

const zhCN: TranslationDict = {
  common: {
    login: "登录",
    logout: "退出",
    register: "注册",
    retry: "重试",
    loading: "加载中...",
    error: "发生错误",
    noData: "暂无数据",
    save: "保存",
    cancel: "取消",
    delete: "删除",
    confirm: "确认",
    search: "搜索",
    back: "返回",
    close: "关闭",
  },
  nav: {
    dashboard: "Dashboard",
    market: "市场",
    watchlist: "自选",
    portfolio: "持仓",
    recommend: "推荐",
    strategy: "策略",
    backtest: "回测",
    aiCenter: "AI 中心",
    settings: "设置",
    branding: "量化交易终端",
  },
  dashboard: {
    title: "市场概览",
    backendError: "无法连接到后端服务",
    backendErrorHint: "请确保 docker-compose up 已启动",
    hotIndustry: "热点行业 Top10",
    hotConcept: "热点概念 Top10",
    marketScore: "Market Score",
  },
  watchlist: {
    title: "自选股",
    groupPlaceholder: "分组名称：",
    noStocks: "暂无股票，请使用顶部搜索框添加",
    selectGroup: "请选择或创建一个自选分组",
    code: "代码",
    name: "名称",
    price: "最新价",
    change: "涨跌幅",
    tags: "标签",
    note: "备注",
    deleteGroup: "删除分组",
  },
  portfolio: {
    title: "持仓管理",
    totalValue: "总资产",
    cash: "现金",
    pnl: "盈亏",
  },
  errorBoundary: {
    title: "页面发生错误",
    unknownError: "未知错误",
    retry: "重试",
  },
  stock: {
    detail: "个股详情",
    technicalIndicators: "技术指标",
    moneyFlow: "资金流向",
    aiAnalysis: "AI分析",
    decision: "决策中心",
  },
};

const en: TranslationDict = {
  common: {
    login: "Login",
    logout: "Logout",
    register: "Register",
    retry: "Retry",
    loading: "Loading...",
    error: "Error occurred",
    noData: "No data",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    confirm: "Confirm",
    search: "Search",
    back: "Back",
    close: "Close",
  },
  nav: {
    dashboard: "Dashboard",
    market: "Market",
    watchlist: "Watchlist",
    portfolio: "Portfolio",
    recommend: "Recommend",
    strategy: "Strategy",
    backtest: "Backtest",
    aiCenter: "AI Center",
    settings: "Settings",
    branding: "Quant Trading Terminal",
  },
  dashboard: {
    title: "Market Overview",
    backendError: "Cannot connect to backend",
    backendErrorHint: "Please ensure docker-compose up is running",
    hotIndustry: "Hot Industries Top 10",
    hotConcept: "Hot Concepts Top 10",
    marketScore: "Market Score",
  },
  watchlist: {
    title: "Watchlist",
    groupPlaceholder: "Group name:",
    noStocks: "No stocks, use the search bar above to add",
    selectGroup: "Please select or create a watchlist group",
    code: "Code",
    name: "Name",
    price: "Price",
    change: "Change",
    tags: "Tags",
    note: "Note",
    deleteGroup: "Delete Group",
  },
  portfolio: {
    title: "Portfolio",
    totalValue: "Total Value",
    cash: "Cash",
    pnl: "P&L",
  },
  errorBoundary: {
    title: "Page Error",
    unknownError: "Unknown error",
    retry: "Retry",
  },
  stock: {
    detail: "Stock Detail",
    technicalIndicators: "Technical Indicators",
    moneyFlow: "Money Flow",
    aiAnalysis: "AI Analysis",
    decision: "Decision Center",
  },
};

export const translations: Record<Locale, TranslationDict> = {
  "zh-CN": zhCN,
  en,
};
