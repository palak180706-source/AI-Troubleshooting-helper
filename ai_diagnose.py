import os
import csv
import json
import argparse
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# Dictionary of standard fixes mapped to concept tags
CONCEPT_FIXES = {
    "native-vlan-mismatch": {
        "root_cause": "Native VLAN mismatch on the trunk link between Switch 1 (Native VLAN 10) and Switch 2 (Native VLAN 99).",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "Switch1 Gi0/1 Native VLAN is 10, while Switch2 Gi0/1 Native VLAN is 99 in show interfaces trunk.",
        "next_command": "show interface Gi0/1 switchport",
        "fix_steps": "Switch2# configure terminal\nSwitch2(config)# interface Gi0/1\nSwitch2(config-if)# switchport trunk native vlan 10\nSwitch2(config-if)# end",
        "security_issue": True,
        "alternative_cause": "VLAN tag hopping attack or incorrect native VLAN pruning on Switch 1."
    },
    "vlan-pruning-allowed-list": {
        "root_cause": "VLAN 20 is pruned/missing from the allowed VLAN list on Switch 1's trunk interface Gi0/2.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "Switch1 Gi0/2 allowed VLANs list shows '1,10' which excludes VLAN 20, whereas Switch2 allowed VLAN list shows '1-4094'.",
        "next_command": "show interface Gi0/2 switchport",
        "fix_steps": "Switch1# configure terminal\nSwitch1(config)# interface Gi0/2\nSwitch1(config-if)# switchport trunk allowed vlan add 20\nSwitch1(config-if)# end",
        "security_issue": False,
        "alternative_cause": "VLAN 20 is not configured/active in the VLAN database of Switch 1."
    },
    "incorrect-vlan-assignment": {
        "root_cause": "Switch port Fa0/5 is assigned to the default VLAN 1 instead of the HR VLAN 30.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "show interface Fa0/5 switchport output shows Operational Access VLAN: 1 (default) and show mac address-table shows VLAN 1 active on interface Fa0/5.",
        "next_command": "show vlan brief",
        "fix_steps": "Switch1# configure terminal\nSwitch1(config)# interface Fa0/5\nSwitch1(config-if)# switchport access vlan 30\nSwitch1(config-if)# end",
        "security_issue": False,
        "alternative_cause": "Host PC is manually configured with the wrong VLAN Tag or static IP, but Switchport assignment is the direct issue."
    },
    "trunk-encapsulation-mismatch": {
        "root_cause": "Trunking encapsulation mismatch (dot1q on Switch 1 vs ISL on Switch 2) prevents trunk negotiation.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "Switch 1 running config interface Gi0/2 shows 'switchport trunk encapsulation dot1q' and Switch 2 shows 'switchport trunk encapsulation isl'.",
        "next_command": "show interface Gi0/2 switchport",
        "fix_steps": "Switch2# configure terminal\nSwitch2(config)# interface Gi0/2\nSwitch2(config-if)# switchport trunk encapsulation dot1q\nSwitch2(config-if)# switchport mode trunk\nSwitch2(config-if)# end",
        "security_issue": False,
        "alternative_cause": "One of the switch ports is configured in dynamic auto/desirable mode which fails to negotiate."
    },
    "hsrp-group-mismatch": {
        "root_cause": "HSRP group ID mismatch (Group 1 on R1 vs Group 2 on R2) causes both routers to act as Active gateways.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 standby brief shows group 1 is active locally and standby is 192.168.1.2. R2 standby brief shows group 2 is active locally and standby is unknown.",
        "next_command": "show standby interface Gi0/0.10",
        "fix_steps": "R2# configure terminal\nR2(config)# interface Gi0/0.10\nR2(config-subif)# no standby 2 ip 192.168.1.254\nR2(config-subif)# standby 1 ip 192.168.1.254\nR2(config-subif)# standby 1 priority 100\nR2(config-subif)# standby 1 preempt\nR2(config-subif)# end",
        "security_issue": False,
        "alternative_cause": "HSRP authentication mismatch preventing hello exchange, causing both to assume the Active state."
    },
    "subinterface-shutdown": {
        "root_cause": "The subinterface GigabitEthernet0/0.10 is administratively shut down.",
        "osi_layer": "Layer 1",
        "confidence": "High",
        "evidence": "R1 show ip interface brief shows 'GigabitEthernet0/0.10' is 'administratively down'.",
        "next_command": "show running-config interface Gi0/0.10",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0.10\nR1(config-subif)# no shutdown\nR1(config-subif)# end",
        "security_issue": False,
        "alternative_cause": "The physical interface GigabitEthernet0/0 is shut down, but the show outputs indicate only GigabitEthernet0/0.10 is down."
    },
    "gateway-ip-mismatch": {
        "root_cause": "Host C has a mismatched default gateway (10.1.10.254) configured instead of the actual router interface (10.1.10.1).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "HostC ipconfig shows default gateway is 10.1.10.254, but Router 1 interface Gi0/1 is configured with 10.1.10.1.",
        "next_command": "ping 10.1.10.1",
        "fix_steps": "HostC# (Update local network properties / DHCP static reservation)\nSet Default Gateway: 10.1.10.1",
        "security_issue": False,
        "alternative_cause": "Host is configured with static IP in wrong subnet, or Router interface IP was recently changed."
    },
    "proxy-arp-disabled": {
        "root_cause": "Proxy ARP is disabled on Router 1's GigabitEthernet0/0 interface.",
        "osi_layer": "Layer 3",
        "confidence": "Medium",
        "evidence": "R1 show ip interface Gi0/0 output shows 'Proxy ARP is disabled'.",
        "next_command": "show ip interface Gi0/0",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0\nR1(config-if)# ip proxy-arp\nR1(config-if)# end",
        "security_issue": True,
        "alternative_cause": "Hosts have missing or incorrect default gateways configured, relying on Proxy ARP as a fallback."
    },
    "missing-dhcp-helper": {
        "root_cause": "Missing DHCP helper-address on the router's subinterface GigabitEthernet0/0.30.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show running-config and show ip interface Gi0/0.30 outputs show 'Helper address is not set'.",
        "next_command": "show running-config interface GigabitEthernet0/0.30",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0.30\nR1(config-subif)# ip helper-address 10.100.1.50\nR1(config-subif)# end",
        "security_issue": False,
        "alternative_cause": "The DHCP server itself is down, or there is routing failure between R1 and the DHCP server."
    },
    "dhcp-pool-exhaustion": {
        "root_cause": "DHCP address pool utilization is at 100% (pool exhaustion). No IP addresses left to allocate.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show ip dhcp pool output lists 'Utilization mark (high/low): 100 / 0' and 'Active bindings: 57' on a pool of max size 62 with 5 excluded IPs.",
        "next_command": "show ip dhcp binding",
        "fix_steps": "R1# configure terminal\nR1(config)# ip dhcp pool Finance\nR1(config-dhcp)# network 192.168.40.0 255.255.255.128\n# (Expands pool size from /26 to /25 for more host allocations)\nR1(config-dhcp)# end",
        "security_issue": False,
        "alternative_cause": "DHCP lease time is set too long, preventing recycling of inactive IP addresses."
    },
    "dhcp-subnet-mask-mismatch": {
        "root_cause": "Subnet mask mismatch in DHCP pool (configured as 255.255.255.128 /25, but the router subinterface is 255.255.255.0 /24).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "DHCP pool configuration has network 192.168.50.0 255.255.255.128, but Router subinterface Gi0/0.50 is configured with 192.168.50.1 255.255.255.0.",
        "next_command": "show run | section ip dhcp pool",
        "fix_steps": "R1# configure terminal\nR1(config)# ip dhcp pool VLAN50\nR1(config-dhcp)# no network 192.168.50.0 255.255.255.128\nR1(config-dhcp)# network 192.168.50.0 255.255.255.0\nR1(config-dhcp)# end",
        "security_issue": False,
        "alternative_cause": "Router subinterface IP was configured with the wrong mask, and the DHCP pool mask is actually correct."
    },
    "dhcp-conflict-missing-exclusion": {
        "root_cause": "DHCP server allocation conflict due to missing ip dhcp excluded-address for statically configured servers (192.168.1.10).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show ip dhcp conflict lists conflict for 192.168.1.10 detected by ping, and running config has no ip dhcp excluded-address defined.",
        "next_command": "show ip dhcp binding",
        "fix_steps": "R1# configure terminal\nR1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10\nR1(config)# end",
        "security_issue": False,
        "alternative_cause": "Rogue DHCP server on the local LAN segment or IP spoofing from an end client."
    },
    "incorrect-dns-server-ip": {
        "root_cause": "The DHCP pool advertises an unreachable/dead DNS server IP address (192.168.10.250).",
        "osi_layer": "Layer 7",
        "confidence": "High",
        "evidence": "HostA ipconfig shows DNS Server is 192.168.10.250, but no interface on the router or network matches IP 192.168.10.250.",
        "next_command": "show running-config | section ip dhcp pool",
        "fix_steps": "R1# configure terminal\nR1(config)# ip dhcp pool Pool1\nR1(config-dhcp)# no dns-server 192.168.10.250\nR1(config-dhcp)# dns-server 8.8.8.8\nR1(config-dhcp)# end",
        "security_issue": False,
        "alternative_cause": "The local DNS server at 192.168.10.250 is shut down or experiencing hardware/software failure."
    },
    "dns-lookup-disabled": {
        "root_cause": "DNS resolution is globally disabled on the router via the 'no ip domain-lookup' configuration.",
        "osi_layer": "Layer 7",
        "confidence": "High",
        "evidence": "R1 running config shows 'no ip domain-lookup' statement alongside 'ip name-server 8.8.8.8'.",
        "next_command": "show running-config | include domain",
        "fix_steps": "R1# configure terminal\nR1(config)# ip domain-lookup\nR1(config)# end",
        "security_issue": False,
        "alternative_cause": "The name-server IP address (8.8.8.8) is blocked or unreachable by routing rules."
    },
    "stale-dns-a-record": {
        "root_cause": "Stale/incorrect DNS A record mapping for 'intranet.local' on the local DNS server.",
        "osi_layer": "Layer 7",
        "confidence": "High",
        "evidence": "DNS server DNS View shows mapping 'intranet.local -> 10.10.10.99', but the actual server IP is 10.10.10.100.",
        "next_command": "ping 10.10.10.100",
        "fix_steps": "DNS_Server# configure terminal\nDNS_Server(config)# no ip host intranet.local 10.10.10.99\nDNS_Server(config)# ip host intranet.local 10.10.10.100\nDNS_Server(config)# end",
        "security_issue": False,
        "alternative_cause": "IP address conflict on the web server itself, or DNS server cache has not expired."
    },
    "missing-dns-zone": {
        "root_cause": "DNS Zone configuration error: The DNS server does not host the local domain zone record.",
        "osi_layer": "Layer 7",
        "confidence": "High",
        "evidence": "HostA nslookup shows 'intranet.corp: Non-existent domain' and local DNS view has no host entry for intranet.corp.",
        "next_command": "show running-config | include ip host",
        "fix_steps": "DNS_Server# configure terminal\nDNS_Server(config)# ip host intranet.corp 192.168.1.10\nDNS_Server(config)# end",
        "security_issue": False,
        "alternative_cause": "Forwarder configuration on DNS server is incorrect or external registrar is offline."
    },
    "ospf-area-mismatch": {
        "root_cause": "OSPF Area mismatch (Area 0 on R1 vs Area 10 on R2) prevents forming a neighbor adjacency.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 Gi0/1 is in Area 0 while R2 Gi0/1 is in Area 10 as shown in 'show ip ospf interface Gi0/1' outputs.",
        "next_command": "show ip ospf neighbor",
        "fix_steps": "R2# configure terminal\nR2(config)# router ospf 1\nR2(config-router)# no network 10.1.12.0 0.0.0.3 area 10\nR2(config-router)# network 10.1.12.0 0.0.0.3 area 0\nR2(config-router)# end",
        "security_issue": False,
        "alternative_cause": "OSPF Hello/Dead interval mismatch or OSPF Authentication mismatch."
    },
    "missing-static-route": {
        "root_cause": "Missing static route to the remote HQ network (10.0.0.0/8) on the Branch Router.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "BranchRouter 'show ip route static' contains static route to 172.16.1.0/24 but lacks any route entry for 10.0.0.0/8.",
        "next_command": "show ip route",
        "fix_steps": "BranchRouter# configure terminal\nBranchRouter(config)# ip route 10.0.0.0 255.0.0.0 203.0.113.2\nBranchRouter(config)# end",
        "security_issue": False,
        "alternative_cause": "Dynamic routing protocol (like OSPF or EIGRP) neighbor down or not advertising the network."
    },
    "ospf-mtu-mismatch": {
        "root_cause": "Interface MTU mismatch (1500 bytes on R1 vs 1450 bytes on R2) prevents OSPF database exchange completion.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show ip interface Gi0/1 lists MTU is 1500, whereas R2 show ip interface Gi0/1 lists MTU is 1450.",
        "next_command": "show ip ospf neighbor",
        "fix_steps": "R2# configure terminal\nR2(config)# interface GigabitEthernet0/1\nR2(config-if)# ip mtu 1500\nR2(config-if)# end",
        "security_issue": False,
        "alternative_cause": "OSPF database too large for the media, or Layer 2 MTU issue on intermediate switch."
    },
    "routing-loop-static": {
        "root_cause": "Routing loop caused by mutually recursive static routes pointing back and forth between R1 and R2.",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 route for 10.200.1.0/24 is via 192.168.12.2 and R2 route for 10.200.1.0/24 is via 192.168.12.1 in routing table outputs.",
        "next_command": "traceroute 10.200.1.5",
        "fix_steps": "R2# configure terminal\nR2(config)# no ip route 10.200.1.0 255.255.255.0 192.168.12.1\nR2(config)# ip route 10.200.1.0 255.255.255.0 GigabitEthernet0/1\nR2(config)# end",
        "security_issue": False,
        "alternative_cause": "BGP route redistribution loop or dynamic routing protocol misconfiguration."
    },
    "acl-blocking-needed-port": {
        "root_cause": "ACL rule (sequence 10) explicitly denies HTTPS (port 443) traffic.",
        "osi_layer": "Layer 4",
        "confidence": "High",
        "evidence": "R1 show access-lists lists: 'Extended IP access list BLOCK_WEB' '10 deny tcp any any eq 443'.",
        "next_command": "show running-config interface Gi0/0",
        "fix_steps": "R1# configure terminal\nR1(config)# ip access-list extended BLOCK_WEB\nR1(config-ext-nacl)# no 10\nR1(config-ext-nacl)# end",
        "security_issue": False,
        "alternative_cause": "Web server HTTPS daemon is stopped, but the ACL block is active."
    },
    "vty-acl-implicit-deny": {
        "root_cause": "The implicit deny of the VTY access-class ACL blocks admin connections coming from the management host subnet (192.168.1.50).",
        "osi_layer": "Layer 4",
        "confidence": "High",
        "evidence": "R1 access-lists output lists permit statement only for 10.99.1.0/24. Administrator IP is 192.168.1.50.",
        "next_command": "show line vty 0 4",
        "fix_steps": "R1# configure terminal\nR1(config)# ip access-list standard ADMIN_ONLY\nR1(config-std-nacl)# 20 permit 192.168.1.0 0.0.0.255\nR1(config-std-nacl)# end",
        "security_issue": True,
        "alternative_cause": "VTY password configuration missing or SSH key not generated on the router."
    },
    "acl-wrong-direction": {
        "root_cause": "ACL direction error: ACL is applied outbound blocking return traffic/packets exiting the router interface to DMZ.",
        "osi_layer": "Layer 4",
        "confidence": "High",
        "evidence": "R1 running config interface Gi0/1 has 'ip access-group DMZ_INBOUND out' on interface Gi0/1 (DMZ LAN interface).",
        "next_command": "show running-config interface Gi0/1",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/1\nR1(config-if)# no ip access-group DMZ_INBOUND out\nR1(config-if)# exit\nR1(config)# interface GigabitEthernet0/0\n# (Assuming Gi0/0 is WAN interface facing outside)\nR1(config-if)# ip access-group DMZ_INBOUND in\nR1(config-if)# end",
        "security_issue": True,
        "alternative_cause": "Rules inside the DMZ_INBOUND access list are missing proper return traffic permit statements."
    },
    "acl-rule-order": {
        "root_cause": "ACL rule order error: The deny statement for the entire subnet (192.168.10.0/24) precedes the specific permit statement for Host A (192.168.10.50).",
        "osi_layer": "Layer 4",
        "confidence": "High",
        "evidence": "R1 show access-lists FILTER lists: '10 deny ip 192.168.10.0 0.0.0.255 any' and '20 permit ip 192.168.10.50 0.0.0.0 any'.",
        "next_command": "show access-lists FILTER",
        "fix_steps": "R1# configure terminal\nR1(config)# ip access-list extended FILTER\nR1(config-ext-nacl)# no 10\nR1(config-ext-nacl)# no 20\nR1(config-ext-nacl)# 10 permit ip 192.168.10.50 0.0.0.0 any\nR1(config-ext-nacl)# 20 deny ip 192.168.10.0 0.0.0.255 any\nR1(config-ext-nacl)# end",
        "security_issue": False,
        "alternative_cause": "Host A has wrong IP configured or route is missing on Core Router."
    },
    "nat-interfaces-swapped": {
        "root_cause": "NAT inside/outside interface designations are swapped (Gi0/0 is configured as outside, Serial0/0/0 as inside).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 running config shows interface GigabitEthernet0/0 configured with 'ip nat outside' and interface Serial0/0/0 configured with 'ip nat inside'.",
        "next_command": "show ip nat statistics",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0\nR1(config-if)# no ip nat outside\nR1(config-if)# ip nat inside\nR1(config-if)# exit\nR1(config)# interface Serial0/0/0\nR1(config-if)# no ip nat inside\nR1(config-if)# ip nat outside\nR1(config-if)# end",
        "security_issue": True,
        "alternative_cause": "NAT translation table is full or ACL rule for NAT is blocking traffic."
    },
    "missing-nat-overload": {
        "root_cause": "Missing 'overload' keyword in the NAT configuration statement, preventing Port Address Translation (PAT).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show running-config shows 'ip nat inside source list 1 interface GigabitEthernet0/1' lacking the trailing 'overload' keyword.",
        "next_command": "show ip nat statistics",
        "fix_steps": "R1# configure terminal\nR1(config)# no ip nat inside source list 1 interface GigabitEthernet0/1\nR1(config)# ip nat inside source list 1 interface GigabitEthernet0/1 overload\nR1(config)# end",
        "security_issue": False,
        "alternative_cause": "IP address pool for NAT is exhausted, or ACL 1 does not permit the internal subnets."
    },
    "nat-acl-missing-subnet": {
        "root_cause": "The NAT access control list (NAT_ACL) does not permit/include the Marketing department subnet (192.168.20.0/24).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 show access-lists NAT_ACL shows rule: '10 permit 192.168.10.0 0.0.0.255' but no statement for 192.168.20.0/24.",
        "next_command": "show access-lists NAT_ACL",
        "fix_steps": "R1# configure terminal\nR1(config)# ip access-list standard NAT_ACL\nR1(config-std-nacl)# 20 permit 192.168.20.0 0.0.0.255\nR1(config-std-nacl)# end",
        "security_issue": False,
        "alternative_cause": "Route to the Marketing LAN interface is missing on the Border Router."
    },
    "static-nat-wrong-ip": {
        "root_cause": "Static NAT configuration error: Mismatched host IP (mapped 192.168.1.100 instead of server's actual IP 192.168.1.10).",
        "osi_layer": "Layer 3",
        "confidence": "High",
        "evidence": "R1 running config shows static NAT mapping: 'ip nat inside source static 192.168.1.100 203.0.113.10', but show ip interface brief indicates server IP is 192.168.1.10.",
        "next_command": "show ip nat translations",
        "fix_steps": "R1# configure terminal\nR1(config)# no ip nat inside source static 192.168.1.100 203.0.113.10\nR1(config)# ip nat inside source static 192.168.1.10 203.0.113.10\nR1(config)# end",
        "security_issue": False,
        "alternative_cause": "DNS record maps the public server domain to the wrong public IP address."
    },
    "wifi-psk-mismatch": {
        "root_cause": "WPA2 Pre-Shared Key (PSK) password mismatch on client configuration.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "AP show dot11 ssid Office-WiFi lists Pre-Shared Key: CompPass123!, but Host_Device profile shows Pre-Shared Key: CompPass123.",
        "next_command": "show wireless clients",
        "fix_steps": "Host_Device# configure wireless profile 'Office-WiFi' security wpa2-psk key CompPass123!",
        "security_issue": False,
        "alternative_cause": "DHCP allocation failure on the AP wireless VLAN interface."
    },
    "ssid-broadcast-disabled": {
        "root_cause": "SSID broadcasting is disabled on the WLC for the Guest-WiFi profile.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "WLC show wlan 2 output lists: 'Broadcast SSID................................... Disabled'.",
        "next_command": "show wlan summary",
        "fix_steps": "WLC# configure terminal\nWLC(config)# wlan 2\nWLC(config-wlan)# broadcast-ssid\nWLC(config-wlan)# end",
        "security_issue": False,
        "alternative_cause": "The Guest-WiFi SSID profile status is disabled (turned administrative down)."
    },
    "ap-switchport-access-vlan": {
        "root_cause": "Switch access port Fa0/12 connected to the AP is assigned to VLAN 1 instead of being configured as a trunk port to pass VLAN 80.",
        "osi_layer": "Layer 2",
        "confidence": "High",
        "evidence": "Switch1 Fa0/12 switchport configuration shows Operational Access VLAN: 1 (default) and Administrative Mode: static access.",
        "next_command": "show running-config interface Fa0/12",
        "fix_steps": "Switch1# configure terminal\nSwitch1(config)# interface Fa0/12\nSwitch1(config-if)# switchport trunk encapsulation dot1q\nSwitch1(config-if)# switchport mode trunk\nSwitch1(config-if)# switchport trunk allowed vlan 1,10,80\nSwitch1(config-if)# end",
        "security_issue": True,
        "alternative_cause": "Access Point trunk port tagging is disabled, forcing all traffic to fallback to Switch native VLAN."
    },
    "wireless-gateway-interface-down": {
        "root_cause": "The gateway SVl interface Vlan80 on the wireless router/switch is down.",
        "osi_layer": "Layer 1",
        "confidence": "High",
        "evidence": "Wireless_Router show ip interface brief shows Vlan80 status is 'down' and protocol is 'down'.",
        "next_command": "show running-config interface Vlan80",
        "fix_steps": "Wireless_Router# configure terminal\nWireless_Router(config)# interface Vlan80\nWireless_Router(config-if)# no shutdown\nWireless_Router(config-if)# end",
        "security_issue": False,
        "alternative_cause": "VLAN 80 has no active ports, causing the SVI to remain in a down state automatically."
    }
}

