#!/usr/bin/env python3
"""Run read-only Google Ads queries through the official MCP server (stdio) and
store each response as a live-read envelope for ``GoogleAdsLiveReadAdapter``.

Usage:
  gaql_via_mcp.py --customer 1234567890 --resource campaign \
      --fields campaign.id campaign.name metrics.cost_micros \
      --conditions "segments.date BETWEEN '2026-08-01' AND '2026-08-27'" \
      --query-id campaign-daily-v1 --out path/to/envelope.json

Secrets stay in the wrapper's environment; this script never prints them.
"""
from __future__ import annotations

import argparse
import os
import json
import select
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "google_ads_mcp.sh"


class MCPClient:
    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            ["bash", str(WRAPPER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self._id = 0
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "adbot-gaql", "version": "0.1"}}})
        self._recv()
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _next(self) -> int:
        self._id += 1
        return self._id

    def _send(self, obj: dict) -> None:
        assert self.proc.stdin
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self, timeout: float = 180) -> dict:
        assert self.proc.stdout
        end = time.time() + timeout
        while time.time() < end:
            ready, _, _ = select.select([self.proc.stdout], [], [], 1)
            if ready:
                line = self.proc.stdout.readline()
                if not line:
                    raise RuntimeError("MCP server closed the connection")
                line = line.strip()
                if line.startswith("{"):
                    return json.loads(line)
        raise TimeoutError("MCP server did not answer in time")

    def call(self, name: str, arguments: dict) -> dict:
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "tools/call",
                    "params": {"name": name, "arguments": arguments}})
        response = self._recv()
        result = response.get("result") or {}
        if response.get("error") or result.get("isError"):
            text = response.get("error") or result.get("content")
            raise RuntimeError(f"{name} failed: {json.dumps(text, ensure_ascii=False)[:2000]}")
        return result

    def close(self) -> None:
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def rows_from_result(result: dict):
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and "result" in structured:
        payload = structured["result"]
    else:
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        payload = json.loads(text) if text else []
    if isinstance(payload, str):
        payload = json.loads(payload)
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"]
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer", required=True, help="10-digit customer ID without dashes")
    parser.add_argument("--resource", required=True)
    parser.add_argument("--fields", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="*", default=[])
    parser.add_argument("--order-by", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--login-customer-id", default=None, help="manager ID; defaults to the customer itself (direct access)")
    parser.add_argument("--api-version", default="v21", help="record the API version the server uses")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    arguments = {"customer_id": args.customer, "resource": args.resource, "fields": args.fields,
                 "conditions": args.conditions}
    if args.order_by:
        arguments["orderings"] = args.order_by
    if args.limit:
        arguments["limit"] = args.limit
    login = args.login_customer_id or args.customer
    os.environ["GOOGLE_ADS_LOGIN_CUSTOMER_ID"] = login
    client = MCPClient()
    try:
        result = client.call("search_search", arguments)
    finally:
        client.close()
    rows = rows_from_result(result)
    if not isinstance(rows, list):
        raise SystemExit(f"unexpected result shape: {type(rows).__name__}")
    envelope = {
        "schema_version": "1.0.0", "platform": "google", "customer_id": args.customer,
        "login_customer_id": login, "api_version": args.api_version,
        "query_id": args.query_id,
        "query": f"SELECT {', '.join(args.fields)} FROM {args.resource}" + (" WHERE " + " AND ".join(args.conditions) if args.conditions else ""),
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "rows": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"query_id": args.query_id, "customer_id": args.customer, "rows": len(rows), "out": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
