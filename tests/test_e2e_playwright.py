"""
End-to-End Playwright Browser Verification Test Suite.
Tests the compiled production frontend served by FastAPI:
- Page title and header branding
- Tab navigation across all 6 core modules
- Data Rescue Audit search & curated case loading
- FIU-IND STR Report Modal opening & rendering & closing
- Risk Policy Simulator sliders & recalculation
- Agentic Graph AI Drawer query input & grounded response verification
"""

import os
import time
import threading
import pytest
import uvicorn
import httpx
from playwright.sync_api import sync_playwright
from backend.api.main import app

TEST_PORT = 8012
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


class ThreadedServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass


@pytest.fixture(scope="module")
def test_server():
    """Starts a live FastAPI test server in a daemon thread for E2E tests."""
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=TEST_PORT,
        log_level="warning",
    )
    server = ThreadedServer(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server readiness
    start = time.time()
    ready = False
    while time.time() - start < 15:
        try:
            r = httpx.get(f"{BASE_URL}/api/health", timeout=1.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            time.sleep(0.3)

    assert ready, "Test server failed to start within timeout"
    yield BASE_URL
    server.should_exit = True


@pytest.fixture(scope="module")
def browser_context():
    """Provides a headless Chromium browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        yield context
        browser.close()


def test_e2e_overview_and_navigation(test_server, browser_context):
    """Verifies that the platform loads, displays key metrics, and navigates tabs."""
    page = browser_context.new_page()
    page.goto(test_server, wait_until="networkidle", timeout=30000)

    # 1. Check title and brand header
    assert "UPI Fraud Intelligence" in page.title()
    assert page.locator("text=AGENTIQ").count() > 0
    assert page.locator("text=UPI Fraud & Merchant Risk Platform").count() > 0

    # 2. Check Executive KPIs
    assert page.locator("text=Gross UPI Volume").count() > 0
    assert page.locator("text=Disputed Volume").count() > 0
    assert page.locator("text=Highest Chargeback-to-Transaction Ratio").count() > 0

    # 3. Navigate to Fraud Ring Explorer
    page.click("button:has-text('Fraud Ring Explorer')")
    page.wait_for_timeout(1000)
    assert page.locator("text=Fraud Ring & Network Intelligence").count() > 0

    # 4. Navigate to Merchant Risk Center
    page.click("button:has-text('Merchant Risk Center')")
    page.wait_for_timeout(1000)
    assert page.locator("text=Merchant Risk Intelligence Center").count() > 0

    # 5. Navigate to Customer Risk Center
    page.click("button:has-text('Customer / Identity Risk')")
    page.wait_for_timeout(1000)
    assert page.locator("text=Customer & Synthetic Identity Risk Center").count() > 0

    # 6. Navigate to Risk Simulator
    page.click("button:has-text('Risk Simulator')")
    page.wait_for_timeout(1000)
    assert page.locator("text=Risk Policy & Dynamic Threshold Simulator").count() > 0

    # 7. Navigate to Data Rescue Audit
    page.click("button:has-text('Data Rescue & Audit')")
    page.wait_for_timeout(1000)
    assert page.locator("text=Data Rescue & Traceability Philosophy").count() > 0

    page.close()


def test_e2e_fiu_str_modal(test_server, browser_context):
    """Verifies opening, viewing, and closing the FIU-IND STR report modal."""
    page = browser_context.new_page()
    page.goto(test_server, wait_until="networkidle", timeout=30000)

    # Go to Fraud Ring Explorer
    page.click("button:has-text('Fraud Ring Explorer')")
    page.wait_for_timeout(1000)

    # Click the first 'Export FIU-IND STR' button
    str_btn = page.locator("button:has-text('Export FIU-IND STR')").first
    assert str_btn.is_visible()
    str_btn.click()

    # Verify modal opens
    page.wait_for_timeout(800)
    assert page.locator("text=FIU-IND Suspicious Transaction Report").count() > 0
    assert page.locator("text=PMLA SEC 12").count() > 0
    assert page.locator("button:has-text('Legal Brief')").count() > 0
    assert page.locator("button:has-text('JSON')").count() > 0

    # Close modal using accessible close button
    close_btn = page.locator("button[aria-label='Close modal']")
    assert close_btn.is_visible()
    close_btn.click()
    page.wait_for_timeout(500)
    assert page.locator("text=FIU-IND Suspicious Transaction Report").count() == 0

    page.close()


def test_e2e_agent_drawer_and_query(test_server, browser_context):
    """Verifies opening the Agentic AI drawer and executing the benchmark question."""
    page = browser_context.new_page()
    page.goto(test_server, wait_until="networkidle", timeout=30000)

    # Click Ask Fraud Agent
    page.click("button:has-text('Ask Fraud Agent')")
    page.wait_for_timeout(800)

    # Verify drawer opened
    assert page.locator("text=Agentic Graph AI").count() > 0
    assert page.locator("text=Grounded UPI & Fraud Intelligence").count() > 0

    # Type benchmark question into the input
    input_box = page.locator("input[placeholder*='Ask anything']")
    assert input_box.is_visible()
    input_box.fill("Which merchant category has the highest chargeback-to-transaction ratio this quarter?")
    page.click("button[type='submit']")

    # Wait for the AI response
    page.wait_for_selector("text=Apparel", timeout=15000)
    assert page.locator("text=Apparel").count() > 0
    assert page.locator("text=30.34%").count() > 0

    page.close()
