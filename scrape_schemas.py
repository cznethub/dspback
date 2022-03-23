import requests
import json

response = requests.get("http://grg-doc-dev.ldeo.columbia.edu:8081/v2/api-docs?group=eclAPI-2.0")

with open("dspback/schemas/earthchem/schema.json", "w") as f:
    f.write(json.dumps(response.json(), indent=2))

