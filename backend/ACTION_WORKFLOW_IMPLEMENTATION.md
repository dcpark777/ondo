# Action Workflow Implementation

Complete implementation of the improvement actions workflow where metadata updates trigger re-scoring, history recording, and UI refresh.

## Changes Made

### 1. Backend Updates

#### New Service: `app/services/dataset_metadata.py`
- `build_metadata_from_dataset()` - Converts Dataset model to metadata dict for scoring
- Handles all required fields for scoring engine

#### Updated Endpoints: `app/api/datasets.py`

**`POST /api/datasets/{id}/owner`**
- Now triggers re-scoring after owner update
- Saves score history
- Updates dimension scores, reasons, and actions

**`POST /api/datasets/{id}/metadata`**
- Now triggers re-scoring after metadata update
- Saves score history
- Updates dimension scores, reasons, and actions

Both endpoints now:
1. Update the dataset fields
2. Build metadata dict from updated dataset
3. Call `score_and_save_dataset()` to:
   - Re-compute score
   - Update dimension scores
   - Update reasons (point losses)
   - Update actions (improvements)
   - Save score history entry
4. Return updated dataset detail with new score

### 2. Frontend Updates

#### Updated: `app/datasets/[id]/page.tsx`
- Already refreshes dataset data after updates
- UI automatically updates with:
  - New score
  - Updated dimension breakdown
  - Updated reasons list
  - Updated actions checklist
  - New score history entry

### 3. Tests Added

#### `test_update_owner_triggers_rescoring`
- Verifies owner update increases score
- Verifies score history is recorded
- Verifies dataset is updated in database

#### `test_update_metadata_triggers_rescoring`
- Verifies metadata update increases score
- Verifies score history is recorded
- Verifies dataset is updated in database

#### `test_update_metadata_updates_actions`
- Verifies actions list updates after metadata changes
- Verifies actions decrease when issues are resolved

## Workflow

### When User Updates Owner:

1. **Frontend**: User clicks "Edit" → fills form → clicks "Save"
2. **API**: `POST /api/datasets/{id}/owner` called
3. **Backend**:
   - Updates `owner_name` and/or `owner_contact`
   - Builds metadata dict from updated dataset
   - Calls `score_and_save_dataset()`
   - Scoring engine computes new score
   - Saves dimension scores, reasons, actions
   - Records score history entry
4. **Response**: Returns updated dataset detail
5. **Frontend**: Updates UI with new score, actions, history

### When User Updates Metadata:

1. **Frontend**: User clicks "Edit" → fills form → clicks "Save"
2. **API**: `POST /api/datasets/{id}/metadata` called
3. **Backend**:
   - Updates `display_name`, `intended_use`, and/or `limitations`
   - Builds metadata dict from updated dataset
   - Calls `score_and_save_dataset()`
   - Scoring engine computes new score
   - Saves dimension scores, reasons, actions
   - Records score history entry
4. **Response**: Returns updated dataset detail
5. **Frontend**: Updates UI with new score, actions, history

## Score Changes

### Owner Update Impact:
- **Before**: No owner → 0 points (Ownership dimension)
- **After**: Owner added → +10 points (Ownership dimension)
- **With Contact**: Owner + contact → +15 points (Ownership dimension)

### Metadata Update Impact:
- **Before**: No intended_use, no limitations → 0 points (Operational dimension)
- **After**: Both added → +10 points (Operational dimension)
- **Partial**: One added → +5 points (Operational dimension)

## Example Scenarios

### Scenario 1: Adding Owner to Draft Dataset
```
Initial Score: 0 (Draft)
- No owner: -10 points
- No contact: -5 points

After adding owner:
New Score: 10 (Draft)
- Owner present: +10 points
- No contact: -5 points

After adding contact:
New Score: 15 (Draft)
- Owner present: +10 points
- Contact present: +5 points
```

### Scenario 2: Adding Metadata to Internal Dataset
```
Initial Score: 50 (Internal)
- Has owner: +15 points
- No intended_use: -5 points
- No limitations: -5 points

After adding intended_use:
New Score: 55 (Internal)
- Has owner: +15 points
- Intended_use present: +5 points
- No limitations: -5 points

After adding limitations:
New Score: 60 (Internal)
- Has owner: +15 points
- Intended_use present: +5 points
- Limitations present: +5 points
```

## Testing

Run tests with:
```bash
pytest tests/test_api.py::test_update_owner_triggers_rescoring -v
pytest tests/test_api.py::test_update_metadata_triggers_rescoring -v
pytest tests/test_api.py::test_update_metadata_updates_actions -v
```

All tests verify:
- Score changes after updates
- Score history is recorded
- Actions list updates
- Database is updated correctly

## UI Behavior

After any update:
1. Score header updates with new score
2. Status badge updates if status changed
3. Dimension breakdown bars update
4. Reasons list updates (fewer reasons if issues resolved)
5. Actions checklist updates (fewer actions if issues resolved)
6. Score history chart adds new entry
7. All changes visible immediately

## Benefits

✅ **Immediate Feedback**: Users see score changes instantly
✅ **Actionable**: Actions update as issues are resolved
✅ **Transparent**: Score history shows progression
✅ **Deterministic**: Same metadata always produces same score
✅ **Tested**: Comprehensive tests ensure correctness

