from playwright.sync_api import sync_playwright

def run_trigger():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to widget page to trigger WebSocket connection...")
        # We don't need to wait for long, just long enough to establish a connection
        # and for the server to log what's happening.
        try:
            page.goto("http://localhost:8000/widget.html", timeout=10000)
        except Exception as e:
            print(f"Navigation timed out, which is expected if the connection hangs. Error: {e}")

        print("Connection triggered. Check server.log for details.")
        browser.close()

if __name__ == "__main__":
    run_trigger()