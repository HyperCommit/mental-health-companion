import json
import yaml
from backend.api.main import app

# Get the OpenAPI schema
openapi_schema = app.openapi()

# Save as JSON
with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)

# Save as YAML
with open("openapi.yaml", "w") as f:
    yaml.dump(openapi_schema, f)

print("OpenAPI specification generated successfully!")