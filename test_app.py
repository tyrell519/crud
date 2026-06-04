import subprocess, time, requests, os

# Start server
proc = subprocess.Popen(
    [os.path.join("venv", "bin", "python"), "-m", "uvicorn", "main:app", "--port", "8001"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(2)
base = "http://localhost:8001"

try:
    # --- USERS ---
    print("=== CREATE USER ===")
    r = requests.post(f"{base}/users", json={"name": "Alice", "email": "alice@test.com", "phone": "123"})
    print(r.status_code, r.json())
    user_id = r.json()["id"]

    print("=== CREATE USER DUPLICATE ===")
    r = requests.post(f"{base}/users", json={"name": "Bob", "email": "alice@test.com"})
    print(r.status_code, r.json())

    print("=== GET USER ===")
    r = requests.get(f"{base}/users/{user_id}")
    print(r.status_code, r.json())

    print("=== UPDATE USER ===")
    r = requests.put(f"{base}/users/{user_id}", json={"name": "Alice Updated", "email": "alice2@test.com", "phone": "456"})
    print(r.status_code, r.json())

    print("=== LIST USERS ===")
    r = requests.get(f"{base}/users")
    print(r.status_code, r.json())

    print("=== DELETE USER ===")
    r = requests.delete(f"{base}/users/{user_id}")
    print(r.status_code, r.json())

    print("=== GET DELETED USER ===")
    r = requests.get(f"{base}/users/{user_id}")
    print(r.status_code, r.json())

    # --- PRODUCTS ---
    print("\n=== CREATE PRODUCT ===")
    r = requests.post(f"{base}/products", json={"name": "Widget", "price": 9.99, "stock": 50})
    print(r.status_code, r.json())
    product_id = r.json()["id"]

    print("=== GET PRODUCT ===")
    r = requests.get(f"{base}/products/{product_id}")
    print(r.status_code, r.json())

    print("=== UPDATE PRODUCT ===")
    r = requests.put(f"{base}/products/{product_id}", json={"name": "Super Widget", "price": 19.99, "stock": 100})
    print(r.status_code, r.json())

    print("=== LIST PRODUCTS ===")
    r = requests.get(f"{base}/products")
    print(r.status_code, r.json())

    print("=== DELETE PRODUCT ===")
    r = requests.delete(f"{base}/products/{product_id}")
    print(r.status_code, r.json())

    # --- ORDERS ---
    print("\n=== CREATE ORDER ===")
    # Need a user and product first
    requests.post(f"{base}/users", json={"name": "Bob", "email": "bob@test.com"})
    requests.post(f"{base}/products", json={"name": "Gadget", "price": 4.99, "stock": 20})
    r = requests.post(f"{base}/orders", json={"product_id": 1, "user_id": 1, "quantity": 3})
    print(r.status_code, r.json())
    order_id = r.json()["id"]

    print("=== GET ORDER ===")
    r = requests.get(f"{base}/orders/{order_id}")
    print(r.status_code, r.json())

    print("=== UPDATE ORDER ===")
    r = requests.put(f"{base}/orders/{order_id}", json={"product_id": 1, "user_id": 1, "quantity": 5})
    print(r.status_code, r.json())

    print("=== LIST ORDERS ===")
    r = requests.get(f"{base}/orders")
    print(r.status_code, r.json())

    print("=== DELETE ORDER ===")
    r = requests.delete(f"{base}/orders/{order_id}")
    print(r.status_code, r.json())

    # --- ERROR CASES ---
    print("\n=== ERROR: GET NONEXISTENT ===")
    r = requests.get(f"{base}/users/9999")
    print(r.status_code, r.json())

    print("\n=== ERROR: CREATE ORDER w/ bad product_id ===")
    r = requests.post(f"{base}/orders", json={"product_id": 9999, "user_id": 1, "quantity": 1})
    print(r.status_code, r.json())

    print("\nALL TESTS PASSED!")

except Exception as e:
    print(f"ERROR: {e}")
finally:
    proc.terminate()
    proc.wait()
    # Clean up db
    try:
        os.remove("crud.db")
    except:
        pass
