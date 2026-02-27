"""Dataset loading and handling for HuggingFace datasets."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from datasets import load_dataset, Dataset
from PIL import Image
from rich.progress import Progress, TaskID

from flatfish.config import FlatfishConfig, EnvSettings
from flatfish.utils.dates import extract_date_from_filename


@dataclass
class DocumentImage:
    """Represents a single document image from the dataset."""

    image: Image.Image
    image_id: str
    filename: str
    split: str
    date: str | None = None
    metadata: dict | None = None


def load_hf_dataset(
    config: FlatfishConfig,
    env: EnvSettings,
    split: str | None = None,
) -> Dataset:
    """Load a HuggingFace dataset.

    Args:
        config: Flatfish configuration.
        env: Environment settings with tokens.
        split: Optional specific split to load.

    Returns:
        Loaded dataset.
    """
    token = env.huggingface_token

    splits_to_load = [split] if split else config.dataset.splits

    datasets = []
    for s in splits_to_load:
        ds = load_dataset(
            config.dataset.source,
            split=s,
            token=token,
        )
        # Add split info to each example
        ds = ds.map(lambda x: {**x, "_split": s})
        datasets.append(ds)

    # Concatenate all splits
    if len(datasets) == 1:
        return datasets[0]

    from datasets import concatenate_datasets
    return concatenate_datasets(datasets)


def iter_document_images(
    dataset: Dataset,
    config: FlatfishConfig,
    limit: int | None = None,
    progress: Progress | None = None,
    task_id: TaskID | None = None,
) -> Iterator[DocumentImage]:
    """Iterate over document images in a dataset.

    Args:
        dataset: HuggingFace dataset.
        config: Flatfish configuration.
        limit: Optional limit on number of images.
        progress: Optional Rich progress bar.
        task_id: Optional task ID for progress updates.

    Yields:
        DocumentImage instances.
    """
    image_column = config.dataset.image_column

    total = min(len(dataset), limit) if limit else len(dataset)

    for i, example in enumerate(dataset):
        if limit and i >= limit:
            break

        # Get image
        img = example.get(image_column)
        if img is None:
            continue

        # Ensure it's a PIL Image
        if not isinstance(img, Image.Image):
            # datasets library sometimes returns dict with bytes
            if isinstance(img, dict) and "bytes" in img:
                from io import BytesIO
                img = Image.open(BytesIO(img["bytes"]))
            else:
                continue

        # Generate image ID and filename
        # Priority: name_column from config > filename > image_id > id > index
        name_column = config.dataset.name_column
        
        if name_column and name_column in example:
            # Use the configured name column
            name_value = str(example[name_column])
            # Extract stem (without extension) for image_id
            image_id = Path(name_value).stem
            # Use original extension or default to jpg
            ext = Path(name_value).suffix
            filename = name_value if ext else f"{name_value}.jpg"
        elif "filename" in example:
            filename = example["filename"]
            image_id = Path(filename).stem
        elif "image_id" in example:
            image_id = str(example["image_id"])
            filename = f"{image_id}.jpg"
        elif "id" in example:
            image_id = str(example["id"])
            filename = f"{image_id}.jpg"
        else:
            image_id = f"img{i:05d}"
            filename = f"{image_id}.jpg"

        # Extract date from filename
        date = extract_date_from_filename(filename)

        # Get any additional metadata
        metadata = {
            k: v for k, v in example.items()
            if k not in [image_column, "_split", "filename", "image_id", "id"]
            and not k.startswith("_")
        }

        split = example.get("_split", "unknown")

        if progress and task_id is not None:
            progress.update(task_id, advance=1)

        yield DocumentImage(
            image=img,
            image_id=image_id,
            filename=filename,
            split=split,
            date=date,
            metadata=metadata if metadata else None,
        )


def save_image(
    doc: DocumentImage,
    output_dir: Path,
    format: str = "JPEG",
) -> Path:
    """Save a document image to disk.

    Args:
        doc: Document image to save.
        output_dir: Directory to save to.
        format: Image format (JPEG, PNG, etc.)

    Returns:
        Path to saved image.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ext = "jpg" if format.upper() == "JPEG" else format.lower()
    output_path = output_dir / f"{doc.image_id}.{ext}"

    # Convert to RGB if necessary (for JPEG)
    img = doc.image
    if format.upper() == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(output_path, format=format)
    return output_path
