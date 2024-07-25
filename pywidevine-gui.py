import tkinter as tk
from tkinter import messagebox, scrolledtext
from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
import requests
import os

# Function to save headers to header.py
def save_headers_to_file(headers):
    with open('headers.py', 'w') as f:
        f.write('headers = {\n')
        for key, value in headers.items():
            f.write(f"    '{key}': '{value}',\n")
        f.write('}\n')

# Function to handle the Widevine licensing logic
def handle_license_flow(pssh_value, lic_url_value, headers_value, output_text):
    try:
        # Prepare PSSH
        pssh = PSSH(pssh_value)

        # Load device
        device = Device.load(r"PATH_TO_WVD_FILE")

        # Load CDM
        cdm = Cdm.from_device(device)

        # Open CDM session
        session_id = cdm.open()

        # Get license challenge
        challenge = cdm.get_license_challenge(session_id, pssh)

        # Send license challenge
        headers = {}
        if headers_value.strip():
            headers = eval(headers_value)
        license_response = requests.post(lic_url_value, headers=headers, data=challenge)
        license_response.raise_for_status()

        # Parse license challenge
        cdm.parse_license(session_id, license_response.content)

        # Prepare keys information
        keys_info = []
        for key in cdm.get_keys(session_id):
            if key.type == 'CONTENT':
                keys_info.append(f"\n--key {key.kid.hex}:{key.key.hex()}")

        # Close session
        cdm.close(session_id)

        # Display keys information in the output box
        keys_output = ''.join(keys_info)
        output_text.config(state=tk.NORMAL)
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, keys_output)
        output_text.config(state=tk.DISABLED)

        # Automatically generate headers if not provided and save them
        if not headers_value.strip():
            headers = license_response.headers

        # Save headers to headers.py
        save_headers_to_file(headers)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Function to handle button click event
def on_submit():
    pssh_value = pssh_entry.get()
    lic_url_value = lic_url_entry.get()
    headers_value = headers_entry.get("1.0", tk.END).strip()

    handle_license_flow(pssh_value, lic_url_value, headers_value, output_text)

# Create GUI window
root = tk.Tk()
root.title("Widevine License GUI")

# PSSH input
tk.Label(root, text="PSSH:").grid(row=0, column=0)
pssh_entry = tk.Entry(root, width=50)
pssh_entry.grid(row=0, column=1, columnspan=2)

# License URL input
tk.Label(root, text="License URL:").grid(row=1, column=0)
lic_url_entry = tk.Entry(root, width=50)
lic_url_entry.grid(row=1, column=1, columnspan=2)

# Headers input
tk.Label(root, text="Headers (format: {'key': 'value'}):").grid(row=2, column=0)
headers_entry = tk.Text(root, width=50, height=4)
headers_entry.grid(row=2, column=1, columnspan=2)

# Submit button
submit_btn = tk.Button(root, text="Submit", command=on_submit)
submit_btn.grid(row=3, column=1)

# Output text box for displaying keys information
output_label = tk.Label(root, text="Keys Information:")
output_label.grid(row=4, column=0, sticky=tk.W)
output_text = scrolledtext.ScrolledText(root, width=80, height=10, wrap=tk.WORD)
output_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
output_text.config(state=tk.DISABLED)

# Run the GUI
root.mainloop()
