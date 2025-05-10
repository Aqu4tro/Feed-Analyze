import requests
from django_backend import settings
import time

METABASE_URL = "http://localhost:3000"
EMAIL = "jonathaspasco77@gmail.com"
PASSWORD = "Edmc23@#"

def login():
    response = requests.post(f"{METABASE_URL}/api/session", json={
        "username": EMAIL,
        "password": PASSWORD
    })
    return response.json()['id']


def create_question(session_id, name, native_query, database_id):
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
        "display": "bar",
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


def enable_public_link(session_id, dashboard_id):
    headers = {"X-Metabase-Session": session_id}
    res = requests.post(f"{METABASE_URL}/api/dashboard/{dashboard_id}/public_link", headers=headers)
    try:
        return f"{METABASE_URL}/public/dashboard/{res.json()['uuid']}"
    except KeyError:
        print(f"Erro ao gerar link público do dashboard {dashboard_id}: {res.text}")
        return None



session_id = login()


time.sleep(10)


database_id = 2


q1 = create_question(session_id, "Usuários registrados hoje", """
    SELECT
      "public"."accounts_feeduser"."id" AS "id",
      COUNT(*) AS "count"
    FROM "public"."accounts_feeduser"
    WHERE "public"."accounts_feeduser"."date_joined" >= CAST(CAST(NOW() AS date) AS timestamptz)
      AND "public"."accounts_feeduser"."date_joined" < CAST(CAST((NOW() + INTERVAL '1 day') AS date) AS timestamptz)
    GROUP BY "public"."accounts_feeduser"."id"
    ORDER BY "public"."accounts_feeduser"."id" ASC
""", database_id)

q2 = create_question(session_id, "Tempo logado por usuário (últimos 7 dias)", """
    SELECT user_id,
           SUM(EXTRACT(EPOCH FROM (logout_time - login_time))) / 60 AS minutos_online
    FROM accounts_usersession
    WHERE login_time >= now() - interval '7 days'
    GROUP BY user_id;
""", database_id)

q3 = create_question(session_id, "Posts por categoria", """
    SELECT category, COUNT(*) AS total
    FROM posts_post
    GROUP BY category
""", database_id)


d1 = create_dashboard(session_id, "Tráfego diário de usuários")
add_card_to_dashboard(session_id, d1, q1)

d2 = create_dashboard(session_id, "Tempo logado por usuário")
add_card_to_dashboard(session_id, d2, q2)

d3 = create_dashboard(session_id, "Distribuição de posts")
add_card_to_dashboard(session_id, d3, q3)


public1 = enable_public_link(session_id, d1)
public2 = enable_public_link(session_id, d2)
public3 = enable_public_link(session_id, d3)

settings.METABASE_DASHBOARD_LINKS["Tráfego_diário"] = public1
settings.METABASE_DASHBOARD_LINKS["Tempo_logado"] = public2
settings.METABASE_DASHBOARD_LINKS["Posts_por_categoria"] = public3