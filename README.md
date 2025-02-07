# TriagePRO: AI-Powered Immediate CTAS Prediction for Emergency Care

## Overview
TriagePRO is an AI-driven system designed to predict the Canadian Triage and Acuity Scale (CTAS) level swiftly, utilizing patient vital signs and key chief complaint details. This tool aids healthcare providers in making rapid, data-informed decisions in emergency settings.

<img width="1279" alt="Homepage" src="https://github.com/user-attachments/assets/7b86dea5-b95a-4980-aa78-042956bbbaec"/>

## Features
- **Instant CTAS Prediction**: Provides real-time triage levels based on patient data.
- **Comprehensive Vital Signs Input**: Accepts heart rate (HR), blood pressure (BP), respiratory rate (RR), temperature (Temp), and oxygen saturation (O2 sat).
- **Chief Complaint Categorization**: Utilizes straightforward complaint categories to enhance prediction accuracy.
- **AI-Powered Analysis**: Employs a machine learning model trained on actual triage cases to ensure reliable predictions.
- **User-Friendly Interface**: Designed for rapid data entry, facilitating quick and efficient triage assessments.

<img width="1279" alt="Homepage" src="https://github.com/user-attachments/assets/e94eb657-0fe8-4f2b-b7c9-b90f137fb61f"/>

## How It Works
1. **Enter Patient Data**: Input vital signs (HR, BP, RR, Temp, O2 sat).
2. **Select Chief Complaint**: Choose from predefined complaint categories.
3. **Get CTAS Prediction**: The AI model processes the data and provides an immediate CTAS level recommendation.

<img width="1279" alt="Homepage" src="https://github.com/user-attachments/assets/e03799b8-0857-4d96-87fb-ae320d635f69"/>


## Installation
Clone the repository and install the required dependencies:
```bash
 git clone https://github.com/AbdelazizGedella/TriagePRO.git
 cd TriagePRO
 pip install -r requirements.txt
```

## Usage
Run the application on the app file run that code:
```bash
 uvicorn app.main:app --reload
```

This tool is intended for use in emergency departments, by paramedics, and in urgent care centers to enhance decision-making and reduce triage time.

## Future Developments
- Web & mobile integration
- API support for seamless integration with hospital systems
- Continuous model training with new data to improve accuracy

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Contact
For more information or to contribute to this project, please contact:
```bash
**[Abdelziz Gedelleila]**
```
```bash
Abdelazizgedella@gmail.com]
```
---

*This project is developed to improve emergency triage efficiency using AI-driven predictions.*
