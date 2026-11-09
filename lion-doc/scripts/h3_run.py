import json, sys, time, urllib.request, urllib.error, os

SERVER = "http://127.0.0.1:6006"
UNET = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
VVAE = "minimax_h3_video_vae_int8_convrot.safetensors"
AVAE = "minimax_h3_audio_vae_fp32.safetensors"
LORA = "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"


def build(image_name, prompt, width, height, seconds, seed, prefix):
    frames = max(5, round(seconds * 24))
    while frames % 17 != 5:
        frames += 1
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": LORA, "strength_model": 1.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "minimax", "device": "default"}},
        "5": {"class_type": "VAELoader", "inputs": {"vae_name": VVAE}},
        "6": {"class_type": "VAELoader", "inputs": {"vae_name": AVAE}},
        "7": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["4", 0], "vae": ["5", 0], "prompt": prompt,
            "width": width, "height": height, "length": frames, "first_frame": ["1", 0]}},
        "8": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "10": {"class_type": "BasicScheduler", "inputs": {"model": ["3", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
        "11": {"class_type": "BasicGuider", "inputs": {"model": ["3", 0], "conditioning": ["7", 0]}},
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["8", 0], "guider": ["11", 0], "sampler": ["9", 0],
            "sigmas": ["10", 0], "latent_image": ["7", 1]}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["5", 0]}},
        "14": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["12", 0], "vae": ["6", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "fps": 24.0, "audio": ["14", 0]}},
        "16": {"class_type": "SaveVideo", "inputs": {"video": ["15", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    }


def post(wf):
    data = json.dumps({"prompt": wf, "client_id": "lion"}).encode()
    req = urllib.request.Request(SERVER + "/prompt", data=data, headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        print("HTTP", e.code, body[:3000])
        raise


def wait(pid, timeout=7200):
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout:
        try:
            h = json.load(urllib.request.urlopen(f"{SERVER}/history/{pid}", timeout=30))
        except Exception as e:
            h = {}
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("completed") or st.get("status_str") == "success":
                return h[pid]
            if st.get("status_str") == "error":
                print(json.dumps(st, ensure_ascii=False)[:4000])
                return h[pid]
        try:
            q = json.load(urllib.request.urlopen(f"{SERVER}/queue", timeout=30))
            running = q.get("queue_running", [])
            msg = f"queue={len(q.get('queue_pending', []))} running={len(running)} {int(time.time()-t0)}s"
        except Exception:
            msg = f"{int(time.time()-t0)}s"
        if msg != last:
            print(msg, flush=True)
            last = msg
        time.sleep(5)
    raise TimeoutError(pid)


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    wf = build(**cfg)
    r = post(wf)
    pid = r["prompt_id"]
    print("PROMPT_ID", pid, flush=True)
    res = wait(pid)
    out = res.get("outputs", {})
    print("OUTPUTS", json.dumps(out, ensure_ascii=False)[:2000])
