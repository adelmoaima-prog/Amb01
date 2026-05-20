import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: number;
  color?: "blue" | "green" | "red" | "amber" | "purple";
  className?: string;
}

const colorMap = {
  blue: "bg-blue-50 text-blue-600 border-blue-100",
  green: "bg-green-50 text-green-600 border-green-100",
  red: "bg-red-50 text-red-600 border-red-100",
  amber: "bg-amber-50 text-amber-600 border-amber-100",
  purple: "bg-purple-50 text-purple-600 border-purple-100",
};

const iconBg = {
  blue: "bg-blue-100",
  green: "bg-green-100",
  red: "bg-red-100",
  amber: "bg-amber-100",
  purple: "bg-purple-100",
};

export function KPICard({ title, value, subtitle, icon: Icon, trend, color = "blue", className }: KPICardProps) {
  return (
    <div className={cn("bg-white rounded-xl border border-gray-200 p-5 shadow-sm", className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
          {typeof trend !== "undefined" && (
            <p className={cn("text-xs mt-2 font-medium", trend >= 0 ? "text-green-600" : "text-red-600")}>
              {trend >= 0 ? "↑" : "↓"} {Math.abs(trend).toFixed(1)}% vs mês anterior
            </p>
          )}
        </div>
        {Icon && (
          <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", iconBg[color])}>
            <Icon className={cn("w-5 h-5", colorMap[color].split(" ")[1])} />
          </div>
        )}
      </div>
    </div>
  );
}
