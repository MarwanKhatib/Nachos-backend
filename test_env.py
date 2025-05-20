from decouple import config

def test_env_vars():
    print("Testing environment variables:")
    print(f"EMAIL_HOST_USER: {config('EMAIL_HOST_USER', default='Not set')}")
    print(f"EMAIL_HOST_PASSWORD: {'Set' if config('EMAIL_HOST_PASSWORD', default=None) else 'Not set'}")
    print(f"REDIS_URL: {config('REDIS_URL', default='Not set')}")

if __name__ == "__main__":
    test_env_vars() 