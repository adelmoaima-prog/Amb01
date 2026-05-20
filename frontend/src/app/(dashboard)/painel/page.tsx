"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { KPICard } from "@/components/shared/KPICard";
import { AlertaBanner } from "@/components/shared/AlertaBanner";
import { formatPercent, formatNumber, formatCompetencia, currentCompetencia } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, AreaChart, Area, Cell,
} from "recharts";
import {
  CalendarCheck, ClipboardList, UserX, TrendingUp, XCircle, Target
} from "lucide-react";
import { useState } from "react";

export default function PainelPage() {
  const [competencia, setCompetencia] = useState(currentCompetencia());

  const { data: resumo, isLoading } = useQuery({
    queryKey: ["dashboard-resumo", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/dashboard/resumo?competencia=${competencia}`);
      return data;
    },
  });

  const { data: producaoEsp = [] } = useQuery({
    queryKey: ["dashboard-producao-esp", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/dashboard/producao-especialidade?competencia=${competencia}`);
      return data;
    },
  });

  const { data: historico = [] } = useQuery({
    queryKey: ["dashboard-historico"],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/historico-mensal?meses=6");
      return data;
    },
  });

  const { data: previsao } = useQuery({
    queryKey: ["dashboard-previsao"],
    queryFn: async () => {
      const { data } = await api.get("/dashboard/previsao-fechamento");
      return data;
    },
  });

  const { data: producaoProfissional = [] } = useQuery({
    queryKey: ["dashboard-producao-prof", competencia],
    queryFn: async () => {
      const { data } = await api.get(`/dashboard/producao-profissional?competencia=${competencia}`);
      return data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const metaPercent = resumo?.taxa_cumprimento_meta ?? 0;
  const metaBarColor = metaPercent >= 90 ? "#16a34a" : metaPercent >= 70 ? "#d97706" : "#dc2626";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Painel Executivo</h1>
          <p className="text-sm text-gray-500">Visão geral do ambulatório em tempo real</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="month"
            value={competencia}
            onChange={(e) => setCompetencia(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      {/* Alertas */}
      <AlertaBanner />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <KPICard
          title="Agendadas"
          value={formatNumber(resumo?.total_agendadas ?? 0)}
          icon={CalendarCheck}
          color="blue"
        />
        <KPICard
          title="Realizadas"
          value={formatNumber(resumo?.total_realizadas ?? 0)}
          icon={ClipboardList}
          color="green"
        />
        <KPICard
          title="Faltas"
          value={formatNumber(resumo?.total_faltas ?? 0)}
          icon={UserX}
          color="red"
        />
        <KPICard
          title="Absenteísmo"
          value={formatPercent(resumo?.taxa_absenteismo ?? 0)}
          icon={TrendingUp}
          color={resumo?.taxa_absenteismo > 25 ? "red" : "amber"}
        />
        <KPICard
          title="Canceladas"
          value={formatNumber(resumo?.total_canceladas ?? 0)}
          icon={XCircle}
          color="amber"
        />
        <KPICard
          title="Meta (%)"
          value={formatPercent(metaPercent)}
          icon={Target}
          color={metaPercent >= 90 ? "green" : metaPercent >= 70 ? "amber" : "red"}
        />
      </div>

      {/* Meta + Previsão */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Cumprimento de Meta Contratual</h2>
          <div className="flex items-center gap-4 mb-2">
            <span className="text-4xl font-bold" style={{ color: metaBarColor }}>
              {metaPercent.toFixed(1)}%
            </span>
            <div className="flex-1">
              <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(metaPercent, 100)}%`, backgroundColor: metaBarColor }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0</span>
                <span>Meta: {formatNumber(resumo?.meta_mensal ?? 0)} consultas</span>
                <span>100%</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-500">
            {formatNumber(resumo?.total_realizadas ?? 0)} realizadas de {formatNumber(resumo?.meta_mensal ?? 0)} previstas
          </p>
          {resumo?.risco_meta === "critico" && (
            <p className="text-sm text-red-600 font-medium mt-2">
              ⚠ Risco crítico de não cumprimento da meta
            </p>
          )}
        </div>

        {previsao && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Previsão de Fechamento</h2>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-400">Realizado até hoje</p>
                <p className="text-lg font-bold">{formatNumber(previsao.realizadas_ate_hoje)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Projeção final do mês</p>
                <p className="text-2xl font-bold text-blue-600">{formatNumber(previsao.previsao_final)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">% projetado da meta</p>
                <p className={`text-lg font-bold ${previsao.suficiente ? "text-green-600" : "text-red-600"}`}>
                  {formatPercent(previsao.percentual_projetado)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Média diária atual</p>
                <p className="text-sm font-medium">{previsao.media_diaria.toFixed(1)} cons/dia</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Produção por especialidade */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Produção por Especialidade</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={producaoEsp} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="especialidade_nome" type="category" tick={{ fontSize: 11 }} width={80} />
              <Tooltip
                formatter={(val: number, name: string) => [
                  name === "realizadas" ? `${val} realizadas` : `Meta: ${val}`,
                  name,
                ]}
              />
              <Bar dataKey="meta" name="Meta" fill="#e5e7eb" radius={[0, 2, 2, 0]} />
              <Bar dataKey="realizadas" name="Realizadas" radius={[0, 2, 2, 0]}>
                {producaoEsp.map((entry: any) => (
                  <Cell key={entry.especialidade_id} fill={entry.especialidade_cor} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Histórico mensal */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Histórico dos Últimos 6 Meses</h2>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={historico.map((h: any) => ({ ...h, competencia: formatCompetencia(h.competencia) }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="competencia" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="realizadas" name="Realizadas" stroke="#2563eb" fill="#dbeafe" strokeWidth={2} />
              <Area type="monotone" dataKey="faltas" name="Faltas" stroke="#dc2626" fill="#fee2e2" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tabela de profissionais */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Produção por Profissional</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Profissional</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Especialidade</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Realizadas</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Faltas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {producaoProfissional.slice(0, 10).map((p: any) => (
                <tr key={p.profissional_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{p.profissional_nome}</td>
                  <td className="px-4 py-3 text-gray-500">{p.especialidade_nome}</td>
                  <td className="px-4 py-3 text-right font-semibold text-green-700">{p.realizadas}</td>
                  <td className="px-4 py-3 text-right text-red-600">{p.faltas}</td>
                </tr>
              ))}
              {producaoProfissional.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">Nenhum dado encontrado</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
