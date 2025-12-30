# AI Assist Implementation

Optional AI assist feature for generating dataset and column descriptions. Behind a feature flag for safety and control.

## Configuration

### Environment Variable

Set `AI_ASSIST_ENABLED=true` in your `.env` file to enable AI assist endpoints.

```bash
AI_ASSIST_ENABLED=true
```

If not set or set to `false`, the endpoints will return 403 Forbidden.

## Endpoints

### 1. Generate Dataset Description

**POST** `/api/ai/dataset-description`

Generates a suggested dataset description based on metadata.

**Request:**
```json
{
  "full_name": "analytics.users",
  "display_name": "Users Table",
  "owner_name": "Data Team",
  "intended_use": "Analytics, experimentation",
  "limitations": "Data delayed by 1 hour",
  "column_names": ["user_id", "email", "created_at"]
}
```

**Response:**
```json
{
  "suggested_description": "This dataset contains users table. Intended use cases: Analytics, experimentation. The dataset includes 3 columns. Limitations: Data delayed by 1 hour. Maintained by Data Team."
}
```

### 2. Generate Column Descriptions

**POST** `/api/ai/column-descriptions`

Generates suggested descriptions for multiple columns based on column names.

**Request:**
```json
{
  "dataset_name": "analytics.users",
  "column_names": ["user_id", "email", "created_at", "status"],
  "existing_descriptions": {
    "user_id": "User identifier"
  }
}
```

**Response:**
```json
{
  "suggested_descriptions": {
    "email": "Email address associated with this record.",
    "created_at": "Timestamp indicating when this record was created or last updated.",
    "status": "Current status of this record."
  }
}
```

## Safety Features

✅ **Metadata Only**: Only uses metadata (names, types, context) - never raw data values
✅ **Never Auto-Applies**: Returns suggestions only - user must manually apply
✅ **Feature Flag**: Disabled by default, must be explicitly enabled
✅ **Error Handling**: Clear error messages if feature is disabled

## Implementation Details

### Backend

- **Template-Based Generation**: For MVP, uses template-based heuristics
- **Production Ready**: Structure supports LLM API integration (OpenAI, Anthropic, etc.)
- **Pattern Recognition**: Recognizes common column name patterns (_id, _at, _type, etc.)

### Frontend

- **"✨ AI Suggest" Button**: Appears in metadata section
- **Suggestion Display**: Shows suggested text in a highlighted box
- **Copy Button**: Allows copying suggestion to clipboard
- **Manual Apply**: User must paste and apply manually (never auto-applied)

## Usage Flow

1. User clicks "✨ AI Suggest" button
2. Frontend sends request with current metadata
3. Backend generates suggestion (metadata-only)
4. Frontend displays suggestion in purple box
5. User can:
   - Copy suggestion to clipboard
   - Paste into description field
   - Manually edit before applying
   - Dismiss suggestion

## Production Integration

To integrate with a real LLM API (e.g., OpenAI):

```python
# In app/api/ai.py
import openai

def _generate_dataset_description(request: DatasetDescriptionRequest) -> str:
    prompt = f"""
    Generate a concise dataset description for:
    - Name: {request.full_name}
    - Display Name: {request.display_name}
    - Owner: {request.owner_name}
    - Intended Use: {request.intended_use}
    - Limitations: {request.limitations}
    - Columns: {', '.join(request.column_names or [])}
    
    Only use the metadata provided. Never use actual data values.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    return response.choices[0].message.content
```

## Testing

Test with feature disabled:
```bash
# Should return 403
curl -X POST http://localhost:8000/api/ai/dataset-description \
  -H "Content-Type: application/json" \
  -d '{"full_name": "test.table"}'
```

Test with feature enabled:
```bash
# Set AI_ASSIST_ENABLED=true in .env
# Should return suggestion
curl -X POST http://localhost:8000/api/ai/dataset-description \
  -H "Content-Type: application/json" \
  -d '{"full_name": "analytics.users", "display_name": "Users Table"}'
```

## Security Considerations

1. **No Raw Data**: Endpoints never receive or process raw data values
2. **Metadata Only**: Only column names, types, and context are used
3. **User Control**: Suggestions are never auto-applied
4. **Feature Flag**: Can be disabled at any time
5. **Rate Limiting**: Consider adding rate limiting for production use

## Future Enhancements

- Integration with OpenAI/Anthropic APIs
- Column-level suggestions in detail view
- Bulk description generation
- Custom prompt templates
- User feedback on suggestions

