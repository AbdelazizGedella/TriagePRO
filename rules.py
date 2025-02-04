def determine_ctas(vitals, chief_complaint, history,symptoms_present,distress_level):
    systolic = vitals["Systolic"]
    diastolic = vitals["Diastolic"]
    gcs = vitals["GCS"]
    o2_sat = vitals["O2_Sat"]
    rr = vitals["RR"]
    temp = vitals["TEMPERATURE"]
    hr = vitals["hr"]
    pain_scale = vitals["Pain_Scale"]
    location_of_pain = vitals["Location_of_Pain"]  # "Central" or "Peripheral"
    pain_duration = vitals["Pain_Duration"]  # "Acute" or "Chronic"
    blood_glucose = vitals["blood_glucose"]
    blood_glucose_symptoms = vitals["blood_glucose_symptoms"]

    rules = []

    # CTAS Level 1 (Life-threatening conditions requiring immediate intervention)

 
    if "cardiac arrest" in chief_complaint.lower():
        rules.append((1, "Cardiac Arrest is a life-threatening condition requiring immediate resuscitation."))
    
    if "respiratory arrest" in chief_complaint.lower():
        rules.append((1, "Respiratory Arrest requires immediate aggressive interventions to prevent fatal outcomes."))
    
    if "major trauma" and "shock" in chief_complaint.lower():
        rules.append((1, "Major trauma with shock requires immediate intervention—assigning CTAS 1."))

    if "shortness of breath" in chief_complaint.lower() and ("severe" in chief_complaint.lower() or "respiratory distress" in chief_complaint.lower()):
        rules.append((1, "Severe shortness of breath or respiratory distress requires immediate intervention—assigning CTAS 1."))


    #SHOCK Rules

    if (
        "shock" in chief_complaint.lower() 
        and (
            (130 <= hr <= 180)  # Tachycardia range, adjust if necessary
            or (hr <= 50)  # Bradycardia range
        )
        and (
            (200 <= systolic <= 220) 
            or (110 <= diastolic <= 130)
        )
        and gcs < 15 
        and (
            temp < 35 
            or temp > 38
        )
    ):
        rules.append((1, "Evidence of severe end-organ hypoperfusion; weak or thready pulse, hypotension, significant tachycardia or bradycardia, decreased level of consciousness. Could also appear as flushed, febrile, toxic, as in septic shock."))


#Hemodynamic compromise Rules

    if (
        "hemodynamic compromise" in chief_complaint.lower() 
        and (
            hr > 100  # Tachycardia, assuming normal HR is 60-100 bpm; adjust as needed
        )
        and (
            systolic < 90  # Hypotension, assuming a systolic BP of less than 90 mmHg indicates hypotension; adjust as needed
            or diastolic < 60  # Diastolic hypotension
        )
        and gcs >= 15  # Presumed intact level of consciousness, no significant neurological compromise
    ):
        rules.append((2, "Evidence of hemodynamic compromise: unexplained tachycardia, postural hypotension (by history), or suspected hypotension (lower than normal blood pressure or expected blood pressure for the patient)."))


# Rules for Blood Pressure and syptoms presentation
    
    if (systolic > 220 or diastolic > 130) and symptoms_present:
        rules.append((2, "SBP > 220 or DBP > 130 with symptoms (e.g., headache, nausea, shortness of breath, chest pain)—assigning CTAS 2."))

    if (systolic > 220 or diastolic > 130) and not symptoms_present:
        rules.append((3, "SBP > 220 or DBP > 130 without symptoms—assigning CTAS 3."))

    if (200 <= systolic <= 220 or 110 <= diastolic <= 130) and symptoms_present:
        rules.append((3, "SBP 200–220 or DBP 110–130 with symptoms (e.g., headache, nausea, shortness of breath, chest pain)—assigning CTAS 3."))

    if (200 <= systolic <= 220 or 110 <= diastolic <= 130) and not symptoms_present:
        rules.append((4, "SBP 200–220 or DBP 110–130 without symptoms—assigning CTAS 4 or 5 depending on other factors."))



