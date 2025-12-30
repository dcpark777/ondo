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

    # Check dimension_scores structure
    assert isinstance(data["dimension_scores"], list)
    if len(data["dimension_scores"]) > 0:
        dim_score = data["dimension_scores"][0]
        assert "dimension_key" in dim_score
        assert "points_awarded" in dim_score
        assert "max_points" in dim_score
        assert "percentage" in dim_score
        assert isinstance(dim_score["percentage"], (int, float))

    # Check reasons structure
    assert isinstance(data["reasons"], list)
    if len(data["reasons"]) > 0:
        reason = data["reasons"][0]
        assert "id" in reason
        assert "dimension_key" in reason
        assert "reason_code" in reason
        assert "message" in reason
        assert "points_lost" in reason

    # Check actions structure
    assert isinstance(data["actions"], list)
    if len(data["actions"]) > 0:
        action = data["actions"][0]
        assert "id" in action
        assert "action_key" in action
        assert "title" in action
        assert "description" in action
        assert "points_gain" in action

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

