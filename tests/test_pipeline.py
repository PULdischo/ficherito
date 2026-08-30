"""Tests for pipeline orchestration, in particular that failed API calls are
never persisted as if they succeeded (which would make them permanently
"skipped" on future runs instead of retried).
"""

from pathlib import Path

import pytest
from PIL import Image

from ficherito.config import EnvSettings, FicheritoConfig
from ficherito.entities.extractor import EntityExtractionResult, Entity
from ficherito.htr.engine import TranscriptionResult
from ficherito import pipeline


def make_config(tmp_path: Path, images_dir: Path) -> FicheritoConfig:
    return FicheritoConfig(**{
        "dataset": {"images_dir": str(images_dir)},
        "output": {
            "transcriptions_dir": str(tmp_path / "transcriptions"),
            "entities_dir": str(tmp_path / "entities"),
        },
    })


def make_env() -> EnvSettings:
    return EnvSettings(OPENAI_API_KEY="test-key")


@pytest.fixture
def images_dir(tmp_path, monkeypatch):
    """A folder with two real images, and cwd set so `images/` writes land in tmp_path."""
    monkeypatch.chdir(tmp_path)
    src_dir = tmp_path / "source_images"
    src_dir.mkdir()
    for name in ("good", "bad"):
        Image.new("RGB", (2, 2), color="white").save(src_dir / f"{name}.jpg")
    return src_dir


class TestExtractionSkipsFailures:
    """A transcription result with empty text must not be written to disk."""

    def test_failed_extraction_is_not_saved(self, tmp_path, images_dir, monkeypatch):
        config = make_config(tmp_path, images_dir)
        env = make_env()

        async def fake_extract_batch_async(self, batch_docs, max_concurrent, on_complete):
            for _img, image_id in batch_docs:
                if image_id == "good":
                    result = TranscriptionResult(image_id=image_id, text="Hello world", model_name="test")
                else:
                    # Simulates HTRModel.extract_text_async swallowing a
                    # connection/API error and returning empty text.
                    result = TranscriptionResult(image_id=image_id, text="", model_name="test")
                on_complete(result)

        monkeypatch.setattr(
            "ficherito.htr.engine.HTREngine.extract_batch_async",
            fake_extract_batch_async,
        )

        errors = pipeline.run_extraction(config, env, max_concurrent=2, batch_size=10)

        transcriptions_dir = tmp_path / "transcriptions"
        assert (transcriptions_dir / "good.md").exists()
        assert not (transcriptions_dir / "bad.md").exists()
        assert errors == 1

    def test_failed_extraction_is_retried_on_next_run(self, tmp_path, images_dir, monkeypatch):
        config = make_config(tmp_path, images_dir)
        env = make_env()

        attempts = []

        async def fake_extract_batch_async(self, batch_docs, max_concurrent, on_complete):
            for _img, image_id in batch_docs:
                attempts.append(image_id)
                text = "Hello world" if image_id == "good" else ""
                on_complete(TranscriptionResult(image_id=image_id, text=text, model_name="test"))

        monkeypatch.setattr(
            "ficherito.htr.engine.HTREngine.extract_batch_async",
            fake_extract_batch_async,
        )

        pipeline.run_extraction(config, env, max_concurrent=2, batch_size=10)
        pipeline.run_extraction(config, env, max_concurrent=2, batch_size=10)

        # "good" only ever needed one attempt; "bad" has no saved
        # transcription so it must be retried on the second run.
        assert attempts.count("good") == 1
        assert attempts.count("bad") == 2


class TestEntityExtractionSkipsFailures:
    """An entity result marked unsuccessful must not be written to disk."""

    def test_failed_entity_extraction_is_not_saved(self, tmp_path, images_dir, monkeypatch):
        config = make_config(tmp_path, images_dir)
        env = make_env()

        transcriptions_dir = tmp_path / "transcriptions"
        transcriptions_dir.mkdir(parents=True)
        (transcriptions_dir / "good.md").write_text("---\ntitle: good\n---\n\nSome text about Paris.")
        (transcriptions_dir / "bad.md").write_text("---\ntitle: bad\n---\n\nSome other text.")

        async def fake_extract_batch_async(self, documents, max_concurrent, on_complete):
            for doc in documents:
                if doc["id"] == "good":
                    result = EntityExtractionResult(
                        source_image=doc["id"],
                        extracted_at="2026-01-01T00:00:00Z",
                        entities=[Entity(text="Paris", type="LOCATION", context="A city")],
                        success=True,
                    )
                else:
                    # Simulates the extractor swallowing an API/timeout error.
                    result = EntityExtractionResult(
                        source_image=doc["id"],
                        extracted_at="2026-01-01T00:00:00Z",
                        entities=[],
                        success=False,
                        error="Connection error.",
                    )
                on_complete(result)

        monkeypatch.setattr(
            "ficherito.entities.extractor.EntityExtractor.extract_batch_async",
            fake_extract_batch_async,
        )

        errors = pipeline.run_entity_extraction(config, env, max_concurrent=2)

        entities_dir = tmp_path / "entities"
        assert (entities_dir / "good.json").exists()
        assert not (entities_dir / "bad.json").exists()
        assert errors == 1
