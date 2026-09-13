"""
Exports the FastAPI app's OpenAPI (Swagger) schema to a static JSON file
at the project root - useful for importing into Swagger Editor/UI,
Postman, or handing to another team without them needing to run the app.

Usage:
    python -m scripts.export_openapi
"""

import json

from app.main import app

OUTPUT_PATH = "openapi.json"


def main():
    schema = app.openapi()
    with open(OUTPUT_PATH, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
