import json
import os
import tempfile
from pathlib import Path
from subprocess import run

from fastapi import FastAPI
from pydantic import BaseModel


class ExecutionRequest(BaseModel):
    language: str = 'python'
    source_code: str
    stdin: str = ''
    timeout_seconds: int = 5


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
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as handle:
        handle.write(payload.source_code)
        temp_path = Path(handle.name)

    try:
        completed = run(
            ['python3', str(temp_path)],
            input=payload.stdin,
            capture_output=True,
            text=True,
            timeout=payload.timeout_seconds,
            check=False,
        )
        return {
            'ok': completed.returncode == 0,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
        }
    except Exception as error:
        return {'ok': False, 'stdout': '', 'stderr': str(error)}
    finally:
        if temp_path.exists():
            os.unlink(temp_path)
