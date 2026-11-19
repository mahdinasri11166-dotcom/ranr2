# -*- coding: utf-8 -*-
"""Agent tools registry: FS + OSINT + advanced + RAG + plugins + browser (read-only)."""
from __future__ import annotations

import json
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Callable

from config_loader import ROOT, workspace_dir, load_approval_policy

WORKSPACE = workspace_dir()

try:
    from osint_tools import OSINT_TOOLS, osint_schema_for_prompt
except ImportError:
    OSINT_TOOLS = {}
    def osint_schema_for_prompt() -> str:
        return ""

try:
    from osint_advanced import ADVANCED_OSINT
except ImportError:
    ADVANCED_OSINT = {}

try:
    from case_manager import CASE_TOOLS
except ImportError:
    CASE_TOOLS = {}

try:
    from elevated_tools import ELEVATED_TOOLS
except ImportError:
    ELEVATED_TOOLS = {}

try:
    from builder_tools import BUILDER_TOOLS
except ImportError:
    BUILDER_TOOLS = {}

try:
    from coding_tools import CODING_TOOLS
except ImportError:
    CODING_TOOLS = {}

try:
    from browser_tools import BROWSER_LAYER_TOOLS
except ImportError:
    BROWSER_LAYER_TOOLS = {}

try:
    from agent_memory import MEMORY_LAYER_TOOLS
except ImportError:
    MEMORY_LAYER_TOOLS = {}

try:
    from system_named_tools import SYSTEM_NAMED_TOOLS
except ImportError:
    SYSTEM_NAMED_TOOLS = {}

try:
    from session_store import session_list, session_load, session_delete, session_export_md
except ImportError:
    session_list = session_load = session_delete = session_export_md = None

try:
    from report_engine import tool_generate_osint_report, save_report
except ImportError:
    tool_generate_osint_report = None
    save_report = None

try:
    from plugin_system import plugin_list, plugin_run, ensure_sample_plugin
except ImportError:
    plugin_list = plugin_run = ensure_sample_plugin = None

try:
    from browser_readonly import browser_read
except ImportError:
    browser_read = None

try:
    from rag_local import rag_search, build_index
except ImportError:
    rag_search = build_index = None

try:
    from policy_guards import refuse_bruteforce, refuse_aggressive_vuln_scan
except ImportError:
    def refuse_bruteforce(**kw):
        return {"ok": False, "blocked": True, "error": "brute-force disabled"}
    def refuse_aggressive_vuln_scan(**kw):
        return {"ok": False, "blocked": True, "error": "aggressive scan disabled"}

try:
    from doctor import run_doctor, model_wizard
except ImportError:
    run_doctor = model_wizard = None


def _safe_path(rel: str) -> Path:
    rel = (rel or "").replace("\\", "/").lstrip("/")
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE.resolve())):
        raise PermissionError(f"Path outside workspace blocked: {rel}")
    return target


def tool_list_dir(path: str = ".") -> dict[str, Any]:
    p = _safe_path(path)
    if not p.exists():
        return {"ok": False, "error": "not found"}
    if not p.is_dir():
        return {"ok": False, "error": "not a directory"}
    items = []
    for child in sorted(p.iterdir())[:500]:
        items.append({
            "name": child.name,
            "type": "dir" if child.is_dir() else "file",
            "size": child.stat().st_size if child.is_file() else None,
        })
    return {"ok": True, "path": str(p.relative_to(WORKSPACE)), "items": items}


def tool_read_file(path: str, max_bytes: int = 200_000) -> dict[str, Any]:
    p = _safe_path(path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "file not found"}
    data = p.read_bytes()[:max_bytes]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
    return {"ok": True, "path": path, "content": text, "truncated": len(data) >= p.stat().st_size}


def tool_write_file(path: str, content: str) -> dict[str, Any]:
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "bytes": len(content.encode("utf-8"))}


