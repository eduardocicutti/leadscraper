import { useAppStore } from "../store";

export function StatusBar() {
  const status = useAppStore((state) => state.status);
  const progress = useAppStore((state) => state.progress);
  const total = useAppStore((state) => state.total);
  const log = useAppStore((state) => state.log);

  if (status === "idle") {
    return null;
  }

  const percent = total > 0 ? Math.min(100, Math.round((progress / total) * 100)) : 0;
  const label =
    status === "done"
      ? "EXTRAÇÃO CONCLUÍDA"
      : status === "error"
        ? "FALHA NA EXTRAÇÃO"
        : "EXTRAINDO";

  return (
    <div className="bg-[#080d14] border border-[#1e2d45] rounded-md p-4 font-['JetBrains_Mono']">
      <div className="flex items-center justify-between text-[12px] text-[#8896ac]">
        <div className="flex items-center gap-2">
          <span className="text-[#2563eb]">▶</span>
          <span className="font-['Geist_Mono'] font-bold text-[#e8edf5]">{label}</span>
          {status === "running" || status === "pending" ? (
            <span className="animate-[blink_1s_step-end_infinite] text-[#2563eb]">|</span>
          ) : null}
        </div>
        <div className="flex items-center gap-4 font-['Geist_Mono'] font-bold text-[#e8edf5]">
          <span>
            {progress} / {total}
          </span>
          <span>{percent}%</span>
        </div>
      </div>
      <div className="mt-3 h-0.5 bg-[#162035] overflow-hidden">
        <div
          className="h-full bg-[#2563eb] transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-3 text-[12px] text-[#8896ac]">
        <span className="text-[#2563eb]">&gt;</span> {log || "Extraindo..."}
      </div>
    </div>
  );
}
