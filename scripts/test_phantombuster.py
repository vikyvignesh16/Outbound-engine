"""
Test script — verify PhantomBuster API connection and dump raw agent output.

Usage:
    PHANTOMBUSTER_API_KEY=xxx python scripts/test_phantombuster.py
    PHANTOMBUSTER_API_KEY=xxx python scripts/test_phantombuster.py --phase1 https://www.linkedin.com/company/deliveroo
"""
import argparse
import json
import os
import sys
import time

import httpx

PB_BASE = "https://api.phantombuster.com/api/v2"
COMPANY_EXTRACTOR_ID = "2647129464753754"
SALES_NAV_ID         = "4820708527700699"


def headers() -> dict:
    key = os.environ.get("PHANTOMBUSTER_API_KEY", "")
    if not key:
        print("ERROR: PHANTOMBUSTER_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)
    return {"X-Phantombuster-Key": key}


def inspect_agent(agent_id: str) -> None:
    """Print agent metadata and last run status."""
    with httpx.Client() as client:
        resp = client.get(f"{PB_BASE}/agents/fetch", headers=headers(), params={"id": agent_id})
        resp.raise_for_status()
        data = resp.json()

    print(f"\n── Agent {agent_id} ──────────────────────")
    print(f"  Name:        {data.get('name')}")
    print(f"  Script:      {data.get('scriptId')}")
    print(f"  Last status: {data.get('lastEndMessage')}")
    print(f"  Last run:    {data.get('updatedAt')}")


def launch_and_poll(agent_id: str, argument: dict, label: str, timeout: int = 120) -> dict | None:
    """Launch agent, poll until done, return container dict."""
    print(f"\n── Launching {label} ──────────────────────")
    print(f"  Argument: {json.dumps(argument, indent=2)}")

    with httpx.Client() as client:
        resp = client.post(
            f"{PB_BASE}/agents/launch",
            headers=headers(),
            json={"id": agent_id, "argument": argument},
            timeout=30,
        )
        resp.raise_for_status()
        container_id = resp.json()["containerId"]
        print(f"  Container ID: {container_id}")

    start = time.time()
    while time.time() - start < timeout:
        time.sleep(10)
        with httpx.Client() as client:
            resp = client.get(
                f"{PB_BASE}/containers/fetch",
                headers=headers(),
                params={"id": container_id},
            )
            resp.raise_for_status()
            container = resp.json()

        status = container.get("status")
        print(f"  Status: {status}")

        if status in ("finished", "error", "stopped"):
            print(f"\n── Raw resultObject ──────────────────────")
            raw = container.get("resultObject") or "[]"
            result = json.loads(raw) if isinstance(raw, str) else raw
            print(json.dumps(result, indent=2))

            if isinstance(result, list) and result:
                print(f"\n── Field names in first row ──────────────")
                for k, v in result[0].items():
                    print(f"  {k}: {repr(v)[:80]}")

            return container

    print(f"  Timed out after {timeout}s")
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase1", metavar="LINKEDIN_URL",
                        help="Test Phase 1: launch Company Extractor against this URL")
    parser.add_argument("--inspect-only", action="store_true",
                        help="Only inspect agents, don't launch anything")
    args = parser.parse_args()

    # Always inspect both agents
    inspect_agent(COMPANY_EXTRACTOR_ID)
    inspect_agent(SALES_NAV_ID)

    if args.inspect_only:
        return

    if args.phase1:
        container = launch_and_poll(
            COMPANY_EXTRACTOR_ID,
            {"linkedInCompanyUrl": args.phase1},
            label="LinkedIn Company Extractor",
        )
        if container:
            raw = container.get("resultObject") or "[]"
            result = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(result, list) and result:
                row = result[0]
                # Show which field contains the numeric org ID
                org_id_candidates = {k: v for k, v in row.items()
                                     if isinstance(v, (int, str)) and str(v).isdigit() and len(str(v)) > 5}
                print(f"\n── Likely org ID fields ──────────────────")
                for k, v in org_id_candidates.items():
                    print(f"  {k}: {v}")
    else:
        print("\nTip: run with --phase1 <linkedin_url> to test a live Phase 1 job")
        print("     run with --inspect-only to only check agent metadata")


if __name__ == "__main__":
    main()
