import re

with open('/Users/supachaitaengyonram/Project01/aicashier/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function line
new_lines = []
skip_until_class = False

for i, line in enumerate(lines):
    if 'def generate_promptpay_qr' in line:
        skip_until_class = True
        # Add the corrected function
        new_lines.append('def generate_promptpay_qr(phone: str, amount: float) -> str:\n')
        new_lines.append('    """สร้าง PromptPay QR Code URL"""\n')
        new_lines.append('    phone_clean = phone.replace("-", "").replace(" ", "")\n')
        new_lines.append('    qr_url = f"https://api.promptpay.io:8443/qr/generate?phoneNumber={phone_clean}&amount={amount:.2f}"\n')
        new_lines.append('    return qr_url\n')
        new_lines.append('\n')
        new_lines.append('\n')
    elif skip_until_class and line.startswith('class '):
        skip_until_class = False
        new_lines.append(line)
    elif not skip_until_class:
        new_lines.append(line)

with open('/Users/supachaitaengyonram/Project01/aicashier/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Fixed generate_promptpay_qr function")
