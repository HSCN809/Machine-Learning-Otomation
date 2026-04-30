import asyncio
import unittest
from io import BytesIO
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.database import Base
from backend.api.dependencies import persist_session, restore_persisted_session, session_manager
from backend.api.redis_cache import make_cache_key
from backend.api.routers.preprocessing import MissingValuesRequest, handle_missing_values
from backend.api.routers.upload import upload_file
from backend.modules.auth.models import User
from backend.modules.data_upload.models import DatasetSession, PreprocessingEvent, TimelineSnapshot
from backend.modules.data_upload.persistence import (
    DataSessionRepository,
    dataframe_from_json,
    dataframe_to_json,
)


class RenameMetadata(BaseModel):
    column: str
    new_name: str


class DummyRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


class DataUploadPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(
            bind=self.engine,
            tables=[
                User.__table__,
                DatasetSession.__table__,
                PreprocessingEvent.__table__,
                TimelineSnapshot.__table__,
            ],
        )
        self.Session = sessionmaker(bind=self.engine, future=True)
        self.user_id = "user-1"
        self.other_user_id = "user-2"

    def create_user(self, db, user_id: str, email: str) -> User:
        user = User(
            id=user_id,
            email=email,
            full_name="Test User",
            password_hash="hashed-password",
        )
        db.add(user)
        db.flush()
        return user

    def create_default_users(self, db) -> None:
        self.create_user(db, self.user_id, "user1@example.com")
        self.create_user(db, self.other_user_id, "user2@example.com")

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
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            record = repository.get_session("session-1", self.user_id)

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
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id=session_id,
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            restored = restore_persisted_session(session_id, self.user_id, db)

            self.assertTrue(restored)
            memory_session = session_manager.get_session(session_id)
            self.assertIsNotNone(memory_session)
            self.assertEqual(memory_session["owner_user_id"], self.user_id)
            self.assertEqual(memory_session["metadata"]["filename"], "cities.csv")
            pd.testing.assert_frame_equal(memory_session["data"], df)

    def test_upsert_accepts_json_safe_metadata(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="metadata-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={
                    "filename": "cities.csv",
                    "renamed_columns": [RenameMetadata(column="city", new_name="location")],
                },
            )
            db.commit()

            record = repository.get_session("metadata-session-1", self.user_id)

            self.assertEqual(
                record.metadata_json["renamed_columns"],
                [{"column": "city", "new_name": "location"}],
            )

    def test_upsert_stores_owner_user_id(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="owned-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            record = repository.get_session("owned-session-1", self.user_id)

            self.assertIsNotNone(record)
            self.assertEqual(record.user_id, self.user_id)

    def test_get_session_is_scoped_to_owner(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="scoped-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            self.assertIsNotNone(repository.get_session("scoped-session-1", self.user_id))
            self.assertIsNone(repository.get_session("scoped-session-1", self.other_user_id))

    def test_list_sessions_returns_only_owner_records_sorted_by_updated_at(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="list-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "first.csv"},
            )
            repository.upsert_session(
                session_id="list-session-2",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "second.csv"},
            )
            repository.upsert_session(
                session_id="list-session-3",
                user_id=self.other_user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "other.csv"},
            )
            db.commit()

            renamed = repository.rename_session("list-session-1", self.user_id, "first-renamed.csv")
            self.assertIsNotNone(renamed)
            db.commit()

            records = repository.list_sessions(self.user_id)

            self.assertEqual([record.id for record in records], ["list-session-1", "list-session-2"])

    def test_rename_session_updates_filename_and_metadata_for_owner(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="rename-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            record = repository.rename_session("rename-session-1", self.user_id, "cities-v2.csv")
            db.commit()

            self.assertIsNotNone(record)
            self.assertEqual(record.filename, "cities-v2.csv")
            self.assertEqual(record.metadata_json["filename"], "cities-v2.csv")
            self.assertIsNone(repository.rename_session("rename-session-1", self.other_user_id, "nope.csv"))

    def test_delete_session_only_deletes_owner_record(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="delete-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            repository.delete_session("delete-session-1", self.other_user_id)
            db.commit()
            self.assertIsNotNone(repository.get_session("delete-session-1", self.user_id))

            repository.delete_session("delete-session-1", self.user_id)
            db.commit()
            self.assertIsNone(repository.get_session("delete-session-1", self.user_id))

    def test_restore_rejects_non_owner(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = "restore-owner-session-1"
        session_manager.delete_session(session_id)
        self.addCleanup(session_manager.delete_session, session_id)

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id=session_id,
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            db.commit()

            restored = restore_persisted_session(session_id, self.other_user_id, db)

            self.assertFalse(restored)
            self.assertIsNone(session_manager.get_session(session_id))

    def test_unsupported_upload_format_preserves_400(self):
        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            file = UploadFile(file=BytesIO(b"plain text"), filename="notes.txt")

            with self.assertRaises(HTTPException) as exc:
                asyncio.run(upload_file(request=DummyRequest(), file=file, session_id=session_id, db=db))

            self.assertEqual(exc.exception.status_code, 400)
            self.assertEqual(
                exc.exception.detail,
                "Unsupported file format. Use CSV, Excel, or JSON.",
            )

    def test_upload_rejects_content_length_over_limit(self):
        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            file = UploadFile(file=BytesIO(b"city,value\nAnkara,10\n"), filename="cities.csv")

            request = DummyRequest(headers={"content-length": str(201 * 1024 * 1024)})

            with self.assertRaises(HTTPException) as exc:
                asyncio.run(upload_file(request=request, file=file, session_id=session_id, db=db))

            self.assertEqual(exc.exception.status_code, 413)

    def test_upload_rejects_fake_xlsx_content(self):
        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            file = UploadFile(file=BytesIO(b"not a real xlsx"), filename="fake.xlsx")

            with self.assertRaises(HTTPException) as exc:
                asyncio.run(upload_file(request=DummyRequest(), file=file, session_id=session_id, db=db))

            self.assertEqual(exc.exception.status_code, 400)
            self.assertEqual(exc.exception.detail, "Invalid XLSX file content.")

    def test_upload_rejects_binary_csv_content(self):
        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            file = UploadFile(file=BytesIO(b"col\x00value\n1\x002\n"), filename="binary.csv")

            with self.assertRaises(HTTPException) as exc:
                asyncio.run(upload_file(request=DummyRequest(), file=file, session_id=session_id, db=db))

            self.assertEqual(exc.exception.status_code, 400)
            self.assertEqual(exc.exception.detail, "Invalid CSV file content.")

    def test_upload_accepts_valid_csv_content(self):
        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            file = UploadFile(file=BytesIO(b"city,value\nAnkara,10\nIzmir,20\n"), filename="cities.csv")

            response = asyncio.run(upload_file(request=DummyRequest(), file=file, session_id=session_id, db=db))

            self.assertTrue(response["success"])
            self.assertEqual(response["rows"], 2)
            self.assertEqual(response["columns"], 2)
            self.assertEqual(response["column_names"], ["city", "value"])

    def test_missing_values_preprocessing_persists_processed_data(self):
        df = pd.DataFrame({"city": ["Ankara", "Izmir"], "value": [10.0, None]})

        with self.Session() as db:
            self.create_default_users(db)
            db.commit()
            session_id = session_manager.create_session(owner_user_id=self.user_id)
            self.addCleanup(session_manager.delete_session, session_id)
            session_manager.set_dataframe(session_id, df.copy(deep=True), is_original=True)
            session_manager.set_metadata(session_id, "filename", "cities.csv")

            response = asyncio.run(
                handle_missing_values(
                    MissingValuesRequest(method="fill_mean", columns=["value"]),
                    session_id=session_id,
                    db=db,
                )
            )

            self.assertTrue(response["success"])
            session_manager.delete_session(session_id)
            self.assertTrue(restore_persisted_session(session_id, self.user_id, db))
            memory_session = session_manager.get_session(session_id)
            self.assertIsNotNone(memory_session)
            self.assertEqual(memory_session["data"]["value"].isnull().sum(), 0)
            self.assertEqual(memory_session["data"].loc[1, "value"], 10.0)
            self.assertEqual(len(memory_session["history"]), 1)
            self.assertEqual(memory_session["history"][0]["step"], "missing_values")

    def test_preprocessing_history_is_scoped_and_persisted_as_events(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        history = [
            {
                "step": "scaling",
                "action": "standard",
                "columns": ["value"],
                "timestamp": "2026-01-01T00:00:00",
            }
        ]

        with self.Session() as db:
            self.create_default_users(db)
            repository = DataSessionRepository(db)
            repository.upsert_session(
                session_id="history-session-1",
                user_id=self.user_id,
                data=df,
                original_data=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
            )
            repository.sync_preprocessing_history(
                session_id="history-session-1",
                user_id=self.user_id,
                history=history,
            )
            db.commit()

            self.assertEqual(
                repository.list_preprocessing_history("history-session-1", self.user_id),
                history,
            )
            self.assertEqual(
                repository.list_preprocessing_history("history-session-1", self.other_user_id),
                [],
            )

    def test_generic_timeline_events_and_snapshots_are_persisted_and_restored(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = "timeline-session-1"
        session_manager.delete_session(session_id)
        self.addCleanup(session_manager.delete_session, session_id)

        with self.Session() as db:
            self.create_default_users(db)
            session_manager.restore_session(
                session_id=session_id,
                df=df.copy(deep=True),
                original_df=df.copy(deep=True),
                metadata={"filename": "cities.csv"},
                owner_user_id=self.user_id,
                timeline_events=[],
                timeline_snapshots=[],
            )
            event = session_manager.add_timeline_event(
                session_id,
                {
                    "category": "editor",
                    "action": "manual_edit_commit",
                    "title": "Edit kaydedildi",
                    "description": "Editor degisikligi kaydedildi.",
                    "undoable": True,
                    "metadata": {"updated_cells": 1},
                    "payload": {"updated_cells": 1},
                },
            )
            session_manager.add_timeline_snapshot(session_id, event["id"], df.copy(deep=True))
            persist_session(session_id, db)

            session_manager.delete_session(session_id)
            self.assertTrue(restore_persisted_session(session_id, self.user_id, db))
            restored = session_manager.get_session(session_id)

            self.assertIsNotNone(restored)
            self.assertEqual(len(restored["timeline_events"]), 1)
            self.assertEqual(restored["timeline_events"][0]["category"], "editor")
            self.assertEqual(len(restored["timeline_snapshots"]), 1)
            pd.testing.assert_frame_equal(restored["timeline_snapshots"][0]["data"], df)

    def test_last_informational_timeline_event_cannot_be_undone(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = session_manager.create_session(owner_user_id=self.user_id)
        self.addCleanup(session_manager.delete_session, session_id)
        session_manager.set_dataframe(session_id, df.copy(deep=True), is_original=True)
        session_manager.add_timeline_event(
            session_id,
            {
                "category": "upload",
                "action": "file_uploaded",
                "title": "Upload",
                "description": "Dosya yuklendi",
                "undoable": False,
            },
        )

        with self.assertRaises(HTTPException) as exc:
            session_manager.undo_last_timeline_event(session_id)

        self.assertEqual(exc.exception.status_code, 409)

    def test_make_cache_key_scopes_entries_by_session_id(self):
        key = make_cache_key("numeric_stats", "session-1")

        self.assertTrue(key.startswith("be:numeric_stats:session-1:"))

    def test_set_dataframe_invalidates_session_cache(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = session_manager.create_session(owner_user_id=self.user_id)
        self.addCleanup(session_manager.delete_session, session_id)

        with patch("backend.api.dependencies.cache_invalidate_session") as invalidate_cache:
            session_manager.set_dataframe(session_id, df.copy(deep=True), is_original=True)

        invalidate_cache.assert_called_once_with(session_id)

    def test_undo_last_timeline_event_invalidates_session_cache(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = session_manager.create_session(owner_user_id=self.user_id)
        self.addCleanup(session_manager.delete_session, session_id)
        session_manager.set_dataframe(session_id, df.copy(deep=True), is_original=True)
        event = session_manager.add_timeline_event(
            session_id,
            {
                "category": "editor",
                "action": "manual_edit_commit",
                "title": "Edit kaydedildi",
                "description": "Editor degisikligi kaydedildi.",
                "undoable": True,
            },
        )
        session_manager.add_timeline_snapshot(session_id, event["id"], df.copy(deep=True))

        with patch("backend.api.dependencies.cache_invalidate_session") as invalidate_cache:
            session_manager.undo_last_timeline_event(session_id)

        invalidate_cache.assert_called_once_with(session_id)

    def test_undo_last_history_action_invalidates_session_cache(self):
        df = pd.DataFrame({"city": ["Ankara"], "value": [10]})
        session_id = session_manager.create_session(owner_user_id=self.user_id)
        self.addCleanup(session_manager.delete_session, session_id)
        session_manager.set_dataframe(session_id, df.copy(deep=True), is_original=True)
        session_manager.add_history_snapshot(session_id, df.copy(deep=True))
        session_manager.add_history(
            session_id,
            {
                "step": "missing_values",
                "action": "fill_mean",
                "columns": ["value"],
            },
        )

        with patch("backend.api.dependencies.cache_invalidate_session") as invalidate_cache:
            session_manager.undo_last_history_action(session_id)

        invalidate_cache.assert_called_once_with(session_id)


if __name__ == "__main__":
    unittest.main()
