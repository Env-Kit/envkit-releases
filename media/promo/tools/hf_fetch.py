#!/usr/bin/env python3
"""Poll the Higgsfield backdrop jobs and download finished clips into assets/ai/.
Uses the local MCP client at ~/.config/envkit/higgsfield/hf.py (OAuth cached there)."""
import json, os, re, subprocess, sys, urllib.request
HF = os.path.expanduser("~/.config/envkit/higgsfield/hf.py")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "ai")
JOBS = {0: ("a5358fbd-a7cb-4245-854f-56ed492c3958", "ribbons-16x9"),
        1: ("7d8a2be8-9b1e-4b28-bc51-d26458ef50c0", "circuit-16x9"),
        2: ("a421ebb1-152b-4bcc-94f9-8df2c6157a27", "monoliths-16x9"),
        3: ("965c59e0-294a-488d-8836-d09ae7d81fb0", "ribbons-9x16"),
        # v3 (tools/hf_generate_v3.py)
        4: ("8aa1b924-811b-403c-b5ee-0d4c53e3253e", "tunnel-16x9"),
        5: ("a01f6f8b-be3e-4a08-b885-dcaa2602de76", "shockwave-16x9")}
args = {"jobs": [{"index": i, "job_id": j} for i, (j, _) in JOBS.items()], "timeout_seconds": 15}
r = subprocess.run(["python3", HF, "call", "jobs_wait", json.dumps(args)], capture_output=True, text=True)
j = json.loads(r.stdout); sc = j.get("structuredContent") or {}
txt = json.dumps(sc)
print(txt[:1500] if "--raw" in sys.argv else "")
for item in sc.get("jobs", []):
    idx = item.get("index"); st = item.get("status")
    urls = re.findall(r'https://[^"\s]+\.mp4[^"\s]*', json.dumps(item))
    print(idx, JOBS[idx][1], st, urls[:1])
    dst = os.path.join(OUT, JOBS[idx][1] + ".mp4")
    if urls and not os.path.exists(dst):
        urllib.request.urlretrieve(urls[0], dst); print("  saved", dst)
