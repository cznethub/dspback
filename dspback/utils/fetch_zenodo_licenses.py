# @deprecated
# https://jsonforms.discourse.group/t/function-nested-too-deeply-error-when-enum-has-many-options/1451/5
# oneOf of title, const pairs are limited to a max number of elements (presumably 300)
# and this array of licenses is longer than that
# this causes an error in Firefox where the schema will fail to render due the resulting
# iteration being too nested

# This script will fetch the zenodo licenses controlled vocabulary and generate a JSON object that can be used to populate
# the `oneOf` subschema inside the license field of the zenodo schema file at `dspback\schemas\zenodo\schema.json`
# The schema file will be modified with the new object

# Example run `python fetch_zenodo_licenses.py`

import json

import requests

response = requests.get(
    "https://zenodo.org/api/vocabularies/licenses?page=1&size=10000&sort=title"
)  # size query param must be an arbitrarily large number

vocabulary = response.json()
licenses = vocabulary["hits"]["hits"]

transformed_licenses = []
for license in licenses:
    transformed_license = {"const": license["id"], "title": license["title"]["en"]}
    transformed_licenses.append(transformed_license)

# Read the existing schema file
with open("../schemas/zenodo/schema.json", "r") as f:
    schema = json.load(f)
    # Replace the property
    schema["properties"]["license"]["oneOf"] = transformed_licenses

# Override the file
with open("../schemas/zenodo/schema.json", "w") as f:
    f.write(json.dumps(schema, indent=2))
