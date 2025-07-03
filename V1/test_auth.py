from auth import AuthManager

try:
    auth = AuthManager()
    driver = auth.login()
    print("Login successful, page title:", driver.title)
    auth.close()
except Exception as e:
    print("Error:", str(e))
