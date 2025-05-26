import requests
import time
import os
from dotenv import load_dotenv
import uuid

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


def create_question(session_id, name, native_query, database_id, display_type="bar", visualization_settings=None):
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

    # Obtém o dashboard completo
    res = requests.get(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers)
    res.raise_for_status()
    dashboard = res.json()

    # Atualiza lista de parâmetros se necessário
    if parameter_name not in [p["name"] for p in dashboard.get("parameters", [])]:
        dashboard["parameters"].append({
            "name": parameter_name,
            "slug": parameter_name,
            "type": "number/=",
            "default": None
        })
        print(f"Adicionando filtro '{parameter_name}' ao dashboard.")
    else:
        print(f"Filtro '{parameter_name}' já existe.")

    # Atualiza os parameter_mappings nos cards
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
            print(f"Conectando filtro '{parameter_name}' ao card {card_id}.")

        updated_cards.append(card)

    parameter_id = str(uuid.uuid4())  # Gera um ID único se necessário

    new_parameter = {
        "id": parameter_id,
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
    print(f"Dashboard {dashboard_id} atualizado com sucesso.")



def add_question_to_dashboard_with_filter(session_id, dashboard_id, question_id, parameter_name):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    # Obter dados do dashboard (nome, parâmetros e dashcards)
    dashboard_res = requests.get(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers)
    dashboard_res.raise_for_status()
    dashboard = dashboard_res.json()

    ordered_cards = dashboard.get("dashcards", [])

    # Criar novo card com parâmetro mapeado
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

    # Atualizar dashboard com novo card e filtros
    payload = {
        "name": dashboard["name"],
        "parameters": dashboard.get("parameters", []),
        "ordered_cards": ordered_cards
    }

    res = requests.put(f"{METABASE_URL}/api/dashboard/{dashboard_id}", headers=headers, json=payload)
    res.raise_for_status()
    print(f"Card {question_id} adicionado com filtro ao dashboard {dashboard_id}.")

def update_question_axes(session_id, question_id, x_axis="login_date", y_axis="minutos_online"):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    # Obter a pergunta atual
    res = requests.get(f"{METABASE_URL}/api/card/{question_id}", headers=headers)
    res.raise_for_status()
    question = res.json()

    # Atualizar visualização
    question["visualization_settings"]["graph.metrics"] = [{"name": y_axis}]
    question["visualization_settings"]["graph.dimensions"] = [x_axis]
    question["visualization_settings"]["x_axis"] = x_axis
    question["visualization_settings"]["y_axis"] = [y_axis]

    # Enviar PUT com os dados atualizados
    res = requests.put(f"{METABASE_URL}/api/card/{question_id}", headers=headers, json={
        "visualization_settings": question["visualization_settings"]
    })
    res.raise_for_status()
    print(f"Visualização da pergunta {question_id} atualizada com sucesso (X: {x_axis}, Y: {y_axis}).")

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

    
    q1 = find_question_by_name(session_id, "Usuários registrados hoje")
    if not q1:
        q1 = create_question(
            session_id,
            "Usuários registrados hoje",
            """
            SELECT
                "public"."accounts_feeduser"."id" AS id,
                COUNT(*) AS count
            FROM
                "public"."accounts_feeduser"
            WHERE
                "public"."accounts_feeduser"."date_joined" >= CAST(CAST(NOW() AS date) AS timestamptz)
                AND "public"."accounts_feeduser"."date_joined" < CAST(CAST((NOW() + INTERVAL '1 day') AS date) AS timestamptz)
            GROUP BY
                "public"."accounts_feeduser"."id"
            ORDER BY
                "public"."accounts_feeduser"."id" ASC
            """,
            database_id,
            display_type="line"
        )
        print("Pergunta 'Usuários registrados hoje' criada.")
    else:
        print("Pergunta 'Usuários registrados hoje' já existe.")

   
    q2 = find_question_by_name(session_id, "Tempo logado por usuário")
    if not q2:
        q2 = create_question(
            session_id,
            "Tempo logado por usuário",            
"""SELECT
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
            }
        )
        print("Pergunta 'Tempo logado por usuário' criada.")
    else:
        print("Pergunta 'Tempo logado por usuário' já existe.")
    
    
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
        print("Pergunta 'Usuários Ativos nos Últimos 10 Minutos' criada.")
    else:
        print("Pergunta 'Usuários Ativos nos Últimos 10 Minutos' já existe.")

    
    d1 = find_dashboard_by_name(session_id, "Tráfego diário de usuários")
    if not d1:
        d1 = create_dashboard(session_id, "Tráfego diário de usuários")
        print("Dashboard 'Tráfego diário de usuários' criado.")
    else:
        print("Dashboard 'Tráfego diário de usuários' já existe.")

    d2 = find_dashboard_by_name(session_id, "Tempo logado por usuário")
    if not d2:
        d2 = create_dashboard(session_id, "Tempo logado por usuário")
        print("Dashboard 'Tempo logado por usuário' criado.")
    else:
        print("Dashboard 'Tempo logado por usuário' já existe.")

    d3 = find_dashboard_by_name(session_id, "Usuários Ativos nos Últimos 10 Minutos")
    if not d3:
        d3 = create_dashboard(session_id, "Usuários Ativos nos Últimos 10 Minutos")
        print("Dashboard 'Usuários Ativos nos Últimos 10 Minutos' criado.")
    else:
        print("Dashboard 'Usuários Ativos nos Últimos 10 Minutos' já existe.")
    update_dashboard_with_filter(session_id, d2, q2, parameter_name="current_user_id")


    add_question_to_dashboard_with_filter(session_id, d2, q2, "current_user_id")
    update_question_axes(session_id, q2, x_axis="login_date", y_axis="minutos_online")
    trafego_public_url = get_or_create_public_link(session_id, d1)
    tempo_logado_public_url = get_or_create_public_link(session_id, d2)
    ativos_public_url = get_or_create_public_link(session_id, d3)

    dashboard_links = [
    {
        "name": "Tráfego_diário",
        "public_url": trafego_public_url,
        "id": d1
    },
    {
        "name": "Tempo_logado",
        "public_url": tempo_logado_public_url,
        "id": d2
    },
    {
        "name": "Usuários_Ativos_nos_Últimos_10_Minutos",
        "public_url": ativos_public_url,
        "id": d3
    }
]

    # Atualizar `settings.py` automaticamente:
    with open("django_backend/settings.py", "a") as f:
        f.write("\n\n# DASHBOARDS DO METABASE\n")
        f.write("METABASE_DASHBOARD_LINKS = [\n")
        for dash in dashboard_links:
            f.write(f"    {{'name': '{dash['name']}', 'public_url': '{dash['public_url']}', 'id': {dash['id']}}},\n")
        f.write("]\n")

if __name__ == "__main__":
    main()
