import requests
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


if __name__ == "__main__":
    main()
