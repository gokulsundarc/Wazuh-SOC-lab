# 🛡️ SOC Lab — Threat Simulation & Detection with Wazuh SIEM

A hands-on Security Operations Center (SOC) lab where I simulated real-world cyber attacks across **three attack vectors**, built custom detection rules mapped to **MITRE ATT&CK**, configured **automated IP blocking**, and integrated a **Telegram Bot** for real-time mobile alerts and interactive SOC analyst queries.

---

## 🚀 What This Lab Does

- Simulates real attacks (port scanning, SSH/FTP brute force, HTTP attacks) using Kali Linux
- Detects them using custom Wazuh rules mapped to MITRE ATT&CK framework
- Automatically blocks the attacker IP via nftables/iptables — no manual action needed
- Sends real-time alerts to a **Telegram Bot** on your phone
- Supports interactive bot commands (`/status`, `/alerts`, `/blocked`, `/clear`)

---

## 🏗️ Lab Architecture

```
┌──────────────────────────────────────────────────────────┐
│           VirtualBox Host (Windows PC - 16GB RAM)        │
│                                                          │
│  ┌──────────────────────┐    ┌───────────────────────┐   │
│  │    Kali Linux        │    │  Ubuntu Server 24.04  │   │
│  │   (Attacker +        │◄───│   (Target Machine +   │   │
│  │    Wazuh Manager)    │    │    Wazuh Agent)       │   │
│  │                      │    │                       │   │
│  │  • Wazuh Manager     │    │  • Wazuh Agent 002    │   │
│  │  • Wazuh Dashboard   │    │  • SSH  (Port 22)     │   │
│  │  • Wazuh Indexer     │    │  • FTP  (Port 21)     │   │
│  │  • Hydra             │    │  • HTTP (Port 80)     │   │
│  │  • Nmap              │    │  • vsftpd / Apache2   │   │
│  │  • Nikto             │    │  • nftables Firewall  │   │
│  │  • Telegram Bot      │    │                       │   │
│  └──────────────────────┘    └───────────────────────┘   │
│                  Bridged Adapter Network                 │
└──────────────────────────────────────────────────────────┘
```

---

## 🔗 Agent Connection

The Wazuh Agent was registered on Ubuntu Server with **Agent ID: 002** and appears as **Active** in the Wazuh Dashboard under Endpoints. Both VMs use **Bridged Adapter** so they can communicate directly on the same network.


<img width="1366" height="702" alt="Screenshot_2026-05-19_10_01_51" src="https://github.com/user-attachments/assets/fc938643-5508-43bf-ac05-dc1ba512e6a5" />


---

## 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| **Wazuh 4.14.5** | SIEM — log analysis, threat detection, active response |
| **Kali Linux 2025.2** | Attacker machine + Wazuh Manager |
| **Ubuntu Server 24.04** | Target machine + Wazuh Agent |
| **VirtualBox 7.x** | Virtualization platform |
| **Hydra 9.6** | SSH & FTP brute force simulation |
| **Nmap** | Network reconnaissance / port scanning |
| **Nikto** | Web vulnerability scanner |
| **Python 3** | Telegram bot development |
| **nftables / iptables** | Automated IP blocking |

---

## ⚔️ Attacks Simulated

### 1. 🔍 Network Reconnaissance (Port Scan)

```bash
nmap -sS -p 1-1000 <target-ip>
```

<img width="1366" height="702" alt="Screenshot_2026-05-09_09_10_56" src="https://github.com/user-attachments/assets/5c2db3e1-e8cc-42b9-8a65-fdb076beb57a" />


**Open ports discovered:** 21 (FTP), 22 (SSH), 80 (HTTP)
**MITRE ATT&CK:** T1046 — Network Service Discovery

---

### 2. 🔐 SSH Brute Force

```bash
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://<target-ip> -t 4
```

<img width="1366" height="702" alt="Screenshot_2026-05-09_04_38_37" src="https://github.com/user-attachments/assets/816b68a3-7756-46cd-8c51-89557c1148e1" />

Generated over 64 failed login attempts per minute against the SSH service.

<img width="1366" height="702" alt="Screenshot_2026-05-09_04_44_18" src="https://github.com/user-attachments/assets/946695dc-40e3-449d-8fdc-e5ddf90532a0" />

**MITRE ATT&CK:** T1110 — Brute Force

---

### 3. 📁 FTP Brute Force

```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://<target-ip> -t 4
```

