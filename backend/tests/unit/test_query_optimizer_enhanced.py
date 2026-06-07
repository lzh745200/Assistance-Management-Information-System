"""Tests for query optimizer enhancements."""

import pytest
from sqlalchemy import create_engine, text, Column, Integer, String, select
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()


class QueryTestModel(Base):
    __test__ = False  # 阻止 pytest 收集
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class TestQueryOptimizer:
    """Query optimizer basic tests."""

    @pytest.fixture
    def engine(self):
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        return engine

    def test_simple_select(self, engine):
        with Session(engine) as session:
            result = session.scalars(select(QueryTestModel)).all()
            assert result == []

    def test_insert_and_select(self, engine):
        with Session(engine) as session:
            session.add(QueryTestModel(name="test"))
            session.commit()
            result = session.scalars(select(QueryTestModel)).all()
            assert len(result) == 1
            assert result[0].name == "test"

    def test_bulk_insert(self, engine):
        with Session(engine) as session:
            session.add_all([QueryTestModel(name=f"item_{i}") for i in range(10)])
            session.commit()
            count = session.query(QueryTestModel).count()
            assert count == 10
