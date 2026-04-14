from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1] / 'apps'
ARENA_API = ROOT / 'arena' / 'api.py'


def _imports_for(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def test_domain_modules_remain_pure():
    for path in sorted(ROOT.rglob('domain/*.py')):
        imports = _imports_for(path)
        assert not any(import_name.startswith('apps.') for import_name in imports), path


def test_non_interface_modules_do_not_depend_on_other_app_interfaces():
    for path in sorted(ROOT.rglob('*.py')):
        if path.name == '__init__.py' or '/interface/' in str(path) or path == ARENA_API:
            continue
        imports = _imports_for(path)
        forbidden = [import_name for import_name in imports if import_name.startswith('apps.') and '.interface' in import_name]
        assert not forbidden, f'{path}: {forbidden}'


def test_arena_api_keeps_external_application_imports_minimal():
    imports = _imports_for(ARENA_API)
    forbidden = [
        import_name
        for import_name in imports
        if import_name.startswith('apps.')
        and '.application.' in import_name
        and import_name != 'apps.progress.application.services'
    ]
    assert not forbidden, forbidden

