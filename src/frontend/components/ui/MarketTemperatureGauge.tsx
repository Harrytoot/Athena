export function MarketTemperatureGauge({ temperature }: { temperature: number }) {
  const rotation = (temperature / 100) * 180 - 90;
  const color = temperature >= 70 ? "#FF5630" : temperature >= 40 ? "#f59e0b" : "#00B8D9";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="80" height="50" viewBox="0 0 100 50" className="overflow-visible">
        <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#2A2E39" strokeWidth="8" />
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={`${(temperature / 100) * 126} 126`}
          strokeLinecap="round"
        />
        <line
          x1="50" y1="40"
          x2={50 + 30 * Math.cos((rotation * Math.PI) / 180)}
          y2={40 + 30 * Math.sin((rotation * Math.PI) / 180)}
          stroke="#8B95A5"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx="50" cy="40" r="4" fill="#8B95A5" />
      </svg>
      <span className="text-lg font-bold" style={{ color }}>
        {temperature}°
      </span>
    </div>
  );
}
