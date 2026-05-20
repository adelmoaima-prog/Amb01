"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { useState } from "react";
import { formatPercent, formatNumber, currentCompetencia } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { KPICard } from "@/components/shared/KPICard";
import { Stethoscope, Users, FlaskConical, Microscope, LogOut, ArrowRightLeft } from "lucide-react";

const PIE_COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706"];

export default function ProducaoPage() {
  const [competencia, setCompetencia] = useState(currentCompetencia());
  const [espFiltro, setEspFiltro] = useState("");

  const { data: especialidades = [] } = useQuery({
    queryKey: ["especialidades"],
    queryFn: async () => { const { data } = await api.get("/recursos/especialidades"); return data; },
  });

  const { data: resumo } = useQuery({
    queryKey: ["producao-resumo", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/producao/resumo?competencia=${competencia}`);
      return data;
    },
  });

  const { data: porEsp = [] } = useQuery({
    queryKey: ["producao-esp", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/producao/por-especialidade?competencia=${competencia}`);
      return data;
    },
  });

  const { data: porProf = [] } = useQuery({
    queryKey: ["producao-prof", competencia, espFiltro],
    queryFn: async () => {
      const params = new URLSearchParams({ competencia });
      if (espFiltro) params.set("especialidade_id", espFiltro);
      const { data } = await api.get(`/producao/por-profissional?${params}`);
      return data;
    },
  });

  const { data: tipos = [] } = useQuery({
    queryKey: ["producao-tipos", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/producao/tipos-consulta?competencia=${competencia}`);
      return data;
    },
  });

  const { data: seguimento = [] } = useQuery({
    queryKey: ["producao-seguimento"],
    queryFn: async () => {
      const { data } = await api.get("/producao/seguimento");
      return data;
    },
  });

  const tipoLabels: Record<string, string> = {
    primeira_consulta: "1ª Consulta",
    retorno: "Retorno",
    urgencia: "Urgência",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Produção Assistencial</h1>
          <p className="text-sm text-gray-500">Consultas, procedimentos, altas e contrarreferências</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={espFiltro} onChange={(e) => setEspFiltro(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none">
            <option value="">Todas especialidades</option>
            {especialidades.map((e: any) => <option key={e.id} value={e.id}>{e.nome}</option>)}
          </select>
          <input type="month" value={competencia} onChange={(e) => setCompetencia(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none" />
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4">
        <KPICard title="Total Realizadas" value={formatNumber(resumo?.total_realizadas ?? 0)} icon={Stethoscope} color="blue" />
        <KPICard title="Multiprofissional" value={formatNumber(resumo?.multiprofissional ?? 0)} icon={Users} color="purple" />
        <KPICard title="Procedimentos" value={formatNumber(resumo?.procedimentos ?? 0)} icon={FlaskConical} color="green" />
        <KPICard title="Exames" value={formatNumber(resumo?.exames ?? 0)} icon={Microscope} color="amber" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard title="1ªs Consultas" value={formatNumber(resumo?.primeiras_consultas ?? 0)} color="blue" />
        <KPICard title="Retornos" value={formatNumber(resumo?.retornos ?? 0)} color="green" />
        <KPICard title="Altas" value={formatNumber(resumo?.altas ?? 0)} icon={LogOut} color="green" />
        <KPICard title="Contrarreferências" value={formatNumber(resumo?.contrarreferencias ?? 0)} icon={ArrowRightLeft} color="purple" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Produção por Especialidade</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={porEsp} layout="vertical" margin={{ left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="especialidade_nome" type="category" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="meta" name="Meta" fill="#e5e7eb" radius={[0, 2, 2, 0]} />
              <Bar dataKey="realizadas" name="Realizadas" fill="#2563EB" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Distribuição por Tipo de Consulta</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={tipos} dataKey="total" nameKey="tipo" cx="50%" cy="50%" outerRadius={90}
                label={({ tipo, percentual }) => `${tipoLabels[tipo] || tipo}: ${percentual}%`}>
                {tipos.map((_: any, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(val: any, name: string) => [val, tipoLabels[name] || name]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Profissionais */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Produção por Profissional</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Profissional", "CRM", "Especialidade", "Realizadas", "1ªs", "Retornos", "Faltas", "Taxa Falta"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {porProf.map((p: any) => (
                <tr key={p.profissional_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{p.profissional_nome}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{p.crm || "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{p.especialidade_nome}</td>
                  <td className="px-4 py-3 font-semibold text-green-700">{p.realizadas}</td>
                  <td className="px-4 py-3">{p.primeiras}</td>
                  <td className="px-4 py-3">{p.retornos}</td>
                  <td className="px-4 py-3 text-red-600">{p.faltas}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${p.taxa_falta > 25 ? "text-red-600" : "text-gray-700"}`}>
                      {p.taxa_falta.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Seguimento */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Seguimento de Pacientes por Especialidade</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Especialidade", "Em Seguimento", "Com Alta", "Contrarreferência", "% Alta"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {seguimento.map((s: any) => (
                <tr key={s.especialidade_nome} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{s.especialidade_nome}</td>
                  <td className="px-4 py-3">{s.em_seguimento}</td>
                  <td className="px-4 py-3 text-green-600 font-semibold">{s.com_alta}</td>
                  <td className="px-4 py-3 text-blue-600">{s.com_contrarreferencia}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${s.percentual_alta > 10 ? "text-green-600" : "text-gray-500"}`}>
                      {s.percentual_alta.toFixed(1)}%
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
