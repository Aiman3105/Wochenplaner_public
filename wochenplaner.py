import streamlit as st
from datetime import datetime
import json
import os

# ---- Einstellungen ----
st.set_page_config(page_title="📆 Wochenplaner", layout="wide")
st.title("📆 Wochenkalender mit mobiler & Desktop-Ansicht")

tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
json_file = "wochenplaene.json"

# ---- JSON laden & speichern ----
def load_wochenplaene():
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        result = {}
        for key, plan in raw.items():
            result[key] = {}
            for tag, aufgaben in plan.items():
                result[key][tag] = [(datetime.strptime(v, "%H:%M").time(),
                                     datetime.strptime(b, "%H:%M").time(),
                                     t) for v, b, t in aufgaben]
        return result
    return {}

def save_wochenplaene(data):
    raw = {}
    for key, plan in data.items():
        raw[key] = {}
        for tag, aufgaben in plan.items():
            raw[key][tag] = [[v.strftime("%H:%M"), b.strftime("%H:%M"), t] for v, b, t in aufgaben]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)

# ---- Session init ----
if "wochenplaene" not in st.session_state:
    st.session_state.wochenplaene = load_wochenplaene()

# ---- Kalenderwoche + Jahr Auswahl ----
heute = datetime.today()
jahr_aktuell = heute.year
kw_aktuell = heute.isocalendar().week

col1, col2, col3 = st.columns([2, 2, 3])
with col1:
    jahr = st.selectbox("📅 Jahr", list(range(jahr_aktuell - 2, jahr_aktuell + 3)), index=2)
with col2:
    kw = st.selectbox("📆 Kalenderwoche", list(range(1, 54)), index=kw_aktuell - 1)
with col3:
    ansicht = st.selectbox("🖥️ Ansicht", ["📱 iPhone", "💻 Desktop"])

key = f"{jahr}-KW{kw:02d}"

# ---- Wochenstruktur vorbereiten ----
if key not in st.session_state.wochenplaene:
    st.session_state.wochenplaene[key] = {tag: [] for tag in tage}

wochenplan = st.session_state.wochenplaene[key]

# ---- Neue Aufgabe eintragen ----
st.header("➕ Neue Aufgabe eintragen")
wochentag = st.selectbox("🗓️ Wochentag", tage)
von = st.time_input("Von", value=datetime.strptime("08:00", "%H:%M").time(), key=f"von_{key}")
bis = st.time_input("Bis", value=datetime.strptime("09:00", "%H:%M").time(), key=f"bis_{key}")
text = st.text_input("✏️ Aufgabe", key=f"text_{key}")

if st.button("✔️ Hinzufügen", key=f"add_{key}"):
    if von < bis and text.strip():
        wochenplan[wochentag].append((von, bis, text.strip()))
        save_wochenplaene(st.session_state.wochenplaene)
        st.success("Aufgabe hinzugefügt!")
        st.rerun()
    else:
        st.warning("Bitte gültigen Zeitraum und eine Aufgabe eingeben.")

# ---- Darstellung: iPhone-Ansicht ----
def mobile_ansicht():
    st.header(f"📋 Wochenübersicht – KW {kw} / {jahr}")
    for tag in tage:
        aufgaben = sorted(wochenplan[tag], key=lambda x: x[0])
        with st.expander(f"📅 {tag} – {len(aufgaben)} Aufgabe(n)"):
            if not aufgaben:
                st.info("Keine Aufgaben eingetragen.")
            for v, b, t in aufgaben:
                st.markdown(f"🕒 **{v.strftime('%H:%M')} – {b.strftime('%H:%M')}**  \n📌 {t}")

# ---- Darstellung: Desktop-Tabelle ----
def desktop_ansicht():
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

    for hour in range(6, 23):
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
    st.markdown(f"### 🖥️ Kalenderansicht – KW {kw} / {jahr}")
    st.markdown(html, unsafe_allow_html=True)

# ---- Ansicht anzeigen ----
if ansicht == "📱 iPhone":
    mobile_ansicht()
else:
    desktop_ansicht()

# ---- Aufgaben löschen ----
st.header("🗑️ Aufgaben löschen")
for tag in tage:
    if wochenplan[tag]:
        with st.expander(f"🧹 {tag} ({len(wochenplan[tag])} Aufgabe(n))"):
            for idx, (v, b, t) in enumerate(wochenplan[tag]):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{v.strftime('%H:%M')} – {b.strftime('%H:%M')}**  \n{t}  \n`KW {kw} / {jahr}`")
                with col2:
                    if st.button("❌", key=f"del_{tag}_{idx}_{key}"):
                        wochenplan[tag].pop(idx)
                        save_wochenplaene(st.session_state.wochenplaene)
                        st.rerun()
