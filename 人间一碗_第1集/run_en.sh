#!/bin/bash
cd /root/autodl-tmp
for i in 0 1 2; do
  /root/autodl-fs/venv/bin/python - "$i" <<'PY'
import json, sys
i = int(sys.argv[1])
d = json.load(open("/root/autodl-tmp/batch_nt2.json"))[i]
json.dump(d, open("/root/autodl-tmp/en_tmp.json", "w"), ensure_ascii=False)
PY
  echo "=== START $i $(date +%H:%M:%S) ==="
  /root/autodl-fs/venv/bin/python /root/autodl-tmp/h3_run.py /root/autodl-tmp/en_tmp.json > /root/autodl-tmp/en_$i.log 2>&1
  tail -2 /root/autodl-tmp/en_$i.log
done
echo ALL_EN_DONE
