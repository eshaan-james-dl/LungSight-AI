import pandas as pd
import numpy as np
import os
import cv2
import re
import tensorflow as tf
from datetime import datetime
from google.adk.tools.tool_context import ToolContext # Import ToolContext

from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.models import Model, load_model

import textwrap
import io
import google.genai.types as types
from typing import Any # Import Any to bypass the strict parser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- ROBUST PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEIGHTS_PATH = os.path.join(CURRENT_DIR, "Data", "Model Weight", "VGG.weights.h5")
CSV_PATH = os.path.join(CURRENT_DIR, "Data", "CSV files", "user_inferences.csv")

def load_classification_model_tool() -> dict:
    """Loads a VGG16-based model."""
    global model
    print(f"DEBUG: Attempting to load weights from: {WEIGHTS_PATH}")

    if not os.path.exists(WEIGHTS_PATH):
        return {"status": "error", "error_message": f"Weight file not found at: {WEIGHTS_PATH}"}

    try:
        # Strategy 1: Build & Load Weights
        print("DEBUG: Strategy 1 - Building architecture...")
        num_classes = 13
        input_shape = (224, 224, 3)
        base_model = VGG16(weights="imagenet", include_top=False, input_shape=input_shape)
        for layer in base_model.layers: layer.trainable = False
        x = GlobalAveragePooling2D()(base_model.output)
        x = Dense(1024, activation='relu')(x)
        x = Dropout(0.5)(x)
        outputs = Dense(num_classes, activation='sigmoid')(x)
        model = Model(inputs=base_model.input, outputs=outputs)
        model.load_weights(WEIGHTS_PATH)
        print("DEBUG: Strategy 1 Successful.")

    except Exception as e_weights:
        print(f"DEBUG: Strategy 1 failed ({e_weights}). Strategy 2...")
        try:
            model = load_model(WEIGHTS_PATH, compile=False)
            print("DEBUG: Strategy 2 Successful.")
        except Exception as e_full:
            return {"status": "error", "error_message": f"Load failed: {str(e_weights)}"}

    try:
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-4), loss='binary_crossentropy', metrics=[tf.keras.metrics.AUC()])
        return {"status": "success", "message": "VGG16 model loaded."}
    except Exception as e:
         return {"status": "error", "error_message": f"Compilation failed: {str(e)}"}


def _resolve_image_path(user_input: str) -> str:
    """
    Intelligently finds the image file based on vague user input.
    Examples:
    - "image 1" -> "Data/CXR Images/img1.jpg"
    - "1st xray" -> "Data/CXR Images/img1.jpg"
    - "img10"    -> "Data/CXR Images/img10.jpg"
    """
    # 1. Base Directory
    base_dir = os.path.join(CURRENT_DIR, "Data", "CXR Images")
    
    # 2. Cleanup Input (Remove quotes/spaces)
    clean_input = user_input.strip().strip('"').strip("'")

    # 3. If it's already a valid path, return it immediately
    if os.path.exists(clean_input):
        return clean_input
    
    # 4. Try joining with base dir directly
    direct_path = os.path.join(base_dir, clean_input)
    if os.path.exists(direct_path):
        return direct_path

    # 5. SMART LOGIC: Extract the first number found
    # This handles "image 1", "1st", "number 1", "img1"
    match = re.search(r'\d+', clean_input)
    
    if match:
        number = match.group() # e.g., "1" or "10"
        
        # Construct likely filenames
        candidates = [
            f"img{number}.jpg",   # Primary format
            f"image{number}.jpg",
            f"{number}.jpg",
            f"img{number}.png"
        ]
        
        for fname in candidates:
            full_path = os.path.join(base_dir, fname)
            if os.path.exists(full_path):
                print(f"DEBUG: Auto-resolved '{user_input}' to -> {full_path}")
                return full_path

    # If all fails, return original to let the error handler catch it
    return clean_input