# Rules for Level of Distress and O2 Saturation

 # Severe distress or very low oxygen saturation
    if distress_level == "Severe" or o2_sat < 90:
        rules.append((1, "Severe distress or O2 Saturation < 90%—assigning CTAS 1."))

    # Moderate distress or low oxygen saturation
    if distress_level == "Moderate" or (90 <= o2_sat < 92):
        rules.append((2, "Moderate distress or O2 Saturation 90–92%—assigning CTAS 2."))

    # Mild distress with borderline oxygen saturation
    if distress_level == "Mild" and 92 <= o2_sat <= 94:
        rules.append((3, "Mild distress and O2 Saturation 92–94%—assigning CTAS 3."))

    # No distress with normal oxygen saturation
    if distress_level == "None" and o2_sat > 94:
        rules.append((5, "No distress and O2 Saturation > 94%—assigning 4 or CTAS 5."))



 # Glassgow Coma Scale CTAS Prediction accordingly

    if gcs >= 3 and gcs <= 9:
        rules.append((1, "Unconscious (GCS 3-9): unable to protect airway, continuous seizure, or progressive deterioration in level of consciousness—assigning CTAS 1."))

    if gcs >= 10 and gcs <= 13:
        rules.append((2, "Altered level of consciousness (GCS 10-13): loss of orientation to person, place, or time; new impairment of recent memory; new onset confusion; agitation—assigning CTAS 2."))

    if gcs == 14:
        # CTAS Level 3, 4, or 5 can be assigned based on other factors
        rules.append((4, "Confusion GCS (14): 3, CTAS 4 based on other symptoms or findings."))

    if gcs == 15:
        # CTAS Level 3, 4, or 5 can be assigned based on other factors
        rules.append((5, "Normal GCS (15): CTAS 5 based on other symptoms or findings."))

    if temp >= 38:
        if "immunocompromised" in chief_complaint.lower():
            rules.append((2, "Immunocompromised (temperature > 38°C): Neutropenia or suspected, chemotherapy, or immunosuppressive drugs, including steroids—assigning CTAS 2."))
        elif "septic" in chief_complaint.lower():
            rules.append((2, "Looks septic (temperature > 38°C): 3 positive SIRS criteria, hemodynamic compromise, moderate respiratory distress, or altered level of consciousness—assigning CTAS 2."))
        elif "unwell" in chief_complaint.lower():
            rules.append((3, "Looks unwell (temperature > 38°C): 1 or 2 positive SIRS criteria, appears ill-looking (flushed, lethargic, anxious, or agitated)—assigning CTAS 3."))
        elif "well" in chief_complaint.lower():
            rules.append((4, "Looks well (temperature > 38°C): Only fever as the positive SIRS criterion, appears comfortable and in no distress—assigning CTAS 4."))

    if temp < 35:
        rules.append((2, "Hypothermia (temperature < 35°C): Suspected sepsis, hypothermic shock, or other life-threatening conditions—assigning CTAS 2."))


       # Severe Pain (8-10)
    if 8 <= pain_scale <= 10:
        if location_of_pain == "Central":
            if pain_duration == "Acute":
                rules.append((2, "Severe pain (8-10) with central acute pain indicates a high urgency condition—assigning CTAS 2."))
            elif pain_duration == "Chronic":
                rules.append((3, "Severe pain (8-10) with central chronic pain indicates a moderately high urgency—assigning CTAS 3."))
        elif location_of_pain == "Peripheral":
            if pain_duration == "Acute":
                rules.append((3, "Severe pain (8-10) with peripheral acute pain requires moderate urgency—assigning CTAS 3."))
            elif pain_duration == "Chronic":
                rules.append((4, "Severe pain (8-10) with peripheral chronic pain suggests a lower urgency—assigning CTAS 4."))

    # Moderate Pain (4-7)
    elif 4 <= pain_scale <= 7:
        if location_of_pain == "Central":
            if pain_duration == "Acute":
                rules.append((3, "Moderate pain (4-7) with central acute pain suggests moderate urgency—assigning CTAS 3."))
            elif pain_duration == "Chronic":
                rules.append((4, "Moderate pain (4-7) with central chronic pain indicates a lower urgency—assigning CTAS 4."))
        elif location_of_pain == "Peripheral":
            if pain_duration == "Acute":
                rules.append((4, "Moderate pain (4-7) with peripheral acute pain indicates moderate urgency—assigning CTAS 4."))
            elif pain_duration == "Chronic":
                rules.append((5, "Moderate pain (4-7) with peripheral chronic pain suggests minimal urgency—assigning CTAS 5."))

    # Mild Pain (1-3)
    elif 1 <= pain_scale <= 3:
        if location_of_pain == "Central":
            if pain_duration == "Acute":
                rules.append((4, "Mild pain (1-3) with central acute pain suggests low urgency—assigning CTAS 4."))
            elif pain_duration == "Chronic":
                rules.append((5, "Mild pain (1-3) with central chronic pain indicates minimal urgency—assigning CTAS 5."))
        elif location_of_pain == "Peripheral":
            if pain_duration in ["Acute", "Chronic"]:
                rules.append((5, "Mild pain (1-3) with peripheral pain (acute or chronic) suggests minimal urgency—assigning CTAS 5."))

    # No Pain (0)
    elif pain_scale == 0:
        rules.append((5, "No pain (0) indicates minimal urgency—assigning CTAS 5."))

 # Blood glucose < 50 mg/dL
    if blood_glucose < 50:
        if blood_glucose_symptoms in ["Confusion", "Diaphoresis", "Behavioural Change", "Seizure", "Acute Focal Deficits"]:
            rules.append((2, "Blood glucose <50 mg/dL with symptoms (e.g., confusion, diaphoresis) indicates critical condition—assigning CTAS 2."))
        elif blood_glucose_symptoms == "None":
            rules.append((3, "Blood glucose <50 mg/dL with no symptoms indicates moderate urgency—assigning CTAS 3."))

    # Blood glucose > 300 mg/dL
    elif blood_glucose > 300:
        if blood_glucose_symptoms in ["Dyspnea", "Dehydration", "Tachypnea", "Thirst", "Polyuria", "Weakness"]:
            rules.append((2, "Blood glucose >300 mg/dL with symptoms (e.g., dyspnea, dehydration) indicates critical condition—assigning CTAS 2."))
        elif blood_glucose_symptoms == "None":
            rules.append((3, "Blood glucose >300 mg/dL with no symptoms indicates moderate urgency—assigning CTAS 3."))


    # CTAS Level 2 (Conditions with significant distress and high potential for deterioration)
    if "shortness of breath" in chief_complaint.lower() and ("moderate" in chief_complaint.lower() or "respiratory distress" in chief_complaint.lower()):
        rules.append((2, "Moderate shortness of breath or respiratory distress requires rapid medical intervention—assigning CTAS 2."))

    if "chest pain" in chief_complaint.lower() and ("radiating" in history.lower() or "sweating" or "cardiac" in history.lower()):
        rules.append((2, "Chest pain with radiating symptoms or sweating suggests possible acute coronary syndrome CTAS 2."))
    

    if "abdominal pain" in chief_complaint.lower() and pain_scale >= 8:
        rules.append((2, "Abdominal pain with moderate severity needs further evaluation—assigning CTAS 2."))
 
    if "headache" in chief_complaint.lower() and pain_scale >= 8:
            rules.append((2, "Headache with sudden onset needs evaluation for possible serious causes—assigning CTAS 2."))
        
    if "major trauma" in chief_complaint.lower():
            rules.append((2, "Major trauma – blunt, no obvious injury + no shock (pedestrian struck by car travelling at speed CTAS 2."))



    # CTAS Level 3 (Conditions with significant distress and high potential for deterioration)
    if "abdominal pain" in chief_complaint.lower() and 4 <= pain_scale <= 7:
            rules.append((3, "Abdominal pain (moderate pain 4-7/10) CTAS 3."))
    
    if "headache" in chief_complaint.lower() and 4 <= pain_scale <= 7:
            rules.append((3, "Headache (moderate pain 4-7/10) CTAS 3."))

    if "Bloody Diarrhea" in chief_complaint.lower():
        rules.append((3, "Diarrhea (uncontrolled bloody diarrhea) CTAS 3"))

    # CTAS Level 4 (Less urgent conditions with stable vitals)

    if "confusion" in chief_complaint.lower() and gcs >= 14:
        rules.append((4, "Confusion (chronic, no change from usual state) CTAS 4"))
   
    if "Constipation" in chief_complaint.lower() and 4 <= pain_scale <= 10:
                rules.append((4, "Constipation (mild pain <4/10) CTAS 4."))
        

    # CTAS Level 5 (Non-urgent conditions)
    
    if "Medication refill" in chief_complaint.lower():
        rules.append((5, "Medication refill requests are non-urgent—assigning CTAS 5."))
    if "Medication request" in chief_complaint.lower():
        rules.append((5, "Medication refill requests are non-urgent—assigning CTAS 5."))
    


    if  "Dressing Change" in chief_complaint.lower():
        rules.append((5, "Dressing change (uncomplicated) CTAS 5."))
      




    if "Dressing Change" in chief_complaint.lower():
        rules.append((5, "Dressing change (uncomplicated) CTAS 5."))
      
    if "bite" in chief_complaint.lower() and 1 <= pain_scale <= 3:
        rules.append((5, "Minor bites (+/- mild acute peripheral pain) CTAS 5."))
    
    if "Diarrhea" in chief_complaint.lower():
        rules.append((5, "Diarrhea (mild, no dehydration CTAS 5"))




