# PFE Reports API

A Flask REST API for browsing student PFE reports. It validates input, enforces
a report limit per student, and protects data with tokens. Student data is
confidential, so access to it uses an expiring JWT.

## Versions

| File | Storage | Notes |
|---|---|---|
| `app_og.py` | Python lists | Runs in Docker |
| `app_mysql.py` | MySQL database | Adds PUT, DELETE and `abort` errors |

## Rules

- A student has 1 report, or 2 if `DMaj` is 1 (double major).
- `level` must be one of: Freshman, Sophomore, Junior, Senior, Master's.
- Reports use a fixed token. Student data uses a token that expires after 15 minutes.

## Setup (MySQL version)

1. Install Python and MySQL, then create the database: `CREATE DATABASE pfe;`
2. Create a virtual environment and install packages:
   ```
   py -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in the values.
4. Run: `python app_mysql.py`

The tables are created automatically on startup. The API runs at http://127.0.0.1:5000

## Run with Docker (lists version)

```
docker build -t pfe-api .
docker run -p 5000:5000 --env-file .env pfe-api
```

Rebuild the image after any code change.

## Endpoints

| Method | URL | Token | Purpose |
|---|---|---|---|
| POST | `/auth/student-token` | none (send `{"secret": ...}`) | Get a student token |
| POST | `/students` | none | Create a student |
| GET | `/students/<ID_S>` | student token | Read one student |
| PUT | `/students/<ID_S>` | student token | Update a student (MySQL version) |
| DELETE | `/students/<ID_S>` | student token | Delete a student and their reports (MySQL version) |
| POST | `/reports` | none | Create a report |
| GET | `/reports` | reports token | List all reports |
| PUT | `/reports/<ID_R>` | reports token | Update a report (MySQL version) |
| DELETE | `/reports/<ID_R>` | reports token | Delete a report (MySQL version) |

Send tokens as `Authorization: Bearer <token>`.

## Status codes

- **200** OK, **201** Created, **204** Deleted
- **400** invalid data or report limit reached
- **401** missing, invalid or expired token
- **403** valid token, wrong endpoint
- **404** student or report not found
