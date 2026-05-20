"use client";

import { Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export function TopBar({ title }: { title?: string }) {
  const { user } = useAuthStore();

  const { data: alertas = [] } = useQuery({
    queryKey: ["alertas"],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/alertas");
      return data;
    },
    refetchInterval: 60_000,
  });

  const criticals = alertas.filter((a: any) => a.tipo === "critico").length;

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 flex-shrink-0">
      <div>
        {title && <h1 className="text-lg font-semibold text-gray-900">{title}</h1>}
      </div>
      <div className="flex items-center gap-4">
        <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <Bell className="w-5 h-5 text-gray-600" />
          {criticals > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {criticals}
            </span>
          )}
        </button>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">{user?.nome}</p>
          <p className="text-xs text-gray-500">{user?.role}</p>
        </div>
      </div>
    </header>
  );
}