<img width="1366" height="702" alt="Screenshot_2026-05-24_01_52_13" src="https://github.com/user-attachments/assets/459169a6-915a-4ad9-b9d0-d85a82953c63" />

Hundreds of failed FTP login attempts captured from `/var/log/vsftpd.log`.

<img width="1366" height="702" alt="Screenshot_2026-05-24_02_01_06" src="https://github.com/user-attachments/assets/eaf5007a-1f8a-4e6a-9f83-9b0be639fd53" />

**MITRE ATT&CK:** T1110 — Brute Force

---

### 4. 🌐 HTTP Attack Simulation

```bash
nikto -h http://<target-ip>
curl http://<target-ip>/../../../../etc/passwd
curl http://<target-ip>/wp-admin
curl 'http://<target-ip>/?id=1'\''OR'\''1'\''='\''1'
```

<img width="1366" height="702" alt="Screenshot_2026-05-24_02_05_03" src="https://github.com/user-attachments/assets/07e5dccc-abd1-4d0e-8a5d-523dd62c8987" />

Web vulnerability scanning, directory traversal, and SQL injection attempts.

<img width="1366" height="702" alt="Screenshot_2026-05-24_02_06_22" src="https://github.com/user-attachments/assets/6e05c078-5f61-4cf5-9dd7-b2fb8bd6e126" />

**MITRE ATT&CK:** T1595, T1083, T1190

---

## 🔍 Custom Detection Rules

Stored in `/var/ossec/etc/rules/local_rules.xml` on the Wazuh Manager:

```xml
<group name="local,">

  <!-- SSH Brute Force Detection -->
  <rule id="100001" level="10" frequency="3" timeframe="120">
    <if_matched_sid>5716</if_matched_sid>
    <description>Custom: SSH Brute Force Attack Detected</description>
    <mitre><id>T1110</id></mitre>
    <group>attack,authentication_failures,</group>
  </rule>

  <!-- High Volume SSH Brute Force -->
  <rule id="100002" level="12" frequency="10" timeframe="60">
    <if_matched_sid>5716</if_matched_sid>
    <description>Custom: High Volume SSH Brute Force - Automated Attack</description>
    <mitre><id>T1110.001</id></mitre>
    <group>attack,authentication_failures,</group>
  </rule>

  <!-- Privilege Escalation -->
  <rule id="100005" level="12">
    <if_sid>5402</if_sid>
    <match>root</match>
    <description>Custom: Privilege Escalation - Sudo to ROOT Executed</description>
    <mitre><id>T1548.003</id></mitre>
    <group>attack,privilege_escalation,</group>
  </rule>

  <!-- Multiple PAM Authentication Failures -->
  <rule id="100006" level="10" frequency="6" timeframe="120">
    <if_matched_sid>5503</if_matched_sid>
    <description>Custom: Multiple PAM Authentication Failures Detected</description>
    <mitre><id>T1110</id></mitre>
    <group>attack,authentication_failures,</group>
  </rule>

  <!-- HTTP Scan Detection -->
  <rule id="100020" level="8" frequency="20" timeframe="60">
    <if_matched_sid>31101</if_matched_sid>
    <description>Custom: HTTP Scan Detected - Multiple 404 Errors</description>
    <mitre><id>T1595</id></mitre>
    <group>attack,web,recon,</group>
  </rule>

  <!-- HTTP Directory Traversal -->
  <rule id="100021" level="12">
    <if_sid>31151</if_sid>
    <description>Custom: Directory Traversal Attack Detected</description>
    <mitre><id>T1083</id></mitre>
    <group>attack,web,</group>
  </rule>

  <!-- SQL Injection Attempt -->
  <rule id="100022" level="12">
    <if_sid>31106</if_sid>
    <description>Custom: SQL Injection Attempt Detected</description>
    <mitre><id>T1190</id></mitre>
    <group>attack,web,</group>
  </rule>

</group>
```

---

## 📊 Alerts Generated

| Rule ID | Description | Level | MITRE | Type |
|---|---|---|---|---|
| 5760 | sshd: Authentication failed | 5 | T1110 | Built-in |
| 5503 | PAM: User login failed | 5 | T1110 | Built-in |
| 40111 | Multiple authentication failures | 10 | T1110 | Built-in |
| 11403 | vsftpd: Login failed | 5 | T1110 | Built-in |
| 11451 | vsftpd: FTP brute force detected | 10 | T1110 | Built-in |
| 31101 | Web server 400 error code | 5 | T1595 | Built-in |
| 31104 | Common web attack | 6 | T1595 | Built-in |
| **100006** | **Custom: Multiple PAM Auth Failures** | **10** | **T1110** | **Custom** |
| **100021** | **Custom: Directory Traversal Attack** | **12** | **T1083** | **Custom** |
| 651 | Host Blocked by firewall-drop | 3 | — | Active Response |
| 652 | Host Unblocked by firewall-drop | 3 | — | Active Response |