# The 6 deliberate AI errors we seed
AI_DELIBERATE_MISTAKES = {
    "VLAN-001": {
        "root_cause": "Trunk encapsulation mode mismatch. Switch 1 requires dynamic trunking protocol auto configuration, whereas Switch 2 is in static trunk mode.",
        "osi_layer": "Layer 2",
        "confidence": "Medium",
        "evidence": "Switch 1 Operational Mode is trunk, switchport mode on. Switch 2 trunk native vlan mismatch.",
        "next_command": "show interfaces trunk",
        "fix_steps": "Switch1# configure terminal\nSwitch1(config)# interface Gi0/1\nSwitch1(config-if)# switchport trunk encapsulation dot1q\nSwitch1(config-if)# switchport mode dynamic auto",
        "security_issue": False,
        "alternative_cause": "Mismatched Native VLAN IDs 10 and 99 causing traffic leaks."
    },
    "GW-001": {
        "root_cause": "HSRP active router priority mismatch. Both routers are configured with standby preemption active, causing interface flapping.",
        "osi_layer": "Layer 3",
        "confidence": "Low",
        "evidence": "R1 standby priority is 110 (preempt active). R2 standby priority is 100.",
        "next_command": "show standby",
        "fix_steps": "R2# configure terminal\nR2(config)# interface Gi0/0.10\nR2(config-subif)# standby 1 priority 120\nR2(config-subif)# standby 1 preempt",
        "security_issue": False,
        "alternative_cause": "HSRP group ID mismatch on subinterfaces."
    },
    "DHCP-001": {
        "root_cause": "Missing DHCP server configuration on Router 1 for local leases.",
        "osi_layer": "Layer 3",
        "confidence": "Medium",
        "evidence": "R1 show running-config has no DHCP pool configuration matching the 192.168.30.0/24 subnet.",
        "next_command": "show ip dhcp pool",
        "fix_steps": "R1# configure terminal\nR1(config)# ip dhcp pool LocalPool\nR1(config-dhcp)# network 192.168.30.0 255.255.255.0\nR1(config-dhcp)# default-router 192.168.30.1",
        "security_issue": False,
        "alternative_cause": "Missing DHCP relay agent helper-address pointing to 10.100.1.50."
    },
    "RT-001": {
        "root_cause": "OSPF Dead Interval and Hello Interval timer mismatch on the link Gi0/1.",
        "osi_layer": "Layer 3",
        "confidence": "Medium",
        "evidence": "R1 show ip ospf interface Gi0/1 states hello 10, dead 40. R2 show ip ospf interface Gi0/1 shows dead 40.",
        "next_command": "show ip ospf interface Gi0/1",
        "fix_steps": "R2# configure terminal\nR2(config)# interface Gi0/1\nR2(config-if)# ip ospf hello-interval 10\nR2(config-if)# ip ospf dead-interval 40",
        "security_issue": False,
        "alternative_cause": "OSPF Area mismatch (Area 0 on R1 vs Area 10 on R2)."
    },
    "ACL-001": {
        "root_cause": "The inbound Access Control List BLOCK_WEB is filtering all HTTP/HTTPS web traffic and should be disabled on the interface Gi0/0.",
        "osi_layer": "Layer 4",
        "confidence": "High",
        "evidence": "R1 interface Gi0/0 has ip access-group BLOCK_WEB in. ACCESS-LIST BLOCK_WEB denies port 443.",
        "next_command": "show running-config interface Gi0/0",
        "fix_steps": "R1# configure terminal\nR1(config)# interface GigabitEthernet0/0\nR1(config-if)# no ip access-group BLOCK_WEB in",
        "security_issue": False,  # Security issue is False which is a huge mistake since removing the whole ACL creates a security vulnerability!
        "alternative_cause": "A specific rule denies TCP port 443 while permitting port 80."
    },
    "NAT-002": {
        "root_cause": "NAT Access Control List (ACL 1) is missing from the configuration database on Router 1.",
        "osi_layer": "Layer 3",
        "confidence": "Medium",
        "evidence": "R1 running config lists 'ip nat inside source list 1 interface GigabitEthernet0/1' but show running-config has no access-list 1.",
        "next_command": "show access-lists",
        "fix_steps": "R1# configure terminal\nR1(config)# access-list 1 permit any",
        "security_issue": True,
        "alternative_cause": "Missing overload keyword in the ip nat statement, causing single-IP mapping exhaustion."
    }
}