# Bleeding Rules

    #CTAS 2 Bleeding Rules
    if "bleeding" in chief_complaint.lower() and ("head" in chief_complaint.lower() or "neck" in chief_complaint.lower()):
        rules.append((2, "Bleeding from head or neck CTAS 2"))

    if "bleeding" in chief_complaint.lower() and ("chest" in chief_complaint.lower() or "abdomen" in chief_complaint.lower() or "pelvis" in chief_complaint.lower() or "spine" in chief_complaint.lower()):
        rules.append((2, "Bleeding from chest, abdomen, pelvis, or spine CTAS 2"))

    if "bleeding" in chief_complaint.lower() and "vaginal" in chief_complaint.lower():
        rules.append((2, "Massive vaginal hemorrhage CTAS 2"))

    if "bleeding" in chief_complaint.lower() and ("iliopsoas" in chief_complaint.lower() or "hip" in chief_complaint.lower()):
        rules.append((2, "Bleeding from iliopsoas muscle or hip CTAS 2"))

    if "bleeding" in chief_complaint.lower() and "extremity muscle compartments" in chief_complaint.lower():
        rules.append((2, "Bleeding from extremity muscle compartments CTAS 2"))

    if "bleeding" in chief_complaint.lower() and ("fractures" in chief_complaint.lower() or "dislocations" in chief_complaint.lower()):
        rules.append((2, "Bleeding from fractures or dislocations CTAS 2"))

    if "bleeding" in chief_complaint.lower() and "deep lacerations" in chief_complaint.lower():
        rules.append((2, "Bleeding from deep lacerations CTAS 2"))

    if "bleeding" in chief_complaint.lower() and "uncontrolled" in chief_complaint.lower():
        rules.append((2, "Any uncontrolled bleeding CTAS 2"))


    #CTAS 3 Bleeding Rules
    if "bleeding" in chief_complaint.lower() and "nose" in chief_complaint.lower():
        rules.append((3, "Bleeding from nose (epistaxis) CTAS 3"))

    if "bleeding" in chief_complaint.lower() and "mouth" in chief_complaint.lower():
        rules.append((3, "Bleeding from mouth (including gums) CTAS 3"))

    if "bleeding" in chief_complaint.lower() and "joints" in chief_complaint.lower():
        rules.append((3, "Bleeding from joints (hemarthroses) CTAS 3"))

    if "bleeding" in chief_complaint.lower() and "menorrhagia" in chief_complaint.lower():
        rules.append((3, "Bleeding from menorrhagia CTAS 3"))

    if "abrasions" in chief_complaint.lower():
        rules.append((3, "Bleeding from abrasions and superficial lacerations CTAS 3"))