---

## 🛡️ Automated Active Response

When detection rules fire, Wazuh automatically:

1. Sends a block command to the Wazuh Agent on Ubuntu Server
2. The `firewall-drop` script executes on the target machine
3. Attacker IP is added to **nftables/iptables DROP rules**
4. Block is automatically lifted after **300 seconds (5 minutes)**

<img width="1366" height="702" alt="Screenshot_2026-05-12_06_58_11" src="https://github.com/user-attachments/assets/6dd9f4ec-5cf8-4b4d-b52e-dc9f1bb118cf" />


```xml
<active-response>
  <command>firewall-drop</command>
  <location>all</location>
  <rules_id>100006</rules_id>
  <timeout>300</timeout>
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>all</location>
  <rules_id>11451</rules_id>
  <timeout>300</timeout>
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>all</location>
  <rules_id>100021</rules_id>
  <timeout>300</timeout>
</active-response>
```

### ⚠️ Key Technical Finding: iptables vs nftables

Ubuntu 24.04 uses **nftables as the kernel firewall backend**. The `iptables` command is a compatibility wrapper that translates to nftables underneath.

```
iptables (compatibility layer)  ──┐
                                  ├──► nftables (kernel firewall)
nft (native interface)          ──┘
```

During testing, SSH blocks appeared in `iptables -L INPUT` while FTP and HTTP blocks appeared in `nft list ruleset`. SOC analysts should check both interfaces on modern Ubuntu systems.

**Verify using iptables (SSH blocks):**
```bash
sudo iptables -L INPUT -n
```

**Verify using nftables (FTP/HTTP blocks):**
```bash
sudo nft list ruleset
```

**nftables output showing 96 packets dropped (HTTP block):**
```
table ip filter {
  chain INPUT {
    ip saddr 10.183.32.99 counter packets 96 bytes 18388 drop
  }
}
```

---

## 🔧 Troubleshooting & Fixes

### Ubuntu 24.04 journald Fix
Ubuntu 24.04 no longer uses `/var/log/auth.log` by default — it uses **journald**. Wazuh Agent was configured to read from journald:

```xml
<localfile>
  <log_format>journald</log_format>
  <location>journald</location>
</localfile>
```
<img width="537" height="179" alt="Screenshot_2026-05-19_06_45_48" src="https://github.com/user-attachments/assets/d745d173-7f77-4912-9560-59b5f73cdff0" />


### FTP IPv6 Fix
vsftpd on Ubuntu 24.04 logs IPs in IPv6-mapped format (`::ffff:10.x.x.x`). To force IPv4 logging, add to `/etc/vsftpd.conf`:

```
listen=YES
listen_ipv6=NO
```

### Telegram Duplicate Alert Fix
FTP attacks triggered multiple Telegram messages. Fixed using `repeated_offenders` in ossec.conf:

```xml
<active-response>
  <command>telegram-alert</command>
  <location>server</location>
  <rules_id>11451</rules_id>
  <timeout>0</timeout>
  <repeated_offenders>1,5,10</repeated_offenders>
</active-response>
```

<img width="1366" height="702" alt="Screenshot_2026-05-24_02_35_54" src="https://github.com/user-attachments/assets/79961160-cec5-4ad1-b470-fdc3f6e21e47" />

---

## 📱 Telegram Bot Integration

A custom Telegram Bot provides **real-time mobile alerts** and **interactive SOC analyst queries**.

### Automatic Alert Notifications

```
🚨 WAZUH SOC ALERT 🚨
━━━━━━━━━━━━━━━━━━━━
🔴 Rule ID: 100006
⚠️  Level: 10
📋 Description: Custom: Multiple PAM Auth Failures
🖥️  Agent: siem-server
🌐 Source IP: 10.183.32.99
🕐 Time: 2026-05-22T09:19:16
━━━━━━━━━━━━━━━━━━━━
🛡️ Auto-block initiated!
```

<img width="393" height="242" alt="alert" src="https://github.com/user-attachments/assets/6258566a-ff3a-4c46-af10-1fde2c982450" />


