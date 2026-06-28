export interface KlineItem {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradeMark {
  time: string;
  type: "BUY" | "SELL";
  price: number;
}

export interface KlineData {
  symbol: string;
  candles: KlineItem[];
  trades: TradeMark[];
}

function ema(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const result: number[] = [];
  let prev = values[0];
  for (let i = 0; i < values.length; i++) {
    if (i === 0) {
      result.push(values[0]);
    } else {
      prev = values[i] * k + prev * (1 - k);
      result.push(prev);
    }
  }
  return result;
}

export function generateMockKline(symbol: string = "MOCK", days: number = 200): KlineData {
  const candles: KlineItem[] = [];
  let close = 50 + Math.random() * 20;
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    if (date.getDay() === 0 || date.getDay() === 6) continue;

    const timeStr = date.toISOString().split("T")[0];
    const volatility = close * 0.025;
    const change = (Math.random() - 0.48) * volatility * 2;
    const open = close;
    close = close + change;
    const high = Math.max(open, close) + Math.random() * volatility * 0.5;
    const low = Math.min(open, close) - Math.random() * volatility * 0.5;
    const volume = 1000000 + Math.random() * 9000000;

    candles.push({ time: timeStr, open, high, low, close, volume });
  }

  const closes = candles.map((c) => c.close);
  const trades: TradeMark[] = [];

  const ma5 = simpleMA(closes, 5);
  const ma20 = simpleMA(closes, 20);

  for (let i = 1; i < candles.length; i++) {
    const prevMa5 = ma5[i - 1];
    const prevMa20 = ma20[i - 1];
    const currMa5 = ma5[i];
    const currMa20 = ma20[i];
    if (prevMa5 !== null && prevMa20 !== null && currMa5 !== null && currMa20 !== null) {
      if (prevMa5 <= prevMa20 && currMa5 > currMa20) {
        trades.push({ time: candles[i].time, type: "BUY", price: candles[i].close });
      }
      if (prevMa5 >= prevMa20 && currMa5 < currMa20) {
        trades.push({ time: candles[i].time, type: "SELL", price: candles[i].close });
      }
    }
  }

  return { symbol, candles, trades };
}

export function computeMAs(closes: number[]): { ma5: (number | null)[]; ma10: (number | null)[]; ma20: (number | null)[] } {
  return {
    ma5: simpleMA(closes, 5),
    ma10: simpleMA(closes, 10),
    ma20: simpleMA(closes, 20),
  };
}

export function computeMACD(closes: number[]): {
  dif: (number | null)[];
  dea: (number | null)[];
  histogram: (number | null)[];
} {
  const ema12 = ema(closes, 12);
  const ema26 = ema(closes, 26);
  const dif = ema12.map((v12, i) => v12 - ema26[i]);
  const deaArr = ema(dif, 9);
  const histogram = dif.map((d, i) => 2 * (d - deaArr[i]));

  return { dif, dea: deaArr, histogram };
}

function simpleMA(values: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      result.push(sum / period);
    }
  }
  return result;
}
