from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from typing import Dict, Optional
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import inspect, logging, io, os, re, json
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/templates"), name="static")

RECORDS_PATH = "app/records.json"
FEEDBACK_PATH = "app/feedback.json"

def save_line_json(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def load_lines_json(path: str):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except:
                    pass
    return out

def classify_vital_signs(vitals: Dict[str, float]) -> Dict[str, str]:
    """Return Normal / Abnormal / OutOfRange / Missing for each vital."""
    result = {}
    ranges = {
        "Systolic": {"valid": (60, 260), "normal": (90, 120)},
        "Diastolic": {"valid": (30, 160), "normal": (60, 80)},
        "TEMPERATURE": {"valid": (30.0, 43.0), "normal": (36.1, 37.8)},
        "hr": {"valid": (30, 220), "normal": (60, 100)},
        "RR": {"valid": (6, 35), "normal": (12, 20)},
        "O2_Sat": {"valid": (50, 100), "normal": (95, 100)},
        "GCS": {"valid": (3, 15), "normal": (15, 15)},
        "blood_glucose": {"valid": (20, 600), "normal": (70, 140)},
        "Pain_Scale": {"valid": (0, 10), "normal": (0, 3)},
    }
    for key, meta in ranges.items():
        v = vitals.get(key)
        if v in (None, ""):
            result[key] = "Missing"
            continue
        vmin, vmax = meta["valid"]; nmin, nmax = meta["normal"]
        try:
            val = float(v)
            if not (vmin <= val <= vmax):
                result[key] = "OutOfRange"
            elif nmin <= val <= nmax:
                result[key] = "Normal"
            else:
                result[key] = "Abnormal"
        except:
            result[key] = "Missing"
    return result

def vitals_any_out_of_range(vital_classes: Dict[str, str]) -> bool:
    return any(v == "OutOfRange" for v in vital_classes.values())

# قواعدك
from app.rules import determine_ctas

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_data(
    request: Request,
    systolic: Optional[int] = Form(None),
    diastolic: Optional[int] = Form(None),
    hr: Optional[int] = Form(None),
    o2_sat: Optional[int] = Form(None),
    rr: Optional[int] = Form(None),
    temp: Optional[float] = Form(None),
    gcs: Optional[int] = Form(None),
    pain_scale: Optional[int] = Form(None),
    location_of_pain: Optional[str] = Form(None),
    pain_duration: Optional[str] = Form(None),
    blood_glucose: Optional[float] = Form(None),
    blood_glucose_symptoms: Optional[str] = Form(None),
    chief_complaint: Optional[str] = Form(None),
    history: Optional[str] = Form(None),
    symptoms_present: Optional[str] = Form(None),
    distress_level: Optional[str] = Form(None)
):
    # نحول yes/no لبوولين
    symptoms_bool = ((symptoms_present or "").lower() == "yes")

    # dict كامل لعرض التصنيف حتى لو مفقود
    vitals_full = {
        "Systolic": systolic, "Diastolic": diastolic, "hr": hr, "TEMPERATURE": temp,
        "O2_Sat": o2_sat, "RR": rr, "GCS": gcs, "Pain_Scale": pain_scale,
        "Location_of_Pain": location_of_pain, "Pain_Duration": pain_duration,
        "blood_glucose": blood_glucose, "blood_glucose_symptoms": blood_glucose_symptoms
    }

    # dict مختصر للrules (بدون None) لتفادي مقارنات مع None
    vitals_for_rules = {k: v for k, v in vitals_full.items() if v not in (None, "")}

    vital_classes = classify_vital_signs(vitals_full)
    form_error = "One or more inputs out of safe range — please review." if vitals_any_out_of_range(vital_classes) else None

    # determine_ctas قد يعتمد على وجود/غياب المفاتيح
    ctas_level, reason = determine_ctas(vitals_for_rules, chief_complaint or "", history or "", symptoms_bool, distress_level or "")

    record = {
        "timestamp": str(datetime.now()),
        "vitals": vitals_full,
        "symptoms_present": symptoms_bool,
        "chief_complaint": chief_complaint or "",
        "history": history or "",
        "distress_level": distress_level or "",
        "ctas_level": ctas_level,
        "reason": reason
    }
    try:
        save_line_json(RECORDS_PATH, record)
    except Exception as e:
        print("save_record error:", e)

    return templates.TemplateResponse("index.html", {
        "request": request, "ctas_level": ctas_level, "reason": reason,
        "vital_classes": vital_classes, "form_error": form_error,
        "systolic": systolic or "", "diastolic": diastolic or "", "temp": temp or "", "hr": hr or "", "rr": rr or "",
        "o2_sat": o2_sat or "", "gcs": gcs or "", "blood_glucose": blood_glucose or "", "pain_scale": pain_scale or "",
        "location_of_pain": location_of_pain or "", "pain_duration": pain_duration or "",
        "symptoms_present": ("yes" if symptoms_bool else "no") if symptoms_present else "",
        "distress_level": distress_level or "",
        "blood_glucose_symptoms": blood_glucose_symptoms or "",
        "chief_complaint": chief_complaint or "", "history": history or ""
    })

@app.post("/save-feedback")
async def save_feedback(request: Request):
    try:
        payload = {}
        if "application/json" in (request.headers.get("content-type") or "").lower():
            payload = await request.json()
        else:
            form = await request.form()
            payload = dict(form)

        # fallback من آخر record
        recs = load_lines_json(RECORDS_PATH)
        last_rec = recs[-1] if recs else {}
        payload.setdefault("timestamp", str(datetime.now()))
        payload.setdefault("ctas_level", last_rec.get("ctas_level"))
        payload.setdefault("chief_complaint", last_rec.get("chief_complaint"))
        payload.setdefault("history", last_rec.get("history"))
        payload.setdefault("reason", last_rec.get("reason"))

        save_line_json(FEEDBACK_PATH, payload)
        return {"ok": True, "saved": payload}
    except Exception as e:
        return JSONResponse({"error": f"Failed to save feedback: {e}"}, status_code=500)

@app.get("/radar_chart")
async def radar_chart(reason: str):
    return await run_in_threadpool(generate_radar_chart, reason)

def generate_radar_chart(reason: str):
    try:
        reason_list = [r.strip() for r in reason.split(",") if r.strip()]
        ctas_levels = ['CTAS 1','CTAS 2','CTAS 3','CTAS 4','CTAS 5']
        ctas_colors = {'CTAS 1':'#206CF9','CTAS 2':'#FF3B30','CTAS 3':'#FFD60A','CTAS 4':'#34C759','CTAS 5':'#E5E7EB'}
        counts = {k:0 for k in ctas_levels}
        for it in reason_list:
            low = it.lower()
            for lvl in ctas_levels:
                if lvl.lower() in low: counts[lvl] += 1
        total = sum(counts.values()) or 1
        probs = [counts[k]/total for k in ctas_levels]

        angles = np.linspace(0, 2*np.pi, len(ctas_levels), endpoint=False).tolist()
        angles += angles[:1]; radii = probs + probs[:1]

        fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))
        bg = '#090e39'; ax.set_facecolor(bg); plt.gcf().set_facecolor(bg)
        ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1); ax.set_ylim(0,1.0)
        ax.set_rgrids([0.25,0.5,0.75,1.0], labels=['25%','50%','75%','100%'], angle=0, color='#8fbff0', alpha=0.9, fontsize=9)
        ax.grid(color='#59d2fd', linestyle='--', linewidth=0.6, alpha=0.35)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels(ctas_levels, color='#59d2fd', fontsize=11)
        ax.plot(angles, radii, linewidth=1.8, color='#59d2fd', alpha=0.9)
        ax.fill(angles, radii, color='#59d2fd', alpha=0.25)
        for i, lvl in enumerate(ctas_levels):
            ax.scatter([angles[i]],[probs[i]], s=80, color=ctas_colors[lvl], zorder=5)
            ax.text(angles[i], min(1.0, probs[i]+0.12), f"{counts[lvl]} • {probs[i]*100:.0f}%", color=ctas_colors[lvl],
                    ha='center', va='center', fontsize=10, fontweight='bold')
        ax.set_title('CTAS Probability Radar', color='#59d2fd', fontsize=15, pad=22)
        buf = BytesIO(); plt.tight_layout(); plt.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0); plt.close()
        return StreamingResponse(buf, media_type='image/png')
    except Exception as e:
        logging.error(f"Radar error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/graph_data")
