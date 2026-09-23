content = open("tests/test_v23_strategy.py").read()
fixture_code = """
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from jobs_automation.db.models import Base

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
"""
content = content.replace("import yaml", "import yaml\n" + fixture_code)
with open("tests/test_v23_strategy.py", "w") as f:
    f.write(content)
