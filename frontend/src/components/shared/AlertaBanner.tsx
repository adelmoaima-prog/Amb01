"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { AlertTriangle, AlertCircle, Info, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Alerta {
  id: string;
  tipo: "critico" | "atencao" | "info";
  titulo: string;
  descricao: string;
  modulo: string;
}

const alertaStyle = {
  critico: "bg-red-50 border-red-200 text-red-800",
  atencao: "bg-amber-50 border-amber-200 text-amber-800",
  info: "bg-blue-50 border-blue-200 text-blue-800",
};

const AlertaIcon = ({ tipo }: { tipo: string }) => {
  if (tipo === "critico") return <AlertCircle className="w-4 h-4 flex-shrink-0" />;
  if (tipo === "atencao") return <AlertTriangle className="w-4 h-4 flex-shrink-0" />;
  return <Info className="w-4 h-4 flex-shrink-0" />;
};

export function AlertaBanner() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const { data: alertas = [] } = useQuery<Alerta[]>({
    queryKey: ["alertas"],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/alertas");
      return data;
    },
    refetchInterval: 60_000,
  });

  const visible = alertas.filter((a) => !dismissed.has(a.id));

  if (visible.length === 0) return null;

  return (
    <div className="space-y-2 mb-4">
      {visible.slice(0, 3).map((alerta) => (
        <div
          key={alerta.id}
          className={cn("flex items-start gap-3 px-4 py-3 rounded-lg border text-sm", alertaStyle[alerta.tipo])}
        >
          <AlertaIcon tipo={alerta.tipo} />
          <div className="flex-1">
            <span className="font-semibold">{alerta.titulo}</span>
            <span className="ml-2 opacity-80">{alerta.descricao}</span>
          </div>
          <button onClick={() => setDismissed(new Set(Array.from(dismissed).concat(alerta.id)))} className="opacity-60 hover:opacity-100">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
      {visible.length > 3 && (
        <p className="text-xs text-gray-500 text-right">+ {visible.length - 3} alertas</p>
      )}
    </div>
  );
}
