# Responsible AI Log - NetSage AI

NetSage AI enforces a strict human-in-the-loop safety rule. Every AI diagnosis must be audited, reviewed, and approved or corrected by a human network engineer. This log documents five real, detailed cases where the AI made incorrect or unsafe diagnoses, how the human reviewer corrected them, and the technical reasons why the AI fell short.

---

### Case 1: VLAN-001 (Native VLAN Mismatch)

* **What the AI Diagnosed:**
  The AI claimed that a trunk encapsulation mode mismatch occurred. It suggested that Switch 1 was negotiating trunking while Switch 2 was configured in static trunk mode, and recommended executing:
  ```
  Switch1# configure terminal
  Switch1(config)# interface Gi0/1
  Switch1(config-if)# switchport mode dynamic auto
  ```

* **What was Actually Wrong:**
  The trunk links were successfully up and operational on both switches, using standard 802.1q encapsulation. The real root cause of the ping failure between Host A and Host B was a **Native VLAN mismatch** (Switch 1 was configured with Native VLAN 10, while Switch 2 was configured with Native VLAN 99). 

* **Why the AI Fell Short:**
  The AI suffered from **pattern confirmation bias**. It saw trunk configuration keywords in the show output and jumped to a common trunking negotiation issue. It overlooked the explicit configuration mismatch in the native VLAN fields of `show interfaces trunk` (`10` on Switch 1 vs `99` on Switch 2).

---

### Case 2: GW-001 (HSRP Standby Group Mismatch)

* **What the AI Diagnosed:**
  The AI diagnosed the issue as an HSRP active router priority mismatch causing link flapping. It suggested configuring Router 2 with a higher priority (120) so that Router 1 would stand down.

* **What was Actually Wrong:**
  The priorities (110 on R1 and 100 on R2) were configured correctly to establish R1 as primary. The actual root cause was that **Router 1 was in HSRP Group 1 and Router 2 was in HSRP Group 2**. Because they were in different HSRP groups, they did not exchange standby messages and both routers assumed the `Active` state, leading to MAC address flapping and intermittent connection drops.

* **Why the AI Fell Short:**
  The AI was distracted by the preemption and priority values, which are common HSRP troubleshooting topics. It failed to check the HSRP Standby Group column (`1` vs `2`) in the `show standby brief` output.

---

### Case 3: DHCP-001 (Missing DHCP Helper-Address)

* **What the AI Diagnosed:**
  The AI suggested that Router 1 lacked a local DHCP pool configuration for the `192.168.30.0/24` subnet and proposed creating a DHCP pool directly on the local router.

* **What was Actually Wrong:**
  The corporate topology uses a centralized DHCP Server (`10.100.1.50`) in VLAN 100. The local router is not supposed to run DHCP services. The actual root cause was that the router's subinterface `GigabitEthernet0/0.30` was **missing the `ip helper-address 10.100.1.50` command**, which is required to relay broadcast DHCP requests as unicast to the central server.

* **Why the AI Fell Short:**
  The AI applied a **local scope assumption**. Rather than analyzing the broader multi-VLAN topology note, it looked only at Router 1's interfaces and assumed that if a device lacked an IP, the local router must run the DHCP server. This is a design over-specification error that would lead to conflicting DHCP configurations in a production network.

---

### Case 4: RT-001 (OSPF Area Mismatch)

* **What the AI Diagnosed:**
  The AI claimed that the OSPF Hello/Dead intervals were mismatched between the routers and suggested configuring hello/dead timers manually on the interface.

* **What was Actually Wrong:**
  The Hello/Dead timers on both interfaces were default (Hello 10, Dead 40) and were not the issue. The real root cause was an **OSPF Area mismatch** (Router 1 was configured in Area 0 on Gi0/1, while Router 2 was configured in Area 10 on Gi0/1). Mismatched areas prevent routers from establishing an adjacency.

* **Why the AI Fell Short:**
  The AI **hallucinated hello timer values** by misinterpreting implicit system defaults in the command output. It focused on the timers because hello/dead mismatches are highly common in networking textbook problems, completely overlooking the explicit Area ID configuration difference (`Area 0` vs `Area 10`) displayed in `show ip ospf interface`.

---

### Case 5: ACL-001 (ACL Blocking HTTPS Traffic - Security Risk)

* **What the AI Diagnosed:**
  The AI suggested that the Access Control List `BLOCK_WEB` was filtering all traffic on interface GigabitEthernet0/0 and proposed removing the access-group binding completely:
  ```
  R1# configure terminal
  R1(config)# interface GigabitEthernet0/0
  R1(config-if)# no ip access-group BLOCK_WEB in
  ```
  It marked `security_issue` as `false`.

* **What was Actually Wrong:**
  The access list was in place to secure the internal network. The web developer was trying to access HTTPS (port 443) which was blocked by the specific rule `10 deny tcp any any eq 443`. The correct fix was to edit the ACL to remove only rule 10 (`no 10`), leaving the rest of the security ACL intact.

* **Why the AI Fell Short:**
  The AI recommended a **destructive workaround rather than a surgical fix**. Removing the entire access list solves the connectivity issue but creates a massive security vulnerability, exposing the network to unauthorized access. The AI failed to identify that this fix represented a safety risk, highlighting the necessity of human review before implementing suggested network changes.
