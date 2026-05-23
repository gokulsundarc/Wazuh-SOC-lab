#!/bin/bash

echo "$(date) - Script called" >> /tmp/telegram-debug.log
echo "$(date) - Lockfile check passed" >> /tmp/telegram-debug.log
BOT_TOKEN="YOUR_TOKEN"
CHAT_ID="YOUR_CHAT_ID"
LOCKDIR="/tmp/wazuh_telegram_locks"

# Create lock directory if not exists
mkdir -p "$LOCKDIR"

# Read alert from Wazuh
read -r INPUT

# Extract rule ID and source IP
RULE_ID=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['parameters']['alert']['rule']['id'])
" 2>/dev/null)

SRC_IP=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['parameters']['alert'].get('data', {}).get('srcip', 'unknown'))
" 2>/dev/null)

# Create unique lock per rule + IP combination
LOCKFILE="$LOCKDIR/${RULE_ID}_${SRC_IP//[:.]/_}.lock"

# Check if this exact alert was already sent
if [ -f "$LOCKFILE" ]; then
    LAST=$(cat "$LOCKFILE")
    NOW=$(date +%s)
    DIFF=$((NOW - LAST))
    # Only block if same rule+IP fired within last 10 minutes
    if [ "$DIFF" -lt 600 ]; then
        exit 0
    fi
fi

# Update lockfile timestamp
date +%s > "$LOCKFILE"

# Extract full alert details
ALERT=$(echo "$INPUT" | python3 -c "
import sys, json

data = json.load(sys.stdin)
rule_id = data['parameters']['alert']['rule']['id']
rule_desc = data['parameters']['alert']['rule']['description']
rule_level = data['parameters']['alert']['rule']['level']
agent = data['parameters']['alert']['agent']['name']
timestamp = data['parameters']['alert']['timestamp']
srcip = data['parameters']['alert'].get('data', {}).get('srcip', 'Unknown')

# Choose emoji based on rule
if rule_id in ['100006', '11451']:
    attack_type = '🔑 Brute Force Attack'
elif rule_id == '100021':
    attack_type = '🌐 Web Attack'
else:
    attack_type = '⚠️ Security Alert'

print(f'''{attack_type} Detected!
━━━━━━━━━━━━━━━━━━━━
🔴 Rule ID: {rule_id}
⚠️ Severity Level: {rule_level}
📋 Description: {rule_desc}
🖥️ Agent: {agent}
🌐 Attacker IP: {srcip}
🕐 Time: {timestamp}
━━━━━━━━━━━━━━━━━━━━
🛡️ IP has been auto-blocked!
⏱️ Block duration: 5 minutes''')
" 2>/dev/null)

# Send to Telegram
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=${ALERT}" \
  -d "parse_mode=HTML" > /dev/null 2>&1

echo "$(date) - Message sent" >> /tmp/telegram-debug.log
exit 0
