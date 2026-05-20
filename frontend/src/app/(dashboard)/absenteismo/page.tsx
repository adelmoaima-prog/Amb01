"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useState } from "react";
import { formatPercent, formatCompetencia, currentCompetencia } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from "recharts";
import { KPICard } from "@/components/shared/KPICard";
import { UserX, MapPin, Calendar, TrendingDown } from "lucide-react";

const MOTIVO_COLORS = ["#3B82F6", "#EF4444", "#F97316", "#A855F7", "#06B6D4", "#84CC16", "#EC4899", "#14B8A6"];

export default function AbsenteismoPage() {
  const [competencia, setCompetencia] = useState(currentCompetencia());
  const [espFiltro, setEspFiltro] = useState("");

  const { data: especialidades = [] } = useQuery({
    queryKey: ["especialidades"],
    queryFn: async () => { const { data } = await api.get("/recursos/especialidades"); return data; },
  });

  const { data: resumo } = useQuery({
    queryKey: ["absenteismo-resumo", competencia, espFiltro],
    queryFn: async () => {
      const params = new URLSearchParams({ competencia });
      if (espFiltro) params.set("especialidade_id", espFiltro);
      const { data } = await api.get(`/absenteismo/resumo?${params}`);
      return data;
    },
  });

  const { data: porEsp = [] } = useQuery({
    queryKey: ["absenteismo-esp", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/absenteismo/por-especialidade?competencia=${competencia}`);
      return data;
    },
  });

  const { data: porMotivo = [] } = useQuery({
    queryKey: ["absenteismo-motivo", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/absenteismo/por-motivo?competencia=${competencia}`);
      return data;
    },
  });

  const { data: porMunicipio = [] } = useQuery({
    queryKey: ["absenteismo-municipio", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/absenteismo/por-municipio?competencia=${competencia}`);
      return data;
    },
  });

  const { data: porDia = [] } = useQuery({
    queryKey: ["absenteismo-dia", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/absenteismo/por-dia-semana?competencia=${competencia}`);
      return data;
    },
  });

  const { data: tendencia = [] } = useQuery({
    queryKey: ["absenteismo-tendencia"],
    queryFn: async () => {
      const { data } = await api.get("/absenteismo/tendencia?meses=6");
      return data;
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Módulo de Absenteísmo</h1>
          <p className="text-sm text-gray-500">Análise de causas, padrões e estratégias de redução</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={espFiltro} onChange={(e) => setEspFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todas especialidades</option>
            {especialidades.map((e: any) => <option key={e.id} value={e.id}>{e.nome}</option>)}
          </select>
          <input type="month" value={competencia} onChange={(e) => setCompetencia(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard title="Total de Faltas" value={resumo?.total_faltas ?? 0} icon={UserX} color="red" />
        <KPICard title="Taxa de Absenteísmo" value={formatPercent(resumo?.taxa_absenteismo ?? 0)}
          icon={TrendingDown} color={resumo?.taxa_absenteismo > 25 ? "red" : "amber"} />
        <KPICard title="Esp. mais falta" value={resumo?.especialidade_maior_falta ?? "—"} icon={Calendar} color="purple" />
        <KPICard title="Município mais falta" value={resumo?.municipio_maior_falta ?? "—"} icon={MapPin} color="amber" />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Motivos */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Motivos de Falta</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={porMotivo} dataKey="total" nameKey="motivo_descricao" cx="50%" cy="50%" outerRadius={80} label={({ percentual }) => `${percentual}%`}>
                {porMotivo.map((_: any, i: number) => (
                  <Cell key={i} fill={MOTIVO_COLORS[i % MOTIVO_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(val: any, name: any) => [val, name]} />
              <Legend formatter={(v: string) => v.length > 25 ? v.slice(0, 25) + "…" : v} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Absenteísmo por dia da semana */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Faltas por Dia da Semana</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={porDia}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="dia_nome" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="total_faltas" name="Faltas" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Por especialidade */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Taxa por Especialidade</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={porEsp} layout="vertical" margin={{ left: 90 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
              <YAxis dataKey="especialidade_nome" type="category" tick={{ fontSize: 11 }} width={90} />
              <Tooltip formatter={(val: number) => [`${val}%`, "Taxa de falta"]} />
              <Bar dataKey="taxa" name="Taxa (%)" radius={[0, 4, 4, 0]}>
                {porEsp.map((e: any) => (
                  <Cell key={e.especialidade_id}
                    fill={e.taxa > 30 ? "#dc2626" : e.taxa > 20 ? "#f59e0b" : "#16a34a"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tendência */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Tendência dos Últimos 6 Meses</h2>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={tendencia.map((t: any) => ({ ...t, competencia: formatCompetencia(t.competencia) }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="competencia" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(val: number) => [`${val}%`, "Taxa de absenteísmo"]} />
              <Line type="monotone" dataKey="taxa" name="Taxa (%)" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Municípios */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Absenteísmo por Município de Origem</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Município", "Total Consultas", "Faltas", "Taxa"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {porMunicipio.slice(0, 15).map((m: any) => (
                <tr key={m.municipio} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{m.municipio}</td>
                  <td className="px-4 py-3">{m.total_consultas}</td>
                  <td className="px-4 py-3 text-red-600 font-semibold">{m.total_faltas}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${m.taxa > 30 ? "text-red-600" : m.taxa > 20 ? "text-amber-600" : "text-green-600"}`}>
                      {m.taxa.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
