FROM python:3.10-slim

WORKDIR /dspback

COPY . .

RUN pip install -r requirements.txt

# build the pydantic models from json-schemas
RUN pip install datamodel-code-generator==0.15.0
RUN datamodel-codegen --input-file-type jsonschema --input dspback/schemas/external/schema.json --output dspback/schemas/external/model.py
RUN pip uninstall -y datamodel-code-generator

EXPOSE 5002

ENV PYTHONPATH "${PYTHONPATH}:/dspback/dspback"

CMD ["python", "dspback/main.py"]
