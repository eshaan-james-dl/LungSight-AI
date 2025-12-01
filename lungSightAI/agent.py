from .customTools import load_classification_model_tool, predict_from_image_tool, save_to_csv_tool, generate_cxr_pdf_report
from .authTools import signup_tool, login_tool, check_login_status
import os
import warnings 
from google.genai import types
from google.adk.agents import LlmAgent, Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search, AgentTool
# Import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

warnings.filterwarnings("ignore")

# --- AGENT DEFINITIONS ---

auth_agent = LlmAgent(
    name="auth_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
    You are the Authentication Agent.
    - Call 'signup_tool' if the user wants to register.
    - Call 'login_tool' if the user wants to login.
    - Confirm success to the user when done.
    """,
    tools=[signup_tool, login_tool],
    output_key="auth_results"
)

cxr_inference_agent = LlmAgent(
    name="cxr_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
    You are a Medical AI Assistant.
    
    1. Call load_classification_model_tool()
    2. Call predict_from_image_tool(image_path)
    3. Call save_to_csv_tool(results) -> This will auto-fetch the user UUID.

    4. FINAL SUMMARY:
       - Review the JSON data yourself.
       - Provide a short, bulleted summary of findings.
       - Say "Normal" if all labels are "N".
       - Highlight "High Probability" if any labels are "Y".
       - DO NOT show the raw JSON to the user.
    """,
    tools=[load_classification_model_tool, predict_from_image_tool, save_to_csv_tool],
    output_key="cxr_output"   
)

user_search_agent = Agent(
    name="helpful_assistant",
    model=Gemini(model="gemini-2.5-flash"),
    description="Medical Q&A Assistant.",
    instruction="Answer in 3-5 bullet points. Be concise.",
    tools=[google_search],
    output_key="search_results"
)


pdf_report_agent = LlmAgent(
    name="pdf_report_agent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
    You are a Medical Reporting Specialist.

    YOUR GOAL:
    Take raw Chest X-Ray inference data and generate a professional PDF report file.

    INPUT DATA:
    You will receive {cxr_output} containing inference probabilities.

    PROCESS:
    1. *Synthesize Content*:
       - Ask the "Patient Name" (use "Unknown" if not provided).
       - Ask age and Gender of the user too.
       - Generate a "Date" (use today's date).
       - *Findings*: Convert the inference probabilities into professional medical sentences (e.g., if 'Cardiomegaly' is high, write " The cardiac silhouette is enlarged."). If the study is normal, use standard normal findings text: "Normal air fluid levels are seen without obvious bowel loop dilatation. Visualized bones appear normal."
       - *Conclusion*: Summarize the findings (e.g., "Normal study" or "Cardiomegaly").
       - *Advice*: Provide standard advice (e.g., "Clinical correlation suggested").

    2. *Generate PDF*:
       - CALL the generate_cxr_pdf_report tool with the synthesized strings.
       - Pass "X-RAY CHEST PA VIEW" (or Abdomen if applicable) as the exam_title.

    3. *Final Output*:
       - Return a confirmation message to the user that the PDF has been created, including the filename.
    """,
    tools=[generate_cxr_pdf_report],
    output_key="pdf_confirmation"
)
# --- ORCHESTRATOR ---

root_agent = LlmAgent(
    name="orchestrator",
    model=Gemini(model="gemini-2.5-flash-lite"),
instruction="""
    You are the ROOT ORCHESTRATOR for LungSight AI.

    YOUR JOB: Route users to the correct specialist.

    ──────────────────────────────
    🛑 CRITICAL HANDOFF RULE (FIX FOR SILENCE)
    - If a sub-agent (Auth, CXR, PDF, etc.) returns a text response:
      YOU MUST output that response to the user immediately.
    - Do not stay silent. If the sub-agent spoke, relay it.
    ──────────────────────────────

    PROTOCOL:
    1. On the FIRST turn, call `check_login_status`.
    
    2. CHECK STATUS:
       - If "logged_out": Route to `auth_agent`.
       - If "logged_in": Route to `cxr_agent`, `helpful_assistant`, or `pdf_report_agent`.

    3. ROUTING GUIDE:
       - "login", "signup", "password" -> auth_agent
       - "upload", "xray", "scan" -> cxr_agent
       - "report", "pdf" -> pdf_report_agent
       - "what is pneumonia?" -> helpful_assistant

    Remember: You don't solve the problem yourself, but you MUST communicate the sub-agent's solution to the user.
    """,
    tools=[
        AgentTool(auth_agent),
        AgentTool(cxr_inference_agent),
        AgentTool(user_search_agent),
        AgentTool(pdf_report_agent),
        check_login_status
    ]
)

APP_NAME = "LungSight_AI"
print("DEBUG: Initializing In-Memory Session Service for Cloud Run...")
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    session_service=session_service,
    app_name=APP_NAME,
)