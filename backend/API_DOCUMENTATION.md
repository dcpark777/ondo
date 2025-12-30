# API Documentation

FastAPI endpoints for Ondo dataset readiness scoring.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/health`

Returns service health status.

**Response:**
```json
{
  "status": "ok",
  "service": "Ondo API"
}
```

---

### List Datasets

**GET** `/api/datasets`

List all datasets with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by readiness status (`draft`, `internal`, `production_ready`, `gold`)
- `owner` (optional): Filter by owner name (partial match, case-insensitive)
- `q` (optional): Search query for `full_name` and `display_name` (partial match, case-insensitive)

**Example Requests:**
```
GET /api/datasets
GET /api/datasets?status=gold
GET /api/datasets?owner=Data%20Team
GET /api/datasets?q=users
GET /api/datasets?status=production_ready&owner=Analytics
```

**Response:**
```json
{
  "datasets": [
    {
      "id": "uuid",
      "full_name": "analytics.users",
      "display_name": "Users Table",
      "owner_name": "Data Team",
      "readiness_score": 85,
      "readiness_status": "gold",
      "last_scored_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Get Dataset Detail

**GET** `/api/datasets/{dataset_id}`

Get complete information about a dataset including score breakdown, reasons, actions, and history.

**Path Parameters:**
- `dataset_id`: UUID of the dataset

**Response:**
```json
{
  "id": "uuid",
  "full_name": "analytics.users",
  "display_name": "Users Table",
  "owner_name": "Data Team",
  "owner_contact": "#data-team",
  "intended_use": "Analytics, experimentation",
  "limitations": "Data delayed by 1 hour",
  "last_seen_at": "2024-01-01T12:00:00Z",
  "last_scored_at": "2024-01-01T12:00:00Z",
  "readiness_score": 85,
  "readiness_status": "gold",
  "dimension_scores": [
    {
      "dimension_key": "ownership",
      "points_awarded": 15,
      "max_points": 15,
      "percentage": 100.0
    },
    {
      "dimension_key": "documentation",
      "points_awarded": 15,
      "max_points": 20,
      "percentage": 75.0
    }
  ],
  "reasons": [
    {
      "id": "uuid",
      "dimension_key": "documentation",
      "reason_code": "insufficient_column_docs",
      "message": "Only 60% of columns documented (2 columns missing docs)",
      "points_lost": 10
    }
  ],
  "actions": [
    {
      "id": "uuid",
      "action_key": "document_columns",
      "title": "Document missing columns",
      "description": "Add descriptions for 2 undocumented columns",
      "points_gain": 10,
      "url": null
    }
  ],
  "score_history": [
    {
      "id": "uuid",
      "readiness_score": 85,
      "recorded_at": "2024-01-01T12:00:00Z",
      "scoring_version": "v1"
    }
  ]
}
```

---

### Update Owner

**POST** `/api/datasets/{dataset_id}/owner`

Update dataset owner and contact information.

**Path Parameters:**
- `dataset_id`: UUID of the dataset

**Request Body:**
```json
{
  "owner_name": "New Owner",
  "owner_contact": "#new-team"
}
```

Both fields are optional - only provided fields will be updated.

**Response:**
Returns the updated dataset detail (same shape as GET `/api/datasets/{dataset_id}`).

---

### Update Metadata

**POST** `/api/datasets/{dataset_id}/metadata`

Update dataset metadata (display_name, intended_use, limitations).

**Path Parameters:**
- `dataset_id`: UUID of the dataset

**Request Body:**
```json
{
  "display_name": "Updated Display Name",
  "intended_use": "New use case",
  "limitations": "Updated limitations"
}
```

All fields are optional - only provided fields will be updated.

**Response:**
Returns the updated dataset detail (same shape as GET `/api/datasets/{dataset_id}`).

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message"
}
```

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --reload

# Or with custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

