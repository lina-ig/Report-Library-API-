# PFE Reports API

A Flask REST API for browsing student PFE reports. It has input validation,
a fixed token for reports, and an expiring JWT for confidential student data.
It runs in Docker.

## Run it
1. Copy `.env.example` to `.env` and fill in the values.
2. docker build -t pfe-api .
3. docker run -p 5000:5000 --env-file .env pfe-api

The API runs at http://127.0.0.1:5000

## Endpoints
- POST /students
- GET /students/<ID_S>  (requires student token)
- POST /reports
- GET /reports  (requires reports token)
- POST /auth/student-token
