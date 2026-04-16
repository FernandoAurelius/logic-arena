import tempfile
from shutil import rmtree
from pathlib import Path
from subprocess import run

from fastapi import FastAPI
from pydantic import BaseModel


class ExecutionRequest(BaseModel):
    language: str = 'python'
    source_code: str
    stdin: str = ''
    timeout_seconds: int = 5
    files: dict = {}
    entrypoint: str = 'main.py'


class ExecutionResponse(BaseModel):
    ok: bool
    stdout: str
    stderr: str


app = FastAPI(title='Logic Arena Runner', version='0.1.0')


@app.get('/health')
def health():
    return {'ok': True}


@app.post('/execute/python', response_model=ExecutionResponse)
def execute_python(payload: ExecutionRequest):
    temp_dir = Path(tempfile.mkdtemp(prefix='logic-arena-runner-'))
    entrypoint = Path(payload.entrypoint or 'main.py')

    if payload.files:
        for relative_path, raw_entry in payload.files.items():
            file_path = temp_dir / str(relative_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = raw_entry.get('content', '') if isinstance(raw_entry, dict) else raw_entry
            file_path.write_text(str(content), encoding='utf-8')
    else:
        file_path = temp_dir / entrypoint
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(payload.source_code, encoding='utf-8')

    entrypoint_path = temp_dir / entrypoint
    if not entrypoint_path.exists():
        entrypoint_path.parent.mkdir(parents=True, exist_ok=True)
        entrypoint_path.write_text(payload.source_code, encoding='utf-8')

    try:
        completed = run(
            ['python3', str(entrypoint_path)],
            input=payload.stdin,
            capture_output=True,
            text=True,
            timeout=payload.timeout_seconds,
            check=False,
            cwd=str(temp_dir),
        )
        return {
            'ok': completed.returncode == 0,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
        }
    except Exception as error:
        return {'ok': False, 'stdout': '', 'stderr': str(error)}
    finally:
        if temp_dir.exists():
            rmtree(temp_dir, ignore_errors=True)
