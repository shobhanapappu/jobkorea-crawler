from crawler import SiteCrawler


def on_new(posts):
    print(f"New posts found: {len(posts)}")
    for post in posts:
        print(f"ID: {post['id']}, Title: {post['title']}, Manager: {post['manager_info']}")


def on_status(message):
    print(f"Status: {message}")


try:
    crawler = SiteCrawler(on_new_callback=on_new, on_status_callback=on_status)
    crawler.join()  # Run until manually stopped (Ctrl+C)
except KeyboardInterrupt:
    crawler.stop()
    print("Crawler stopped")
except Exception as e:
    print("Error:", str(e))
