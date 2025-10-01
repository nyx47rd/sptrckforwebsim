from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the widget page
        page.goto("http://localhost:8000/widget.html", wait_until="networkidle")

        state_locator = page.locator("#state")

        # 1. Wait for the server to send the configuration error.
        expect(state_locator).to_have_text(
            "Server is not configured. Contact site owner.",
            timeout=15000
        )

        # 2. CRITICAL TEST: Wait for 6 seconds to ensure the client
        # does NOT try to reconnect. The state should remain as the error message.
        # The reconnect timeout is 5 seconds, so 6 seconds is a safe margin.
        page.wait_for_timeout(6000)

        # 3. Assert that the text has NOT changed to "Yeniden bağlanılıyor...".
        # This confirms the intentionalClose flag is working.
        expect(state_locator).to_have_text("Server is not configured. Contact site owner.")

        # 4. Take a screenshot to verify the final, correct, and STABLE error state.
        page.screenshot(path="jules-scratch/verification/final_fix_screenshot.png")

        browser.close()

if __name__ == "__main__":
    run_verification()