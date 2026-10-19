import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SOURCE_DIRS = ('app_bot/bot', 'app_worker/worker', 'app_api/api', 'yt_shared/src')
_CLASS_NAME_VIA_METACLASS = re.compile(
    r'\b[A-Z]\w*\.__class__\.__name__|_cls\.__class__\.__name__|_CLS\.__class__\.__name__'
)


def _source_files() -> list[Path]:
    return [path for root in _SOURCE_DIRS for path in (_REPO_ROOT / root).rglob('*.py')]


@pytest.mark.parametrize(
    'path', _source_files(), ids=lambda p: str(p.relative_to(_REPO_ROOT))
)
def test_class_names_are_not_read_from_the_metaclass(path: Path) -> None:
    assert not _CLASS_NAME_VIA_METACLASS.search(path.read_text())
