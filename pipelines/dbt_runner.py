import logging
import os
import subprocess
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def run_dbt_tests() -> dict:
    raw_url = os.environ.get("SUPABASE_DB_URL", "")
    if not raw_url:
        logger.warning("dbt: SUPABASE_DB_URL not set — skipping tests")
        return {"passed": False, "stdout": "", "stderr": "SUPABASE_DB_URL not set"}

    url = urlparse(raw_url)
    env = {
        **os.environ,
        "DBT_POSTGRES_HOST":     url.hostname or "",
        "DBT_POSTGRES_PORT":     str(url.port or 5432),
        "DBT_POSTGRES_USER":     url.username or "",
        "DBT_POSTGRES_PASSWORD": url.password or "",
        "DBT_POSTGRES_DBNAME":   (url.path or "").lstrip("/"),
    }

    try:
        result = subprocess.run(
            ["dbt", "test", "--profiles-dir", "dbt", "--project-dir", "dbt", "--target", "prod"],
            capture_output=True,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        logger.warning("dbt: dbt command not found — skipping tests")
        return {"passed": False, "stdout": "", "stderr": "dbt not installed"}

    logger.info("dbt: returncode=%d", result.returncode)
    return {
        "passed": result.returncode == 0,
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-1000:] if result.returncode != 0 else "",
    }
