FROM python:3.9-slim-buster

WORKDIR /dspback

COPY . .

RUN pip install -r requirements.txt

# build the pydantic models from json-schemas
RUN pip install datamodel-code-generator==0.15.0
RUN datamodel-codegen --input-file-type jsonschema --input dspback/schemas/hydroshare/schema.json --output dspback/schemas/hydroshare/model.py
RUN datamodel-codegen --input-file-type jsonschema --input dspback/schemas/zenodo/schema.json --output dspback/schemas/zenodo/model.py
RUN datamodel-codegen --input-file-type jsonschema --input dspback/schemas/external/schema.json --output dspback/schemas/external/model.py
RUN datamodel-codegen --input-file-type jsonschema --input dspback/schemas/earthchem/schema.json --output dspback/schemas/earthchem/model.py
RUN pip uninstall -y datamodel-code-generator

EXPOSE 5002

ENV PYTHONPATH "${PYTHONPATH}:/dspback/dspback"

CMD ["python", "dspback/main.py"]
