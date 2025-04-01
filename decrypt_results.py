import os

# Caesar-style decryption
def simple_decrypt(text, shift=3):
	result = ""
	for char in text:
		result += chr((ord(char) - shift) % 256)
	return result

def main():
	print("📄 Decrypted results from all *.enc files:\n")

	# List all encrypted files in the current directory
	enc_files = [f for f in os.listdir() if f.endswith(".enc")]

	if not enc_files:
		print("⚠️ No .enc files found in this folder.")
		return

	for filename in enc_files:
		print(f"\n📁 File: {filename}")
		print("-" * (len(filename) + 8))

		try:
			with open(filename, "r") as f:
				lines = f.readlines()
				if not lines:
					print("⚠️ This file is empty.")
					continue

				for line in lines:
					decrypted = simple_decrypt(line.strip())
					print(f"➡️ {decrypted}")

		except Exception as e:
			print(f"❌ Error reading {filename}: {e}")

	print("\n✅ All results loaded successfully.")

if __name__ == "__main__":
	main()
