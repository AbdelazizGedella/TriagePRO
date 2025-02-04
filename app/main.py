from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from datetime import datetime
from app.rules import determine_ctas
from jinja2 import Environment, FileSystemLoader
import numpy as np
import logging
import matplotlib
matplotlib.use('Agg')
from fastapi.concurrency import run_in_threadpool
import matplotlib.pyplot as plt
import io
from io import BytesIO
import json
from datetime import datetime
import os



app = FastAPI()

# Templates and static files setup
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/templates"), name="static")

# Record inputs and outputs
def save_record(data):
    try:
        with open("app/records.json", "a") as file:
            file.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"Error saving record: {e}")
        
@app.post("/save-feedback")
async def save_feedback(request: Request):
    try:
        # Parse incoming form data
        form_data = await request.form()

        # Create a dictionary with all the submitted data
        feedback_data = {
            "timestamp": str(datetime.now()),
            "systolic": form_data.get("systolic"),
            "diastolic": form_data.get("diastolic"),
            "temp": form_data.get("temp"),
            "hr": form_data.get("hr"),
            "rr": form_data.get("rr"),
            "o2_sat": form_data.get("o2_sat"),
            "gcs": form_data.get("gcs"),
            "blood_glucose": form_data.get("blood_glucose"),
            "pain_scale": form_data.get("pain_scale"),
            "location_of_pain": form_data.get("location_of_pain"),
            "pain_duration": form_data.get("pain_duration"),
            "symptoms_present": form_data.get("symptoms_present"),
            "distress_level": form_data.get("distress_level"),
            "blood_glucose_symptoms": form_data.get("blood_glucose_symptoms"),
            "chief_complaint": form_data.get("chief_complaint"),
            "history": form_data.get("history"),
            "ctas_level": form_data.get("ctas_level"),
            "reason": form_data.get("reason"),
            "decision": form_data.get("decision"),
            "feedback_text": form_data.get("feedback_text"),
        }

        # Define the feedback file path
        feedback_file_path = "app/feedback.json"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(feedback_file_path), exist_ok=True)

        # Save the feedback in the JSON file
        with open(feedback_file_path, "a") as feedback_file:
            feedback_file.write(json.dumps(feedback_data) + "\n")

        # Return success response
        return {"message": "Feedback saved successfully!", "data": feedback_data}

    except Exception as e:
        # Return error response in case of failure
        return {"error": f"Failed to save feedback: {str(e)}"}


    

@app.get("/radar_chart")
async def radar_chart(reason: str):
    return await run_in_threadpool(generate_radar_chart, reason)

def generate_radar_chart(reason: str):
    try:
        reason_list = reason.split(",")  # Split on commas
        ctas_levels = ['CTAS 1', 'CTAS 2', 'CTAS 3', 'CTAS 4', 'CTAS 5']
        ctas_colors = ['#0000FF', '#FF0000', '#FFFF00', '#00FF00', '#FFFFFF']  # Blue, Red, Yellow, Green, White
        ctas_counts = {level: 0 for level in ctas_levels}

        for item in reason_list:
            for level in ctas_levels:
                if level in item:
                    ctas_counts[level] += 1

        probabilities = [count for count in ctas_counts.values()]
        total = sum(probabilities)
        probabilities = [p / total if total > 0 else 0 for p in probabilities]
        probabilities += probabilities[:1]

        angles = np.linspace(0, 2 * np.pi, len(ctas_levels), endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        ax.set_facecolor('#090e39')
        plt.gcf().set_facecolor('#090e39')

        for i in range(len(ctas_levels)):
            ax.plot(
                [angles[i], angles[i]], [0, probabilities[i]],
                color=ctas_colors[i], linewidth=2,
                label=f'{ctas_levels[i]}: {ctas_counts[ctas_levels[i]]} ({probabilities[i] * 100:.1f}%)'
            )

        ax.fill(angles, probabilities, color='#59d2fd', alpha=0.45)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(ctas_levels, color='#59d2fd')
        ax.set_title('Radar Chart of CTAS Level Probabilities', size=15, color='#59d2fd')
        ax.grid(color='#59d2fd', linestyle='--', linewidth=0.7)

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type='image/png')

    except Exception as e:
        logging.error(f"Error generating radar chart: {e}")
        return {"error": f"Failed to generate radar chart: {e}"}










@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_data(
    request: Request,
    systolic: int = Form(...),
    diastolic: int = Form(...),
    hr: int = Form(...),
    o2_sat: int = Form(...),
    rr: int = Form(...),
    temp: float = Form(...),
    gcs: int = Form(...),
    pain_scale: int = Form(...),
    location_of_pain: str = Form(...),  # New field
    pain_duration: str = Form(...),    # New field
    blood_glucose: float = Form(...),  # Blood glucose in mg/dL
    blood_glucose_symptoms: str = Form(...),  # New field
    chief_complaint: str = Form(...),
    history: str = Form(...),
    symptoms_present: str = Form(...),
    distress_level: str = Form(...)  # New parameter

    

):
    


    # Convert symptoms_present to boolean
    symptoms_present = symptoms_present.lower() == "yes"









    # Evaluate CTAS level
    vitals = {
        "Systolic": systolic,
        "Diastolic": diastolic,
        "hr": hr,
        "TEMPERATURE": temp,
        "O2_Sat": o2_sat,
        "RR": rr,
        "GCS": gcs,
        "Pain_Scale": pain_scale,
        "Location_of_Pain": location_of_pain,
        "Pain_Duration": pain_duration,
        "blood_glucose": blood_glucose,
        "blood_glucose_symptoms": blood_glucose_symptoms


    }
    ctas_level, reason = determine_ctas(vitals, chief_complaint, history, symptoms_present, distress_level)

    # Save inputs and outputs
    record = {
        "timestamp": str(datetime.now()),
        "vitals": vitals,
        "symptoms_present": symptoms_present,
        "chief_complaint": chief_complaint,
        "history": history,
        "distress_level": distress_level,  # Save the distress level
        "ctas_level": ctas_level,
        "reason": reason
    }
    save_record(record)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "ctas_level": ctas_level,
            "reason": reason,
            "inputs": record,
              # Pass individual input values
        "systolic": systolic,
        "diastolic": diastolic,
        "temp": temp,
        "hr": hr,
        "rr": rr,
        "o2_sat": o2_sat,
        "gcs": gcs,
        "blood_glucose": blood_glucose,
        "pain_scale": pain_scale,
        "location_of_pain": location_of_pain,
        "pain_duration": pain_duration,
        "symptoms_present": symptoms_present,
        "distress_level": distress_level,
        "blood_glucose_symptoms": blood_glucose_symptoms,
        "chief_complaint": chief_complaint,
        "history": history,
        
        }
    )
