#!/usr/bin/env python3

import requests
import subprocess
import json
import time
import re

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(text, chat_id=CHAT_ID):
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

def get_status():
    try:
        result = subprocess.run(
            ["sudo", "/var/ossec/bin/agent_control", "-l"],
            capture_output=True, text=True
        )
        if "Active" in result.stdout:
            return "✅ <b>Wazuh Agent Status</b>\n━━━━━━━━━━━━━━━━\n🟢 Agent 002 (siem-server) is <b>Active</b>\n🕐 Time: " + time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "❌ <b>Wazuh Agent Status</b>\n━━━━━━━━━━━━━━━━\n🔴 Agent 002 is <b>Disconnected</b>"
    except:
        return "⚠️ Could not retrieve agent status"

def get_alerts():
    try:
        result = subprocess.run(
            ["sudo", "grep", "Rule:", "/var/ossec/logs/alerts/alerts.log"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        # Get unique last 5 alerts
        unique = list(dict.fromkeys(lines))[-5:]
        msg = "📋 <b>Last 5 Alerts</b>\n━━━━━━━━━━━━━━━━\n"
        for i, line in enumerate(unique, 1):
            # Extract rule info
            match = re.search(r"Rule: (\d+) \(level (\d+)\) -> '(.+)'", line)
            if match:
                rule_id, level, desc = match.groups()
                emoji = "🔴" if int(level) >= 10 else "🟡" if int(level) >= 5 else "🟢"
                msg += f"{i}. {emoji} Rule {rule_id} (L{level}): {desc}\n"
        return msg
    except:
        return "⚠️ Could not retrieve alerts"

def get_blocked():
    try:
        result = subprocess.run(
            ["sudo", "nft", "list", "ruleset"],
            capture_output=True, text=True
        )
        ips = re.findall(r"ip saddr ([\d.]+).*drop", result.stdout)
        if ips:
            msg = "🛡️ <b>Currently Blocked IPs</b>\n━━━━━━━━━━━━━━━━\n"
            for ip in set(ips):
                msg += f"🚫 {ip}\n"
            return msg
        else:
            return "✅ <b>No IPs currently blocked</b>\n━━━━━━━━━━━━━━━━\nFirewall is clean!"
    except:
        return "⚠️ Could not retrieve blocked IPs"

def clear_blocks():
    try:
        subprocess.run(["sudo", "nft", "flush", "ruleset"], capture_output=True)
        return "✅ <b>Firewall Cleared</b>\n━━━━━━━━━━━━━━━━\nAll IP blocks have been removed!"
    except:
        return "⚠️ Could not clear firewall rules"

def get_help():
    return """🤖 <b>Wazuh SOC Bot Commands</b>
━━━━━━━━━━━━━━━━
/status  - Check Wazuh agent status
/alerts  - Show last 5 security alerts
/blocked - Show currently blocked IPs
/clear   - Clear all firewall blocks
/help    - Show this help message
━━━━━━━━━━━━━━━━
🛡️ Powered by Wazuh SIEM"""

def handle_command(command):
    if command == "/status":
        return get_status()
    elif command == "/alerts":
        return get_alerts()
    elif command == "/blocked":
        return get_blocked()
    elif command == "/clear":
        return clear_blocks()
    elif command == "/help" or command == "/start":
        return get_help()
    else:
        return "❓ Unknown command. Send /help for available commands."

def main():
    print("🤖 Wazuh Telegram Bot started!")
    send_message("🚀 <b>Wazuh SOC Bot is Online!</b>\nSend /help to see available commands.")
    
    last_update_id = 0
    
    while True:
        try:
            # Get updates
            url = f"{API_URL}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"].strip()
                        
                        # Only respond to your chat ID
                        if str(chat_id) == str(CHAT_ID):
                            print(f"Received command: {text}")
                            response_text = handle_command(text)
                            send_message(response_text, chat_id)
                        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
