p = '/root/ml-projects/stock-prediction/backend/app/services/auth_service.py'
with open(p) as f:
    c = f.read()

# Find and fix login response (line 125 area)
old = "\"firm_name\": u['firm_name']}}"
new = "\"firm_name\": u['firm_name'], \"is_admin\": u['is_admin']}}"

if old in c:
    c = c.replace(old, new)
    with open(p, 'w') as f:
        f.write(c)
    print("FIXED! is_admin added to login response")
else:
    print("Pattern not found. Showing all lines with firm_name + user:")
    for i, line in enumerate(c.split('\n'), 1):
        if 'firm_name' in line and 'user' in line:
            print(f"Line {i}: {line.strip()}")
