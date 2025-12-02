# Tests Directory

Unit and integration tests for the Bensley Operations Platform.

## Running Tests

```bash
# Run all tests
make test

# Or directly with pytest
pytest tests/ -v

# Run specific test file
pytest tests/test_email_service.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html
```

## Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── test_*.py            # Test files (prefix with test_)
└── README.md            # This file
```

## Writing Tests

1. Create test files with `test_` prefix
2. Use fixtures from `conftest.py` for common setup
3. Use `temp_database` fixture for database tests (auto-cleanup)
4. Follow naming: `test_<function_name>_<scenario>`

## Fixtures Available

- `project_root` - Path to project root
- `database_path` - Path to main database
- `temp_database` - Temporary test database (auto-cleanup)
- `db_connection` - SQLite connection to temp database
- `sample_project` - Sample project data dict
- `sample_proposal` - Sample proposal data dict
- `sample_email` - Sample email data dict

## Example Test

```python
def test_project_creation(db_connection, sample_project):
    """Test creating a project in the database."""
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO projects (project_code, project_title, status) VALUES (?, ?, ?)",
        (sample_project["project_code"], sample_project["project_title"], sample_project["status"])
    )
    db_connection.commit()

    cursor.execute("SELECT * FROM projects WHERE project_code = ?", (sample_project["project_code"],))
    result = cursor.fetchone()

    assert result is not None
    assert result["project_title"] == sample_project["project_title"]
```
