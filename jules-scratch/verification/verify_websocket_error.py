from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the widget page
        page.goto("http://localhost:8000/widget.html", wait_until="networkidle")

        # Check for the initial connecting state
        state_locator = page.locator("#state")
        expect(state_locator).to_have_text("Bağlanılıyor...", timeout=5000)

        # Now, wait for the WebSocket to connect, receive the error, and update the UI.
        expect(state_locator).to_have_text(
            "Server is not configured. Contact site owner.",
            timeout=10000
        )

        # Take a screenshot to verify the final, correct error state
        page.screenshot(path="jules-scratch/verification/websocket_error_screenshot.png")

        browser.close()

if __name__ == "__main__":
    run_verification()