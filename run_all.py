# run_all.py
import subprocess

def run_script(script_name):
    print(f"\n🚀 Running {script_name}...\n")
    result = subprocess.run(["python3", script_name], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {script_name} finished successfully.\n")
        print(result.stdout)
    else:
        print(f"❌ {script_name} failed!\n")
        print(result.stderr)

if __name__ == "__main__":
    # Step 1: Fetch new orders into master sheet
    run_script("multi_master_updater.py")

    # Step 2: Distribute orders to agents
    run_script("order_distributor.py")

    # Step 3: Send orders to WhatsApp
    run_script("whatsapp_sender.py")

    print("\n🎉 All steps completed!\n")
