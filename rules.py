from typing import Any, Dict, List, Tuple

def determine_ctas(
    vitals: Dict[str, Any],
    chief_complaint: str,
    history: str,
    symptoms_present: bool,
    distress_level: str
) -> Tuple[int, List[str]]:
    # helpers
    def num(x):
        try:
            if x is None or x == "": return None
            return float(x)
        except:
            return None

    def between(v, a, b): return v is not None and a <= v <= b
    def lt(v, a):        return v is not None and v <  a
    def lte(v, a):       return v is not None and v <= a
    def gt(v, a):        return v is not None and v >  a
    def gte(v, a):       return v is not None and v >= a

    chief = (chief_complaint or "").lower()
    hist  = (history or "").lower()

    systolic   = num(vitals.get("Systolic"))
    diastolic  = num(vitals.get("Diastolic"))
    gcs        = num(vitals.get("GCS"))
    o2_sat     = num(vitals.get("O2_Sat"))
    rr         = num(vitals.get("RR"))
    temp       = num(vitals.get("TEMPERATURE"))
    hr         = num(vitals.get("hr"))
    pain_scale = num(vitals.get("Pain_Scale"))
    location_of_pain = (vitals.get("Location_of_Pain") or "")
    pain_duration    = (vitals.get("Pain_Duration") or "")
    blood_glucose    = num(vitals.get("blood_glucose"))
    blood_glucose_symptoms = (vitals.get("blood_glucose_symptoms") or "")

    rules: List[Tuple[int,str]] = []

    # ---------- CTAS 1 ----------
    if "cardiac arrest" in chief:
        rules.append((1, "Cardiac Arrest is a life-threatening condition requiring immediate resuscitation. (CTAS 1)"))

    if "respiratory arrest" in chief:
        rules.append((1, "Respiratory Arrest requires immediate aggressive interventions. (CTAS 1)"))

    if "major trauma" in chief and "shock" in chief:
        rules.append((1, "Major trauma with shock requires immediate intervention—assigning CTAS 1."))

    if "shortness of breath" in chief and ("severe" in chief or "respiratory distress" in chief):
        rules.append((1, "Severe shortness of breath/respiratory distress—CTAS 1."))

    # Shock bundle (guarded)
    if (
        "shock" in chief and
        (between(hr,130,180) or lte(hr,50)) and
        (between(systolic,200,220) or between(diastolic,110,130)) and
        lt(gcs,15) and
        (lt(temp,35) or gt(temp,38))
    ):
        rules.append((1, "Severe end-organ hypoperfusion pattern—CTAS 1."))

    # ---------- Hemodynamic compromise ----------
    if ("hemodynamic compromise" in chief and gt(hr,100) and ((systolic is not None and systolic < 90) or (diastolic is not None and diastolic < 60)) and gte(gcs,15)):
        rules.append((2, "Evidence of hemodynamic compromise—CTAS 2."))

    # ---------- Blood pressure + symptoms ----------
    if ((gt(systolic,220) or gt(diastolic,130)) and symptoms_present):
        rules.append((2, "SBP > 220 or DBP > 130 with symptoms—CTAS 2."))
    if ((gt(systolic,220) or gt(diastolic,130)) and not symptoms_present):
        rules.append((3, "SBP > 220 or DBP > 130 without symptoms—CTAS 3."))
    if ((between(systolic,200,220) or between(diastolic,110,130)) and symptoms_present):
        rules.append((3, "SBP 200–220 / DBP 110–130 with symptoms—CTAS 3."))
    if ((between(systolic,200,220) or between(diastolic,110,130)) and not symptoms_present):
        rules.append((4, "SBP 200–220 / DBP 110–130 without symptoms—CTAS 4."))

    # ---------- Distress + O2 ----------
    if (distress_level == "Severe") or lt(o2_sat,90):
        rules.append((1, "Severe distress or O2 < 90%—CTAS 1."))
    if (distress_level == "Moderate") or (o2_sat is not None and 90 <= o2_sat < 92):
        rules.append((2, "Moderate distress or O2 90–92%—CTAS 2."))
    if (distress_level == "Mild") and (o2_sat is not None and 92 <= o2_sat <= 94):
        rules.append((3, "Mild distress with O2 92–94%—CTAS 3."))
    if (distress_level == "None") and gt(o2_sat,94):
        rules.append((5, "No distress and O2 > 94%—CTAS 5."))

    # ---------- GCS ----------
    if between(gcs,3,9):
        rules.append((1, "Unconscious (GCS 3–9) / seizure—CTAS 1."))
    if between(gcs,10,13):
        rules.append((2, "Altered LOC (GCS 10–13)—CTAS 2."))
    if gcs == 14:
        rules.append((4, "Confusion (GCS 14)—CTAS 4 (context)."))
    if gcs == 15:
        rules.append((5, "Normal GCS (15)—CTAS 5 (context)."))

    # ---------- Temperature ----------
    if gte(temp,38):
        if "immunocompromised" in chief:
            rules.append((2, "Immunocompromised with fever—CTAS 2."))
        elif "septic" in chief:
            rules.append((2, "Looks septic (fever + SIRS)—CTAS 2."))
        elif "unwell" in chief:
            rules.append((3, "Looks unwell (fever)—CTAS 3."))
        elif "well" in chief:
            rules.append((4, "Looks well (isolated fever)—CTAS 4."))
    if lt(temp,35):
        rules.append((2, "Hypothermia < 35°C—CTAS 2."))

    # ---------- Pain ----------
    if pain_scale is not None:
        if between(pain_scale,8,10):
            if location_of_pain == "Central":
                rules.append((2 if pain_duration == "Acute" else 3,
                              f"Severe central {(pain_duration or '').lower()} pain—CTAS {'2' if pain_duration=='Acute' else '3'}."))
            elif location_of_pain == "Peripheral":
                rules.append((3 if pain_duration == "Acute" else 4,
                              f"Severe peripheral {(pain_duration or '').lower()} pain—CTAS {'3' if pain_duration=='Acute' else '4'}."))
        elif between(pain_scale,4,7):
            if location_of_pain == "Central":
                rules.append((3 if pain_duration == "Acute" else 4,
                              f"Moderate central {(pain_duration or '').lower()} pain—CTAS {'3' if pain_duration=='Acute' else '4'}."))
            elif location_of_pain == "Peripheral":
                rules.append((4 if pain_duration == "Acute" else 5,
                              f"Moderate peripheral {(pain_duration or '').lower()} pain—CTAS {'4' if pain_duration=='Acute' else '5'}."))
        elif between(pain_scale,1,3):
            if location_of_pain == "Central":
                rules.append((4 if pain_duration == "Acute" else 5,
                              f"Mild central {(pain_duration or '').lower()} pain—CTAS {'4' if pain_duration=='Acute' else '5'}."))
            elif location_of_pain == "Peripheral":
                rules.append((5, "Mild peripheral pain—CTAS 5."))
        elif pain_scale == 0:
            rules.append((5, "No pain—CTAS 5."))

    # ---------- Glucose ----------
    if lt(blood_glucose,50):
        if blood_glucose_symptoms in ["Confusion","Diaphoresis","Behavioural Change","Seizure","Acute Focal Deficits"]:
            rules.append((2, "Hypoglycemia <50 with symptoms—CTAS 2."))
        else:
            rules.append((3, "Hypoglycemia <50 without symptoms—CTAS 3."))
    elif gt(blood_glucose,300):
        if blood_glucose_symptoms in ["Dyspnea","Dehydration","Tachypnea","Thirst","Polyuria","Weakness"]:
            rules.append((2, "Hyperglycemia >300 with symptoms—CTAS 2."))
        else:
            rules.append((3, "Hyperglycemia >300 without symptoms—CTAS 3."))

    # ---------- CTAS 2 examples ----------
    if "shortness of breath" in chief and ("moderate" in chief or "respiratory distress" in chief):
        rules.append((2, "Moderate SOB/respiratory distress—CTAS 2."))
    if "chest pain" in chief and (("radiating" in hist) or ("sweating" in hist) or ("cardiac" in hist)):
        rules.append((2, "Chest pain with radiating/sweating/cardiac features—CTAS 2."))
    if "abdominal pain" in chief and (pain_scale is not None and pain_scale >= 8):
        rules.append((2, "Abdominal pain with high severity—CTAS 2."))
    if "headache" in chief and (pain_scale is not None and pain_scale >= 8):
        rules.append((2, "Severe headache, consider serious causes—CTAS 2."))
    if "major trauma" in chief:
        rules.append((2, "Major trauma (no shock) example—CTAS 2."))

    # ---------- CTAS 3 ----------
    if "abdominal pain" in chief and (pain_scale is not None and 4 <= pain_scale <= 7):
        rules.append((3, "Abdominal pain (4–7/10)—CTAS 3."))
    if "headache" in chief and (pain_scale is not None and 4 <= pain_scale <= 7):
        rules.append((3, "Headache (4–7/10)—CTAS 3."))
    if "bloody diarrhea" in chief:
        rules.append((3, "Diarrhea (uncontrolled bloody)—CTAS 3."))

    # ---------- CTAS 4 ----------
    if "confusion" in chief and gte(gcs,14):
        rules.append((4, "Chronic confusion baseline—CTAS 4."))
    if "constipation" in chief and (pain_scale is not None and 4 <= pain_scale <= 10):
        rules.append((4, "Constipation (mild/mod pain)—CTAS 4."))

    # ---------- CTAS 5 ----------
    if "medication refill" in chief or "medication request" in chief:
        rules.append((5, "Medication refill/request—CTAS 5."))
    if "dressing change" in chief:
        rules.append((5, "Dressing change (uncomplicated)—CTAS 5."))
    if "bite" in chief and (pain_scale is not None and 1 <= pain_scale <= 3):
        rules.append((5, "Minor bite + mild pain—CTAS 5."))
    if "diarrhea" in chief and "bloody" not in chief:
        rules.append((5, "Diarrhea (mild, no dehydration)—CTAS 5."))

    # ---------- Bleeding ----------
    if "bleeding" in chief and ("head" in chief or "neck" in chief):
        rules.append((2, "Bleeding from head/neck—CTAS 2."))
    if "bleeding" in chief and any(s in chief for s in ["chest","abdomen","pelvis","spine"]):
        rules.append((2, "Bleeding chest/abdomen/pelvis/spine—CTAS 2."))
    if "bleeding" in chief and "vaginal" in chief:
        rules.append((2, "Massive vaginal hemorrhage—CTAS 2."))
    if "bleeding" in chief and any(s in chief for s in ["iliopsoas","hip"]):
        rules.append((2, "Bleeding iliopsoas/hip—CTAS 2."))
    if "bleeding" in chief and "extremity muscle compartments" in chief:
        rules.append((2, "Bleeding extremity compartments—CTAS 2."))
    if "bleeding" in chief and any(s in chief for s in ["fractures","dislocations"]):
        rules.append((2, "Bleeding with fractures/dislocations—CTAS 2."))
    if "bleeding" in chief and "deep lacerations" in chief:
        rules.append((2, "Bleeding deep lacerations—CTAS 2."))
    if "bleeding" in chief and "uncontrolled" in chief:
        rules.append((2, "Any uncontrolled bleeding—CTAS 2."))
    if "bleeding" in chief and "nose" in chief:
        rules.append((3, "Epistaxis—CTAS 3."))
    if "bleeding" in chief and "mouth" in chief:
        rules.append((3, "Oral/gums bleeding—CTAS 3."))
    if "bleeding" in chief and "joints" in chief:
        rules.append((3, "Hemarthroses—CTAS 3."))
    if "menorrhagia" in chief:
        rules.append((3, "Menorrhagia—CTAS 3."))
    if "abrasions" in chief:
        rules.append((3, "Abrasions/superficial lacerations—CTAS 3."))

    # ---------- Mechanism of injury ----------
    if "ejection from vehicle" in chief:
        rules.append((2, "Ejection/rollover—CTAS 2."))
    if "intrusion" in chief and "passenger" in chief:
        rules.append((2, "Significant intrusion into passenger space—CTAS 2."))
    if "fall" in chief and ">18 ft" in chief:
        rules.append((2, "Fall >18 ft—CTAS 2."))
    if "penetrating injury" in chief:
        rules.append((2, "Penetrating head/neck/torso—CTAS 2."))
    if "head" in chief and "striking windshield" in chief:
        rules.append((2, "Unrestrained head trauma w/ windshield—CTAS 2."))
    if "pedestrian struck" in chief:
        rules.append((2, "Pedestrian struck—CTAS 2."))
    if "fall" in chief and ">3 ft" in chief:
        rules.append((2, "Head injury fall >3ft/5 stairs—CTAS 2."))
    if "axial load to the head" in chief:
        rules.append((2, "Axial load—CTAS 2."))
    if "rollover" in chief:
        rules.append((2, "Vehicle rollover—CTAS 2."))

    # ---------- Dehydration ----------
    if ("severe dehydration" in chief) or ("dehydration" in chief and "shock" in chief):
        rules.append((1, "Severe dehydration + shock—CTAS 1."))
    if ("moderate dehydration" in chief or
        ("dehydration" in chief and any(s in chief for s in ["dry mucous membranes","tachycardia","decreased skin turgor","decreased urine output"]))):
        rules.append((2, "Moderate dehydration features—CTAS 2."))
    if ("mild dehydration" in chief or
        ("dehydration" in chief and any(s in chief for s in ["stable vital signs","thirst","concentrated urine","decreased fluid intake"]))):
        rules.append((3, "Mild dehydration—CTAS 3."))
    if ("potential dehydration" in chief or ("fluid loss" in chief and "ongoing" in chief) or ("difficulty tolerating oral fluids" in chief)):
        rules.append((4, "Potential dehydration—CTAS 4."))

    # ---------- Second-order modifiers ----------
    if "chest pain" in chief and ("ripping" in chief or "tearing" in chief):
        rules.append((2, "Ripping/tearing chest pain—CTAS 2."))
    if "extremity weakness" in chief or "cva symptoms" in chief:
        if "onset < 4.5 hours" in chief:
            rules.append((2, "CVA symptoms onset <4.5h—CTAS 2."))
        elif "onset > 4.5 hours" in chief or "resolved" in chief:
            rules.append((3, "CVA symptoms onset >4.5h / resolved—CTAS 3."))
    if "difficulty swallowing" in chief or "dysphagia" in chief:
        if "drooling" in chief or "stridor" in chief:
            rules.append((2, "Dysphagia + drooling/stridor—CTAS 2."))
        elif "foreign body" in chief:
            rules.append((3, "Dysphagia + FB—CTAS 3."))
    if ("extremity injury" in chief or "upper extremity" in chief or "lower extremity" in chief) and "obvious deformity" in chief:
        rules.append((3, "Extremity injury + deformity—CTAS 3."))

    # ---------- Others ----------
    if "stroke" in chief and "slurred speech" in hist:
        rules.append((2, "Possible stroke + slurred speech—CTAS 2."))
    if "seizure" in chief and lt(gcs,14):
        rules.append((2, "Post-seizure with low GCS—CTAS 2."))
    if "mild skin rash" in chief:
        rules.append((4, "Mild rash—CTAS 4."))
    if "sore throat" in chief and "no fever" in hist:
        rules.append((5, "Sore throat without fever—CTAS 5."))

    # Fallback
    if not rules:
        return 5, ["Insufficient data or minor complaints — defaulting to CTAS 5."]

    highest = min(r[0] for r in rules)
    return highest, [r[1] for r in rules]
