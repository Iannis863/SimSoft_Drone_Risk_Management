import requests

# Config from YAML
BASE_URL = "https://authentication.stg.flux.aero"
EMAIL = "hackathon3@flux.aero"


def get_flux_access():
    # --- STEP 1: Request Temporary Token ---
    req_url = f"{BASE_URL}/auth/code/request"

    try:
        # Step 1 definitely needs type: login
        req_resp = requests.post(
            req_url,
            json={"email": EMAIL, "type": "login"},
            headers={"Accept": "application/json"}
        )
        req_resp.raise_for_status()
        temp_token = req_resp.json().get("token")
        print("✅ Step 1: Temporary token received.")
    except Exception as e:
        print(f"❌ Step 1 Failed: {e}")
        return None

    # --- STEP 2: Input OTP from Argonian Dome ---
    print("\n" + "=" * 40)
    otp_code = input("ENTER 6-DIGIT CODE FROM DEVICE: ").strip()
    print("=" * 40 + "\n")

    # --- STEP 3: Verify and get Permanent Token ---
    verify_url = f"{BASE_URL}/auth/code/verify"
    verify_headers = {
        "Authorization": f"Bearer {temp_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # ADDED "type": "login" here to satisfy the validation error you received
    verify_body = {
        "code": otp_code,
        "type": "login"
    }

    try:
        verify_resp = requests.post(verify_url, json=verify_body, headers=verify_headers)

        if verify_resp.status_code == 200:
            # Based on YAML, the key might be 'token' or 'accessToken'
            data = verify_resp.json()
            access_token = data.get("token") or data.get("accessToken")
            print("🎉 SUCCESS! You are now authenticated.")
            return access_token
        else:
            print(f"❌ Step 2 Failed ({verify_resp.status_code}): {verify_resp.text}")
            return None

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None


if __name__ == "__main__":
    final_token = get_flux_access()
    if final_token:
        print(f"\nYour Permanent Access Token:\n{final_token}")