def predict_from_image_tool(image_path: str, threshold: float = 0.3) -> dict:
    """
    Preprocesses image, runs inference, returns probabilities.
    Accepts vague names like "image 1" or full paths.
    """
    try:
        if "model" not in globals():
            return {"status": "error", "error_message": "Model not loaded. Call load_classification_model_tool() first."}

        # ⬇⬇ USE SMART RESOLVER HERE ⬇⬇
        resolved_path = _resolve_image_path(image_path)

        if not os.path.exists(resolved_path):
             return {
                 "status": "error", 
                 "error_message": f"Could not find image for input '{image_path}'. Tried path: {resolved_path}"
             }

        img = cv2.imread(resolved_path)
        if img is None: 
            return {"status": "error", "error_message": "Invalid image format or corrupted file."}

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (224, 224))
        img_array = np.expand_dims(img_resized, axis=0).astype("float32")
        img_array = preprocess_input(img_array)

        diseases = [
            'Enlarged Cardiomediastinum', 'Cardiomegaly', 'Lung Opacity',
            'Lung Lesion', 'Edema', 'Consolidation', 'Pneumonia',
            'Atelectasis', 'Pneumothorax', 'Pleural Effusion',
            'Pleural Other', 'Fracture', 'Support Devices'
        ]

        preds = model.predict(img_array).flatten()

        results = {
            disease: {
                "probability": float(prob),
                "label": "Y" if prob >= threshold else "N"
            }
            for disease, prob in zip(diseases, preds)
        }
        
        # Return the resolved path so the Agent knows which file was actually used
        return {
            "status": "success", 
            "analyzed_file": os.path.basename(resolved_path),
            "results": results
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def save_to_csv_tool(results: dict, tool_context: ToolContext) -> dict:
    """Saves inference to CSV using the LOGGED-IN user's UUID."""
    
    # 1. Retrieve UUID from Session State
    user_uuid = tool_context.state.get("uuid")
    
    if not user_uuid:
        return {"status": "error", "message": "User not logged in. Cannot save to CSV."}

    try:
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        conditions = [
            'Enlarged Cardiomediastinum', 'Cardiomegaly', 'Lung Opacity',
            'Lung Lesion', 'Edema', 'Consolidation', 'Pneumonia',
            'Atelectasis', 'Pneumothorax', 'Pleural Effusion',
            'Pleural Other', 'Fracture', 'Support Devices'
        ]

        row = {"uuid": user_uuid}
        
        for cond in conditions:
            if cond in results:
                row[cond] = results[cond]["probability"]
            else:
                row[cond] = 0.0

        row["timestamp"] = datetime.now().isoformat()
        df_row = pd.DataFrame([row])

        if not os.path.exists(CSV_PATH):
            df_row.to_csv(CSV_PATH, index=False)
        else:
            df_row.to_csv(CSV_PATH, mode="a", index=False, header=False)

        return {
            "status": "success",
            "message": f"Inference saved for User ID: {user_uuid}"
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}
      
async def generate_cxr_pdf_report(
    patient_name: str,
    age_sex: str,
    ref_by: str,
    date: str,
    xray_no: str,
    exam_title: str,
    findings: str,
    conclusion: str,
    advice: str,
    tool_context: Any = None
):
    """
    Generates a formatted Chest X-Ray PDF report and saves it as an artifact.
    """
    
    # --- PDF Generation Setup ---
    # We use 'with' block context logic manually to ensure safety
    buffer = io.BytesIO()
    
    try:
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # ... [Keep your helper functions draw_centered_text etc. exactly as they are] ...
        # (For brevity, I am not pasting the helper functions again, keep them here)
        def draw_centered_text(c, y, text, font, size, underlined=False):
            c.setFont(font, size)
            text_width = c.stringWidth(text, font, size)
            x = (width - text_width) / 2
            c.drawString(x, y, text)
            if underlined:
                c.line(x, y - 2, x + text_width, y - 2)

        def draw_wrapped_section(c, x, y, label, text, font_label, font_text, size, wrap_width=85):
            c.setFont(font_label, size)
            c.drawString(x, y, label)
            if "Findings" in label:
                label_width = c.stringWidth(label, font_label, size)
                c.line(x, y - 2, x + label_width, y - 2)
                y -= 25 
            
            c.setFont(font_text, size - 1)
            
            if "Findings" in label:
                full_text = text
            else:
                full_text = f"{label} {text}"
            
            lines = textwrap.wrap(full_text, width=wrap_width)
            for line in lines:
                c.drawString(x, y, line)
                y -= 18 
            return y - 10 

        # Ensure inputs are strings
        patient_name = str(patient_name or "Unknown")
        age_sex = str(age_sex or "")
        ref_by = str(ref_by or "")
        date = str(date or "")
        xray_no = str(xray_no or "Unknown")
        exam_title = str(exam_title or "X-RAY CHEST PA VIEW")
        findings = str(findings or "No findings recorded.")
        conclusion = str(conclusion or "")
        advice = str(advice or "")

        # --- DRAWING CONTENT ---
        # 1. Main Header
        draw_centered_text(c, 750, "X-RAYS REPORTING FORMATE", "Helvetica-Bold", 16, underlined=True)

        # 2. Patient Details
        c.setFont("Helvetica-BoldOblique", 11)
        c.drawString(50, 700, "PATIENT NAME:")
        c.drawString(350, 700, "AGE / SEX:")
        c.drawString(50, 675, "REF. BY DR     :")
        c.drawString(350, 675, "DATE:")
        c.drawString(50, 650, "X-RAY NO        :")

        c.setFont("Helvetica", 11)
        c.drawString(160, 700, patient_name)
        c.drawString(430, 700, age_sex)
        c.drawString(160, 675, ref_by)
        c.drawString(430, 675, date)
        c.drawString(160, 650, xray_no)

        # 3. Exam Title
        c.setFont("Helvetica-BoldOblique", 14)
        text_width = c.stringWidth(exam_title, "Helvetica-BoldOblique", 14)
        x_center = (width - text_width) / 2
        c.drawString(x_center, 600, exam_title)
        c.line(x_center, 598, x_center + text_width, 598)

        # --- DYNAMIC SECTIONS ---
        y_cursor = 560

        # 4. Findings
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_cursor, "Findings:")
        c.line(50, y_cursor - 2, 105, y_cursor - 2)
        y_cursor -= 25
        
        c.setFont("Helvetica-Oblique", 11)
        findings_lines = textwrap.wrap(findings, width=85)
        for line in findings_lines:
            c.drawString(50, y_cursor, line)
            y_cursor -= 18
        y_cursor -= 10 

        # 5. Conclusion
        c.setFont("Helvetica-Bold", 11)
        conc_full = f"Conclusion: {conclusion}" 
        conc_lines = textwrap.wrap(conc_full, width=85)
        for line in conc_lines:
            c.drawString(50, y_cursor, line)
            y_cursor -= 18
        y_cursor -= 10 

        # 6. Advice
        c.setFont("Helvetica-BoldOblique", 11)
        adv_full = f"Adv: {advice}"
        adv_lines = textwrap.wrap(adv_full, width=85)
        for line in adv_lines:
            c.drawString(50, y_cursor, line)
            y_cursor -= 18

        # 7. Footer
        y_cursor -= 40
        c.setFont("Helvetica-BoldOblique", 12)
        c.drawString(50, y_cursor, "THANKS FOR THE REFERAL,")

        # --- FINALIZE PDF ---
        c.showPage()
        c.save()
        
        # 🟢 CRITICAL FIX HERE 🟢
        # Move the pointer to start so we can read it
        buffer.seek(0)
        # Read the bytes BEFORE closing
        pdf_bytes = buffer.getvalue()

    except Exception as e:
        buffer.close()
        return f"Error generating PDF content: {str(e)}"

    # Close buffer only AFTER we have the data
    buffer.close()

    # --- Save Artifact ---
    safe_xray_no = "".join([c for c in xray_no if c.isalnum() or c in ('-', '_')])
    filename = f"Report_{safe_xray_no}.pdf"

    try:
        pdf_artifact = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf"
        )

        version = await tool_context.save_artifact(
            filename=filename, 
            artifact=pdf_artifact
        )
        
        # Return success with metadata for the Agent to use
        return {
            "status": "success",
            "message": "PDF Report generated successfully.",
            "filename": filename,
            "artifact_id": filename
        }

    except Exception as e:
        return f"Error saving PDF artifact: {str(e)}"