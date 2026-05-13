import os
import requests
from datetime import datetime, timezone
import pytz

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = "2388a75ef0764bc49543f816d92b577e"
ROME_TZ = pytz.timezone("Europe/Rome")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

now_rome = datetime.now(ROME_TZ)
today_str = now_rome.strftime("%Y-%m-%d")
weekday = now_rome.weekday()   # 0 = Monday
day_of_month = now_rome.day


def get_tasks_by_recurrence(recurrence: str) -> list:
    """Query Notion database filtering by Recurrence field."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Recurrence",
            "select": {
                "equals": recurrence
            }
        }
    }
    results = []
    while True:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return results


def reset_task(page_id: str) -> None:
    """Reset Checkbox to false and update Date to today."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Checkbox": {
                "checkbox": False
            },
            "Date": {
                "date": {
                    "start": today_str
                }
            }
        }
    }
    response = requests.patch(url, headers=headers, json=payload)
    response.raise_for_status()


def process(recurrence: str, label: str) -> None:
    tasks = get_tasks_by_recurrence(recurrence)
    print(f"[{label}] Found {len(tasks)} task(s)")
    for task in tasks:
        page_id = task["id"]
        title = task["properties"].get("Task", {}).get("title", [])
        name = title[0]["plain_text"] if title else "(no title)"
        reset_task(page_id)
        print(f"  ✓ Reset: {name}")


# --- DAILY: runs every day ---
process("Daily", "DAILY")

# --- WEEKLY: runs only on Monday ---
if weekday == 0:
    process("Weekly", "WEEKLY")
else:
    print(f"[WEEKLY] Skipped — today is not Monday (weekday={weekday})")

# --- MONTHLY: runs only on the 1st of the month ---
if day_of_month == 1:
    process("Monthly", "MONTHLY")
else:
    print(f"[MONTHLY] Skipped — today is not the 1st (day={day_of_month})")

print("Done.")
