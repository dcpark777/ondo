"""
Tests for API endpoints and response shapes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base
from app.db import get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Ondo API"


def test_list_datasets_empty(client):
    """Test list datasets endpoint with no data."""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert "total" in data
    assert data["total"] == 0
    assert isinstance(data["datasets"], list)
    assert len(data["datasets"]) == 0


def test_list_datasets_response_shape(client, db_session):
    """Test list datasets response shape."""
    from app.models import Dataset, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create a test dataset
    dataset = Dataset(
        id=uuid.uuid4(),
        full_name="test.sample_table",
        display_name="Sample Table",
        owner_name="Test Owner",
        readiness_score=75,
        readiness_status=ReadinessStatusEnum.PRODUCTION_READY,
        last_seen_at=datetime.utcnow(),
        last_scored_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "datasets" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["datasets"]) == 1

    # Check dataset item structure
    dataset_item = data["datasets"][0]
    required_fields = [
        "id",
        "full_name",
        "display_name",
        "owner_name",
        "readiness_score",
        "readiness_status",
        "last_scored_at",
    ]
    for field in required_fields:
        assert field in dataset_item, f"Missing field: {field}"

    assert isinstance(dataset_item["id"], str)  # UUID as string
    assert dataset_item["full_name"] == "test.sample_table"
    assert dataset_item["display_name"] == "Sample Table"
    assert dataset_item["owner_name"] == "Test Owner"
    assert dataset_item["readiness_score"] == 75
    assert dataset_item["readiness_status"] == "production_ready"


def test_list_datasets_filtering(client, db_session):
    """Test dataset list filtering."""
    from app.models import Dataset, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create test datasets
    dataset1 = Dataset(
        id=uuid.uuid4(),
        full_name="test.table1",
        display_name="Table 1",
        owner_name="Owner A",
        readiness_score=90,
        readiness_status=ReadinessStatusEnum.GOLD,
        last_seen_at=datetime.utcnow(),
    )
    dataset2 = Dataset(
        id=uuid.uuid4(),
        full_name="test.table2",
        display_name="Table 2",
        owner_name="Owner B",
        readiness_score=60,
        readiness_status=ReadinessStatusEnum.INTERNAL,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add_all([dataset1, dataset2])
    db_session.commit()

    # Test status filter
    response = client.get("/api/datasets?status=gold")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["datasets"][0]["readiness_status"] == "gold"

    # Test owner filter
    response = client.get("/api/datasets?owner=Owner%20A")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["datasets"][0]["owner_name"] == "Owner A"

    # Test search query
    response = client.get("/api/datasets?q=table1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "table1" in data["datasets"][0]["full_name"].lower()


def test_get_dataset_detail_not_found(client):
    """Test dataset detail endpoint with non-existent dataset."""
    import uuid
    response = client.get(f"/api/datasets/{uuid.uuid4()}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_get_dataset_detail_response_shape(client, db_session):
    """Test dataset detail endpoint response shape."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        DatasetScoreHistory,
        ReadinessStatusEnum,
        DimensionKeyEnum,
    )
    from datetime import datetime
    import uuid

    dataset_id = uuid.uuid4()

    # Create dataset
    dataset = Dataset(
        id=dataset_id,
        full_name="test.detailed_table",
        display_name="Detailed Table",
        owner_name="Test Owner",
        owner_contact="#test-team",
        intended_use="Testing",
        limitations="None",
        readiness_score=80,
        readiness_status=ReadinessStatusEnum.PRODUCTION_READY,
        last_seen_at=datetime.utcnow(),
        last_scored_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.flush()

    # Create dimension score
    dim_score = DatasetDimensionScore(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key=DimensionKeyEnum.OWNERSHIP,
        points_awarded=15,
        max_points=15,
    )
    db_session.add(dim_score)

    # Create reason
    reason = DatasetReason(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key=DimensionKeyEnum.DOCUMENTATION,
        reason_code="missing_description",
        message="Dataset description is missing",
        points_lost=5,
    )
    db_session.add(reason)

    # Create action
    action = DatasetAction(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        action_key="add_description",
        title="Add dataset description",
        description="Write a clear description",
        points_gain=5,
    )
    db_session.add(action)

    # Create score history
    history = DatasetScoreHistory(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        readiness_score=80,
        recorded_at=datetime.utcnow(),
        scoring_version="v1",
    )
    db_session.add(history)
    db_session.commit()

    # Get dataset detail
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = [
        "id",
        "full_name",
        "display_name",
        "owner_name",
        "owner_contact",
        "intended_use",
        "limitations",
        "last_seen_at",
        "last_scored_at",
        "readiness_score",
        "readiness_status",
        "dimension_scores",
        "reasons",
        "actions",
        "score_history",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Check dimension_scores structure (Contract v1)
    assert isinstance(data["dimension_scores"], list)
    if len(data["dimension_scores"]) > 0:
        dim_score = data["dimension_scores"][0]
        assert "dimension_key" in dim_score
        assert "points_awarded" in dim_score
        assert "max_points" in dim_score
        assert "measured" in dim_score  # Contract v1: measured field
        assert isinstance(dim_score["measured"], bool)
        assert "percentage" in dim_score
        assert isinstance(dim_score["percentage"], (int, float))

    # Check reasons structure (Contract v1)
    assert isinstance(data["reasons"], list)
    if len(data["reasons"]) > 0:
        reason = data["reasons"][0]
        assert "id" in reason
        assert "dimension_key" in reason
        assert "reason_code" in reason  # Contract v1: stable constant
        assert isinstance(reason["reason_code"], str)
        assert "message" in reason
        assert "points_lost" in reason

    # Check actions structure (Contract v1)
    assert isinstance(data["actions"], list)
    if len(data["actions"]) > 0:
        action = data["actions"][0]
        assert "id" in action
        assert "action_key" in action  # Contract v1: stable constant
        assert isinstance(action["action_key"], str)
        assert "title" in action
        assert "description" in action
        assert "points_gain" in action
        # url is optional
        if "url" in action:
            assert action["url"] is None or isinstance(action["url"], str)

    # Check score_history structure
    assert isinstance(data["score_history"], list)
    if len(data["score_history"]) > 0:
        history = data["score_history"][0]
        assert "id" in history
        assert "readiness_score" in history
        assert "recorded_at" in history
        assert "scoring_version" in history


def test_update_owner(client, db_session):
    """Test update owner endpoint."""
    from app.models import Dataset, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.update_test",
        display_name="Update Test",
        readiness_score=50,
        readiness_status=ReadinessStatusEnum.INTERNAL,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Update owner
    response = client.post(
        f"/api/datasets/{dataset_id}/owner",
        json={"owner_name": "New Owner", "owner_contact": "#new-team"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["owner_name"] == "New Owner"
    assert data["owner_contact"] == "#new-team"


def test_update_metadata(client, db_session):
    """Test update metadata endpoint."""
    from app.models import Dataset, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.metadata_test",
        display_name="Metadata Test",
        readiness_score=50,
        readiness_status=ReadinessStatusEnum.INTERNAL,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Update metadata
    response = client.post(
        f"/api/datasets/{dataset_id}/metadata",
        json={
            "display_name": "Updated Name",
            "intended_use": "New use case",
            "limitations": "New limitations",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Name"
    assert data["intended_use"] == "New use case"
    assert data["limitations"] == "New limitations"


def test_ingest_mock_data(client, db_session):
    """Test mock ingestion endpoint."""
    response = client.post("/api/ingest/mock")
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "ingested" in data
    assert "errors" in data
    assert "datasets" in data
    assert data["ingested"] == 10
    assert data["errors"] == 0
    assert len(data["datasets"]) == 10

    # Check dataset structure
    dataset = data["datasets"][0]
    assert "id" in dataset
    assert "full_name" in dataset
    assert "display_name" in dataset
    assert "readiness_score" in dataset
    assert "readiness_status" in dataset

    # Verify datasets were created in database
    from app.models import Dataset, DatasetDimensionScore, DatasetReason, DatasetAction, DatasetScoreHistory
    datasets = db_session.query(Dataset).all()
    assert len(datasets) == 10

    # Verify scoring was run (check for dimension scores)
    for dataset in datasets:
        dim_scores = db_session.query(DatasetDimensionScore).filter(
            DatasetDimensionScore.dataset_id == dataset.id
        ).all()
        assert len(dim_scores) > 0, f"Dataset {dataset.full_name} should have dimension scores"

        # Verify score history was recorded
        history = db_session.query(DatasetScoreHistory).filter(
            DatasetScoreHistory.dataset_id == dataset.id
        ).all()
        assert len(history) > 0, f"Dataset {dataset.full_name} should have score history"

        # Verify score is set
        assert dataset.readiness_score >= 0
        assert dataset.readiness_score <= 100


def test_ingest_mock_data_idempotent(client, db_session):
    """Test that ingest can be run multiple times (updates existing)."""
    # First ingestion
    response1 = client.post("/api/ingest/mock")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["ingested"] == 10

    # Second ingestion (should update existing)
    response2 = client.post("/api/ingest/mock")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["ingested"] == 10

    # Should still have 10 datasets (not 20)
    from app.models import Dataset
    datasets = db_session.query(Dataset).all()
    assert len(datasets) == 10


def test_update_owner_triggers_rescoring(client, db_session):
    """Test that updating owner triggers re-scoring and updates score."""
    from app.models import Dataset, DatasetScoreHistory, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create a dataset without owner (should score low)
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.rescoring_test",
        display_name="Re-scoring Test",
        owner_name=None,  # No owner
        intended_use="Testing",
        limitations="None",
        readiness_score=0,
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Get initial score
    initial_score = dataset.readiness_score
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()

    # Update owner (should increase score)
    response = client.post(
        f"/api/datasets/{dataset_id}/owner",
        json={"owner_name": "Test Owner", "owner_contact": "#test-team"},
    )
    assert response.status_code == 200
    data = response.json()

    # Score should have increased (owner dimension adds 10-15 points)
    assert data["readiness_score"] > initial_score
    assert data["readiness_score"] >= 10  # At least ownership points

    # Score history should have a new entry
    new_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()
    assert new_history_count == initial_history_count + 1

    # Verify the dataset was updated in DB
    db_session.refresh(dataset)
    assert dataset.readiness_score > initial_score
    assert dataset.owner_name == "Test Owner"


def test_update_metadata_triggers_rescoring(client, db_session):
    """Test that updating metadata triggers re-scoring and updates score."""
    from app.models import Dataset, DatasetScoreHistory, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create a dataset without intended_use or limitations
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.metadata_rescoring",
        display_name="Metadata Re-scoring Test",
        owner_name="Test Owner",
        intended_use=None,  # Missing
        limitations=None,  # Missing
        readiness_score=15,  # Just ownership points
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Get initial score
    initial_score = dataset.readiness_score
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()

    # Update metadata (should increase score)
    response = client.post(
        f"/api/datasets/{dataset_id}/metadata",
        json={
            "intended_use": "Analytics, experimentation",
            "limitations": "Data delayed by 1 hour",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Score should have increased (operational dimension adds 10 points)
    assert data["readiness_score"] > initial_score
    assert data["readiness_score"] >= initial_score + 10  # Operational metadata points

    # Score history should have a new entry
    new_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()
    assert new_history_count == initial_history_count + 1

    # Verify the dataset was updated in DB
    db_session.refresh(dataset)
    assert dataset.readiness_score > initial_score
    assert dataset.intended_use == "Analytics, experimentation"
    assert dataset.limitations == "Data delayed by 1 hour"


def test_update_metadata_updates_actions(client, db_session):
    """Test that updating metadata updates the actions list."""
    from app.models import Dataset, DatasetAction, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create a dataset without intended_use (should have action to add it)
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.actions_update",
        display_name="Actions Update Test",
        owner_name="Test Owner",
        intended_use=None,  # Missing - should generate action
        limitations=None,  # Missing - should generate action
        readiness_score=15,
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Score the dataset initially
    from app.services.dataset_metadata import build_metadata_from_dataset
    from app.services.scoring_service import score_and_save_dataset
    metadata = build_metadata_from_dataset(dataset, columns=[])
    score_and_save_dataset(db_session, dataset, metadata)
    db_session.commit()

    # Get initial actions count
    initial_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    initial_actions_count = len(initial_actions)

    # Should have actions for missing intended_use and limitations
    assert initial_actions_count >= 2

    # Update metadata to add intended_use and limitations
    response = client.post(
        f"/api/datasets/{dataset_id}/metadata",
        json={
            "intended_use": "Analytics",
            "limitations": "None",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Actions should be updated (fewer actions now)
    updated_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    updated_actions_count = len(updated_actions)

    # Should have fewer actions (operational actions removed)
    assert updated_actions_count < initial_actions_count

    # Verify actions in response
    assert len(data["actions"]) == updated_actions_count


def test_dataset_detail_response_contract_v1(client, db_session):
    """Test that dataset detail response matches Contract v1 exactly."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        DatasetScoreHistory,
        ReadinessStatusEnum,
    )
    from datetime import datetime
    import uuid

    dataset_id = uuid.uuid4()

    # Create dataset with scoring data
    dataset = Dataset(
        id=dataset_id,
        full_name="test.contract_test",
        display_name="Contract Test",
        owner_name="Test Owner",
        readiness_score=75,
        readiness_status=ReadinessStatusEnum.PRODUCTION_READY,
        last_seen_at=datetime.utcnow(),
        last_scored_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.flush()

    # Create dimension score with measured field
    dim_score = DatasetDimensionScore(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="ownership",
        points_awarded=15,
        max_points=15,
        measured=1,  # Stored as integer
    )
    db_session.add(dim_score)

    # Create reason with stable reason_code
    reason = DatasetReason(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="documentation",
        reason_code="missing_description",  # Stable constant
        message="Dataset description is missing",
        points_lost=5,
    )
    db_session.add(reason)

    # Create action with stable action_key
    action = DatasetAction(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        action_key="add_description",  # Stable constant
        title="Add dataset description",
        description="Write a clear description",
        points_gain=5,
        url=None,
    )
    db_session.add(action)

    # Create score history
    history = DatasetScoreHistory(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        readiness_score=75,
        recorded_at=datetime.utcnow(),
        scoring_version="v1",
    )
    db_session.add(history)
    db_session.commit()

    # Get dataset detail
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()

    # Validate Contract v1: dimension_scores[]
    assert "dimension_scores" in data
    assert isinstance(data["dimension_scores"], list)
    assert len(data["dimension_scores"]) > 0
    
    dim = data["dimension_scores"][0]
    required_dim_fields = ["dimension_key", "points_awarded", "max_points", "measured", "percentage"]
    for field in required_dim_fields:
        assert field in dim, f"Missing dimension_scores field: {field}"
    assert isinstance(dim["dimension_key"], str)
    assert isinstance(dim["points_awarded"], int)
    assert isinstance(dim["max_points"], int)
    assert isinstance(dim["measured"], bool)  # Contract v1: boolean
    assert isinstance(dim["percentage"], (int, float))

    # Validate Contract v1: reasons[]
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    if len(data["reasons"]) > 0:
        reason_data = data["reasons"][0]
        required_reason_fields = ["id", "dimension_key", "reason_code", "message", "points_lost"]
        for field in required_reason_fields:
            assert field in reason_data, f"Missing reasons field: {field}"
        assert isinstance(reason_data["reason_code"], str)  # Stable constant
        # Verify it's a valid reason code (from constants)
        from app.scoring.constants import ReasonCode
        valid_reason_codes = [
            ReasonCode.MISSING_OWNER,
            ReasonCode.MISSING_CONTACT,
            ReasonCode.MISSING_DESCRIPTION,
            ReasonCode.INSUFFICIENT_COLUMN_DOCS,
            ReasonCode.NAMING_CONVENTION_VIOLATIONS,
            ReasonCode.HIGH_NULLABLE_RATIO,
            ReasonCode.LEGACY_COLUMNS_DETECTED,
            ReasonCode.MISSING_QUALITY_CHECKS,
            ReasonCode.MISSING_SLA,
            ReasonCode.UNRESOLVED_FAILURES,
            ReasonCode.BREAKING_CHANGES_DETECTED,
            ReasonCode.MISSING_CHANGELOG,
            ReasonCode.BACKWARD_INCOMPATIBLE,
            ReasonCode.MISSING_INTENDED_USE,
            ReasonCode.MISSING_LIMITATIONS,
        ]
        assert reason_data["reason_code"] in valid_reason_codes, f"Invalid reason_code: {reason_data['reason_code']}"

    # Validate Contract v1: actions[]
    assert "actions" in data
    assert isinstance(data["actions"], list)
    if len(data["actions"]) > 0:
        action_data = data["actions"][0]
        required_action_fields = ["id", "action_key", "title", "description", "points_gain"]
        for field in required_action_fields:
            assert field in action_data, f"Missing actions field: {field}"
        assert isinstance(action_data["action_key"], str)  # Stable constant
        # url is optional
        if "url" in action_data:
            assert action_data["url"] is None or isinstance(action_data["url"], str)
        # Verify it's a valid action key (from constants)
        from app.scoring.constants import ActionKey
        valid_action_keys = [
            ActionKey.ASSIGN_OWNER,
            ActionKey.ADD_OWNER_CONTACT,
            ActionKey.ADD_DESCRIPTION,
            ActionKey.DOCUMENT_COLUMNS,
            ActionKey.FIX_NAMING,
            ActionKey.REDUCE_NULLABLE_COLUMNS,
            ActionKey.REMOVE_LEGACY_COLUMNS,
            ActionKey.ADD_QUALITY_CHECKS,
            ActionKey.DEFINE_SLA,
            ActionKey.RESOLVE_FAILURES,
            ActionKey.PREVENT_BREAKING_CHANGES,
            ActionKey.ADD_CHANGELOG,
            ActionKey.MAINTAIN_COMPATIBILITY,
            ActionKey.DEFINE_INTENDED_USE,
            ActionKey.DOCUMENT_LIMITATIONS,
        ]
        assert action_data["action_key"] in valid_action_keys, f"Invalid action_key: {action_data['action_key']}"


def test_all_dimension_scores_have_measured_field(client, db_session):
    """Test that all dimension scores in response have the measured field."""
    from app.models import Dataset, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create and score a dataset
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.measured_test",
        display_name="Measured Test",
        owner_name="Test Owner",
        readiness_score=50,
        readiness_status=ReadinessStatusEnum.INTERNAL,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Score the dataset
    from app.services.dataset_metadata import build_metadata_from_dataset
    from app.services.scoring_service import score_and_save_dataset
    metadata = build_metadata_from_dataset(dataset, columns=[])
    score_and_save_dataset(db_session, dataset, metadata)
    db_session.commit()

    # Get dataset detail
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()

    # All dimension scores should have measured field
    assert len(data["dimension_scores"]) == 6  # All 6 dimensions
    for dim in data["dimension_scores"]:
        assert "measured" in dim
        assert isinstance(dim["measured"], bool)


def test_unmeasured_dimensions_hide_reasons_and_actions(client, db_session):
    """Test that reasons and actions are hidden for unmeasured dimensions."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        ReadinessStatusEnum,
    )
    from datetime import datetime
    import uuid

    dataset_id = uuid.uuid4()

    # Create dataset
    dataset = Dataset(
        id=dataset_id,
        full_name="test.unmeasured_test",
        display_name="Unmeasured Test",
        owner_name="Test Owner",
        readiness_score=15,  # Just ownership
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
        last_scored_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.flush()

    # Create dimension scores - schema_hygiene is NOT measured (no columns)
    ownership_score = DatasetDimensionScore(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="ownership",
        points_awarded=15,
        max_points=15,
        measured=1,  # Measured
    )
    schema_score = DatasetDimensionScore(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="schema_hygiene",
        points_awarded=0,
        max_points=15,
        measured=0,  # NOT measured
    )
    db_session.add_all([ownership_score, schema_score])
    db_session.flush()

    # Create reasons - one for measured dimension, one for unmeasured
    ownership_reason = DatasetReason(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="ownership",
        reason_code="missing_contact",
        message="Owner contact missing",
        points_lost=5,
    )
    schema_reason = DatasetReason(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        dimension_key="schema_hygiene",
        reason_code="naming_convention_violations",
        message="Naming violations",
        points_lost=5,
    )
    db_session.add_all([ownership_reason, schema_reason])
    db_session.flush()

    # Create actions - one for measured dimension, one for unmeasured
    ownership_action = DatasetAction(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        action_key="add_owner_contact",
        title="Add contact",
        description="Add owner contact",
        points_gain=5,
    )
    schema_action = DatasetAction(
        id=uuid.uuid4(),
        dataset_id=dataset_id,
        action_key="fix_naming",
        title="Fix naming",
        description="Fix column naming",
        points_gain=5,
    )
    db_session.add_all([ownership_action, schema_action])
    db_session.commit()

    # Get dataset detail
    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    data = response.json()

    # Verify schema_hygiene is not measured
    schema_dim = next(
        (d for d in data["dimension_scores"] if d["dimension_key"] == "schema_hygiene"),
        None
    )
    assert schema_dim is not None
    assert schema_dim["measured"] is False

    # Verify reasons are filtered - should only include ownership reason
    assert len(data["reasons"]) == 1
    assert data["reasons"][0]["dimension_key"] == "ownership"
    assert data["reasons"][0]["reason_code"] == "missing_contact"

    # Verify actions are filtered - should only include ownership action
    assert len(data["actions"]) == 1
    assert data["actions"][0]["action_key"] == "add_owner_contact"


def test_update_owner_persists_and_rescores_complete(client, db_session):
    """Test that updating owner persists to DB and triggers complete rescore workflow."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        DatasetScoreHistory,
        ReadinessStatusEnum,
    )
    from datetime import datetime
    import uuid

    # Create dataset without owner
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.complete_workflow",
        display_name="Complete Workflow Test",
        owner_name=None,
        owner_contact=None,
        intended_use="Testing",
        limitations="None",
        readiness_score=5,  # Low score without owner
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Get initial state
    initial_score = dataset.readiness_score
    initial_dim_scores_count = db_session.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset_id
    ).count()
    initial_reasons_count = db_session.query(DatasetReason).filter(
        DatasetReason.dataset_id == dataset_id
    ).count()
    initial_actions_count = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).count()
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()

    # Update owner
    response = client.post(
        f"/api/datasets/{dataset_id}/owner",
        json={"owner_name": "New Owner", "owner_contact": "#new-team"},
    )
    assert response.status_code == 200
    data = response.json()

    # 1. Verify dataset fields persisted and updated
    db_session.refresh(dataset)
    assert dataset.owner_name == "New Owner"
    assert dataset.owner_contact == "#new-team"
    assert dataset.readiness_score != initial_score
    assert dataset.readiness_score > initial_score  # Should increase with owner
    assert dataset.last_scored_at is not None
    assert dataset.readiness_status in ["draft", "internal", "production_ready", "gold"]

    # 2. Verify dimension_scores were replaced
    new_dim_scores = db_session.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset_id
    ).all()
    assert len(new_dim_scores) > 0
    # Should have scores for all 6 dimensions
    assert len(new_dim_scores) == 6
    # Verify ownership dimension has points
    ownership_score = next(
        (ds for ds in new_dim_scores if ds.dimension_key == "ownership"), None
    )
    assert ownership_score is not None
    assert ownership_score.points_awarded > 0

    # 3. Verify reasons were replaced
    new_reasons = db_session.query(DatasetReason).filter(
        DatasetReason.dataset_id == dataset_id
    ).all()
    # Reasons list may be empty or have items, but should be fresh
    assert isinstance(new_reasons, list)

    # 4. Verify actions were replaced
    new_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    assert isinstance(new_actions, list)

    # 5. Verify score_history was appended (not replaced)
    new_history = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).order_by(DatasetScoreHistory.recorded_at.desc()).all()
    assert len(new_history) == initial_history_count + 1
    # Latest history entry should match new score
    assert new_history[0].readiness_score == dataset.readiness_score
    assert new_history[0].scoring_version == "v1"

    # Verify response contains all updated data
    assert data["readiness_score"] == dataset.readiness_score
    assert data["readiness_status"] == dataset.readiness_status
    assert len(data["dimension_scores"]) == 6
    assert len(data["score_history"]) >= 1


def test_update_metadata_persists_and_rescores_complete(client, db_session):
    """Test that updating metadata persists to DB and triggers complete rescore workflow."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        DatasetScoreHistory,
        ReadinessStatusEnum,
    )
    from datetime import datetime
    import uuid

    # Create dataset without operational metadata
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.metadata_complete",
        display_name="Metadata Complete Test",
        owner_name="Test Owner",
        owner_contact="#test",
        intended_use=None,  # Missing
        limitations=None,  # Missing
        readiness_score=15,  # Just ownership
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Get initial state
    initial_score = dataset.readiness_score
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()

    # Update metadata
    response = client.post(
        f"/api/datasets/{dataset_id}/metadata",
        json={
            "display_name": "Updated Display Name",
            "intended_use": "Analytics and ML training",
            "limitations": "Data delayed by 2 hours",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # 1. Verify dataset fields persisted and updated
    db_session.refresh(dataset)
    assert dataset.display_name == "Updated Display Name"
    assert dataset.intended_use == "Analytics and ML training"
    assert dataset.limitations == "Data delayed by 2 hours"
    assert dataset.readiness_score != initial_score
    assert dataset.readiness_score > initial_score  # Should increase with operational metadata
    assert dataset.last_scored_at is not None

    # 2. Verify dimension_scores were replaced
    new_dim_scores = db_session.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset_id
    ).all()
    assert len(new_dim_scores) == 6
    # Verify operational dimension has points now
    operational_score = next(
        (ds for ds in new_dim_scores if ds.dimension_key == "operational"), None
    )
    assert operational_score is not None
    assert operational_score.points_awarded > 0

    # 3. Verify reasons were replaced
    new_reasons = db_session.query(DatasetReason).filter(
        DatasetReason.dataset_id == dataset_id
    ).all()
    assert isinstance(new_reasons, list)

    # 4. Verify actions were replaced (should have fewer now)
    new_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    assert isinstance(new_actions, list)

    # 5. Verify score_history was appended
    new_history = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).order_by(DatasetScoreHistory.recorded_at.desc()).all()
    assert len(new_history) == initial_history_count + 1
    assert new_history[0].readiness_score == dataset.readiness_score

    # Verify response contains all updated data
    assert data["display_name"] == "Updated Display Name"
    assert data["intended_use"] == "Analytics and ML training"
    assert data["limitations"] == "Data delayed by 2 hours"
    assert data["readiness_score"] == dataset.readiness_score


def test_update_all_fields_triggers_rescore(client, db_session):
    """Test updating all metadata fields (owner_name, owner_contact, intended_use, limitations, display_name) triggers rescore."""
    from app.models import Dataset, DatasetScoreHistory, ReadinessStatusEnum
    from datetime import datetime
    import uuid

    # Create minimal dataset
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.all_fields",
        display_name="All Fields Test",
        owner_name=None,
        owner_contact=None,
        intended_use=None,
        limitations=None,
        readiness_score=0,
        readiness_status=ReadinessStatusEnum.DRAFT,
        last_seen_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    initial_score = dataset.readiness_score
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()

    # Update owner first
    response1 = client.post(
        f"/api/datasets/{dataset_id}/owner",
        json={"owner_name": "Complete Owner", "owner_contact": "#complete-team"},
    )
    assert response1.status_code == 200
    data1 = response1.json()
    score_after_owner = data1["readiness_score"]
    assert score_after_owner > initial_score

    # Update metadata
    response2 = client.post(
        f"/api/datasets/{dataset_id}/metadata",
        json={
            "display_name": "Complete Dataset",
            "intended_use": "Full analytics pipeline",
            "limitations": "Real-time updates",
        },
    )
    assert response2.status_code == 200
    data2 = response2.json()
    final_score = data2["readiness_score"]
    assert final_score > score_after_owner  # Should increase further

    # Verify all fields persisted
    db_session.refresh(dataset)
    assert dataset.owner_name == "Complete Owner"
    assert dataset.owner_contact == "#complete-team"
    assert dataset.display_name == "Complete Dataset"
    assert dataset.intended_use == "Full analytics pipeline"
    assert dataset.limitations == "Real-time updates"

    # Verify score history has 2 new entries
    final_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()
    assert final_history_count == initial_history_count + 2

    # Verify final score is correct
    assert final_score == dataset.readiness_score
    assert dataset.last_scored_at is not None


def test_rescore_updates_all_tables_correctly(client, db_session):
    """Test that rescoring updates all 5 tables correctly: datasets, dimension_scores, reasons, actions, score_history."""
    from app.models import (
        Dataset,
        DatasetDimensionScore,
        DatasetReason,
        DatasetAction,
        DatasetScoreHistory,
        ReadinessStatusEnum,
    )
    from datetime import datetime
    import uuid

    # Create dataset and score it initially
    dataset_id = uuid.uuid4()
    dataset = Dataset(
        id=dataset_id,
        full_name="test.table_updates",
        display_name="Table Updates Test",
        owner_name="Initial Owner",
        owner_contact="#initial",
        intended_use="Initial use",
        limitations="Initial limits",
        readiness_score=50,
        readiness_status=ReadinessStatusEnum.INTERNAL,
        last_seen_at=datetime.utcnow(),
        last_scored_at=datetime.utcnow(),
    )
    db_session.add(dataset)
    db_session.commit()

    # Initial score to populate dimension_scores, reasons, actions, history
    from app.services.dataset_metadata import build_metadata_from_dataset
    from app.services.scoring_service import score_and_save_dataset
    metadata = build_metadata_from_dataset(dataset, columns=[])
    score_and_save_dataset(db_session, dataset, metadata)
    db_session.commit()

    # Get initial counts
    initial_dim_scores = db_session.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset_id
    ).all()
    initial_dim_score_ids = {ds.id for ds in initial_dim_scores}
    initial_reasons = db_session.query(DatasetReason).filter(
        DatasetReason.dataset_id == dataset_id
    ).all()
    initial_reason_ids = {r.id for r in initial_reasons}
    initial_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    initial_action_ids = {a.id for a in initial_actions}
    initial_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()
    initial_score = dataset.readiness_score

    # Update owner to trigger rescore
    response = client.post(
        f"/api/datasets/{dataset_id}/owner",
        json={"owner_name": "Updated Owner", "owner_contact": "#updated"},
    )
    assert response.status_code == 200

    # 1. Verify datasets table updated
    db_session.refresh(dataset)
    assert dataset.readiness_score != initial_score
    assert dataset.owner_name == "Updated Owner"
    assert dataset.last_scored_at is not None

    # 2. Verify dimension_scores were REPLACED (new IDs)
    new_dim_scores = db_session.query(DatasetDimensionScore).filter(
        DatasetDimensionScore.dataset_id == dataset_id
    ).all()
    new_dim_score_ids = {ds.id for ds in new_dim_scores}
    assert len(new_dim_scores) == 6
    # All IDs should be different (replaced, not appended)
    assert initial_dim_score_ids.isdisjoint(new_dim_score_ids)

    # 3. Verify reasons were REPLACED
    new_reasons = db_session.query(DatasetReason).filter(
        DatasetReason.dataset_id == dataset_id
    ).all()
    new_reason_ids = {r.id for r in new_reasons}
    # All IDs should be different (replaced, not appended)
    assert initial_reason_ids.isdisjoint(new_reason_ids)

    # 4. Verify actions were REPLACED
    new_actions = db_session.query(DatasetAction).filter(
        DatasetAction.dataset_id == dataset_id
    ).all()
    new_action_ids = {a.id for a in new_actions}
    # All IDs should be different (replaced, not appended)
    assert initial_action_ids.isdisjoint(new_action_ids)

    # 5. Verify score_history was APPENDED (count increased)
    new_history_count = db_session.query(DatasetScoreHistory).filter(
        DatasetScoreHistory.dataset_id == dataset_id
    ).count()
    assert new_history_count == initial_history_count + 1

    # Verify latest history entry
    latest_history = (
        db_session.query(DatasetScoreHistory)
        .filter(DatasetScoreHistory.dataset_id == dataset_id)
        .order_by(DatasetScoreHistory.recorded_at.desc())
        .first()
    )
    assert latest_history.readiness_score == dataset.readiness_score
    assert latest_history.scoring_version == "v1"

