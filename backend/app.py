"""Flask application for network pre/post change testing.

Environment variables required before starting:
  NET_USERNAME  — SSH username for all devices
  NET_PASSWORD  — SSH password for all devices
  NET_SECRET    — Enable password (optional)

The YAML configuration is uploaded by the user at runtime via POST /api/upload.
Nothing is read from or written to the local filesystem except snapshot files.
"""

import datetime
import difflib
import json
import os

import yaml
from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.environ.get("SNAPSHOTS_DIR", os.path.join(BASE_DIR, "snapshots"))

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload_config():
    """
    Accept a YAML file upload, parse it, and return the config as JSON.
    The frontend stores the parsed config in memory and sends it with
    subsequent /api/run requests.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file in request"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".yaml", ".yml"):
        return jsonify({"error": "File must have a .yaml or .yml extension"}), 400

    try:
        content = file.read().decode("utf-8")
        config = yaml.safe_load(content)
    except UnicodeDecodeError:
        return jsonify({"error": "File is not valid UTF-8 text"}), 400
    except yaml.YAMLError as exc:
        return jsonify({"error": f"YAML parse error: {exc}"}), 400

    if not isinstance(config, dict):
        return jsonify({"error": "YAML root must be a mapping (dict)"}), 400

    config.setdefault("inventory", [])
    config.setdefault("tests", [])

    return jsonify(config)


@app.route("/api/snapshots", methods=["GET"])
def get_snapshots():
    result = {}
    for mode in ("pre", "post"):
        path = os.path.join(SNAPSHOTS_DIR, f"{mode}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            result[mode] = {"exists": True, "timestamp": data.get("timestamp")}
        else:
            result[mode] = {"exists": False, "timestamp": None}
    return jsonify(result)


@app.route("/api/snapshots/<mode>", methods=["DELETE"])
def delete_snapshot(mode):
    if mode not in ("pre", "post"):
        return jsonify({"error": "Invalid mode"}), 400
    path = os.path.join(SNAPSHOTS_DIR, f"{mode}.json")
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"status": "deleted"})
    return jsonify({"status": "not_found"})


@app.route("/api/run", methods=["POST"])
def run_tests():
    """
    Stream test execution results as Server-Sent Events.

    Expected body:
      { "mode": "pre"|"post"|"immediate", "config": { inventory: [...], tests: [...] } }

    The config is provided entirely by the frontend (from the uploaded YAML);
    the backend does not read any config from disk.
    """
    body = request.json or {}
    mode = body.get("mode", "immediate")
    if mode not in ("pre", "post", "immediate"):
        return jsonify({"error": "Invalid mode"}), 400

    config = body.get("config")
    if not config:
        return jsonify({"error": "No config provided — upload a YAML file first"}), 400

    enabled_tests = [t for t in config.get("tests", []) if t.get("enabled", False)]
    devices = config.get("inventory", [])

    # Split tests by type: ping tests run from the host; everything else runs on devices
    ping_tests = [t for t in enabled_tests if t.get("type") == "ping"]
    command_tests = [t for t in enabled_tests if t.get("type") != "ping"]

    def generate():
        from network_handler import run_device_tests
        from ping_handler import ping_host

        results = {}

        if not enabled_tests:
            yield _sse({"type": "error", "message": "No tests are enabled"})
            return

        if command_tests and not devices:
            yield _sse({"type": "error", "message": "No devices in inventory for command tests"})
            return

        yield _sse({
            "type": "start",
            "total_devices": len(devices),
            "total_ping_tests": len(ping_tests),
            "total_command_tests": len(command_tests),
        })

        # ── Host ping tests ──────────────────────────────────────────────────
        if ping_tests:
            yield _sse({"type": "ping_section"})
            results["HOST"] = {}

            for test in ping_tests:
                test_name = test.get("name", "Ping Test")
                destinations = test.get("destinations") or []
                count = int(test.get("count", 4))

                yield _sse({
                    "type": "ping_test_start",
                    "test": test_name,
                    "destinations": destinations,
                    "count": count,
                })

                for dest in destinations:
                    output, success = ping_host(dest, count=count)
                    # Store under "test_name — destination" so diffs are per-destination
                    snapshot_key = f"{test_name} \u2014 {dest}"
                    results["HOST"][snapshot_key] = output
                    yield _sse({
                        "type": "ping_result",
                        "test": test_name,
                        "destination": dest,
                        "output": output,
                        "success": success,
                    })

        # ── Device command tests ─────────────────────────────────────────────
        if command_tests and devices:
            if ping_tests:
                yield _sse({"type": "device_section"})

            for device in devices:
                device_name = device.get("name", "Unknown")
                results[device_name] = {}
                yield _sse({"type": "device_start", "device": device_name, "host": device_name})

                try:
                    for test_name, command, output in run_device_tests(device, command_tests):
                        results[device_name][test_name] = output
                        yield _sse({
                            "type": "test_result",
                            "device": device_name,
                            "test": test_name,
                            "command": command,
                            "output": output,
                        })
                except Exception as exc:
                    error_msg = str(exc)
                    results[device_name]["__error__"] = error_msg
                    yield _sse({"type": "device_error", "device": device_name, "message": error_msg})

                yield _sse({"type": "device_complete", "device": device_name})

        if mode in ("pre", "post"):
            snapshot_path = os.path.join(SNAPSHOTS_DIR, f"{mode}.json")
            with open(snapshot_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {"timestamp": datetime.datetime.now().isoformat(), "results": results},
                    fh,
                    indent=2,
                )

        yield _sse({"type": "complete", "mode": mode, "saved": mode in ("pre", "post")})

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/diff", methods=["GET"])
def get_diff():
    pre_path = os.path.join(SNAPSHOTS_DIR, "pre.json")
    post_path = os.path.join(SNAPSHOTS_DIR, "post.json")

    missing = [m for m in ("pre", "post") if not os.path.exists(os.path.join(SNAPSHOTS_DIR, f"{m}.json"))]
    if missing:
        return jsonify({"error": f"Missing snapshots: {', '.join(missing)}"}), 404

    with open(pre_path, encoding="utf-8") as fh:
        pre = json.load(fh)
    with open(post_path, encoding="utf-8") as fh:
        post = json.load(fh)

    diffs = []
    all_devices = sorted(set(pre["results"]) | set(post["results"]))

    for device in all_devices:
        pre_device = pre["results"].get(device, {})
        post_device = post["results"].get(device, {})
        all_tests = sorted(
            t for t in (set(pre_device) | set(post_device)) if not t.startswith("__")
        )

        for test in all_tests:
            pre_out = pre_device.get(test, "")
            post_out = post_device.get(test, "")
            diff_lines = list(
                difflib.unified_diff(
                    pre_out.splitlines(keepends=True),
                    post_out.splitlines(keepends=True),
                    fromfile=f"{device}/{test} (pre)",
                    tofile=f"{device}/{test} (post)",
                )
            )
            diffs.append({
                "device": device,
                "test": test,
                "pre": pre_out,
                "post": post_out,
                "diff": "".join(diff_lines),
                "changed": bool(diff_lines),
            })

    return jsonify({
        "pre_timestamp": pre["timestamp"],
        "post_timestamp": post["timestamp"],
        "diffs": diffs,
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
