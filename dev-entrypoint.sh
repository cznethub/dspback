datamodel-codegen --input-file-type jsonschema --input /dspback/dspback/schemas/hydroshare/schema.json --output /dspback/dspback/schemas/hydroshare/model.py
datamodel-codegen --input-file-type jsonschema --input /dspback/dspback/schemas/zenodo/schema.json --output /dspback/dspback/schemas/zenodo/model.py
datamodel-codegen --input-file-type jsonschema --input /dspback/dspback/schemas/external/schema.json --output /dspback/dspback/schemas/external/model.py
datamodel-codegen --input-file-type jsonschema --input /dspback/dspback/schemas/earthchem/schema.json --output /dspback/dspback/schemas/earthchem/model.py

python dspback/main.py