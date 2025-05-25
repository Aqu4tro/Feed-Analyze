import requests
from django_backend import settings
import time
import os
from dotenv import load_dotenv

load_dotenv()

METABASE_URL = "http://localhost:3000"
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def login():
    response = requests.post(f"{METABASE_URL}/api/session", json={
        "username": EMAIL,
        "password": PASSWORD
    })
    return response.json()['id']

def find_dashboard_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/dashboard", headers=headers)
    dashboards = res.json()
    for dashboard in dashboards:
        if dashboard["name"] == name:
            return dashboard["id"]
    return None

def find_question_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/card", headers=headers)
    cards = res.json()
    for card in cards:
        if card["name"] == name:
            return card["id"]
    return None
def create_question(session_id, name, native_query, database_id, display_type="bar"):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }
    data = {
        "name": name,
        "dataset_query": {
            "type": "native",
            "native": {"query": native_query},
            "database": database_id
        },
        "display": display_type,
        "visualization_settings": {}
    }
    res = requests.post(f"{METABASE_URL}/api/card", headers=headers, json=data)
    return res.json()["id"]


def create_dashboard(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    data = {"name": name}
    res = requests.post(f"{METABASE_URL}/api/dashboard", headers=headers, json=data)
    return res.json()["id"]


def add_card_to_dashboard(session_id, dashboard_id, card_id):
    headers = {"X-Metabase-Session": session_id}
    data = {
        "dashboard_id": dashboard_id,
        "card_id": card_id,
        "sizeX": 6,
        "sizeY": 4,
        "col": 0,
        "row": 0
    }
    url = f"{METABASE_URL}/api/card/{card_id}"
    res = requests.put(url, headers=headers, json=data)
    try:
        print(f"Card {card_id} adicionado ao dashboard {dashboard_id}")
    except Exception as e:
        print(f"Erro ao adicionar card {card_id} ao dashboard {dashboard_id}: {res.text}")

def map_dashboard_filter_to_card(session_id, dashboard_id, card_id, filter_id, template_tag):
    headers = {"X-Metabase-Session": session_id}
    data = {
        "parameter_mappings": [
            {
                "parameter_id": filter_id,
                "card_id": card_id,
                "target": ["dimension", ["template-tag", template_tag]]
            }
        ]
    }
    requests.post(f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards", headers=headers, json=data)
def create_dashboard_filter(session_id, dashboard_id, filter_name, filter_type="date/single", default="past7days"):
    headers = {"X-Metabase-Session": session_id}
    data = {
        "name": filter_name,
        "slug": filter_name,
        "type": filter_type,
        "default": default
    }
    res = requests.post(f"{METABASE_URL}/api/dashboard/{dashboard_id}/parameters", headers=headers, json=data)
    return res.json()["id"]

def enable_public_link(session_id, dashboard_id):
    headers = {"X-Metabase-Session": session_id}
    res = requests.post(f"{METABASE_URL}/api/dashboard/{dashboard_id}/public_link", headers=headers)
    try:
        return f"{METABASE_URL}/public/dashboard/{res.json()['uuid']}", dashboard_id
    except KeyError:
        print(f"Erro ao gerar link público do dashboard {dashboard_id}: {res.text}")
        return None



session_id = login()


time.sleep(10)


database_id = 2 # id do banco de dados hospedado no postgresql

q1 = find_question_by_name(session_id, "Usuários registrados hoje") or create_question(session_id, "Usuários registrados hoje", """
    SELECT
      "public"."accounts_feeduser"."id" AS "id",
      COUNT(*) AS "count"
    FROM "public"."accounts_feeduser"
    WHERE "public"."accounts_feeduser"."date_joined" >= CAST(CAST(NOW() AS date) AS timestamptz)
      AND "public"."accounts_feeduser"."date_joined" < CAST(CAST((NOW() + INTERVAL '1 day') AS date) AS timestamptz)
    GROUP BY "public"."accounts_feeduser"."id"
    ORDER BY "public"."accounts_feeduser"."id" ASC
""", database_id, display_type="line")

q2 = find_question_by_name(session_id, "Tempo logado por usuário (com filtro)") or create_question(
    session_id,
    "Tempo logado por usuário (com filtro)",
    """
    SELECT
      login_time::date AS login_date,
      SUM(EXTRACT(EPOCH FROM (COALESCE(logout_time, now()) - login_time)) / 60) AS online_minutes
    FROM accounts_usersession
    WHERE {{login_date}}
    GROUP BY login_time::date
    ORDER BY login_date ASC;
    """,
    database_id,
    display_type="bar",
    parameters=[{
        "type": "date/single",
        "target": ["variable", ["template-tag", "login_date"]],
        "name": "login_date",
        "default": "past7days"
    }]
)

q3 = find_question_by_name(session_id, "Usuários Ativos nos Últimos 10 Minutos") or create_question(session_id, "Usuários Ativos nos Últimos 10 Minutos", """
    SELECT COUNT(*) AS usuarios_online
    FROM accounts_feeduser
    WHERE last_login >= NOW() - INTERVAL '10 minutes';
""", database_id, display_type="scalar")

d1 = find_dashboard_by_name(session_id, "Tráfego diário de usuários") or create_dashboard(session_id, "Tráfego diário de usuários")
add_card_to_dashboard(session_id, d1, q1)
filter_id = create_dashboard_filter(session_id, d1, "login_date")
map_dashboard_filter_to_card(session_id, d1, q2, filter_id, "login_date")

d2 = find_dashboard_by_name(session_id, "Tempo logado por usuário") or create_dashboard(session_id, "Tempo logado por usuário")
add_card_to_dashboard(session_id, d2, q2)

d3 = find_dashboard_by_name(session_id, "Usuários Ativos nos Últimos 10 Minutos") or create_dashboard(session_id, "Usuários Ativos nos Últimos 10 Minutos")
add_card_to_dashboard(session_id, d3, q3)

public1 = enable_public_link(session_id, d1)
public2 = enable_public_link(session_id, d2)
public3 = enable_public_link(session_id, d3)

def update_settings_dashboard_links(links):
    settings_path = os.path.join(os.path.dirname(__file__), "django_backend", "settings.py")

    with open(settings_path, "r") as f:
        content = f.read()

    import re

    new_links_str = f"""METABASE_DASHBOARD_LINKS = [
    {{"Tráfego_diário": "{links['Tráfego_diário']}", "id": {d1}}},
    {{"Tempo_logado": "{links['Tempo_logado']}", "id": {d2}}},
    {{"Usuários_Ativos_nos_Últimos_10_Minutos": "{links['Usuários_Ativos_nos_Últimos_10_Minutos']}", "id": {d3}}},
]"""

    content = re.sub(r"METABASE_DASHBOARD_LINKS\s*=\s*\[.*?\]", new_links_str, content, flags=re.DOTALL)

    with open(settings_path, "w") as f:
        f.write(content)

update_settings_dashboard_links({
    "Tráfego_diário": public1,
    "Tempo_logado": public2,
    "Usuários_Ativos_nos_Últimos_10_Minutos": public3
})
