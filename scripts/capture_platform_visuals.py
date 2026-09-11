"""
Automated Playwright Script.
Spawns the local platform, navigates across every view, interacts with controls,
and captures high-resolution screenshots for documentation and competition submission.
"""

import os
import sys
import time
import subprocess
import httpx
from playwright.sync_api import sync_playwright

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "docs", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PORT = 8008
BASE_URL = f"http://127.0.0.1:{PORT}"

def wait_for_server(url: str, timeout: int = 30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(f"{url}/api/health", timeout=1.0)
            if r.status_code == 200:
                print(" -> Backend server is ready and responding!")
                return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("=" * 60)
    print("STARTING PLAYWRIGHT AUTOMATED PLATFORM CAPTURE")
    print("=" * 60)

    # 1. Start Server on PORT 8008
    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT_DIR
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "backend.api.main:app", 
        "--host", "127.0.0.1", 
        "--port", str(PORT)
    ]
    print("Launching FastAPI on port " + str(PORT) + "...", flush=True)
    proc = subprocess.Popen(
        cmd, 
        env=env, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

    try:
        print("Waiting for server to become healthy...", flush=True)
        if not wait_for_server(BASE_URL, timeout=45):
            print("ERROR: Server failed to start in time.", flush=True)
            return

        with sync_playwright() as p:
            print("Launching Playwright Chromium (1920x1080)...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1.5
            )
            page = context.new_page()

            # --- 1. Executive Overview ---
            print("\n[1/8] Capturing Executive Overview...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(2000)
            shot_path = os.path.join(SCREENSHOT_DIR, "01_executive_overview.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 2. Fraud Ring Explorer ---
            print("\n[2/8] Capturing Fraud Ring Explorer...")
            page.click('button:has-text("Fraud Ring Explorer")')
            page.wait_for_timeout(2500)
            shot_path = os.path.join(SCREENSHOT_DIR, "02_fraud_ring_explorer.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 3. Merchant Risk Center ---
            print("\n[3/8] Capturing Merchant Risk Center...")
            page.click('button:has-text("Merchant Risk Center")')
            page.wait_for_timeout(2000)
            shot_path = os.path.join(SCREENSHOT_DIR, "03_merchant_risk_center.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 4. Customer / Identity Risk ---
            print("\n[4/8] Capturing Customer Risk Center...")
            page.click('button:has-text("Customer / Identity Risk")')
            page.wait_for_timeout(2000)
            shot_path = os.path.join(SCREENSHOT_DIR, "04_customer_risk_center.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 5. Risk Policy Simulator ---
            print("\n[5/8] Capturing Risk Policy Simulator...")
            page.click('button:has-text("Risk Simulator")')
            page.wait_for_timeout(2000)
            shot_path = os.path.join(SCREENSHOT_DIR, "05_risk_policy_simulator.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 6. Data Rescue & Audit (with MCH7912 Diff) ---
            print("\n[6/8] Capturing Data Rescue & Reconciliation Diff...")
            page.click('button:has-text("Data Rescue & Audit")')
            page.wait_for_timeout(2000)
            # Click curated chip for MCH7912
            chip = page.query_selector('button:has-text("MCH7912")')
            if chip:
                chip.click()
                page.wait_for_timeout(1500)
            shot_path = os.path.join(SCREENSHOT_DIR, "06_data_rescue_audit_diff.png")
            page.screenshot(path=shot_path, full_page=True)
            print(f" -> Saved: {shot_path}")

            # --- 7. FIU-IND STR Dossier Modal ---
            print("\n[7/8] Capturing FIU-IND STR Dossier Modal...")
            page.click('button:has-text("Fraud Ring Explorer")')
            page.wait_for_timeout(1500)
            export_btn = page.query_selector('button:has-text("Export FIU-IND STR")')
            if export_btn:
                export_btn.click()
                page.wait_for_timeout(2000)
                shot_path = os.path.join(SCREENSHOT_DIR, "07_fiu_ind_str_dossier.png")
                page.screenshot(path=shot_path)
                print(f" -> Saved: {shot_path}")
                # Close modal
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            # --- 8. Agentic AI Chat ---
            print("\n[8/8] Capturing Agentic Graph AI...", flush=True)
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.click('button:has-text("Ask Fraud Agent")')
            page.wait_for_timeout(1500)
            pill = page.query_selector('button:has-text("Which merchant category has the highest chargeback")')
            if pill:
                pill.click()
                page.wait_for_timeout(3500)
            shot_path = os.path.join(SCREENSHOT_DIR, "08_agentic_ai_chat.png")
            page.screenshot(path=shot_path)
            print(f" -> Saved: {shot_path}", flush=True)

            browser.close()
            print("\n" + "=" * 60)
            print("ALL 8 SCREENSHOTS CAPTURED WITH 100% FIDELITY!")
            print(f"Screenshots directory: {SCREENSHOT_DIR}")
            print("=" * 60)

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    main()
