
### **Project Overview - LungSightAI**
An agentic, multi-modal chest X-ray diagnostic system that automates user authentication, X-ray upload, inference, report generation, and medical query assistance using Google ADK


###  **Problem Statement**
With **3.6 billion** annual X-rays overwhelming radiologists, patients face anxiety-inducing delays. LungSight AI bridges this gap as a dedicated **secondary screening** tool. Our Agent provides instant preliminary insights and guidance, acting as a rapid triage layer that offers patients immediate clarity and peace of mind while awaiting official medical interpretation.

### **Solution Statement**

LungSight AI addresses the critical bottleneck in diagnostic radiology, the time gap between imaging and interpretation. By creating an autonomous multi-Agent architecture, our system provides an instant, automated second opinion for **13 thoracic conditions.** We replace the passive waiting period with active, intelligent analysis, delivering **deep learning** verified insights in seconds rather than days. 

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F30661572%2F2c226549183321c4777734af43b2ecd0%2FWhatsApp%20Image%202025-12-01%20at%2022.33.23_afdfc86b.jpg?generation=1764608892719032&alt=media)
### **Architecture**

**'LungSight AI'** is an **'AI for Good'** based agentic monolithic solution that automates many features, such as authorisation, chest x ray inference, patient doubt search, Chest X-ray report generation. Each of these features become a separate agent. These agents follow strict routing enforced by an orchestration layer. This design removes manual intervention and enables a fully automated, end-to-end medical assistant.

**Agents -**

1. **auth_agent -** this agent is the agent that is called by the central root_agent when any user attempts to use this application without logging in. User has the feature of new account creation using the `signup_tool` and  login using `login_tool`. Upon successful login, user get access to other agents via their unique `uuid`.

2. **cxr_agent -**  It is the main agent that **sequentially** executes the prime functionality, which is to load the finetuned VGG16 weights via `load_classification_model_tool`, returns inferences on the input image after calling the `predict_from_image_tool` and on the backend saves the inferences with user's `uuid` 

3. **pdf_agent -**  **TO BE REVISED** consumes findings from cxr_agent, fetches user details via their `uuid' generates a PDF. It states in its report that this AI was generated and the X-ray should be examined by a Radiologist for further confirmation and suggestions.

4. **user_search_agent -** It is a utility to the user for further search and any medical assistance-related queries. Enhanced by an integrated `google_search` tool, this agent also provides recommendations and next steps and educate the users about their condition.

5. **root_agent -** It is constructed using the **LLM Agent** class from the **Google ADK**. It is a **stateful agent**, whose role is critical in being the **orchestrator agent** for initiating the other agents and operating the same by a tool-based and task delegation approach at its disposal. The orchestrator is **restricted** from answering user requests by itself.

### **Demo** 
Here is the demo of our agent working live in production [Youtube](https://www.youtube.com/watch?v=10s-U3Nmx3A)

The following section briefly explains a senerio of users interaction with our Agentic system.

1. `check_login_status` - This is the first tool that gets invoked when ever a user tries to interact with the system. Once the login status is approved the agents are accessible to the user. 

2. `signup_tool' / 'login_tool' - These tools are called when a new user wants to sign up or an existing user wants to access the system. The signup tool takes user's details and stores them in backend. 

3. load_classification_model_tool - This tool loads the model weights and initializes the global model instance. It functions as a key foundational component that the LungsightAI system uses to determine the relative weightage of various health conditions and their associated probabilities for the patient.

4. predict_from_image_tool - This tool loads and processes the user's chest X-ray images, applies the classification model’s weights, identifies any potential issues, and generates the corresponding diagnostic predictions.

5. save_to_csv_tool - This custom tool captures and stores chest X-ray inferences—predicted using the cxr_agent and predict_from_image tools—in a CSV file. The saved data can be used for future reference, auditing, and historical review.


### Conclusion

The power of LungSight AI lies in its coordinated ecosystem of specialized tools and agents.
Each tool focuses solely on one responsibility authentication, inference, storage, search, or reporting, while the orchestrator agent binds everything together into a unified medical diagnostic workflow.
This modular design reduces errors, improves maintainability, encourages scalability, demonstrates a real-world multi-agent system using Google ADK

The result is a medically meaningful assistant that processes X-rays, generates insights, and supports users through a clear agentic pipeline bridging the gap between Radiologist shortage and diagnosis delays. 

### Value Statement

LungSightAI transforms a traditionally slow, specialist-dependent process into an automated, user-friendly experience. By leveraging agent coordination, ADK tooling, and deep learning, it enables:

1. Faster secondary medical insight
2. Structured and explainable inference outputs
3. Downloadable medical reports **if possible**
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
