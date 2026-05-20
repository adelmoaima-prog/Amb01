"""
Seed script: loads realistic demo data for 3 months.
Run: python -m app.seed.seed_data
"""
import asyncio
import random
from datetime import date, datetime, timedelta
import uuid
import calendar

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

from app.config import settings
from app.database import Base
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.especialidade import Especialidade
from app.models.profissional import Profissional
from app.models.consultorio import Consultorio
from app.models.agenda import Agenda
from app.models.escala import EscalaMedica, AlteracaoEscala
from app.models.consulta import Consulta, MotivoFalta, ConfirmacaoPresenca
from app.models.meta import MetaContratual
from app.models.capacidade import CapacidadeTurno

random.seed(42)

ESPECIALIDADES = [
    {"nome": "Cardiologia", "sigla": "CARD", "cor": "#EF4444", "meta_mensal": 200},
    {"nome": "Ortopedia", "sigla": "ORT", "cor": "#F97316", "meta_mensal": 180},
    {"nome": "Neurologia", "sigla": "NEUR", "cor": "#A855F7", "meta_mensal": 150},
    {"nome": "Endocrinologia", "sigla": "ENDO", "cor": "#06B6D4", "meta_mensal": 160},
    {"nome": "Ginecologia", "sigla": "GINE", "cor": "#EC4899", "meta_mensal": 200},
    {"nome": "Gastroenterologia", "sigla": "GAST", "cor": "#84CC16", "meta_mensal": 140},
    {"nome": "Pneumologia", "sigla": "PNEU", "cor": "#14B8A6", "meta_mensal": 120},
    {"nome": "Vascular", "sigla": "VASC", "cor": "#6366F1", "meta_mensal": 100},
    {"nome": "Cirurgia Geral", "sigla": "CG", "cor": "#64748B", "meta_mensal": 160},
    {"nome": "Oncologia", "sigla": "ONCO", "cor": "#DC2626", "meta_mensal": 130},
]

MUNICIPIOS = [
    "Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde",
    "Luziânia", "Águas Lindas de Goiás", "Valparaíso de Goiás",
    "Trindade", "Senador Canedo", "Formosa", "Catalão", "Itumbiara",
    "Jataí", "Goianésia", "Jaraguá",
]

MOTIVOS_FALTA = [
    {"codigo": "MF001", "descricao": "Telefone incorreto/desatualizado", "categoria": "contato"},
    {"codigo": "MF002", "descricao": "Reside em outro município", "categoria": "logistica"},
    {"codigo": "MF003", "descricao": "Dificuldade de transporte sanitário", "categoria": "logistica"},
    {"codigo": "MF004", "descricao": "Mudança de agenda não comunicada", "categoria": "agendamento"},
    {"codigo": "MF005", "descricao": "Agendamento com antecedência excessiva", "categoria": "agendamento"},
    {"codigo": "MF006", "descricao": "Falta recorrente (histórico de ausências)", "categoria": "recorrente"},
    {"codigo": "MF007", "descricao": "Esquecimento", "categoria": "outros"},
    {"codigo": "MF008", "descricao": "Problemas de saúde no dia", "categoria": "outros"},
]

PROFISSIONAIS_NOMES = [
    "Dr. Alexandre Ferreira", "Dra. Beatriz Oliveira", "Dr. Carlos Mendes",
    "Dra. Daniela Santos", "Dr. Eduardo Lima", "Dra. Fernanda Costa",
    "Dr. Gustavo Rocha", "Dra. Helena Martins", "Dr. Igor Alves",
    "Dra. Juliana Pereira", "Dr. Kleber Souza", "Dra. Larissa Ribeiro",
    "Dr. Marcos Nascimento", "Dra. Natália Carvalho", "Dr. Otávio Gomes",
    "Dra. Patrícia Moreira", "Dr. Rafael Teixeira", "Dra. Sandra Araújo",
    "Dr. Thiago Barbosa", "Dra. Úrsula Nunes", "Dr. Vitor Lopes",
    "Dra. Wanda Cardoso", "Dr. Xavier Dias", "Dra. Yasmin Freitas",
    "Dr. Zacarias Corrêa", "Dra. Adriana Pinto", "Dr. Bruno Assis",
    "Dra. Camila Borges", "Dr. Danilo Cunha", "Dra. Eliane Andrade",
]

