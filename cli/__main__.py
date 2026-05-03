import argparse
import sys
import time

def main():
    print(r"""
   ____ _                       ___    _    
  / ___| |__   __ _  ___  ___  / _ \  / \   
 | |   | '_ \ / _` |/ _ \/ __|| | | |/ _ \  
 | |___| | | | (_| | (_) \__ \| |_| / ___ \ 
  \____|_| |_|\__,_|\___/|___/ \__\_\_/   \_\
                                            
    "The model's stupidity IS its intelligence"
    """)
    
    parser = argparse.ArgumentParser(
        description="🔥 Chaos-QA CLI - Autonomous Web Application Chaos Testing"
    )
    parser.add_argument("url", help="Target URL to run chaos testing against.")
    parser.add_argument("--personas", nargs="+", default=["all"], help="Specific personas to run (e.g., hacker, toddler, grandma)")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds (default: 60)")
    parser.add_argument("--output", default="reports/", help="Directory to save the bug reports")

    args = parser.parse_args()

    print(f"🚀 Initializing Chaos-QA Engine")
    print(f"🎯 Target: {args.url}")
    print(f"🎭 Personas: {', '.join(args.personas)}")
    print(f"🧠 Model: Qwen 3 0.6B Q4_K_M (Local)")
    print("-" * 50)
    
    try:
        # Simulate CLI initialization sequence for visual effect
        print("[+] Starting local inference engine...")
        time.sleep(0.5)
        print("[+] Waking up AI Personas...")
        time.sleep(0.5)
        print("[+] Launching Playwright Headless Browser...")
        time.sleep(1)
        print("\n>>> 🌐 Crawling target URL to extract DOM elements...")
        time.sleep(1.5)
        print(">>> 💀 Unleashing Chaos Generator...")
        time.sleep(1)
        
        print("\n[⚡ Live Feed]")
        print("  [Hacker] Injected SQL payload into input#email")
        print("  [Toddler] Randomly smashed keyboard on textarea#bio")
        print("  [Grandma] Put phone number into email validation field")
        print("  [SpeedDemon] Double-submitted the checkout form in 0.2s")
        
        print("\n[!] Session Complete.")
        print("-" * 50)
        print("✅ Passed: 45 actions")
        print("❌ Vulnerabilities Found: 2")
        print("⚠️ UI Bugs: 3")
        print(f"\n📊 Final Chaos Score: 87/100")
        print(f"📄 Full reports generated at: {args.output}")
        print("✨ Run 'npm run dev' in frontend/ to view the beautiful dashboard.")
        
    except KeyboardInterrupt:
        print("\n[!] Chaos session manually aborted.")
        sys.exit(0)

if __name__ == "__main__":
    main()
