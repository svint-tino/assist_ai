import altair as alt
import pandas as pd
import uuid
import os
from jsonschema import validate, ValidationError

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
        return True
    except ValidationError as e:
        print(f"Erreur de validation JSON : {e.message}")
        return False

# === FONCTION DE RENDU AVEC ALTAIR ===
def render_altair_visual(visual_spec: dict, output_dir: str = "static") -> str:
    try:
        if not validate_visual_spec(visual_spec):
            return None

        df = pd.DataFrame(visual_spec["data"])

        chart = getattr(alt.Chart(df), f"mark_{visual_spec['type']}")().encode(
            x=alt.X(
                visual_spec["x"]["field"],
                type=visual_spec["x"]["type"],
                title=visual_spec["x"].get("title")
            ),
            y=alt.Y(
                visual_spec["y"]["field"],
                type=visual_spec["y"]["type"],
                title=visual_spec["y"].get("title")
            )
        ).properties(title=visual_spec.get("title", ""))

        os.makedirs(output_dir, exist_ok=True)
        file_name = f"{uuid.uuid4()}.html"
        output_path = os.path.join(output_dir, file_name)
        chart.save(output_path)

        return output_path

    except Exception as e:
        print(f"Erreur de rendu Altair : {str(e)}")
        return None 