AGE_FAIXAS = ["0-17", "18-30", "31-45", "46-60", "60+"]
AGE_WEIGHTS = [0.05, 0.10, 0.20, 0.30, 0.35]

TIPOS_CONSULTA = ["primeira_consulta", "retorno"]
TIPOS_CONSULTA_WEIGHTS = [0.40, 0.60]

TIPOS_ATENDIMENTO = ["medico", "multiprofissional", "procedimento", "exame"]
TIPOS_ATEND_WEIGHTS = [0.70, 0.10, 0.12, 0.08]

STATUS_WEIGHTS = {
    "realizado": 0.72,
    "falta": 0.16,
    "cancelado": 0.07,
    "remarcado": 0.05,
}


def get_crm():
    return f"GO-{random.randint(10000, 99999)}"


def get_patient_code():
    return f"PAC{random.randint(100000, 999999)}"


def workdays_in_month(year: int, month: int) -> list[date]:
    days = []
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        d = date(year, month, day)
        if d.weekday() < 5:
            days.append(d)
    return days


async def seed(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        # Check if already seeded
        existing = await session.execute(select(Especialidade).limit(1))
        if existing.scalar_one_or_none():
            print("Dados já existem. Pulando seed.")
            return

        print("Iniciando seed de dados demo...")

        # Roles
        roles_map = {}
        for role_name in ["Admin", "Coordenador", "Medico", "Recepcionista"]:
            role = Role(nome=role_name, descricao=f"Perfil {role_name}")
            session.add(role)
            roles_map[role_name] = role
        await session.flush()

        # Especialidades
        esp_map = {}
        for e in ESPECIALIDADES:
            esp = Especialidade(**e)
            session.add(esp)
            esp_map[e["nome"]] = esp
        await session.flush()

        # Motivos de falta
        motivos_map = {}
        for m in MOTIVOS_FALTA:
            motivo = MotivoFalta(**m)
            session.add(motivo)
            motivos_map[m["codigo"]] = motivo
        await session.flush()

        # Consultorios (20 salas: 10 no 1o andar, 10 no 2o)
        consultorios = []
        for andar in [1, 2]:
            for num in range(1, 11):
                numero = f"{andar}{num:02d}"
                tipo = "sala_procedimento" if num > 8 else "consultorio"
                c = Consultorio(numero=numero, andar=andar, tipo=tipo, nome=f"Sala {numero}")
                session.add(c)
                consultorios.append(c)
        await session.flush()

        # Profissionais (3 por especialidade)
        prof_list = []
        nome_idx = 0
        for i, (esp_nome, esp) in enumerate(esp_map.items()):
            for j in range(3):
                nome = PROFISSIONAIS_NOMES[nome_idx % len(PROFISSIONAIS_NOMES)]
                nome_idx += 1
                turno = ["manha", "tarde", "manha"][j]
                p = Profissional(
                    nome=nome,
                    crm=get_crm(),
                    tipo="medico",
                    especialidade_id=esp.id,
                    carga_horaria=20 if j == 0 else 12,
                    turno_preferencial=turno,
                    municipio="Goiânia",
                )
                session.add(p)
                prof_list.append((p, esp))
        await session.flush()

        # Users
        admin_role = roles_map["Admin"]
        coord_role = roles_map["Coordenador"]
        med_role = roles_map["Medico"]
        recep_role = roles_map["Recepcionista"]

        users_data = [
            ("Administrador HUC", "admin@huc.br", admin_role, None),
            ("Coordenador Ambulatorial", "coordenador@huc.br", coord_role, None),
            ("Dr. Alexandre Ferreira", "dr.alexandre@huc.br", med_role, prof_list[0][0]),
            ("Recepção 1", "recepcao1@huc.br", recep_role, None),
            ("Recepção 2", "recepcao2@huc.br", recep_role, None),
        ]
        for nome, email, role, prof in users_data:
            u = User(
                nome=nome,
                email=email,
                senha_hash=get_password_hash("Admin@2024"),
                role_id=role.id,
                profissional_id=prof.id if prof else None,
            )
            session.add(u)
        await session.flush()

        # Agendas (1 por profissional, dias variados)
        agendas = []
        dias_semana = [0, 1, 2, 3, 4]
        for idx, (prof, esp) in enumerate(prof_list):
            dia = dias_semana[idx % 5]
            turno = prof.turno_preferencial
            hora_ini = {"manha": "07:00", "tarde": "13:00", "noite": "19:00"}[turno]
            hora_fim = {"manha": "12:00", "tarde": "17:30", "noite": "22:00"}[turno]
            consultorio = consultorios[idx % len(consultorios)]
            agenda = Agenda(
                especialidade_id=esp.id,
                profissional_id=prof.id,
                consultorio_id=consultorio.id,
                turno=turno,
                dia_semana=dia,
                hora_inicio=hora_ini,
                hora_fim=hora_fim,
                vagas_total=8,
                vagas_reserva=1,
                data_inicio=date(2024, 11, 1),
                status="aberta",
            )
            session.add(agenda)
            agendas.append((agenda, prof, esp, consultorio))
        await session.flush()

        # Generate 3 months of data: Nov 2024, Dec 2024, Jan 2025 (relative to May 2026)
        today = date(2026, 5, 20)
        months = []
        for offset in range(2, -1, -1):
            m = today.month - offset
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            months.append((y, m))

        motivos_list = list(motivos_map.values())
        todas_consultas = []
        todas_escalas = []
        todos_caps = []

        for ano, mes in months:
            days = workdays_in_month(ano, mes)
            comp = date(ano, mes, 1)

            # Meta contratual global
            meta_global = MetaContratual(
                especialidade_id=None,
                competencia=comp,
                meta_consultas=sum(e["meta_mensal"] for e in ESPECIALIDADES),
            )
            session.add(meta_global)

            for esp_nome, esp in esp_map.items():
                meta_val = esp.meta_mensal
                meta_adj = int(meta_val * random.uniform(0.95, 1.05))
                meta = MetaContratual(
                    especialidade_id=esp.id,
                    competencia=comp,
                    meta_consultas=meta_adj,
                )
                session.add(meta)

            # Escalas e consultas por dia
            for d in days:
                for agenda, prof, esp, consultorio in agendas:
                    turno = prof.turno_preferencial
                    # Escala médica
                    escala_status = "confirmado"
                    if random.random() < 0.05:
                        escala_status = "cancelado"

                    escala = EscalaMedica(
                        profissional_id=prof.id,
                        agenda_id=agenda.id,
                        data=d,
                        turno=turno,
                        hora_inicio=agenda.hora_inicio,
                        hora_fim=agenda.hora_fim,
                        status=escala_status,
                    )
                    session.add(escala)
                    todas_escalas.append(escala)

                    # Capacidade
                    vagas_of = agenda.vagas_total if escala_status == "confirmado" else 0
                    vagas_oc = int(vagas_of * random.uniform(0.5, 1.0))
                    status_sala = "ocupada" if vagas_oc > 0 else "ociosa"
                    if escala_status == "cancelado":
                        status_sala = "ociosa"
                        vagas_of = 0
                        vagas_oc = 0

                    cap = CapacidadeTurno(
                        data=d,
                        turno=turno,
                        consultorio_id=consultorio.id,
                        agenda_id=agenda.id,
                        profissional_id=prof.id,
                        vagas_ofertadas=vagas_of,
                        vagas_ocupadas=vagas_oc,
                        status_sala=status_sala,
                    )
                    session.add(cap)

                    if escala_status == "cancelado":
                        continue

                    # Consultas do dia
                    num_consultas = random.randint(4, agenda.vagas_total)
                    for _ in range(num_consultas):
                        tipo_c = random.choices(TIPOS_CONSULTA, weights=TIPOS_CONSULTA_WEIGHTS)[0]
                        tipo_a = random.choices(TIPOS_ATENDIMENTO, weights=TIPOS_ATEND_WEIGHTS)[0]
                        status_c = random.choices(
                            list(STATUS_WEIGHTS.keys()),
                            weights=list(STATUS_WEIGHTS.values())
                        )[0]
                        municipio = random.choice(MUNICIPIOS)
                        idade = random.choices(AGE_FAIXAS, weights=AGE_WEIGHTS)[0]

                        motivo_id = None
                        if status_c == "falta":
                            motivo_id = random.choice(motivos_list).id

                        foi_alta = False
                        foi_contra = False
                        em_seg = True
                        if status_c == "realizado" and tipo_c == "retorno":
                            foi_alta = random.random() < 0.08
                            foi_contra = random.random() < 0.05 if not foi_alta else False
                            em_seg = not foi_alta and not foi_contra

                        hora = datetime(ano, mes, d.day, random.randint(7, 17), random.choice([0, 15, 30, 45]))
                        consulta = Consulta(
                            agenda_id=agenda.id,
                            profissional_id=prof.id,
                            especialidade_id=esp.id,
                            consultorio_id=consultorio.id,
                            data_hora=hora,
                            tipo_consulta=tipo_c,
                            tipo_atendimento=tipo_a,
                            paciente_codigo=get_patient_code(),
                            paciente_municipio=municipio,
                            paciente_idade_faixa=idade,
                            status=status_c,
                            motivo_falta_id=motivo_id,
                            foi_alta=foi_alta,
                            foi_contrarreferencia=foi_contra,
                            em_seguimento=em_seg,
                        )
                        session.add(consulta)
                        todas_consultas.append(consulta)

        await session.flush()

        # Some scale change history
        if todas_escalas:
            result = await session.execute(select(User).where(User.email == "coordenador@huc.br"))
            coord_user = result.scalar_one_or_none()
            if coord_user:
                for escala in random.sample(todas_escalas, min(30, len(todas_escalas))):
                    alt = AlteracaoEscala(
                        escala_id=escala.id,
                        user_id=coord_user.id,
                        tipo_alteracao=random.choice(["cancelamento", "substituicao", "reagendamento"]),
                        justificativa=random.choice([
                            "Médico em congresso médico",
                            "Afastamento por doença",
                            "Férias programadas",
                            "Substituição solicitada pelo profissional",
                            "Necessidade de reorganização da agenda",
                        ]),
                        pacientes_impactados=random.randint(2, 8),
                        producao_perdida=random.randint(2, 8),
                        dados_anteriores={"status": "confirmado"},
                        dados_novos={"status": escala.status},
                    )
                    session.add(alt)

        await session.commit()
        print(f"Seed concluído!")
        print(f"  Especialidades: {len(ESPECIALIDADES)}")
        print(f"  Profissionais: {len(prof_list)}")
        print(f"  Consultorios: 20")
        print(f"  Agendas: {len(agendas)}")
        print(f"  Consultas: ~{len(todas_consultas)}")
        print(f"  Meses: {[f'{y}-{m:02d}' for y, m in months]}")
        print(f"\nUsuários de acesso:")
        print(f"  admin@huc.br / Admin@2024  (Admin)")
        print(f"  coordenador@huc.br / Admin@2024  (Coordenador)")
        print(f"  dr.alexandre@huc.br / Admin@2024  (Médico)")
        print(f"  recepcao1@huc.br / Admin@2024  (Recepcionista)")


async def main():
    eng = create_async_engine(settings.DATABASE_URL, echo=False)
    await seed(eng)
    await eng.dispose()


if __name__ == "__main__":
    asyncio.run(main())
