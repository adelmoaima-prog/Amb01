"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { useState } from "react";
import { cn, getStatusColor, turnoLabel, diaSemanaLabel } from "@/lib/utils";
import { Calendar, Plus, RefreshCw, Clock, AlertCircle } from "lucide-react";

export default function AgendasPage() {
  const qc = useQueryClient();
  const [espFiltro, setEspFiltro] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [turnoFiltro, setTurnoFiltro] = useState("");
  const [showAlteracaoModal, setShowAlteracaoModal] = useState<string | null>(null);
  const [justificativa, setJustificativa] = useState("");
  const [novoStatus, setNovoStatus] = useState("");

  const { data: especialidades = [] } = useQuery({
    queryKey: ["especialidades"],
    queryFn: async () => {
      const { data } = await api.get("/recursos/especialidades");
      return data;
    },
  });

  const { data: agendas = [], isLoading } = useQuery({
    queryKey: ["agendas", espFiltro, statusFiltro, turnoFiltro],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (espFiltro) params.set("especialidade_id", espFiltro);
      if (statusFiltro) params.set("status", statusFiltro);
      if (turnoFiltro) params.set("turno", turnoFiltro);
      const { data } = await api.get(`/agendas/?${params}`);
      return data;
    },
  });

  const { data: escalas = [] } = useQuery({
    queryKey: ["escalas", espFiltro],
    queryFn: async () => {
      const params = new URLSearchParams();
      const now = new Date();
      params.set("mes", `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`);
      if (espFiltro) params.set("especialidade_id", espFiltro);
      const { data } = await api.get(`/escalas/?${params}`);
      return data;
    },
  });

  const updateAgenda = useMutation({
    mutationFn: async ({ id, status, justificativa: just }: { id: string; status: string; justificativa?: string }) => {
      await api.patch(`/agendas/${id}`, { status });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agendas"] });
      setShowAlteracaoModal(null);
      setJustificativa("");
    },
  });

  const statusLabels: Record<string, string> = {
    aberta: "Aberta",
    bloqueada: "Bloqueada",
    pendente: "Pendente",
    encerrada: "Encerrada",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agendas e Escalas Médicas</h1>
          <p className="text-sm text-gray-500">Gestão de turnos, vagas e impacto na produção</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <div className="flex flex-wrap gap-3">
          <select
            value={espFiltro}
            onChange={(e) => setEspFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas as especialidades</option>
            {especialidades.map((e: any) => (
              <option key={e.id} value={e.id}>{e.nome}</option>
            ))}
          </select>
          <select
            value={statusFiltro}
            onChange={(e) => setStatusFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos os status</option>
            <option value="aberta">Aberta</option>
            <option value="bloqueada">Bloqueada</option>
            <option value="pendente">Pendente</option>
          </select>
          <select
            value={turnoFiltro}
            onChange={(e) => setTurnoFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos os turnos</option>
            <option value="manha">Manhã</option>
            <option value="tarde">Tarde</option>
            <option value="noite">Noite</option>
          </select>
        </div>
      </div>

      {/* Tabela de Agendas */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Calendar className="w-4 h-4" /> Agendas Cadastradas
          </h2>
          <span className="text-xs text-gray-400">{agendas.length} registros</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Especialidade", "Profissional", "Dia", "Turno", "Horário", "Vagas", "Consultório", "Status", "Ações"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Carregando...</td></tr>
              ) : agendas.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-gray-400">Nenhuma agenda encontrada</td></tr>
              ) : agendas.map((a: any) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{a.especialidade_nome}</td>
                  <td className="px-4 py-3 text-gray-600">{a.profissional_nome}</td>
                  <td className="px-4 py-3">{diaSemanaLabel(a.dia_semana)}</td>
                  <td className="px-4 py-3">{turnoLabel(a.turno)}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {a.hora_inicio} – {a.hora_fim}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-semibold">{a.vagas_total}</span>
                    <span className="text-gray-400"> (+{a.vagas_reserva} reserva)</span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{a.consultorio_numero || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", getStatusColor(a.status))}>
                      {statusLabels[a.status] || a.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => { setShowAlteracaoModal(a.id); setNovoStatus(a.status === "aberta" ? "bloqueada" : "aberta"); }}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Alterar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Escalas do mês */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Clock className="w-4 h-4" /> Escalas Médicas — Mês Atual
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Data", "Profissional", "Especialidade", "Turno", "Horário", "Status"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {escalas.slice(0, 20).map((e: any) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{new Date(e.data + "T00:00").toLocaleDateString("pt-BR")}</td>
                  <td className="px-4 py-3">{e.profissional_nome}</td>
                  <td className="px-4 py-3 text-gray-500">{e.especialidade_nome}</td>
                  <td className="px-4 py-3">{turnoLabel(e.turno)}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {e.hora_inicio ? `${e.hora_inicio} – ${e.hora_fim}` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", getStatusColor(e.status))}>
                      {e.status}
                    </span>
                  </td>
                </tr>
              ))}
              {escalas.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Nenhuma escala encontrada</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Alteração */}
      {showAlteracaoModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <h3 className="text-lg font-semibold">Alterar Status da Agenda</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Novo Status</label>
                <select
                  value={novoStatus}
                  onChange={(e) => setNovoStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none"
                >
                  <option value="aberta">Aberta</option>
                  <option value="bloqueada">Bloqueada</option>
                  <option value="pendente">Pendente</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Justificativa <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={justificativa}
                  onChange={(e) => setJustificativa(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none resize-none"
                  rows={3}
                  placeholder="Informe o motivo da alteração..."
                />
              </div>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700">
                <strong>Atenção:</strong> Esta alteração será registrada no histórico de auditoria e pode impactar pacientes já agendados.
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => { setShowAlteracaoModal(null); setJustificativa(""); }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => updateAgenda.mutate({ id: showAlteracaoModal!, status: novoStatus, justificativa })}
                disabled={!justificativa || updateAgenda.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:bg-blue-300"
              >
                {updateAgenda.isPending ? "Salvando..." : "Confirmar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