#Mechanism of Injury rules

    # General Trauma
    if "ejection from vehicle" in chief_complaint.lower():
        rules.append((2, "Ejection from vehicle or rollover suggests CTAS 2 due to high risk of serious injury."))
    if "intrusion" in chief_complaint.lower() and "passenger" in chief_complaint.lower():
        rules.append((2, "Significant intrusion into passenger space is a CTAS 2 mechanism."))
    if "fall" in chief_complaint.lower() and ">18 ft" in chief_complaint.lower():
        rules.append((2, "Falls from >18 ft (6 m) suggest CTAS 2 severity."))
    if "penetrating injury" in chief_complaint.lower():
        rules.append((2, "Penetrating injury to head, neck, or torso indicates CTAS 2 urgency."))

    # Head Trauma
    if "head" in chief_complaint.lower() and "striking windshield" in chief_complaint.lower():
        rules.append((2, "Unrestrained head trauma involving windshield impact is CTAS 2."))
    if "pedestrian struck" in chief_complaint.lower():
        rules.append((2, "Pedestrian struck by vehicle suggests CTAS 2 head trauma."))
    if "fall" in chief_complaint.lower() and ">3 ft" in chief_complaint.lower():
        rules.append((2, "Falls from >3 ft or 5 stairs involving head injury indicate CTAS 2."))

    # Neck Trauma
    if "axial load to the head" in chief_complaint.lower():
        rules.append((2, "Axial load to the head is a CTAS 2 neck trauma indicator."))
    if "rollover" in chief_complaint.lower():
        rules.append((2, "Vehicle rollover, particularly if unrestrained, suggests CTAS 2 for neck trauma."))

