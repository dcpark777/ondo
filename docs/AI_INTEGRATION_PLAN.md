# Real AI/LLM Integration — Planning Document

## Current State

The AI Assist feature in Ondo is **template-based** — it generates canned suggestions
based on dataset metadata patterns rather than calling a real LLM.

**Existing code:**
- `backend/app/api/ai.py` — Endpoints for dataset/column description generation
- `backend/app/services/ai_descriptions.py` — Template-based description generator
- `backend/app/config.py` — `ai_assist_enabled` flag (env: `AI_ASSIST_ENABLED`)
- Frontend components in OverviewTab.tsx and SchemaTab.tsx consume the API

## Proposed Architecture

### Option A: Direct LLM API Integration
- Add `anthropic` or `openai` SDK to `requirements.txt`
- Replace template logic in `ai_descriptions.py` with LLM API calls
- Use dataset context (name, columns, types, lineage, tags, domain) as prompt context
- Stream responses for better UX

### Option B: Plugin/Provider Pattern
- Define an `AIProvider` interface in `backend/app/services/ai_provider.py`
- Implement `TemplateProvider` (current behavior) and `LLMProvider`
- Configure via environment variable: `AI_PROVIDER=template|anthropic|openai`
- Easier to test and extend

## Features to Power with AI

1. **Dataset Description Generation** (existing endpoint, upgrade quality)
2. **Column Description Generation** (existing endpoint, upgrade quality)
3. **Quality Rule Suggestions** — Analyze column types/names → suggest rules
4. **Classification Suggestions** — Analyze content → suggest PII/classification
5. **Glossary Term Matching** — Auto-link columns to glossary terms by semantic similarity
6. **Anomaly Detection** — Compare profile snapshots → flag unusual changes
7. **Natural Language Search** — Convert user queries to structured filters

## Key Considerations

- **Cost control**: Cache LLM responses, set rate limits per user
- **Latency**: Use streaming for long responses, show progress indicators
- **Privacy**: Ensure dataset metadata sent to LLM doesn't contain actual data values
- **Fallback**: Always keep template-based fallback when LLM is unavailable
- **Testing**: Mock LLM responses in tests, don't depend on external APIs

## Environment Variables Needed

```
AI_PROVIDER=template        # template | anthropic | openai
ANTHROPIC_API_KEY=sk-...    # Required if AI_PROVIDER=anthropic
OPENAI_API_KEY=sk-...       # Required if AI_PROVIDER=openai
AI_MODEL=claude-sonnet-4-5-20250514   # Model to use
AI_MAX_TOKENS=1024          # Max tokens per request
AI_CACHE_TTL=3600           # Cache TTL in seconds
```

## Implementation Steps

1. Create `AIProvider` abstract base class
2. Implement `AnthropicProvider` with Anthropic SDK
3. Update `ai_descriptions.py` to use provider pattern
4. Add streaming support to description endpoints
5. Add quality rule suggestion endpoint
6. Add classification suggestion endpoint
7. Add glossary auto-linking endpoint
8. Update frontend to show streaming responses
9. Add caching layer (in-memory or Redis)
10. Add rate limiting

## Status: NOT STARTED
_Created: 2026-02-21. Revisit when core data catalog features are stable._