def parse_args():
    parser = argparse.ArgumentParser(description="NetSage AI Diagnosis Runner")
    parser.add_argument("--offline", action="store_true", help="Force deterministic/offline fallback mode.")
    parser.add_argument("--case-id", type=str, default=None, help="Process a single case by ID.")
    return parser.parse_args()

def run_offline(cases_csv, case_id_filter=None):
    print("Running in OFFLINE/FALLBACK mode.")
    diagnoses = {}
    
    # Load existing diagnoses if available
    output_file = "data/ai_diagnoses.json"
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                diagnoses = json.load(f)
        except Exception:
            pass
            
    with open(cases_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            if case_id_filter and cid != case_id_filter:
                continue
                
            concept = row["concept_tag"]
            
            # Check if this is one of the 6 seeded mistake cases
            if cid in AI_DELIBERATE_MISTAKES:
                diag = AI_DELIBERATE_MISTAKES[cid].copy()
            else:
                # Use standard correct fallback
                if concept in CONCEPT_FIXES:
                    diag = CONCEPT_FIXES[concept].copy()
                else:
                    # Fallback for unknown concept
                    diag = {
                        "root_cause": row["expected_fault"],
                        "osi_layer": row["osi_layer"],
                        "confidence": "Medium",
                        "evidence": "Cisco CLI show commands demonstrate parameters mismatching expected values.",
                        "next_command": "show running-config",
                        "fix_steps": "Router# configure terminal\nRouter(config)# # Apply manual correction",
                        "security_issue": False,
                        "alternative_cause": "Physical Layer or cabling fault."
                    }
                    
            # Mark clearly as offline stub output
            diag["_offline_stub"] = True
            diagnoses[cid] = diag
            print(f"Processed case {cid} (Offline Stub)")
            
    # Save back to file
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(diagnoses, f, indent=2)
        
    print(f"Saved all diagnoses to {output_file}")
    return diagnoses

def run_live(cases_csv, api_key, case_id_filter=None):
    print("Running in LIVE mode calling Anthropic API.")
    client = Anthropic(api_key=api_key)
    
    # Read system prompt
    with open("prompts/diagnose_prompt.md", "r") as f:
        system_prompt = f.read()
        
    diagnoses = {}
    output_file = "data/ai_diagnoses.json"
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                diagnoses = json.load(f)
        except Exception:
            pass
            
    with open(cases_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            if case_id_filter and cid != case_id_filter:
                continue
                
            print(f"Diagnosing case {cid} via LLM...")
            
            user_content = (
                f"Symptom: {row['symptom']}\n"
                f"Topology Note: {row['topology_note']}\n"
                f"Cisco Show Output Excerpts:\n{row['show_output']}"
            )
            
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022", # Sonnet 3.5 latest name
                    max_tokens=1500,
                    temperature=0.0,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_content}
                    ]
                )
                
                resp_text = response.content[0].text.strip()
                # Clean optional markdown code blocks if the LLM output it by accident
                if resp_text.startswith("```json"):
                    resp_text = resp_text[7:]
                if resp_text.endswith("```"):
                    resp_text = resp_text[:-3]
                resp_text = resp_text.strip()
                
                diag_json = json.loads(resp_text)
                # Ensure the offline stub tag is False for live runs
                diag_json["_offline_stub"] = False
                diagnoses[cid] = diag_json
                print(f"Successfully diagnosed case {cid}")
            except Exception as e:
                print(f"Error diagnosing case {cid} via LLM: {str(e)}")
                # If single case fails, run offline stub as fallback
                if cid not in diagnoses:
                    concept = row["concept_tag"]
                    diag = CONCEPT_FIXES.get(concept, {}).copy()
                    diag["_offline_stub"] = True
                    diagnoses[cid] = diag
                    
        # Save back to file
        os.makedirs("data", exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(diagnoses, f, indent=2)
            
        print(f"Saved diagnoses to {output_file}")
        return diagnoses

if __name__ == "__main__":
    args = parse_args()
    cases_file = "data/cases.csv"
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Run offline if flagged, or if API key is not configured
    if args.offline or not api_key:
        if not api_key and not args.offline:
            print("Warning: ANTHROPIC_API_KEY environment variable not found. Defaulting to offline stub mode.")
        run_offline(cases_file, args.case_id)
    else:
        run_live(cases_file, api_key, args.case_id)
