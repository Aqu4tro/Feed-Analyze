import requests
import time
import os
import re
import uuid
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
    response.raise_for_status()
    return response.json()['id']


def find_dashboard_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/dashboard", headers=headers)
    res.raise_for_status()
    dashboards = res.json()
    for dashboard in dashboards:
        if dashboard["name"] == name:
            return dashboard["id"]
    return None


def find_question_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/card", headers=headers)
    res.raise_for_status()
    cards = res.json()
    for card in cards:
        if card["name"] == name:
            return card["id"]
    return None


def create_question(session_id, name, native_query, database_id, display_type="bar", visualization_settings=None, template_tags=None):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }
    data = {
        "name": name,
        "dataset_query": {
            "type": "native",
            "native": {
                "query": native_query,
                "template_tags": template_tags or {}
            },
            "database": database_id
        },
        "display": display_type,
        "visualization_settings": visualization_settings or {}
    }
    res = requests.post(f"{METABASE_URL}/api/card", headers=headers, json=data)
    res.raise_for_status()
    return res.json()["id"]


def create_dashboard(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    data = {"name": name}
    res = requests.post(f"{METABASE_URL}/api/dashboard", headers=headers, json=data)
    res.raise_for_status()
    return res.json()["id"]


def update_dashboard_with_filter(session_id, dashboard_id, card_id, parameter_name="current_user_id"):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers)
    res.raise_for_status()
    dashboard = res.json()

    if parameter_name not in [p["name"] for p in dashboard.get("parameters", [])]:
        dashboard["parameters"].append({
            "name": parameter_name,
            "slug": parameter_name,
            "type": "number/=",
            "default": None
        })

    updated_cards = []
    for card in dashboard["dashcards"]:
        mapping_exists = any(
            m.get("parameter_name") == parameter_name
            for m in card.get("parameter_mappings", [])
        )

        if card["card"]["id"] == card_id and not mapping_exists:
            card["parameter_mappings"].append({
                "parameter_name": parameter_name,
                "card_id": card_id,
                "target": ["variable", ["template-tag", parameter_name]]
            })

        updated_cards.append(card)

    new_parameter = {
        "id": str(uuid.uuid4()),
        "name": parameter_name,
        "slug": parameter_name,
        "type": "number/=",
        "default": None,
        "required": False
    }

    payload = {
        "name": dashboard["name"],
        "parameters": [new_parameter],
        "ordered_cards": updated_cards
    }

    res = requests.put(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers, json=payload)
    res.raise_for_status()


def add_question_to_dashboard_with_filter(session_id, dashboard_id, question_id, parameter_name):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    dashboard_res = requests.get(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers)
    dashboard_res.raise_for_status()
    dashboard = dashboard_res.json()

    ordered_cards = dashboard.get("dashcards", [])
    new_card = {
        "cardId": question_id,
        "sizeX": 12,
        "sizeY": 6,
        "col": 0,
        "row": len(ordered_cards) * 6,
        "parameter_mappings": [
            {
                "parameter_name": parameter_name,
                "card_id": question_id,
                "target": ["variable", ["template-tag", parameter_name]]
            }
        ]
    }
    ordered_cards.append(new_card)

    payload = {
        "name": dashboard["name"],
        "parameters": dashboard.get("parameters", []),
        "ordered_cards": ordered_cards
    }

    res = requests.put(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers, json=payload)
    res.raise_for_status()


def update_question_axes(session_id, question_id, x_axis="login_date", y_axis="minutos_online"):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    res = requests.get(f"{METABASE_URL}/api/card/{question_id}", headers=headers)
    res.raise_for_status()
    question = res.json()

    question["visualization_settings"]["graph.metrics"] = [{"name": y_axis}]
    question["visualization_settings"]["graph.dimensions"] = [x_axis]
    question["visualization_settings"]["x_axis"] = x_axis
    question["visualization_settings"]["y_axis"] = [y_axis]

    res = requests.put(f"{METABASE_URL}/api/card/{question_id}", headers=headers, json={
        "visualization_settings": question["visualization_settings"]
    })
    res.raise_for_status()


