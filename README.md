# Data Submission Portal Backend
The Data Submission Portal is a website that provides recommendations, best practices, and supports submitting research data and other products to multiple Earth Science Data repositories. 

## Getting Started

*These instructions assume Docker and docker-compose are installed.

#### Run dspback with a development image

```commandline
make up
```

Access the OpenAPI docs at http://0.0.0.0:5002/redoc

#### Run the full stack (with dspfront)
A make command exists for building the dspfront image.  It temporarily clones the repository with the default branch and builds the image for you.

```commandline
make build-dspfront
```

Run the full stack (The dspfront image is a prerequisite and currently must be built from source)

```commandline
make up-all
```

Access the application at https://localhost/

These instructions built with the following versions:
```
Docker version 20.10.11, build dea9396
docker-compose version 1.29.2, build 5becea4c
```

## Development
TODO: Explain make commands available for building, configuration, adding new repositories and outline of the current architecture
## License
The Data Submission Portal is released under the BSD 3-Clause License. This means that [you can do what you want, so long as you don't mess with the trademark, and as long as you keep the license with the source code](https://github.com/cznethub/dspback/blob/develop/LICENSE).

©2021 CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards 2012893, 2012748, and 2012593. Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.
