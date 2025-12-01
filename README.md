### **Project Overview - LungSightAI**
An agentic, multi-modal chest X-ray diagnostic system that automates user authentication, X-ray upload, inference, report generation, and medical query assistance using Google ADK


###  **Problem Statement**
With **3.6 billion** annual X-rays overwhelming radiologists, patients face anxiety-inducing delays. LungSight AI bridges this gap as a dedicated **secondary screening** tool. Our agent provides instant preliminary insights and guidance, acting as a rapid triage layer that offers patients immediate clarity and peace of mind while they await official medical interpretation.

### **Solution Statement**

LungSight AI addresses the critical bottleneck in diagnostic radiology, the time gap between imaging and interpretation. By creating an autonomous multi-Agent architecture, our system provides an instant, automated second opinion for **13 thoracic conditions.** We replace the passive waiting period with active, intelligent analysis, delivering **deep learning** verified insights in seconds rather than days. 

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F30661572%2Fe268ae3ff1ddf89a8fc6a886c3a661c4%2FGenerated%20Image%20December%2001%202025%20-%2010_50PM.jpg?generation=1764610927013549&alt=media)

### **Demo** 
Here is the demo of our agent working live in production: [**Youtube**](https://www.youtube.com/watch?v=10s-U3Nmx3A)

### **Architecture**

**'LungSight AI'** is an **'AI for Good'** based agentic monolithic solution that automates many features, such as authorization, chest X-ray inference, patient doubt search, Chest X-ray report generation. Each of these features become a separate agent. These agents follow strict routing enforced by an orchestration layer. This design removes manual intervention and enables a fully automated, end-to-end medical assistant.

#### Project Structure

```text
lungSightAI/
├── .dockerignore          # Excludes heavy local files (venv, DBs) from Docker builds
├── .gcloudignore          # Excludes files from Google Cloud uploads (prevents timeouts)
├── .gitignore             # Tells Git to ignore sensitive keys (.env) and user data
├── Dockerfile             # Blueprint for building the container on Cloud Run
├── README.md              # Project documentation and setup guide
├── requirements.txt       # List of Python dependencies (lightweight versions)
└── lungSightAI/           # Main application package
    ├── __init__.py        # Marks directory as a Python package
    ├── agent.py           # Core Orchestrator and Agent logic (Entry point)
    ├── authTools.py       # Authentication tools (Signup/Login) and DB management
    ├── customTools.py     # Medical tools (VGG16 Inference, PDF Generation, Logging)
    └── Data/              # Data directory for assets
        └── CXR Images/    # Sample X-ray images for testing the agent
        └── Model Weights/ # Store your model weights here
```

**Agents -**

1. **auth_agent -** this agent is called by the central root_agent when any user attempts to use this application without logging in. User has the feature of new account creation using the `signup_tool` and  login using `login_tool`. Upon successful login, users get access to other agents via their unique `uuid`.

2. **cxr_agent -**  It is the main agent that **sequentially** executes the prime functionality, which is to load the finetuned VGG16 weights via `load_classification_model_tool`, returns inferences on the input image after calling the `predict_from_image_tool` and on the backend saves the inferences with user's `uuid` 

3. **pdf_report_agent -**   consumes findings from cxr_agent, fetches user details via their `uuid' generates a PDF. It states in its report that this AI was generated and the X-ray should be examined by a Radiologist for further confirmation and suggestions.

4. **helpful_assistant -** It is a utility to the user for further search and any medical assistance-related queries. Enhanced by an integrated `google_search` tool, this agent also provides recommendations and next steps and educates users about their condition.

5. **root_agent -** It is constructed using the **LLM Agent** class from the **Google ADK**. It is a **stateful agent**, whose role is critical in being the **orchestrator agent** for initiating the other agents and operating the same by a tool-based and task delegation approach at its disposal. The orchestrator is **restricted** from answering user requests by itself.

**Tools**

The following section briefly explains a scenario of users interaction with our Agentic system.

1. `check_login_status` - This is the first tool that gets invoked whenever a user tries to interact with the system. Once the login status is approved the agents are accessible to the user. 

2. `signup_tool' / 'login_tool'` - These tools are called when a new user wants to sign up or an existing user wants to access the system. The signup tool takes user's details and stores them in backend. 

3. `load_classification_model_tool` - This tool loads the model weights and initializes the global model instance. It functions as a key foundational component that the LungsightAI system uses to determine the relative weightage of various health conditions and their associated probabilities for the patient.

4. `predict_from_image_tool` - This tool loads and processes the user's chest X-ray images, applies the classification model’s weights, identifies any potential issues, and generates the corresponding diagnostic predictions.

5. `save_to_csv_tool` - This custom tool captures and stores chest X-ray inferences—predicted using the cxr_agent and predict_from_image tools—in a CSV file. The saved data can be used for future reference, auditing, and historical review.

### Workflow
The `root_agent` (Orchestrator) follows this workflow for LungSight AI:

1.  **Authenticate:** On the initial interaction, the agent executes `check_login_status`. If the user is not logged in, the workflow routes to the `auth_agent`, which handles account creation or login via `signup_tool` and `login_tool`.
2.  **Analyze:** If an authenticated user provides an X-ray image, the task is delegated to the `cxr_agent`. It ensures the Deep Learning model is ready using `load_classification_model_tool` and performs inference using `predict_from_image_tool`.
3.  **Record:** Simultaneously, the `cxr_agent` persists the inference probabilities and diagnostic outcome to the secure database using `save_to_csv_tool`, ensuring an audit trail tagged with the user's UUID.
4.  **Report:** If the user requests a formal summary, the `pdf_report_agent` takes over. It synthesizes the findings, verifies necessary patient details, and generates a downloadable PDF document using `generate_cxr_pdf_report`.
5.  **Assist:** For follow-up questions or medical definitions (e.g., "What is Edema?"), the workflow routes to the `helpful_assistant`. This agent utilizes `Google Search` to retrieve and summarize relevant medical information for the user.

### **Deployment**

We transitioned LungSight AI to a scalable production environment by containerizing the application with **Docker** and deploying it via **Google Cloud Run**. This serverless architecture, managed through the **Google Cloud Console**, ensures consistent performance for our deep learning model and provides instant global accessibility without infrastructure overhead.

### Conclusion

The power of LungSight AI lies in its coordinated ecosystem of specialized tools and agents.
Each tool focuses solely on one responsibility authentication, inference, storage, search, or reporting, while the orchestrator agent binds everything together into a unified medical diagnostic workflow.
This modular design reduces errors, improves maintainability, encourages scalability, demonstrates a real-world multi-agent system using Google ADK

The result is a medically meaningful assistant that processes X-rays, generates insights, and supports users through a clear agentic pipeline bridging the gap between Radiologist shortage and diagnosis delays. 

### Value Statement

LungSightAI transforms a traditionally slow, specialist-dependent process into an automated, user-friendly experience. By leveraging agent coordination, ADK tooling, and deep learning, it enables:

1. Faster secondary medical insight
2. Structured and explainable inference outputs
3. Downloadable medical reports 
4. A guided, conversational medical assistant


This agentic solution has the potential to meaningfully reduce patient uncertainty, support early screening, and streamline preliminary diagnostics, offering real value in clinical and home-health environments.


### Future Scope
Constrained by hardware limitations to minimal training epochs, our immediate focus is leveraging high-performance compute to maximize accuracy. Future enhancements include integrating multimodal patient data and adding specialized agents for validation and medication safety. These steps will evolve the prototype into a robust clinical tool designed to complement **not replace** radiologists


## Prerequisites

  * **Python 3.10+**
  * **Google Gemini API Key** (Get it from [Google AI Studio](https://aistudio.google.com/))
  * **TensorFlow compatible hardware** (Optional but recommended for inference speed)

## Installation

### 1\. Clone the Repository

```bash
git clone https://github.com/eshaan-james-dl/LungSight-AI.git
cd lungSightAI
```

### 2\. Set up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3\. Install Dependencies

Install the required packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Configuration & Setup

### Environment Variables

Create a `.env` file in the `lungSightAI` directory and add your Google API Key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=0
```

## Usage

To start the LungSight AI interactive web interface, use the ADK web command:

```bash
adk web
```

This will automatically launch the application in your default web browser (typically at `http://localhost:8000`).

## Disclaimer

*This tool is for educational and development purposes only. It is not intended for real clinical diagnosis. Always consult a medical professional.

## Production Link 
Click here to try out our solution [Cloud Run](https://tinyurl.com/lungsightai)