### Interactive Bot Commands

| Command | Description |
|---|---|
| `/help` | Show all available commands |
| `/status` | Check Wazuh agent status |
| `/alerts` | Show last 5 security alerts |
| `/blocked` | Show currently blocked IPs |
| `/clear` | Clear all firewall blocks |


<img width="594" height="768" alt="alert2" src="https://github.com/user-attachments/assets/e498b1db-8844-4a82-8694-934caec7276e" />  <img width="569" height="768" alt="alert3" src="https://github.com/user-attachments/assets/f6bd9d2e-da6b-4333-a5f5-5dc384d949b3" />


### Bot Files
- [`telegram-alert.sh`](./telegram-alert.sh) — Active response script for automatic Wazuh alerts
- [`wazuh-telegram-bot.py`](./wazuh-telegram-bot.py) — Interactive query bot

---

## 📋 Incident Response Playbook

### SSH Brute Force — Rule 100006

| Step | Phase | Action |
|---|---|---|
| 1 | Detect | Rule 100006 fires — 6+ failed SSH logins in 120 seconds |
| 2 | Auto-Contain | Wazuh auto-blocks attacker IP via firewall-drop (300s) |
| 3 | Alert | Telegram bot sends instant notification |
| 4 | Investigate | Check source IP and frequency in Wazuh Threat Hunting |
| 5 | Analyze | Verify no successful login — check for Rule 5501 |
| 6 | Eradicate | Rotate credentials, audit accounts if breach confirmed |
| 7 | Document | Record IOCs, timeline, and all actions taken |

### FTP Brute Force — Rule 11451

| Step | Phase | Action |
|---|---|---|
| 1 | Detect | Rule 11451 fires — FTP brute force in vsftpd.log |
| 2 | Auto-Contain | Wazuh blocks attacker IP in nftables |
| 3 | Alert | Telegram notification sent automatically |
| 4 | Investigate | Check vsftpd.log for targeted usernames |
| 5 | Analyze | Verify no successful FTP login occurred |
| 6 | Eradicate | Disable anonymous FTP, change credentials |
| 7 | Document | Record attack details and remediation steps |

### HTTP Attack — Rule 100021

| Step | Phase | Action |
|---|---|---|
| 1 | Detect | Rule 100021 fires — Directory traversal in Apache logs |
| 2 | Auto-Contain | Wazuh blocks attacker IP (96+ packets dropped) |
| 3 | Alert | Telegram notification with source IP and rule details |
| 4 | Investigate | Review Apache access.log for full attack scope |
| 5 | Analyze | Check if sensitive files were accessed |
| 6 | Eradicate | Patch web app, update Apache config |
| 7 | Document | Log HTTP attack patterns and IOCs |

---

## 💡 Key Learnings

- Installed and configured Wazuh SIEM (Manager, Indexer, Dashboard, Agent) from scratch
- Wrote custom XML detection rules with MITRE ATT&CK mapping for SSH, FTP, and HTTP attacks
- Discovered Ubuntu 24.04 uses **journald** instead of `/var/log/auth.log` and configured Wazuh accordingly
- Key finding: **iptables is a compatibility wrapper over nftables** on Ubuntu 24.04 — check both interfaces
- Configured Active Response for automated threat containment across three attack vectors
- Developed a Python **Telegram bot** with real-time alerts and interactive analyst commands
- Simulated real attacks using Hydra, Nmap, and Nikto
- Troubleshot VM networking (NAT vs Bridged adapters, IPv4 vs IPv6 log formats)

---

## 🔮 Future Improvements

- [ ] Run Telegram bot as systemd service for 24/7 monitoring
- [ ] Add Windows VM as Wazuh Agent for Windows-specific attacks
- [ ] Integrate with TheHive for incident case management
- [ ] Implement File Integrity Monitoring (FIM)
- [ ] Add vulnerability scanning with OpenVAS
- [ ] Build compliance dashboards (PCI-DSS, NIST 800-53)

---

## 👤 Author

**Gokul Sundar C**
Aspiring SOC Analyst | Cybersecurity Enthusiast

📧 gokulsundar.x07@gmail.com
🔗 [LinkedIn](https://www.linkedin.com/in/thegokulsundar)
🐙 [GitHub](https://github.com/gokulsundarc)

---

> ⚠️ *This project is for educational purposes only. Do not use these techniques on systems you don't own or have explicit permission to test.*
```
