import requests
import time
import os
import re
import uuid
from dotenv import load_dotenv

load_dotenv()

metabase_url = "http://localhost:3000"
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")


def login():
    response = requests.post(f"{metabase_url}/api/session", json={
        "username": email,
        "password": password
    })
    response.raise_for_status()
    return response.json()['id']


def find_dashboard_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{metabase_url}/api/dashboard", headers=headers)
    res.raise_for_status()
    dashboards = res.json()
    for dashboard in dashboards:
        if dashboard["name"] == name:
            return dashboard["id"]
    return None


def find_question_by_name(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{metabase_url}/api/card", headers=headers)
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
    res = requests.post(f"{metabase_url}/api/card", headers=headers, json=data)
    res.raise_for_status()
    return res.json()["id"]


def create_dashboard(session_id, name):
    headers = {"X-Metabase-Session": session_id}
    data = {"name": name}
    res = requests.post(f"{metabase_url}/api/dashboard", headers=headers, json=data)
    res.raise_for_status()
    return res.json()["id"]


def add_question_to_dashboard_with_filter(session_id, user_id, dashboard_id, question_id, add_parameter, parameter_name="current_user_id", field_reference="user.id"):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    response = requests.get(f"{metabase_url}/api/dashboard/{dashboard_id}", headers=headers)
    response.raise_for_status()
    dashboard = response.json()

    dashcards = dashboard.get("dashcards", [])
    parameters = dashboard.get("parameters", [])

    parameter_id = None

    if add_parameter:
        parameter_id = next((p["id"] for p in parameters if p["slug"] == parameter_name), None)
        if not parameter_id:
            parameter_id = str(uuid.uuid4())
            parameters.append({
                "id": parameter_id,
                "name": parameter_name,
                "slug": parameter_name,
                "type": "number/=",
                "field": {"field_ref": [field_reference]},
                "required": False,
                "allow_override": True,
                "default": int(user_id)
            })

    new_dashcard = {
        "id": question_id,
        "card_id": question_id,
        "col": 0,
        "row": len(dashcards) * 6,
        "size_x": 12,
        "size_y": 6
    }

    if add_parameter and parameter_id:
        new_dashcard["parameter_mappings"] = [
            {
                "parameter_id": parameter_id,
                "card_id": question_id,
                "target": ["variable", ["template-tag", parameter_name]]
            }
        ]

    dashcards.append(new_dashcard)

    payload = {
        "name": dashboard["name"],
        "enable_embedding": True,
        "parameters": parameters,
        "dashcards": dashcards,
        "embedding_params": {
            "current_user_id": "enabled"
        }
    }

    put_res = requests.put(
        f"{metabase_url}/api/dashboard/{dashboard_id}",
        headers=headers,
        json=payload
    )
    put_res.raise_for_status()


def update_question_axes(session_id, question_id, x_axis="login_date", y_axis="minutes_online"):
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    res = requests.get(f"{metabase_url}/api/card/{question_id}", headers=headers)
    res.raise_for_status()
    question = res.json()

    question["visualization_settings"]["graph.metrics"] = [y_axis]
    question["visualization_settings"]["graph.dimensions"] = [x_axis]
    question["visualization_settings"]["x_axis"] = x_axis
    question["visualization_settings"]["y_axis"] = [y_axis]

    res = requests.put(f"{metabase_url}/api/card/{question_id}", headers=headers, json={
        "visualization_settings": question["visualization_settings"]
    })
    res.raise_for_status()


def get_or_create_public_link(session_id, dashboard_id):
    headers = {"X-Metabase-Session": session_id}
    res = requests.get(f"{metabase_url}/api/dashboard/{dashboard_id}", headers=headers)
    res.raise_for_status()
    dashboard = res.json()
    if dashboard.get("public_uuid"):
        public_uuid = dashboard["public_uuid"]
    else:
        res = requests.post(f"{metabase_url}/api/dashboard/{dashboard_id}/public_link", headers=headers)
        res.raise_for_status()
        public_uuid = res.json()["uuid"]
    return f"{metabase_url}/public/dashboard/{public_uuid}"


def main():
    session_id = login()
    time.sleep(5)
    database_id = 2

    question1 = find_question_by_name(session_id, "Usuários cadastrados hoje")
    if not question1:
        question1 = create_question(
            session_id,
            "Usuários cadastrados hoje",
            """
            SELECT
                date_trunc('day', login_time) AS day,
                floor(EXTRACT(hour FROM login_time) / 4) AS block_4h,
                COUNT(DISTINCT user_id) AS registered_users
            FROM accounts_usersession
            WHERE
                logout_time IS NULL
                OR logout_time >= NOW() - INTERVAL '1 day'
            GROUP BY day, block_4h
            ORDER BY day, block_4h
            """,
            database_id,
            display_type="line",
            visualization_settings={
                "x_axis": "block_4h",
                "y_axis": ["registered_users"],
            }
        )

    question2 = find_question_by_name(session_id, "Tempo online do usuário")
    if not question2:
        question2 = create_question(
            session_id,
            "Tempo online do usuário",
            """
            SELECT
              id AS session_id,
              user_id,
              login_time::date AS login_date,
              EXTRACT(EPOCH FROM (COALESCE(logout_time, now()) - login_time)) / 60 AS minutes_online
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
                "y_axis": ["minutes_online"]
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

    question3 = find_question_by_name(session_id, "Usuários ativos nos últimos 10 minutos")
    if not question3:
        question3 = create_question(
            session_id,
            "Usuários ativos nos últimos 10 minutos",
            """
            SELECT
                COUNT(DISTINCT user_id) AS active_users
            FROM accounts_usersession
            WHERE
                logout_time IS NULL
                OR logout_time >= NOW() - INTERVAL '10 minutes'
            """,
            database_id,
            display_type="scalar",
        )


    dashboard1 = find_dashboard_by_name(session_id, "Usuários cadastrados hoje") or create_dashboard(session_id, "Usuários cadastrados hoje")
    dashboard2 = find_dashboard_by_name(session_id, "Tempo online do usuário") or create_dashboard(session_id, "Tempo online do usuário")
    dashboard3 = find_dashboard_by_name(session_id, "Usuários ativos nos últimos 10 minutos") or create_dashboard(session_id, "Usuários ativos nos últimos 10 minutos")
    
    add_question_to_dashboard_with_filter(session_id=session_id, dashboard_id=dashboard1, question_id=question1, add_parameter=False, user_id=0)
    
    add_question_to_dashboard_with_filter(session_id=session_id, dashboard_id=dashboard2, question_id=question2, add_parameter=True, parameter_name="current_user_id", user_id=0)
    
    update_question_axes(session_id, question2)

    add_question_to_dashboard_with_filter(session_id=session_id, dashboard_id=dashboard3, question_id=question3, add_parameter=False, user_id=0)
    
    update_question_axes(session_id, question1, x_axis="block_4h", y_axis="registered_users") 
    
    traffic_public_url = get_or_create_public_link(session_id, dashboard1)
    logged_time_public_url = get_or_create_public_link(session_id, dashboard2)
    active_public_url = get_or_create_public_link(session_id, dashboard3)

    dashboard_links = [
        {"name": "Usuarios_cadastrados_hoje", "public_url": traffic_public_url, "id": dashboard1},
        {"name": "Tempo_online_usuario", "public_url": logged_time_public_url, "id": dashboard2},
        {"name": "Usuarios_ativos_ultimos_10_minutos", "public_url": active_public_url, "id": dashboard3}
    ]

    with open("django_backend/settings.py", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(?:(?:#\s*METABASE DASHBOARDS\s*\n)?METABASE_DASHBOARD_LINKS\s*=\s*\[[\s\S]*?\])"
    content = re.sub(pattern, "", content)

    new_block = "METABASE_DASHBOARD_LINKS = [\n"
    for dash in dashboard_links:
        new_block += f"    {{'name': '{dash['name']}', 'public_url': '{dash['public_url']}', 'id': {dash['id']}}},\n"
    new_block += "]\n"

    with open("django_backend/settings.py", "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n\n" + new_block)


if __name__ == "__main__":
    main()
