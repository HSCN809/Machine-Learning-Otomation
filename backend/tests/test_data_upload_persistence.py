import unittest

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.database import Base
from backend.api.dependencies import restore_persisted_session, session_manager
from backend.modules.data_upload.models import DatasetSession
from backend.modules.data_upload.persistence import (
    DataSessionRepository,
    dataframe_from_json,
    dataframe_to_json,
)


class RenameMetadata(BaseModel):
    column: str
    new_name: str


class DataUploadPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=self.engine, tables=[DatasetSession.__table__])
        self.Session = sessionmaker(bind=self.engine, future=True)

    def test_round_trips_uploaded_dataframe(self):
        df = pd.DataFrame(
            {
                "name": ["Ada", "Linus"],
                "score": [1.5, None],
                "active": [True, False],
            }
        )

        restored = dataframe_from_json(dataframe_to_json(df))

        pd.testing.assert_frame_equal(restored, df)

    def test_upserts_dataset_session_record(self):
        df = pd.DataFrame({"city": ["Ankara", "Izmir"], "value": [10, 20]})

        with self.Session() as db:
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="session-1",
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            record = repository.get_session("session-1")

            self.assertIsNotNone(record)
            self.assertEqual(record.filename, "cities.csv")
            self.assertEqual(record.row_count, 2)
            self.assertEqual(record.column_count, 2)
            pd.testing.assert_frame_equal(dataframe_from_json(record.data_json), df)

    def test_restores_persisted_session_into_memory(self):
        df = pd.DataFrame({"city": ["Ankara", "Izmir"], "value": [10, 20]})
        session_id = "restore-session-1"
        session_manager.delete_session(session_id)
        self.addCleanup(session_manager.delete_session, session_id)

        with self.Session() as db:
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id=session_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            restored = restore_persisted_session(session_id, db)

            self.assertTrue(restored)
            memory_session = session_manager.get_session(session_id)
            self.assertIsNotNone(memory_session)
            self.assertEqual(memory_session["metadata"]["filename"], "cities.csv")
            pd.testing.assert_frame_equal(memory_session["data"], df)

    def test_upsert_accepts_json_safe_metadata(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="metadata-session-1",
                data=df,
                original_data=df.copy(deep=True),
                metadata={
                    "filename": "cities.csv",
                    "renamed_columns": [RenameMetadata(column="city", new_name="location")],
                },
            )
            db.commit()

            record = repository.get_session("metadata-session-1")

            self.assertEqual(
                record.metadata_json["renamed_columns"],
                [{"column": "city", "new_name": "location"}],
            )


if __name__ == "__main__":
    unittest.main()
