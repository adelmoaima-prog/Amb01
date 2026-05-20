"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Calendar, UserCheck, Activity,
  Building2, FileText, LogOut, ChevronLeft, ChevronRight,
  Bell, Hospital
} from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { logout } from "@/lib/auth";

const navItems = [
  { href: "/painel", icon: LayoutDashboard, label: "Painel Executivo" },
  { href: "/agendas", icon: Calendar, label: "Agendas e Escalas" },
  { href: "/absenteismo", icon: UserCheck, label: "Absenteísmo" },
  { href: "/producao", icon: Activity, label: "Produção" },
  { href: "/capacidade", icon: Building2, label: "Capacidade" },
  { href: "/relatorios", icon: FileText, label: "Relatórios" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, clearAuth } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    clearAuth();
    logout();
  }

  return (
    <div
      className={cn(
        "flex flex-col bg-slate-900 text-slate-100 h-screen sticky top-0 transition-all duration-200",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-700 flex-shrink-0">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <Hospital className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="ml-3 overflow-hidden">
            <p className="text-sm font-bold leading-tight">HUC Ambulatorial</p>
            <p className="text-xs text-slate-400 leading-tight">Gestão Inteligente</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto p-1 rounded hover:bg-slate-700 flex-shrink-0"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center px-4 py-2.5 text-sm transition-colors rounded-lg mx-2",
                active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-700 hover:text-white"
              )}
            >
              <item.icon className={cn("flex-shrink-0", collapsed ? "w-5 h-5" : "w-4 h-4")} />
              {!collapsed && <span className="ml-3">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="border-t border-slate-700 p-4 flex-shrink-0">
        {!collapsed && user && (
          <div className="mb-3">
            <p className="text-sm font-medium truncate">{user.nome}</p>
            <p className="text-xs text-slate-400 truncate">{user.role}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex items-center text-slate-400 hover:text-red-400 text-sm transition-colors w-full"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!collapsed && <span className="ml-2">Sair</span>}
        </button>
      </div>
    </div>
  );
}