#Dehydration Severity

    # Severe dehydration
    if ("severe dehydration" in chief_complaint.lower() or 
        ("dehydration" in chief_complaint.lower() and "shock" in chief_complaint.lower())):
        rules.append((1, "Marked volume loss with classic signs of dehydration and signs and symptoms of shock indicate CTAS 1."))

    # Moderate dehydration
    if ("moderate dehydration" in chief_complaint.lower() or
        ("dehydration" in chief_complaint.lower() and 
        ("dry mucous membranes" in chief_complaint.lower() or "tachycardia" in chief_complaint.lower() or 
        "decreased skin turgor" in chief_complaint.lower() or "decreased urine output" in chief_complaint.lower()))):
        rules.append((2, "Dry mucous membranes, tachycardia, decreased skin turgor, or decreased urine output suggest moderate dehydration and CTAS 2."))

    # Mild dehydration
    if ("mild dehydration" in chief_complaint.lower() or
        ("dehydration" in chief_complaint.lower() and
        ("stable vital signs" in chief_complaint.lower() or "thirst" in chief_complaint.lower() or 
        "concentrated urine" in chief_complaint.lower() or "decreased fluid intake" in chief_complaint.lower()))):
        rules.append((3, "Stable vital signs with thirst, concentrated urine, or decreased fluid intake suggest mild dehydration and CTAS 3."))

    # Potential dehydration
    if ("potential dehydration" in chief_complaint.lower() or
        ("fluid loss" in chief_complaint.lower() and "ongoing" in chief_complaint.lower()) or
        ("difficulty tolerating oral fluids" in chief_complaint.lower())):
        rules.append((4, "No symptoms of dehydration but ongoing fluid loss or difficulty tolerating fluids suggests CTAS 4."))



#2nd Order Modifiers
    # Chest pain, non-cardiac features
    if ("chest pain" in chief_complaint.lower() and 
        ("ripping" in chief_complaint.lower() or "tearing" in chief_complaint.lower())):
        rules.append((2, "Significant chest pain with ripping or tearing features suggests CTAS 2."))

    # Extremity weakness / symptoms of CVA
    if ("extremity weakness" in chief_complaint.lower() or "cva symptoms" in chief_complaint.lower()):
        if "onset < 4.5 hours" in chief_complaint.lower():
            rules.append((2, "Extremity weakness or symptoms of CVA with onset < 4.5 hours indicates CTAS 2."))
        elif "onset > 4.5 hours" in chief_complaint.lower() or "resolved" in chief_complaint.lower():
            rules.append((3, "Extremity weakness or symptoms of CVA with onset > 4.5 hours or resolved indicates CTAS 3."))

    # Difficulty swallowing / dysphagia
    if ("difficulty swallowing" in chief_complaint.lower() or "dysphagia" in chief_complaint.lower()):
        if "drooling" in chief_complaint.lower() or "stridor" in chief_complaint.lower():
            rules.append((2, "Difficulty swallowing with drooling or stridor suggests CTAS 2."))
        elif "foreign body" in chief_complaint.lower():
            rules.append((3, "Difficulty swallowing with a possible foreign body indicates CTAS 3."))

    # Upper or lower extremity injury
    if ("extremity injury" in chief_complaint.lower() or 
        ("upper extremity" in chief_complaint.lower() or "lower extremity" in chief_complaint.lower())):
        if "obvious deformity" in chief_complaint.lower():
            rules.append((3, "Obvious deformity in upper or lower extremity injury suggests CTAS 3."))

#Others

    if "stroke" in chief_complaint.lower() and "slurred speech" in history.lower():
        rules.append((2, "Possible stroke with slurred speech indicates a high risk of deterioration—assigning CTAS 2."))
    
    if "seizure" in chief_complaint.lower() and gcs < 14:
        rules.append((2, "Post-seizure with GCS < 14 indicates ongoing risk of deterioration—assigning CTAS 2."))

    if "mild skin rash" in chief_complaint.lower():
        rules.append((4, "Mild rash without systemic symptoms is less urgent—assigning CTAS 4."))

    if "sore throat" in chief_complaint.lower() and "no fever" in history.lower():
        rules.append((5, "Sore throat without fever or systemic symptoms is non-urgent—assigning CTAS 5."))

    if not rules:
        return 5, ["No immediate distress or minor complaints."]
   
    # Select highest CTAS level
    highest_ctas = min(rule[0] for rule in rules)
    
    # Collect all reasons for all CTAS levels
    matched_rules = [rule[1] for rule in rules]

    return highest_ctas, matched_rules