import streamlit as st
from datetime import datetime, timedelta
import json
import os

# ---------- Einstellungen ----------
st.set_page_config(page_title="📆 Wochenplaner", layout="wide")
st.title("📆 Wochenkalender mit Zeitbereichen, KW-Auswahl & Speicherung")

tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
zeit_start = 6
zeit_ende = 23
json_file = "wochenplaene.json"

# ---------- JSON laden & speichern ----------
def load_wochenplaene():
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        result = {}
        for key, wochenplan in raw.items():
            result[key] = {}
            for tag, aufgaben in wochenplan.items():
                result[key][tag] = [(datetime.strptime(von, "%H:%M").time(),
                                     datetime.strptime(bis, "%H:%M").time(),
                                     text)
                                     for von, bis, text in aufgaben]
        return result
    else:
        return {}

def save_wochenplaene(data):
    raw = {}
    for key, wochenplan in data.items():
        raw[key] = {}
        for tag, aufgaben in wochenplan.items():
            raw[key][tag] = [[von.strftime("%H:%M"), bis.strftime("%H:%M"), text] for von, bis, text in aufgaben]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

# ---------- Session State ----------
if "wochenplaene" not in st.session_state:
    st.session_state.wochenplaene = load_wochenplaene()

# ---------- Aktuelle KW & Jahr ----------
heute = datetime.today()
kw_aktuell = heute.isocalendar().week
jahr_aktuell = heute.year

# ---------- Auswahl: Kalenderwoche & Jahr ----------
col_w1, col_w2 = st.columns(2)
with col_w1:
    jahr = st.selectbox("Jahr", list(range(jahr_aktuell - 2, jahr_aktuell + 3)), index=2)
with col_w2:
    kw = st.selectbox("Kalenderwoche", list(range(1, 54)), index=kw_aktuell - 1)

wochen_key = f"{jahr}-KW{kw:02d}"

# ---------- Daten vorbereiten ----------
if wochen_key not in st.session_state.wochenplaene:
    st.session_state.wochenplaene[wochen_key] = {tag: [] for tag in tage}

wochenplan = st.session_state.wochenplaene[wochen_key]

# ---------- Neue Aufgabe eintragen ----------
st.subheader("➕ Neue Aufgabe eintragen")
col1, col2, col3, col4 = st.columns(4)

with col1:
    wochentag = st.selectbox("Wochentag", tage)
with col2:
    zeit_von = st.time_input("Von", value=datetime.strptime("08:00", "%H:%M").time(), key=f"von_{wochen_key}")
with col3:
    zeit_bis = st.time_input("Bis", value=datetime.strptime("09:00", "%H:%M").time(), key=f"bis_{wochen_key}")
with col4:
    text = st.text_input("Aufgabe", key=f"text_{wochen_key}")

if st.button("📌 Hinzufügen", key=f"add_{wochen_key}"):
    if zeit_von < zeit_bis and text.strip():
        wochenplan[wochentag].append((zeit_von, zeit_bis, text.strip()))
        save_wochenplaene(st.session_state.wochenplaene)
        st.rerun()
    else:
        st.warning("Bitte gültigen Zeitraum und Aufgabe angeben.")

# ---------- Kalenderansicht ----------
def generate_schedule_table():
    html = """
    <style>
        .kalender { border-collapse: collapse; width: 100%; table-layout: fixed; }
        .kalender th, .kalender td { border: 1px solid #ccc; padding: 8px; font-size: 12px; vertical-align: top; min-height: 30px; }
        .kalender th { background-color: #f0f0f0; }
        .zeitfeld { background-color: #f9f9f9; text-align: right; white-space: nowrap; }
        .taskbox { background-color: #cce5ff; margin: 2px 0; padding: 4px 6px; border-radius: 4px; }
    </style>
    <table class="kalender">
        <tr>
            <th>Zeit</th>
            """ + "".join(f"<th>{tag}</th>" for tag in tage) + "</tr>"

    for hour in range(zeit_start, zeit_ende):
        zeit_label = f"{hour:02d}:00 - {hour+1:02d}:00"
        html += f"<tr><td class='zeitfeld'>{zeit_label}</td>"

        for tag in tage:
            zelle = ""
            for von, bis, text in wochenplan[tag]:
                if (von.hour <= hour < bis.hour) or (von.hour == hour and von.minute == 0):
                    zelle += f"<div class='taskbox'>{von.strftime('%H:%M')}–{bis.strftime('%H:%M')}<br>{text}</div>"
            html += f"<td>{zelle}</td>"
        html += "</tr>"

    html += "</table>"
    return html

# ---------- Anzeige Wochenplan ----------
st.subheader(f"📋 Kalenderansicht – KW {kw}, {jahr}")
st.markdown(generate_schedule_table(), unsafe_allow_html=True)

# ---------- Aufgaben löschen ----------
st.subheader(f"🗑️ Aufgaben löschen – KW {kw} / {jahr}")
for tag in tage:
    for idx, (von, bis, text) in enumerate(wochenplan[tag]):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
        with col1:
            st.markdown(f"**{tag}**")
        with col2:
            st.markdown(f"{von.strftime('%H:%M')} – {bis.strftime('%H:%M')}")
        with col3:
            st.markdown(f"*{text}*")
        with col4:
            st.markdown(f"`KW {kw} / {jahr}`")
        with col5:
            if st.button("❌", key=f"remove_{tag}_{idx}_{wochen_key}"):
                wochenplan[tag].pop(idx)
                save_wochenplaene(st.session_state.wochenplaene)
                st.rerun()
