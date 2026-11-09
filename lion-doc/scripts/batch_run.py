import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
shots = json.load(open(os.path.join(HERE, "batch.json")))

for cfg in shots:
    name = cfg["prefix"].split("/")[-1]
    log = f"/root/autodl-tmp/{name}.log"
    print(f"=== START {name} {time.strftime('%H:%M:%S')} ===", flush=True)
    cfg_path = f"/root/autodl-tmp/{name}.json"
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, ensure_ascii=False)
    t0 = time.time()
    r = subprocess.run(
        ["/root/autodl-fs/venv/bin/python", "/root/autodl-tmp/h3_run.py", cfg_path],
        capture_output=True, text=True)
    with open(log, "w") as f:
        f.write(r.stdout + "\n" + r.stderr)
    dt = int(time.time() - t0)
    ok = "OUTPUTS" in r.stdout
    print(f"=== DONE {name} ok={ok} {dt}s ===", flush=True)
    if not ok:
        print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
print("ALL DONE", flush=True)