def graph_data(reason: str = Query(default=""), chief: str = Query(default=""), history: str = Query(default="")):
    reasons = [r.strip() for r in reason.split(",") if r.strip()]
    ctas_levels = [f"CTAS {i}" for i in range(1,6)]

    nodes = [{"id":"Patient","name":"Patient","group":"patient"}]
    nodes += [{"id":lvl,"name":lvl,"group":"ctas"} for lvl in ctas_levels]
    if chief:   nodes.append({"id":"Chief", "name": f"Chief: {chief[:80]}", "group":"text"})
    if history: nodes.append({"id":"History", "name": f"History: {history[:80]}", "group":"text"})

    links = []
    for i, txt in enumerate(reasons, start=1):
        rid = f"R{i}"
        lvl_found = next((L for L in ctas_levels if L.lower() in txt.lower()), None)
        nodes.append({"id":rid,"name":txt,"group":"rule"})
        links.append({"source":"Patient","target":rid,"value":1})
        if lvl_found: links.append({"source":rid,"target":lvl_found,"value":2})
    if chief:   links.append({"source":"Patient","target":"Chief","value":1})
    if history: links.append({"source":"Patient","target":"History","value":1})
    present = [lvl for lvl in ctas_levels if any(lvl.lower() in it.lower() for it in reasons)]
    if present: links.append({"source":"Patient","target":present[0],"value":3})

    in_count = {}
    for l in links:
        t = l["target"]["id"] if isinstance(l.get("target"), dict) else l.get("target")
        s = l["source"]["id"] if isinstance(l.get("source"), dict) else l.get("source")
        if str(t).startswith("CTAS") and s not in ("Patient","Chief","History"):
            in_count[t] = in_count.get(t,0)+1
    for n in nodes: n["inCount"] = in_count.get(n["id"],0)
    return {"nodes": nodes, "links": links}

