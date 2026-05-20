"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useState } from "react";
import { cn, turnoLabel } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { KPICard } from "@/components/shared/KPICard";
import { Building2, DoorOpen, DoorClosed, Users } from "lucide-react";

const statusColors: Record<string, string> = {
  ocupada: "bg-blue-500",
  ociosa: "bg-gray-200",
  disponivel: "bg-green-400",
  manutencao: "bg-amber-400",
};

const statusTextColors: Record<string, string> = {
  ocupada: "text-blue-800",
  ociosa: "text-gray-500",
  disponivel: "text-green-800",
  manutencao: "text-amber-800",
};

export default function CapacidadePage() {
  const [turnoFiltro, setTurnoFiltro] = useState("");
  const today = new Date().toISOString().split("T")[0];
  const [dataFiltro, setDataFiltro] = useState(today);
  const [simEsp, setSimEsp] = useState("");
  const [simVagas, setSimVagas] = useState(8);
  const [simTurno, setSimTurno] = useState("manha");
  const [showSimulacao, setShowSimulacao] = useState(false);

  const params = new URLSearchParams({ data: dataFiltro });
  if (turnoFiltro) params.set("turno", turnoFiltro);

  const { data: resumo } = useQuery({
    queryKey: ["capacidade-resumo", dataFiltro, turnoFiltro],
    queryFn: async () => {
      const { data } = await api.get(`/capacidade/resumo?${params}`);
      return data;
    },
  });

  const { data: consultorios = [] } = useQuery({
    queryKey: ["capacidade-consultorios", dataFiltro, turnoFiltro],
    queryFn: async () => {
      const { data } = await api.get(`/capacidade/consultorios?${params}`);
      return data;
    },
  });

  const { data: porTurno = [] } = useQuery({
    queryKey: ["capacidade-turnos", dataFiltro],
    queryFn: async () => {
      const { data } = await api.get(`/capacidade/por-turno?data=${dataFiltro}`);
      return data;
    },
  });

  const { data: equipe = [] } = useQuery({
    queryKey: ["capacidade-equipe", dataFiltro],
    queryFn: async () => {
      const { data } = await api.get(`/capacidade/equipe?data=${dataFiltro}`);
      return data;
    },
  });

  const { data: simulacao } = useQuery({
    queryKey: ["capacidade-simulacao", simEsp, simVagas, simTurno],
    queryFn: async () => {
      if (!simEsp) return null;
      const { data } = await api.get(
        `/capacidade/simulacao?nova_especialidade=${encodeURIComponent(simEsp)}&vagas=${simVagas}&turno=${simTurno}`
      );
      return data;
    },
    enabled: showSimulacao && !!simEsp,
  });

  const andar1 = consultorios.filter((c: any) => c.andar === 1);
  const andar2 = consultorios.filter((c: any) => c.andar === 2);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Capacidade Instalada</h1>
          <p className="text-sm text-gray-500">Consultórios, equipe, ocupação e simulações</p>
        </div>
        <div className="flex items-center gap-3">
          <input type="date" value={dataFiltro} onChange={(e) => setDataFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
          <select value={turnoFiltro} onChange={(e) => setTurnoFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
            <option value="">Todos os turnos</option>
            <option value="manha">Manhã</option>
            <option value="tarde">Tarde</option>
            <option value="noite">Noite</option>
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard title="Consultórios Totais" value={resumo?.consultorios_total ?? 0} icon={Building2} color="blue" />
        <KPICard title="Ocupados" value={resumo?.consultorios_ocupados ?? 0} icon={DoorClosed} color="purple" />
        <KPICard title="Ociosos" value={resumo?.consultorios_ociosos ?? 0} icon={DoorOpen} color="amber" />
        <KPICard title="Taxa de Ocupação" value={`${(resumo?.taxa_ocupacao ?? 0).toFixed(1)}%`} icon={Users} color="green" />
      </div>

      {/* Grid de consultórios */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Mapa de Consultórios</h2>

        <div className="space-y-4">
          {[{ label: "1º Andar", rooms: andar1 }, { label: "2º Andar", rooms: andar2 }].map(({ label, rooms }) => (
            <div key={label}>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-2">{label}</p>
              <div className="flex flex-wrap gap-2">
                {rooms.map((c: any) => (
                  <div key={c.id} className={cn(
                    "w-20 h-20 rounded-xl flex flex-col items-center justify-center text-center p-1",
                    c.status === "ocupada" ? "bg-blue-100 border-2 border-blue-300" :
                    c.status === "ociosa" ? "bg-gray-100 border-2 border-gray-200" :
                    "bg-green-50 border-2 border-green-200"
                  )}>
                    <Building2 className={cn("w-5 h-5 mb-1",
                      c.status === "ocupada" ? "text-blue-500" :
                      c.status === "ociosa" ? "text-gray-400" : "text-green-500"
                    )} />
                    <p className="text-xs font-bold">{c.numero}</p>
                    <p className={cn("text-xs capitalize", statusTextColors[c.status] || "text-gray-500")}>
                      {c.status}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex gap-4 mt-4 pt-4 border-t border-gray-100">
          {[
            { status: "ocupada", label: "Ocupada", color: "bg-blue-100 border-blue-300" },
            { status: "ociosa", label: "Ociosa", color: "bg-gray-100 border-gray-200" },
            { status: "disponivel", label: "Disponível", color: "bg-green-50 border-green-200" },
          ].map((s) => (
            <div key={s.status} className="flex items-center gap-1.5">
              <div className={cn("w-3 h-3 rounded border", s.color)} />
              <span className="text-xs text-gray-500">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Ocupação por turno */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Ocupação por Turno</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={porTurno.map((t: any) => ({ ...t, turno: turnoLabel(t.turno) }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="turno" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="consultorios_disponiveis" name="Disponíveis" fill="#d1fae5" />
              <Bar dataKey="consultorios_ocupados" name="Ocupados" fill="#2563EB" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Equipe escalada */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="p-5 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Equipe Escalada — {dataFiltro}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Turno", "Médicos", "Enfermeiros", "Técnicos", "Total"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {equipe.map((e: any) => (
                  <tr key={e.turno} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{turnoLabel(e.turno)}</td>
                    <td className="px-4 py-3">{e.medicos}</td>
                    <td className="px-4 py-3">{e.enfermeiros}</td>
                    <td className="px-4 py-3">{e.tecnicos}</td>
                    <td className="px-4 py-3 font-semibold">{e.total_equipe}</td>
                  </tr>
                ))}
                {equipe.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Sem escala nesta data</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Simulação */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Simulação de Novo Serviço</h2>
          <button onClick={() => setShowSimulacao(!showSimulacao)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            {showSimulacao ? "Ocultar" : "Abrir Simulador"}
          </button>
        </div>
        {showSimulacao && (
          <div className="p-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nova Especialidade</label>
                <input value={simEsp} onChange={(e) => setSimEsp(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none"
                  placeholder="Ex: Dermatologia" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Vagas/semana</label>
                <input type="number" value={simVagas} onChange={(e) => setSimVagas(Number(e.target.value))} min={1} max={40}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Turno</label>
                <select value={simTurno} onChange={(e) => setSimTurno(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
                  <option value="manha">Manhã</option>
                  <option value="tarde">Tarde</option>
                  <option value="noite">Noite</option>
                </select>
              </div>
            </div>

            {simulacao && (
              <div className={cn("p-4 rounded-lg border", simulacao.viavel ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200")}>
                <h3 className={cn("font-semibold mb-2", simulacao.viavel ? "text-green-800" : "text-red-800")}>
                  {simulacao.viavel ? "✓ Viável" : "✗ Inviável no turno selecionado"}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div><p className="text-gray-500">Consultórios disponíveis</p><p className="font-bold">{simulacao.consultorios_disponiveis}</p></div>
                  <div><p className="text-gray-500">Sala sugerida</p><p className="font-bold">{simulacao.consultorio_sugerido || "Nenhuma"}</p></div>
                  <div><p className="text-gray-500">Nova taxa ocupação</p><p className="font-bold">{simulacao.impacto_taxa_ocupacao.toFixed(1)}%</p></div>
                  <div><p className="text-gray-500">Requer nova equipe</p><p className="font-bold">{simulacao.requer_nova_equipe ? "Sim" : "Não"}</p></div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