def tool_make_zip(paths: list[str] | None = None, out_name: str = "export.zip") -> dict[str, Any]:
    paths = paths or ["."]
    out = _safe_path(out_name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in paths:
            src = _safe_path(rel)
            if src.is_file():
                zf.write(src, arcname=src.name)
            elif src.is_dir():
                for f in src.rglob("*"):
                    if f.is_file():
                        zf.write(f, arcname=str(f.relative_to(src.parent)))
    return {"ok": True, "zip": str(out.relative_to(WORKSPACE))}


def tool_run_python(code: str, timeout: int = 15) -> dict[str, Any]:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8", dir=str(WORKSPACE)) as f:
        f.write(code)
        tmp = f.name
    try:
        r = subprocess.run(
            [os.environ.get("PYTHON", "python"), tmp],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        return {
            "ok": r.returncode == 0,
            "stdout": (r.stdout or "")[:8000],
            "stderr": (r.stderr or "")[:4000],
            "returncode": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def tool_app_settings(action: str = "get") -> dict[str, Any]:
    from config_loader import load_ini
    if action == "get":
        return {"ok": True, "config": load_ini()}
    return {"ok": False, "error": "only get supported from tools"}


def tool_save_osint_report(name: str, data: dict | str = None) -> dict[str, Any]:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in (name or "report"))[:80]
    rel = f"osint/{safe}.json"
    p = _safe_path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "path": rel}


def tool_memory_search(query: str, top_k: int = 5) -> dict[str, Any]:
    from urllib.request import Request, urlopen
    try:
        body = json.dumps({"query": query, "top_k": top_k}).encode()
        req = Request("http://127.0.0.1:8765/search", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        if rag_search:
            return rag_search(query, top_k=top_k)
        return {"ok": False, "error": f"memory server unreachable: {e}"}


CORE_TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_dir": tool_list_dir,
    "fs_list": tool_list_dir,
    "read_file": tool_read_file,
    "fs_read": tool_read_file,
    "write_file": tool_write_file,
    "fs_write": tool_write_file,
    "make_zip": tool_make_zip,
    "fs_zip": tool_make_zip,
    "run_python": tool_run_python,
    "code_run": tool_run_python,
    "app_settings": tool_app_settings,
    "app_config": tool_app_settings,
    "save_osint_report": tool_save_osint_report,
    "memory_search": tool_memory_search,
    "rag_search": tool_memory_search,
}

if tool_generate_osint_report:
    CORE_TOOLS["generate_osint_report"] = tool_generate_osint_report
if plugin_list:
    CORE_TOOLS["plugin_list"] = lambda: plugin_list()
    CORE_TOOLS["plugin_run"] = lambda plugin_id, arguments=None: plugin_run(plugin_id, arguments or {})
if browser_read:
    CORE_TOOLS["browser_read"] = browser_read
if rag_search:
    CORE_TOOLS["rag_local_search"] = rag_search
    CORE_TOOLS["rag_build_index"] = lambda max_docs=400: build_index(max_docs=max_docs)
if run_doctor:
    CORE_TOOLS["doctor"] = lambda: run_doctor()
    CORE_TOOLS["model_wizard"] = lambda: model_wizard()
if session_list:
    CORE_TOOLS["session_list"] = lambda limit=50: session_list(limit=limit)
    CORE_TOOLS["session_load"] = lambda file_name: session_load(file_name)
    CORE_TOOLS["session_delete"] = lambda file_name: session_delete(file_name)
    CORE_TOOLS["session_export_md"] = lambda file_name, out_name=None: session_export_md(file_name, out_name)

# Policy: register refusal names so agent/docs know they are blocked
CORE_TOOLS["bruteforce"] = refuse_bruteforce
CORE_TOOLS["brute_force"] = refuse_bruteforce
CORE_TOOLS["vuln_scan"] = refuse_aggressive_vuln_scan
CORE_TOOLS["aggressive_scan"] = refuse_aggressive_vuln_scan
CORE_TOOLS["port_scan"] = refuse_aggressive_vuln_scan

TOOLS: dict[str, Callable[..., dict[str, Any]]] = {**CORE_TOOLS, **OSINT_TOOLS, **ADVANCED_OSINT, **CASE_TOOLS, **ELEVATED_TOOLS, **BUILDER_TOOLS, **CODING_TOOLS, **BROWSER_LAYER_TOOLS, **MEMORY_LAYER_TOOLS, **SYSTEM_NAMED_TOOLS}


def needs_approval(tool_name: str) -> bool:
    try:
        policy = load_approval_policy() or {}
        if tool_name in (policy.get("blocked_tools") or []):
            return True
        tools = policy.get("tools") or {}
        level = tools.get(tool_name) or policy.get("default") or "REQUIRE_APPROVAL"
        return str(level).upper() == "REQUIRE_APPROVAL"
    except Exception:
        return True  # fail closed


def execute_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(name, str) or not name.strip():
        return {"ok": False, "error": "tool name required"}
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return {"ok": False, "error": "arguments must be a dict"}
    fn = TOOLS.get(name)
    if not fn:
        return {"ok": False, "error": f"unknown tool: {name}", "available": sorted(TOOLS.keys())[:80]}
    try:
        import inspect
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return fn(**arguments)
        params = sig.parameters
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
            result = fn(**arguments)
        else:
            allowed = {k: v for k, v in arguments.items() if k in params}
            # fill defaults-only call if no args needed
            result = fn(**allowed)
        if result is None:
            return {"ok": True, "result": None}
        if not isinstance(result, dict):
            return {"ok": True, "result": result}
        return result
    except TypeError as e:
        return {"ok": False, "error": f"bad arguments: {e}", "tool": name}
    except Exception as e:
        return {"ok": False, "error": str(e), "tool": name, "type": type(e).__name__}


def tools_schema_for_prompt(include_osint: bool = True) -> str:
    base = """Available tools (JSON tool call when needed):
FILE (workspace only): list_dir, read_file, write_file, make_zip, run_python, app_settings
MEMORY: memory_search / rag_local_search / rag_build_index
REPORT: save_osint_report, generate_osint_report(name, target, data_json)
PLUGINS: plugin_list, plugin_run(plugin_id, arguments)
BROWSER (read-only): browser_read(url)
DOCTOR: doctor, model_wizard
SESSIONS: session_list, session_load(file_name), session_delete(file_name)
CODE: search_code, apply_patch, run_tests, shell_allowlisted, git_status/diff/log/commit
BROWSER: browser_fetch, browser_playwright, fetch_json
MEMORY: todo_plan/list/tick, memory_save/get, session_reflect, workspace_rag_search/rebuild
SYS_NAMED (elevated): process_list, env_get, open_app, clipboard_get/set, notify
BUILD: build_scaffold(name, template), build_write_files(files), build_list_templates, build_tree(path)
ELEVATED (need elevated_mode=true + approval): sys_info, sys_list_dir, sys_read_file,
  sys_write_file, sys_run_cmd, sys_open_path, sys_open_url
BLOCKED (will refuse): bruteforce, vuln_scan, aggressive_scan, port_scan

Tool call: {"tool": "name", "arguments": {...}}
"""
    if include_osint:
        base += "\n" + osint_schema_for_prompt()
        base += """
Cases:
- case_create(name, target="", notes="")
- case_list() / case_get(case_id)
- case_add_note(case_id, text) / case_add_event(case_id, event, detail="")
- case_attach_json(case_id, artifact_name, data)
- case_export_report(case_id)

Advanced OSINT:
- osint_email_dns(email) — MX/SPF/DMARC via DNS (no breach dump)
- osint_crtsh(domain) — subdomains from certificate transparency
- osint_domain_graph(domain) — DNS+TLS+crt.sh relationship graph
- osint_username_parallel(username) — parallel checks + cache + confidence
- osint_file_metadata(path) — EXIF / PDF producer under workspace
"""
    return base


# Ensure sample plugin exists on import (safe)
try:
    if ensure_sample_plugin:
        ensure_sample_plugin()
except Exception:
    pass
