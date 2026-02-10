import os
import json
import base64
from typing import List
import requests


def request_video_from_llm(frame_paths: List[str], intent: dict, output_path: str, timeout: int = 60) -> bool:
    """Send frames and intent to an external LLM-backed API to request a regenerated video.

    Expects environment variables:
      - LLM_API_URL: full URL to POST frames to (e.g. https://api.example.com/generate)
      - LLM_API_KEY: optional API key passed as Bearer token

    The endpoint is expected to return JSON with either `video_base64` or `video_url`,
    or the raw video bytes as the response body.
    """
    api_url = os.environ.get("LLM_API_URL")
    api_key = os.environ.get("LLM_API_KEY")

    if not api_url:
        print("[LLM CLIENT] LLM_API_URL not set; skipping LLM call")
        return False

    files = []
    opened = []
    for p in frame_paths:
        try:
            f = open(p, "rb")
            opened.append(f)
            files.append(("frames", (os.path.basename(p), f, "image/jpeg")))
        except Exception as e:
            print(f"[LLM CLIENT] Failed to open frame {p}: {e}")

    data = {"intent": json.dumps(intent)}
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(api_url, data=data, files=files, headers=headers, timeout=timeout)
    except Exception as e:
        print(f"[LLM CLIENT] Request to LLM failed: {e}")
        for f in opened:
            try:
                f.close()
            except:
                pass
        return False

    for f in opened:
        try:
            f.close()
        except:
            pass

    if resp.status_code != 200:
        print(f"[LLM CLIENT] LLM request failed: {resp.status_code} {resp.text}")
        return False

    # Try to parse JSON response first
    try:
        payload = resp.json()
    except ValueError:
        # Not JSON; treat body as raw video bytes
        try:
            with open(output_path, "wb") as out:
                out.write(resp.content)
            print("[LLM CLIENT] Saved raw binary response to output video")
            return True
        except Exception as e:
            print(f"[LLM CLIENT] Failed to write binary response: {e}")
            return False

    # JSON response handling
    if isinstance(payload, dict):
        if "video_base64" in payload:
            try:
                data_b = base64.b64decode(payload["video_base64"])
                with open(output_path, "wb") as out:
                    out.write(data_b)
                print("[LLM CLIENT] Received video (base64) from LLM")
                return True
            except Exception as e:
                print(f"[LLM CLIENT] Failed to decode/write base64 video: {e}")
                return False

        if "video_url" in payload:
            try:
                dl = requests.get(payload["video_url"], timeout=timeout)
                if dl.status_code == 200:
                    with open(output_path, "wb") as out:
                        out.write(dl.content)
                    print("[LLM CLIENT] Downloaded video from LLM URL")
                    return True
                else:
                    print(f"[LLM CLIENT] Failed to download video_url: {dl.status_code}")
            except Exception as e:
                print(f"[LLM CLIENT] Error downloading video_url: {e}")

    print("[LLM CLIENT] No usable video found in LLM response")
    return False
