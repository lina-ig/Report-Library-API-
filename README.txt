# Student REST API

A simple REST API built with Flask for managing student records. It lets clients create students and retrieve the full list of students as JSON.

## Features

- Add a new student with first name, last name, and reports
- Retrieve all stored students
- Auto-generated student IDs
- JSON request and response format

## Endpoints

| Method | Endpoint   | Description          |
|--------|------------|----------------------|
| GET    | `/student` | Get all students     |
| POST   | `/student` | Add a new student    |

### Example POST body

```json
{
  "Fname": "John",
  "Lname": "Doe",
  "reports": []
}
```

## Getting Started

1. Install Flask:
```bash
   pip install flask
```
2. Run the app:
```bash
   flask run
```
3. The API will be available at `http://127.0.0.1:5000`.

## Notes

Data is stored in memory, so it resets whenever the server restarts.
