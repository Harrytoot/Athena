export function UpdateTimeLabel({ time }: { time: string }) {
  if (!time) return null;
  const formatted = new Date(time).toLocaleString("zh-CN");
  return (
    <div className="text-right text-xs text-gray-400">
      数据更新：{formatted}
    </div>
  );
}
