import hashlib
from pathlib import Path
from datetime import datetime, timezone


def compute_hash(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def get_metadata(filepath: str | Path) -> dict:
    p = Path(filepath).resolve()
    if not p.exists():
        raise FileNotFoundError(f"No such file: {p}")

    stat = p.stat()
    return {
        "hash":          compute_hash(p),
        "path":          str(p),
        "filename":      p.name,
        "extension":     p.suffix.lower() or None,
        "size_bytes":    stat.st_size,
        "modified_at":   datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "registered_at": datetime.now(tz=timezone.utc).isoformat(),
    }


def register_file(filepath: str) -> dict:
    from fg.db.session import get_session
    meta = get_metadata(filepath)
    with get_session() as conn:
        conn.execute("""
            INSERT INTO files (hash, path, filename, extension, size_bytes, modified_at, registered_at)
            VALUES (:hash, :path, :filename, :extension, :size_bytes, :modified_at, :registered_at)
            ON CONFLICT(hash) DO UPDATE SET
                path        = excluded.path,
                modified_at = excluded.modified_at
        """, meta)
    return meta
