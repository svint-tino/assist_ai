import altair as alt
import pandas as pd
import uuid
import logging
import os
from jsonschema import validate, ValidationError

# === CONFIGURATION DU LOGGER ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(f"{log_dir}/database.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)

# === SCHEMA JSON POUR VALIDATION DE SPEC ALTAIR ===
altair_spec_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["bar", "line", "area", "point", "scatter"]},
        "title": {"type": "string"},
        "x": {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
                "type": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["field", "type"]
        },
        "y": {
            "type": "object",
            "properties": {
                "field": {"type": "string"},
                "type": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["field", "type"]
        },
        "data": {
            "type": "array",
            "items": {"type": "object"}
        }
    },
    "required": ["type", "x", "y", "data"]
}

# === FONCTION DE VALIDATION ===
def validate_visual_spec(spec: dict) -> bool:
    try:
        validate(instance=spec, schema=altair_spec_schema)
        print("La spécification est valide.")
        logger.info("La spécification Altair est valide.", extra={"spec": spec})
        return True
    except ValidationError as e:
        print(f"Erreur de validation JSON : {e.message}")
        logger.error(f"Erreur de validation JSON : {e.message}", extra={"spec": spec})
        return False

# === FONCTION DE RENDU AVEC ALTAIR ===
def render_altair_visual(visual_spec: dict, output_dir: str = "static") -> str:
    try:
        df = pd.DataFrame(visual_spec["data"])

        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X(visual_spec["encoding"]["x"]["field"], type=visual_spec["encoding"]["x"]["type"]),
            y=alt.Y(visual_spec["encoding"]["y"]["field"], type=visual_spec["encoding"]["y"]["type"])
        ).properties(title=visual_spec.get("title", "Visualisation"))

        os.makedirs(output_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.html"
        output_path = os.path.join(output_dir, filename)
        chart.save(output_path)
        
        logger.info(f"Visualisation Altair enregistrée : {output_path}")
        return output_path
    except Exception as e:
        print(f"Erreur de rendu Altair : {str(e)}")
        logger.error(f"Erreur de rendu Altair : {str(e)}")
        return None