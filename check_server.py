import requests
import time
import sys

def check_server():
    url = "https://nachos-backend.onrender.com/"
    max_retries = 30  # Maximum number of retries
    retry_interval = 10  # Time to wait between retries in seconds
    
    print("Checking if server is up...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200 and response.text.strip() == "Hello, world!":
                print("\n✅ Server is up and running!")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"\rAttempt {attempt + 1}/{max_retries}: Server not ready yet...", end="")
                sys.stdout.flush()
                
        except requests.exceptions.RequestException as e:
            print(f"\rAttempt {attempt + 1}/{max_retries}: Connection error - {str(e)}", end="")
            sys.stdout.flush()
        
        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            time.sleep(retry_interval)
    
    print("\n❌ Server check failed after maximum retries")
    return False

if __name__ == "__main__":
    check_server() 