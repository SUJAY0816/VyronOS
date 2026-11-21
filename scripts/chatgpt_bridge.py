#!/usr/bin/env python3
"""
==============================================================================
VYRON OS — ChatGPT Two-Agent Collaboration Bridge
Connects Antigravity (Execution Agent) with ChatGPT (Architecture/Review Agent).

Supports two modes:
1. Direct DOM Automation (via Chrome AppleScript JavaScript) if enabled in Chrome.
2. macOS Clipboard Sync Bridge (pbcopy / pbpaste) if Chrome JS is not enabled.
==============================================================================
"""

import sys
import os
import time
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
REQUEST_FILE = os.path.join(DOCS_DIR, "CHATGPT_REVIEW_REQUEST.md")
RESPONSE_FILE = os.path.join(DOCS_DIR, "CHATGPT_REVIEW_RESPONSE.md")

def check_chrome_js_enabled():
    sc = '''
    tell application "Google Chrome"
        set cTab to active tab of front window
        execute cTab javascript "document.title"
    end tell
    '''
    res = subprocess.run(["osascript", "-e", sc], capture_output=True, text=True)
    return res.returncode == 0

def copy_to_clipboard(text):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
    p.communicate(input=text)

def get_from_clipboard():
    res = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return res.stdout

def send_via_chrome_js(message_text):
    # Escape for JavaScript string literal
    import json
    js_msg = json.dumps(message_text)
    
    inject_script = f'''
    tell application "Google Chrome"
        set cTab to active tab of front window
        execute cTab javascript "
            (function() {{
                const input = document.querySelector('#prompt-textarea') || document.querySelector('div[contenteditable=\\"true\\"]');
                if (!input) return 'ERR_NO_INPUT';
                
                if (input.tagName === 'TEXTAREA') {{
                    input.value = {js_msg};
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }} else {{
                    input.focus();
                    document.execCommand('selectAll', false, null);
                    document.execCommand('insertText', false, {js_msg});
                }}
                
                setTimeout(() => {{
                    const btn = document.querySelector('button[data-testid=\\"send-button\\"]') || document.querySelector('button[aria-label=\\"Send prompt\\"]');
                    if (btn) btn.click();
                }}, 300);
                
                return 'OK_SENT';
            }})();
        "
    end tell
    '''
    res = subprocess.run(["osascript", "-e", inject_script], capture_output=True, text=True)
    return res.stdout.strip()

def read_latest_assistant_response():
    read_script = '''
    tell application "Google Chrome"
        set cTab to active tab of front window
        execute cTab javascript "
            (function() {
                const msgs = document.querySelectorAll('[data-message-author-role=\\"assistant\\"], article .markdown');
                if (msgs.length === 0) return 'ERR_NO_MESSAGES';
                const latest = msgs[msgs.length - 1];
                return latest.innerText;
            })();
        "
    end tell
    '''
    res = subprocess.run(["osascript", "-e", read_script], capture_output=True, text=True)
    return res.stdout.strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 chatgpt_bridge.py [status|send|read|sync]")
        sys.exit(1)

    action = sys.argv[1].lower()
    js_enabled = check_chrome_js_enabled()

    if action == "status":
        print("==========================================================================")
        print("  CHATGPT COLLABORATION BRIDGE STATUS")
        print("==========================================================================")
        print(f"  Chrome JavaScript from Apple Events: {'ENABLED (Direct DOM Mode)' if js_enabled else 'DISABLED (Clipboard Mode)'}")
        print(f"  Request Document Path : {REQUEST_FILE}")
        print(f"  Response Document Path: {RESPONSE_FILE}")
        print("==========================================================================")
        sys.exit(0)

    elif action == "send":
        if not os.path.exists(REQUEST_FILE):
            print(f"ERROR: {REQUEST_FILE} does not exist.")
            sys.exit(1)

        with open(REQUEST_FILE, "r") as f:
            content = f.read()

        copy_to_clipboard(content)
        print(f">>> Review request copied to macOS clipboard ({len(content)} characters).")

        if js_enabled:
            print(">>> Sending directly into ChatGPT browser tab...")
            res = send_via_chrome_js(content)
            print(f">>> Result: {res}")
        else:
            print(">>> [Notice] Direct Chrome JS is disabled.")
            print(">>> Content is currently copied to your macOS clipboard!")
            print(">>> Simply click into the ChatGPT window on the right and press Cmd + V, then Enter.")

    elif action == "read":
        if js_enabled:
            print(">>> Reading latest response directly from ChatGPT DOM...")
            ans = read_latest_assistant_response()
            with open(RESPONSE_FILE, "w") as f:
                f.write(ans)
            print(f">>> Response written to {RESPONSE_FILE}")
            print(ans[:500] + "..." if len(ans) > 500 else ans)
        else:
            print(">>> Direct DOM read unavailable. Reading from macOS clipboard (pbpaste)...")
            ans = get_from_clipboard()
            if not ans.strip():
                print("WARNING: Clipboard is empty.")
                sys.exit(1)
            with open(RESPONSE_FILE, "w") as f:
                f.write(ans)
            print(f">>> Clipboard content saved to {RESPONSE_FILE} ({len(ans)} characters).")

    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
