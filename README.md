🧱 SOC Lab — Threat Detection & Automated Response with Wazuh

A hands-on SOC lab where I simulated real attacks, wrote custom Wazuh detection rules, and configured automated IP blocking using iptables — all on a local virtualized network.

---

# What This Lab Does

* Simulates real attacks (port scanning, SSH brute force) using Kali Linux
* Detects them using custom Wazuh rules mapped to MITRE ATT&CK
* Automatically blocks the attacker IP via iptables — no manual action needed

---

#🔎 Lab Architecture

```
┌─────────────────────────────────────────────────────┐
│                VirtualBox (Host: Windows)           │
│                                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐ │
│  │   Kali Linux          │  │  Ubuntu Server 24.04 ││
│  │   (Attacker +         │  │  (Target Machine +   ││
│  │    Wazuh Manager)     │  │   Wazuh Agent)       ││
│  │                       │  │                      ││
│  │  • Wazuh Manager      │◄─│  • Wazuh Agent 002   ││
│  │  • Wazuh Dashboard    │  │  • SSH  (Port 22)    ││
│  │  • Wazuh Indexer      │  │  • FTP  (Port 21)    ││
│  │  • Hydra              │  │  • HTTP (Port 80)    ││
│  │  • Nmap               │  │  • iptables Firewall ││
│  └──────────────────────┘  └──────────────────────┘ │
│          Network: Bridged Adapter                   │
└─────────────────────────────────────────────────────┘
```

---

#🔨 Tools Used


1. Wazuh 4.x -- SIEM — log analysis, detection, active response 
2. Kali Linux -- Attacker machine + Wazuh Manager  
3. Ubuntu Server 24.04 -- Target machine + Wazuh Agent  
4. VirtualBox -- Virtualization 
5. Hydra -- SSH brute force simulation  
6. Nmap -- Port scan / reconnaissance
7. iptables -- Automated IP blocking

---

#📎 Attacks Simulated

1. Port Scan (Nmap)

```bash
nmap -sS -p 1-1000 <target-ip>
```
Discovered open ports: 21 (FTP), 22 (SSH), 80 (HTTP)  
MITRE ATT&CK: T1046 — Network Service Discovery
<img width="1366" height="702" alt="image" src="https://github.com/user-attachments/assets/557a8ee4-b312-40f7-8452-dd9cf451126a" />


2. SSH Brute Force (Hydra)
   
```bash
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://<target-ip> -t 4
```
Generated hundreds of failed login attempts  
MITRE ATT&CK: T1110 — Brute Force
<img width="1366" height="702" alt="image" src="https://github.com/user-attachments/assets/e805d31c-e3d3-4506-b617-1fe60518c6ea" />

---

# Custom Detection Rules

I Stored the custom commands in separate as local_rules.xml and to congfig it in location `/var/ossec/etc/rules/local_rules.xml`:

```xml
<group name="local,">

  <!-- SSH Brute Force Detection -->
  <rule id="100001" level="10" frequency="3" timeframe="120">
    <if_matched_sid>5716</if_matched_sid>
    <description>Custom: SSH Brute Force Attack Detected from same source</description>
    <mitre><id>T1110</id></mitre>
    <group>attack,authentication_failures,</group>
  </rule>

  <!-- High Volume Brute Force -->
  <rule id="100002" level="12" frequency="10" timeframe="60">
    <if_matched_sid>5716</if_matched_sid>
    <description>Custom: High Volume SSH Brute Force - Possible Automated Attack</description>
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

</group>
```

---

## Automated Active Response

When Rule 100006 fires (6+ failed logins in 120 seconds):

1. Wazuh sends a block command to the agent on Ubuntu
2. The `firewall-drop` script runs on the target machine
3. Attacker IP gets added to iptables DROP rules
4. Block lifts automatically after 300 seconds
<img width="1366" height="702" alt="image" src="https://github.com/user-attachments/assets/804794b6-5ec5-44d7-af2c-6b77cb3f8134" />
Verification of automated Ip drop


**Config in `ossec.conf`:**
```xml
<active-response>
  <command>firewall-drop</command>
  <location>all</location>
  <rules_id>100006</rules_id>
  <timeout>300</timeout>
</active-response>
```

* Resulting iptables rule:
```bash
iptables -I INPUT -s <attacker-ip> -j DROP
```
before the command
<img width="994" height="768" alt="WhatsApp Image 2026-05-09 at 8 08 00 PM" src="https://github.com/user-attachments/assets/adb1b899-1e2c-4c48-8955-c3fe90c9aafb" />
after the command

---

# 📊 Alerts Generated

| Rule ID   | Description                                      | Level | MITRE     | Notes                     |
|-----------|--------------------------------------------------|-------|-----------|---------------------------|
| 5760      | sshd: authentication failed                      | 5     | T1110     | Basic failed login        |
| 5503      | PAM: User login failed                           | 5     | T1110     | PAM authentication fail   |
| 40111     | Multiple authentication failures                 | 10    | T1110     | Wazuh default rule        |
| 100006    | Custom: Multiple PAM Auth Failures               | 10    | T1110     | Triggers Active Response  |
| 651       | Host Blocked by firewall-drop                    | 3     | -         | Active Response           |
---

# 📖Incident Response Playbook

SSH Brute Force — Rule 100006

1. Detect -- Rule 100006 fires — 6+ failed SSH logins in 120 seconds
2. Auto -- Contain,Wazuh automatically blocks attacker IP using firewall-drop
3. Investigate -- Check source IP, timestamp, and attack frequency in Wazuh Threat Hunting
4. Analyze -- Verify if any login was successful (journalctl -u ssh or /var/log/auth.log)
5. Eradicate -- If breach confirmed: Rotate credentials, audit user accounts, remove unauthorized access
6. Recover -- Verify system integrity, remove blocks if needed, re-enable services safely
7. Document -- Record IOCs (attacker IP, timestamp), timeline, and all actions taken

---


#🏫 What I Learned

* Installing and configuring Wazuh SIEM from scratch
* Writing custom XML detection rules with MITRE ATT&CK mapping with help of AI
* Setting up active response for automated threat containment
* Reading and analyzing logs from journald and syslog
* Simulating attacks with Hydra and Nmap
* Troubleshooting VM network issues 
* Working with iptables firewall rules

---

#🙍 Author

Hi I'm Gokul Sundar C and a Aspiring SOC Analyst and Cybersecurity Enthusiast. 
📧 gokulsundar.x07@gmail.com  
🔗 www.linkedin.com/in/thegokulsundar

---

*This project is for educational purposes only. Do not use these techniques on systems you don't own or have explicit permission to test.*
