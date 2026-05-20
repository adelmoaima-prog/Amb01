"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useState } from "react";
import { FileText, Download, Clock, CheckCircle, AlertCircle, Loader } from "lucide-react";
import { cn } from "@/lib/utils";

const TIPOS_RELATORIO = [
  { value: "producao", label: "Relatório de Produção" },
  { value: "absenteismo", label: "Relatório de Absenteísmo" },
  { value: "metas", label: "Relatório de Metas" },
  { value: "especialidade", label: "Relatório por Especialidade" },
  { value: "capacidade", label: "Relatório de Capacidade" },
  { value: "gargalos", label: "Relatório de Gargalos" },
];

const statusIcon: Record<string, any> = {
  pendente: Clock,
  processando: Loader,
  pronto: CheckCircle,
  erro: AlertCircle,
};

const statusColor: Record<string, string> = {
  pendente: "text-amber-500",
  processando: "text-blue-500",
  pronto: "text-green-500",
  erro: "text-red-500",
};

export default function RelatoriosPage() {
  const qc = useQueryClient();
  const [tipo, setTipo] = useState("producao");
  const [inicio, setInicio] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return d.toISOString().split("T")[0];
  });
  const [fim, setFim] = useState(() => {
    const d = new Date();
    return d.toISOString().split("T")[0];
  });
  const [espFiltro, setEspFiltro] = useState("");

  const { data: especialidades = [] } = useQuery({
    queryKey: ["especialidades"],
    queryFn: async () => { const { data } = await api.get("/recursos/especialidades"); return data; },
  });

  const { data: gerados = [], isLoading } = useQuery({
    queryKey: ["relatorios-gerados"],
    queryFn: async () => {
      const { data } = await api.get("/relatorios/gerados");
      return data;
    },
    refetchInterval: 5000,
  });

  const gerar = useMutation({
    mutationFn: async () => {
      const body: any = {
        tipo,
        periodo_inicio: inicio,
        periodo_fim: fim,
      };
      if (espFiltro) body.especialidade_id = espFiltro;
      const { data } = await api.post("/relatorios/gerar", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["relatorios-gerados"] });
    },
  });

  function formatDate(str: string) {
    return new Date(str).toLocaleDateString("pt-BR");
  }

  function formatDateTime(str: string) {
    return new Date(str).toLocaleString("pt-BR");
  }

  function tipoLabel(t: string) {
    return TIPOS_RELATORIO.find((r) => r.value === t)?.label || t;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Relatórios Automáticos</h1>
        <p className="text-sm text-gray-500">Gere relatórios prontos em PDF e CSV para gestão, auditorias e pesquisa</p>
      </div>

      {/* Gerador */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <FileText className="w-4 h-4" /> Gerar Novo Relatório
          </h2>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Relatório</label>
              <select value={tipo} onChange={(e) => setTipo(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500">
                {TIPOS_RELATORIO.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data Início</label>
              <input type="date" value={inicio} onChange={(e) => setInicio(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data Fim</label>
              <input type="date" value={fim} onChange={(e) => setFim(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Especialidade (opcional)</label>
              <select value={espFiltro} onChange={(e) => setEspFiltro(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
                <option value="">Todas</option>
                {especialidades.map((e: any) => <option key={e.id} value={e.id}>{e.nome}</option>)}
              </select>
            </div>
          </div>

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
            <strong>Informação LGPD:</strong> Relatórios para fins acadêmicos serão anonimizados automaticamente, removendo dados que permitam a identificação individual de pacientes.
          </div>

          <button
            onClick={() => gerar.mutate()}
            disabled={gerar.isPending}
            className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {gerar.isPending ? (
              <><Loader className="w-4 h-4 animate-spin" /> Gerando...</>
            ) : (
              <><FileText className="w-4 h-4" /> Gerar Relatório</>
            )}
          </button>
        </div>
      </div>

      {/* Histórico */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Relatórios Gerados</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Tipo", "Período", "Gerado por", "Data/Hora", "Status", "Downloads"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Carregando...</td></tr>
              ) : gerados.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Nenhum relatório gerado</td></tr>
              ) : gerados.map((r: any) => {
                const Icon = statusIcon[r.status] || Clock;
                return (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{tipoLabel(r.tipo)}</td>
                    <td className="px-4 py-3 text-gray-500">
                      {r.periodo_inicio && r.periodo_fim
                        ? `${formatDate(r.periodo_inicio)} – ${formatDate(r.periodo_fim)}`
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{r.user_nome}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{formatDateTime(r.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <Icon className={cn("w-4 h-4", statusColor[r.status], r.status === "processando" && "animate-spin")} />
                        <span className={cn("text-xs font-medium capitalize", statusColor[r.status])}>{r.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {r.arquivo_pdf && (
                          <a href={`${process.env.NEXT_PUBLIC_API_URL}${r.arquivo_pdf.replace("/api", "")}`}
                            target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-red-600 hover:text-red-800 font-medium">
                            <Download className="w-3 h-3" /> PDF
                          </a>
                        )}
                        {r.arquivo_csv && (
                          <a href={`${process.env.NEXT_PUBLIC_API_URL}${r.arquivo_csv.replace("/api", "")}`}
                            target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-green-600 hover:text-green-800 font-medium">
                            <Download className="w-3 h-3" /> CSV
                          </a>
                        )}
                        {r.status === "pendente" || r.status === "processando" ? (
                          <span className="text-xs text-gray-400">Processando...</span>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