@app.get("/analytics")
def analytics():
    recs = load_lines_json(RECORDS_PATH)
    fbs  = load_lines_json(FEEDBACK_PATH)
    samples = len(recs) or None
    accepted = declined = 0
    for fb in fbs:
        d = (fb.get("decision") or fb.get("feedback_decision") or "").lower()
        if d == "accept": accepted += 1
        elif d == "decline": declined += 1
    return {"accepted": accepted or None, "declined": declined or None, "samples": samples, "feedback": (len(fbs) or None)}

@app.get("/rules_meta")
def rules_meta():
    try:
        import app.rules as rules_mod
        src = inspect.getsource(rules_mod.determine_ctas)
        nums = re.findall(r"rules\.append\(\(\s*([1-5])\s*,", src)
        per = {"CTAS 1":0,"CTAS 2":0,"CTAS 3":0,"CTAS 4":0,"CTAS 5":0}
        for n in nums: per[f"CTAS {n}"] += 1
        return {"per_ctas": per, "total": sum(per.values())}
    except Exception:
        return {"per_ctas": None, "total": None}

@app.get("/rules_search")
def rules_search(term: str = Query(default="")):
    try:
        import app.rules as rules_mod
        src = inspect.getsource(rules_mod.determine_ctas)
        patt = re.compile(r"rules\.append\(\(\s*([1-5])\s*,\s*([ru]?)?['\"](.+?)['\"]\s*\)\)", re.S)
        items = []
        for m in patt.finditer(src):
            items.append({"ctas": int(m.group(1)), "desc": m.group(3).strip()})
        if term:
            t = term.lower()
            items = [x for x in items if t in x["desc"].lower()]
        items.sort(key=lambda x: (x["ctas"], x["desc"]))
        return items
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ---- Analytics for CTAS cards/modals
@app.get("/analytics_by_ctas")
def analytics_by_ctas():
    recs = load_lines_json(RECORDS_PATH)
    fbs  = load_lines_json(FEEDBACK_PATH)

    totals = {f"CTAS {i}": 0 for i in range(1,6)}
    records_by_ctas = {f"CTAS {i}": [] for i in range(1,6)}
    for r in recs:
        lvl = r.get("ctas_level")
        if isinstance(lvl, str) and lvl.isdigit(): lvl = int(lvl)
        if isinstance(lvl, int) and 1 <= lvl <= 5:
            key = f"CTAS {lvl}"
            totals[key] += 1
            records_by_ctas[key].append({
                "id": r.get("timestamp",""),
                "ctas": key,
                "chief": r.get("chief_complaint",""),
                "history": r.get("history",""),
                "timestamp": r.get("timestamp",""),
                "source": "record"
            })
    for k,v in records_by_ctas.items():
        v.sort(key=lambda x: x["timestamp"], reverse=True)
        records_by_ctas[k] = v[:120]

    acc = {f"CTAS {i}": 0 for i in range(1,6)}
    rej = {f"CTAS {i}": 0 for i in range(1,6)}
    cases_acc, cases_rej = [], []

    for fb in fbs:
        d = (fb.get("decision") or fb.get("feedback_decision") or "").lower()
        lvl = fb.get("ctas_level")
        if isinstance(lvl, str) and lvl.isdigit(): lvl = int(lvl)
        if not (isinstance(lvl, int) and 1 <= lvl <= 5):
            m = re.search(r"ctas\s*([1-5])", (fb.get("reason") or fb.get("reasons") or ""), re.I)
            if m: lvl = int(m.group(1))
        if not (isinstance(lvl, int) and 1 <= lvl <= 5): continue

        key = f"CTAS {lvl}"
        obj = {
            "id": fb.get("id") or fb.get("timestamp") or "",
            "ctas": key,
            "chief": fb.get("chief_complaint") or fb.get("chief") or "",
            "history": fb.get("history") or "",
            "timestamp": fb.get("timestamp") or "",
            "source": "feedback"
        }
        if d == "accept": acc[key] += 1; cases_acc.append(obj)
        elif d == "decline": rej[key] += 1; cases_rej.append(obj)

    accepted = {k: {"count": acc[k],
                    "conf": int(round((acc[k] / totals[k] * 100), 0)) if totals[k] else None}
                for k in totals.keys()}
    rejected = {k: {"count": rej[k]} for k in totals.keys()}

    return {
        "accepted": accepted,
        "rejected": rejected,
        "totals": totals,
        "cases": {"accepted": cases_acc, "rejected": cases_rej},
        "records": records_by_ctas
    }
