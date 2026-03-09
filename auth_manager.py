import requests
from config import AUTH_URL, EMAIL


def get_access_token():
    try:
        req = requests.post(f"{AUTH_URL}/auth/code/request",
                            json={"email": EMAIL, "type": "login"})
        temp_token = req.json().get("token")

        print("\n" + "=" * 30)
        otp = input("ENTER OTP FROM DOME DEVICE: ").strip()
        print("=" * 30)

        verify = requests.post(f"{AUTH_URL}/auth/code/verify",
                               json={"code": otp, "type": "login"},
                               headers={"Authorization": f"Bearer {temp_token}"})

        if verify.status_code == 200:
            return verify.json().get("token")
        else:
            print(f"Auth Failed: {verify.text}")
            return None
    except Exception as e:
        print(f"Auth Error: {e}")
        return None