def get_or_create_public_link(session_id, dashboard_id):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers)
    res.raise_for_status()
    dashboard = res.json()
    if dashboard.get("public_uuid"):
        public_uuid = dashboard["public_uuid"]
    else:
        res = requests.post(f"{METABASE_URL}/api/dashboard/{dashboard_id}/public_link", headers=headers)
        res.raise_for_status()
        public_uuid = res.json()["uuid"]
    return f"{METABASE_URL}/public/dashboard/{public_uuid}"


def main():
    session_id = login()
    time.sleep(2)
    database_id = 2

    # Pergunta 1
    q1 = find_question_by_name(session_id, "Usuários registrados hoje")
    if not q1:
        q1 = create_question(
            session_id,
            "Usuários registrados hoje",
            """
            SELECT COUNT(*) AS count
            FROM accounts_feeduser
            WHERE date_joined >= CURRENT_DATE
              AND date_joined < CURRENT_DATE + INTERVAL '1 day'
            """,
            database_id,
            display_type="line"
        )

    # Pergunta 2
    q2 = find_question_by_name(session_id, "Tempo logado por usuário")
    if not q2:
        q2 = create_question(
            session_id,
            "Tempo logado por usuário",
            """
            SELECT
              id AS session_id,
              user_id,
              login_time::date AS login_date,
              EXTRACT(EPOCH FROM (COALESCE(logout_time, now()) - login_time)) / 60 AS minutos_online
            FROM
              accounts_usersession
            WHERE
              user_id = CAST({{current_user_id}} AS bigint)
            ORDER BY
              login_time ASC
            """,
            database_id,
            display_type="bar",
            visualization_settings={
                "x_axis": "login_date",
                "y_axis": ["minutos_online"]
            },
            template_tags={
                "current_user_id": {
                    "id": "current_user_id",
                    "name": "current_user_id",
                    "display_name": "current_user_id",
                    "type": "number",
                    "required": False
                }
            }
        )

    # Pergunta 3
    q3 = find_question_by_name(session_id, "Usuários Ativos nos Últimos 10 Minutos")
    if not q3:
        q3 = create_question(
            session_id,
            "Usuários Ativos nos Últimos 10 Minutos",
            """
            SELECT COUNT(*) AS usuarios_online
            FROM accounts_feeduser
            WHERE last_login >= NOW() - INTERVAL '10 minutes'
            """,
            database_id,
            display_type="scalar"
        )

    # Dashboards
    d1 = find_dashboard_by_name(session_id, "Usuários registrados hoje") or create_dashboard(session_id, "Usuários registrados hoje")
    d2 = find_dashboard_by_name(session_id, "Tempo logado por usuário") or create_dashboard(session_id, "Tempo logado por usuário")
    d3 = find_dashboard_by_name(session_id, "Usuários Ativos nos Últimos 10 Minutos") or create_dashboard(session_id, "Usuários Ativos nos Últimos 10 Minutos")

    # Atualizações
    update_dashboard_with_filter(session_id, d2, q2, parameter_name="current_user_id")
    add_question_to_dashboard_with_filter(session_id, d2, q2, "current_user_id")
    update_question_axes(session_id, q2)

    # Links públicos
    trafego_public_url = get_or_create_public_link(session_id, d1)
    tempo_logado_public_url = get_or_create_public_link(session_id, d2)
    ativos_public_url = get_or_create_public_link(session_id, d3)

    dashboard_links = [
        {"name": "Usuários_registrados_hoje", "public_url": trafego_public_url, "id": d1},
        {"name": "Tempo_logado", "public_url": tempo_logado_public_url, "id": d2},
        {"name": "Usuários_Ativos_nos_Últimos_10_Minutos", "public_url": ativos_public_url, "id": d3}
    ]

    # Atualizar settings.py
    with open("django_backend/settings.py", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(?:(?:#\s*DASHBOARDS DO METABASE\s*\n)?METABASE_DASHBOARD_LINKS\s*=\s*\[[\s\S]*?\])"
    content = re.sub(pattern, "", content)

    novo_bloco = "METABASE_DASHBOARD_LINKS = [\n"
    for dash in dashboard_links:
        novo_bloco += f"    {{'name': '{dash['name']}', 'public_url': '{dash['public_url']}', 'id': {dash['id']}}},\n"
    novo_bloco += "]\n"

    with open("django_backend/settings.py", "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n\n" + novo_bloco)


if __name__ == "__main__":
    main()
