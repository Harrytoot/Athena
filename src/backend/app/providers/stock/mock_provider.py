from app.providers.stock.base import StockSearchProvider, StockSearchResult

MOCK_STOCKS = [
    ("600519", "贵州茅台", "SH"),
    ("000858", "五粮液", "SZ"),
    ("601318", "中国平安", "SH"),
    ("000333", "美的集团", "SZ"),
    ("600036", "招商银行", "SH"),
    ("002415", "海康威视", "SZ"),
    ("600276", "恒瑞医药", "SH"),
    ("000651", "格力电器", "SZ"),
    ("601166", "兴业银行", "SH"),
    ("002475", "立讯精密", "SZ"),
    ("600900", "长江电力", "SH"),
    ("000001", "平安银行", "SZ"),
    ("601012", "隆基绿能", "SH"),
    ("002714", "牧原股份", "SZ"),
    ("600809", "山西汾酒", "SH"),
    ("300750", "宁德时代", "SZ"),
    ("688981", "中芯国际", "SH"),
    ("002230", "科大讯飞", "SZ"),
    ("600031", "三一重工", "SH"),
    ("000725", "京东方A", "SZ"),
]


class MockStockSearchProvider(StockSearchProvider):

    async def search(self, query: str, limit: int = 20) -> list[StockSearchResult]:
        q = query.strip().lower()
        results = []
        for symbol, name, market in MOCK_STOCKS:
            if q in symbol or q in name.lower():
                results.append(StockSearchResult(symbol=symbol, name=name, market=market))
                if len(results) >= limit:
                    break
        return results
