import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function formatCompetencia(competencia: string): string {
  const [ano, mes] = competencia.split("-");
  const meses = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
  ];
  return `${meses[parseInt(mes) - 1]}/${ano}`;
}

export function currentCompetencia(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function getRiscoColor(risco: string): string {
  switch (risco) {
    case "critico": return "text-red-600 bg-red-50 border-red-200";
    case "atencao": return "text-amber-600 bg-amber-50 border-amber-200";
    default: return "text-green-600 bg-green-50 border-green-200";
  }
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    realizado: "bg-green-100 text-green-800",
    falta: "bg-red-100 text-red-800",
    cancelado: "bg-gray-100 text-gray-800",
    remarcado: "bg-yellow-100 text-yellow-800",
    agendado: "bg-blue-100 text-blue-800",
    confirmado: "bg-emerald-100 text-emerald-800",
    aberta: "bg-green-100 text-green-800",
    bloqueada: "bg-red-100 text-red-800",
    pendente: "bg-yellow-100 text-yellow-800",
  };
  return map[status] || "bg-gray-100 text-gray-800";
}

export function turnoLabel(turno: string): string {
  return { manha: "Manhã", tarde: "Tarde", noite: "Noite" }[turno] || turno;
}

export function diaSemanaLabel(dia: number): string {
  return ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][dia] || "";
}
