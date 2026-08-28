import os
import csv

def generate():
    cases = [
        # --- VLAN CATEGORY ---
        {
            "case_id": "VLAN-001",
            "category": "VLAN",
            "symptom": "Host A (VLAN 10) cannot ping Host B (VLAN 10) across the trunk link between Switch 1 and Switch 2.",
            "topology_note": "Host A (192.168.10.5/24) is connected to Switch 1 FastEthernet 0/1. Host B (192.168.10.6/24) is connected to Switch 2 FastEthernet 0/1. Switch 1 Gi0/1 connects to Switch 2 Gi0/1.",
            "show_output": (
                "Switch1# show interfaces trunk\n"
                "Port        Mode         Encapsulation  Status        Native vlan\n"
                "Gi0/1       on           802.1q         trunking      10\n\n"
                "Switch2# show interfaces trunk\n"
                "Port        Mode         Encapsulation  Status        Native vlan\n"
                "Gi0/1       on           802.1q         trunking      99\n\n"
                "Switch1# show interface Gi0/1 switchport\n"
                "Name: Gi0/1\n"
                "Operational Mode: trunk\n"
                "Administrative Trunking Encapsulation: dot1q\n"
                "Operational Trunking Encapsulation: dot1q\n"
                "Negotiation of Trunking: On\n"
                "Access Mode VLAN: 1 (default)\n"
                "Trunking Native Mode VLAN: 10 (Finance)\n"
                "Administrative Native VLAN tagging: disabled\n"
            ),
            "expected_fault": "Native VLAN mismatch on the trunk link between Switch 1 (Native VLAN 10) and Switch 2 (Native VLAN 99).",
            "osi_layer": "Layer 2",
            "concept_tag": "native-vlan-mismatch",
            "severity": "High"
        },
        {
            "case_id": "VLAN-002",
            "category": "VLAN",
            "symptom": "Users in VLAN 20 on Switch 2 cannot reach the default gateway on Router 1.",
            "topology_note": "Switch 2 is connected to Switch 1 via trunk port Gi0/2. Switch 1 is connected to Router 1. VLAN 20 is configured on both switches.",
            "show_output": (
                "Switch2# show interfaces trunk\n"
                "Port        Mode         Encapsulation  Status        Native vlan\n"
                "Gi0/2       on           802.1q         trunking      1\n"
                "Port        Vlans allowed on trunk\n"
                "Gi0/2       1-4094\n"
                "Port        Vlans allowed and active in management domain\n"
                "Gi0/2       1,10,20\n\n"
                "Switch1# show interfaces trunk\n"
                "Port        Mode         Encapsulation  Status        Native vlan\n"
                "Gi0/2       on           802.1q         trunking      1\n"
                "Port        Vlans allowed on trunk\n"
                "Gi0/2       1,10\n"
                "Port        Vlans allowed and active in management domain\n"
                "Gi0/2       1,10\n"
            ),
            "expected_fault": "VLAN 20 is pruned/missing from the allowed VLAN list on Switch 1's trunk interface Gi0/2.",
            "osi_layer": "Layer 2",
            "concept_tag": "vlan-pruning-allowed-list",
            "severity": "High"
        },
        {
            "case_id": "VLAN-003",
            "category": "VLAN",
            "symptom": "A newly deployed PC in the HR department cannot get an IP address or ping any devices.",
            "topology_note": "PC is plugged into Switch 1 FastEthernet 0/5. The HR department uses VLAN 30 (192.168.30.0/24).",
            "show_output": (
                "Switch1# show mac address-table interface Fa0/5\n"
                "          Mac Address Table\n"
                "-------------------------------------------\n"
                "Vlan    Mac Address       Type        Ports\n"
                "----    -----------       --------    -----\n"
                "1       00e0.f711.2233    DYNAMIC     Fa0/5\n\n"
                "Switch1# show interface Fa0/5 switchport\n"
                "Name: Fa0/5\n"
                "Switchport: Enabled\n"
                "Administrative Mode: static access\n"
                "Operational Mode: static access\n"
                "Administrative Access VLAN: 1 (default)\n"
                "Operational Access VLAN: 1 (default)\n"
            ),
            "expected_fault": "Switch port Fa0/5 is assigned to the default VLAN 1 instead of the HR VLAN 30.",
            "osi_layer": "Layer 2",
            "concept_tag": "incorrect-vlan-assignment",
            "severity": "Medium"
        },
        {
            "case_id": "VLAN-004",
            "category": "VLAN",
            "symptom": "The link between Switch 1 and Switch 2 shows down/down and trunking is not operational.",
            "topology_note": "Switch 1 Gi0/2 is cabled to Switch 2 Gi0/2. They are configured for trunking.",
            "show_output": (
                "Switch1# show run interface Gi0/2\n"
                "interface GigabitEthernet0/2\n"
                " switchport trunk encapsulation dot1q\n"
                " switchport mode trunk\n"
                "!\n\n"
                "Switch2# show run interface Gi0/2\n"
                "interface GigabitEthernet0/2\n"
                " switchport trunk encapsulation isl\n"
                " switchport mode trunk\n"
                "!\n"
            ),
            "expected_fault": "Trunking encapsulation mismatch (dot1q on Switch 1 vs ISL on Switch 2) prevents trunk negotiation.",
            "osi_layer": "Layer 2",
            "concept_tag": "trunk-encapsulation-mismatch",
            "severity": "High"
        },

        # --- GATEWAY CATEGORY ---
        {
            "case_id": "GW-001",
            "category": "Gateway",
            "symptom": "Hosts experience intermittent packet loss and connection drops when trying to reach the gateway IP 192.168.1.254.",
            "topology_note": "Router 1 (R1) and Router 2 (R2) run HSRP for the default gateway 192.168.1.254 in VLAN 10.",
            "show_output": (
                "R1# show standby brief\n"
                "                     P indicates configured to preempt.\n"
                "                     |\n"
                "Interface   Grp  Pri P State    Active          Standby         Virtual IP\n"
                "Gi0/0.10    1    110 P Active   local           192.168.1.2     192.168.1.254\n\n"
                "R2# show standby brief\n"
                "                     P indicates configured to preempt.\n"
                "                     |\n"
                "Interface   Grp  Pri P State    Active          Standby         Virtual IP\n"
                "Gi0/0.10    2    100   Active   local           unknown         192.168.1.254\n"
            ),
            "expected_fault": "HSRP group ID mismatch (Group 1 on R1 vs Group 2 on R2) causes both routers to act as Active gateways.",
            "osi_layer": "Layer 3",
            "concept_tag": "hsrp-group-mismatch",
            "severity": "Critical"
        },
        {
            "case_id": "GW-002",
            "category": "Gateway",
            "symptom": "PCs in VLAN 10 cannot ping their gateway or external networks, but VLAN 20 is working fine.",
            "topology_note": "Router 1 acts as router-on-a-stick for VLAN 10 and VLAN 20 via interface Gi0/0.",
            "show_output": (
                "R1# show ip interface brief | exclude unassigned\n"
                "Interface              IP-Address      OK? Method Status                Protocol\n"
                "GigabitEthernet0/0     unassigned      YES unset  up                    up\n"
                "GigabitEthernet0/0.10  192.168.10.1    YES manual administratively down down\n"
                "GigabitEthernet0/0.20  192.168.20.1    YES manual up                    up\n"
            ),
            "expected_fault": "The subinterface GigabitEthernet0/0.10 is administratively shut down.",
            "osi_layer": "Layer 1",
            "concept_tag": "subinterface-shutdown",
            "severity": "High"
        },
        {
            "case_id": "GW-003",
            "category": "Gateway",
            "symptom": "Host C (static IP) can ping other hosts in its local subnet but cannot access any external subnets or the internet.",
            "topology_note": "Host C is configured with static IP 10.1.10.50/24. The subnet default gateway is Router 1 (10.1.10.1).",
            "show_output": (
                "HostC# ipconfig\n"
                "FastEthernet0 Connection:\n"
                "   Link-local IPv6 Address.........: fe80::2e0:f7ff:fe22:3344\n"
                "   IPv4 Address....................: 10.1.10.50\n"
                "   Subnet Mask.....................: 255.255.255.0\n"
                "   Default Gateway.................: 10.1.10.254\n\n"
                "R1# show ip interface brief\n"
                "Interface              IP-Address      OK? Method Status                Protocol\n"
                "GigabitEthernet0/1     10.1.10.1       YES manual up                    up\n"
            ),
            "expected_fault": "Host C has a mismatched default gateway (10.1.10.254) configured instead of the actual router interface (10.1.10.1).",
            "osi_layer": "Layer 3",
            "concept_tag": "gateway-ip-mismatch",
            "severity": "Medium"
        },
        {
            "case_id": "GW-004",
            "category": "Gateway",
            "symptom": "Legacy hosts using Router-Less configurations cannot communicate across subnets despite having Proxy ARP expected.",
            "topology_note": "Hosts are configured without a gateway and expect the router to reply to ARP requests for non-local IPs.",
            "show_output": (
                "R1# show ip interface Gi0/0\n"
                "GigabitEthernet0/0 is up, line protocol is up\n"
                "  Internet address is 192.168.1.1/24\n"
                "  Broadcast address is 255.255.255.255\n"
                "  Address determined by setup program\n"
                "  Helper address is not set\n"
                "  Directed broadcast forwarding is disabled\n"
                "  Proxy ARP is disabled\n"
                "  Local Proxy ARP is disabled\n"
            ),
            "expected_fault": "Proxy ARP is disabled on Router 1's GigabitEthernet0/0 interface.",
            "osi_layer": "Layer 3",
            "concept_tag": "proxy-arp-disabled",
            "severity": "Low"
        },

        # --- DHCP CATEGORY ---
        {
            "case_id": "DHCP-001",
            "category": "DHCP",
            "symptom": "PCs in VLAN 30 fail to get an IP address via DHCP and get a 169.254.x.x autoconfiguration address.",
            "topology_note": "Hosts are in VLAN 30. The DHCP Server (10.100.1.50) is in VLAN 100. Router 1 is the default gateway for VLAN 30.",
            "show_output": (
                "R1# show running-config interface Gi0/0.30\n"
                "interface GigabitEthernet0/0.30\n"
                " encapsulation dot1Q 30\n"
                " ip address 192.168.30.1 255.255.255.0\n"
                "!\n\n"
                "R1# show ip interface Gi0/0.30\n"
                "GigabitEthernet0/0.30 is up, line protocol is up\n"
                "  Internet address is 192.168.30.1/24\n"
                "  Helper address is not set\n"
            ),
            "expected_fault": "Missing DHCP helper-address (`ip helper-address 10.100.1.50`) on the router's subinterface Gi0/0.30.",
            "osi_layer": "Layer 3",
            "concept_tag": "missing-dhcp-helper",
            "severity": "High"
        },
        {
            "case_id": "DHCP-002",
            "category": "DHCP",
            "symptom": "New employees in the Finance department cannot connect to the network. Existing users are working normally.",
            "topology_note": "A router acts as the DHCP server for the Finance subnet 192.168.40.0/26 (62 usable hosts).",
            "show_output": (
                "R1# show ip dhcp pool Finance\n"
                "Pool Finance :\n"
                " Utilization mark (high/low)    : 100 / 0\n"
                " Subnet size (allocated/total)  : 62 / 62\n"
                " IP addresses                   : Current: 62  Max: 62  Excluded: 5\n"
                " Active bindings                : 57\n"
                " Expired bindings               : 0\n"
                " IP address leases              : 57\n"
            ),
            "expected_fault": "DHCP address pool utilization is at 100% (pool exhaustion). No IP addresses left to allocate.",
            "osi_layer": "Layer 3",
            "concept_tag": "dhcp-pool-exhaustion",
            "severity": "Medium"
        },
        {
            "case_id": "DHCP-003",
            "category": "DHCP",
            "symptom": "Hosts receiving DHCP addresses cannot ping their gateway, and subnets seem misconfigured.",
            "topology_note": "Router 1 is the DHCP Server for VLAN 50. Gateway is 192.168.50.1.",
            "show_output": (
                "R1# show running-config | section ip dhcp pool\n"
                "ip dhcp pool VLAN50\n"
                " network 192.168.50.0 255.255.255.128\n"
                " default-router 192.168.50.1\n\n"
                "R1# show ip interface brief | include Gi0/0.50\n"
                "GigabitEthernet0/0.50  192.168.50.1    YES manual up                    up\n"
                "R1# show running-config interface Gi0/0.50\n"
                "interface GigabitEthernet0/0.50\n"
                " encapsulation dot1Q 50\n"
                " ip address 192.168.50.1 255.255.255.0\n"
            ),
            "expected_fault": "Subnet mask mismatch in DHCP pool (configured as 255.255.255.128 /25, but the router subinterface is 255.255.255.0 /24).",
            "osi_layer": "Layer 3",
            "concept_tag": "dhcp-subnet-mask-mismatch",
            "severity": "High"
        },
        {
            "case_id": "DHCP-004",
            "category": "DHCP",
            "symptom": "Host D receives an IP but gets an IP conflict warning. Host D cannot browse internal systems.",
            "topology_note": "A file server has a static IP 192.168.1.10. The DHCP server allocates IPs on the same subnet.",
            "show_output": (
                "R1# show ip dhcp conflict\n"
                "IP Address        Detection Method   Detection Time\n"
                "192.168.1.10      Ping               Aug 28 2026 10:15 AM\n\n"
                "R1# show running-config | section ip dhcp\n"
                "ip dhcp pool Pool1\n"
                " network 192.168.1.0 255.255.255.0\n"
                " default-router 192.168.1.1\n"
                "! (Note: no excluded-address configuration found)\n"
            ),
            "expected_fault": "DHCP server allocation conflict due to missing `ip dhcp excluded-address` for statically configured servers (192.168.1.10).",
            "osi_layer": "Layer 3",
            "concept_tag": "dhcp-conflict-missing-exclusion",
            "severity": "Medium"
        },

        # --- DNS CATEGORY ---
        {
            "case_id": "DNS-001",
            "category": "DNS",
            "symptom": "Hosts can ping 8.8.8.8 but cannot open website google.com in the browser.",
            "topology_note": "Hosts are configured via DHCP. Active DNS server should be 8.8.8.8.",
            "show_output": (
                "HostA# ipconfig /all\n"
                "FastEthernet0 Connection:\n"
                "   IPv4 Address....................: 192.168.10.55\n"
                "   Subnet Mask.....................: 255.255.255.0\n"
                "   Default Gateway.................: 192.168.10.1\n"
                "   DNS Servers.....................: 192.168.10.1\n\n"
                "R1# show run | include dns-server\n"
                "   dns-server 192.168.10.250\n"
                "R1# show ip interface brief | include 192.168.10.250\n"
                "   (No interface matches IP 192.168.10.250. DNS server is unreachable/dead)\n"
            ),
            "expected_fault": "The DHCP pool advertises an unreachable/dead DNS server IP address (192.168.10.250).",
            "osi_layer": "Layer 7",
            "concept_tag": "incorrect-dns-server-ip",
            "severity": "High"
        },
        {
            "case_id": "DNS-002",
            "category": "DNS",
            "symptom": "Network administrator cannot resolve server hostnames from the router's CLI interface.",
            "topology_note": "Admin attempts to ping 'webserver.corp.local' from Router 1.",
            "show_output": (
                "R1# ping webserver.corp.local\n"
                "Translating \"webserver.corp.local\"...domain server (255.255.255.255)\n"
                "% Unrecognized host or address, or protocol not running.\n\n"
                "R1# show running-config | include domain\n"
                "no ip domain-lookup\n"
                "ip name-server 8.8.8.8\n"
            ),
            "expected_fault": "DNS resolution is globally disabled on the router via the `no ip domain-lookup` configuration.",
            "osi_layer": "Layer 7",
            "concept_tag": "dns-lookup-disabled",
            "severity": "Low"
        },
        {
            "case_id": "DNS-003",
            "category": "DNS",
            "symptom": "Users trying to reach 'intranet.local' are redirected to an old server page, or get connection timeout.",
            "topology_note": "A local DNS server handles internal DNS records.",
            "show_output": (
                "DNS_Server# show ip dns view\n"
                "DNS View: Default\n"
                " Domain Name: intranet.local\n"
                "   Type: A (IPv4 Address)\n"
                "   IP Address: 10.10.10.99  (Old IP address. Actual server IP is 10.10.10.100)\n"
            ),
            "expected_fault": "Stale/incorrect DNS A record mapping for 'intranet.local' on the local DNS server.",
            "osi_layer": "Layer 7",
            "concept_tag": "stale-dns-a-record",
            "severity": "Medium"
        },
        {
            "case_id": "DNS-004",
            "category": "DNS",
            "symptom": "Internal hosts can resolve external websites but cannot resolve intranet resources.",
            "topology_note": "Local DNS Server is 192.168.1.5. External forwarder should be active.",
            "show_output": (
                "HostA# nslookup intranet.corp\n"
                "Server: LocalDNS\n"
                "Address: 192.168.1.5\n"
                "*** LocalDNS can't find intranet.corp: Non-existent domain\n\n"
                "DNS_Server# show ip dns view\n"
                "   (No zone or record loaded for domain corp or intranet.corp)\n"
            ),
            "expected_fault": "DNS Zone configuration error: The DNS server does not host the local domain zone record.",
            "osi_layer": "Layer 7",
            "concept_tag": "missing-dns-zone",
            "severity": "Medium"
        },

        # --- ROUTING CATEGORY ---
        {
            "case_id": "RT-001",
            "category": "Routing",
            "symptom": "Router 1 and Router 2 fail to form an OSPF neighbor adjacency. No routes are exchanged.",
            "topology_note": "R1 Gi0/1 (10.1.12.1/30) is cabled to R2 Gi0/1 (10.1.12.2/30). OSPF process 1 is active on both.",
            "show_output": (
                "R1# show ip ospf neighbor\n"
                "   (Output is empty)\n\n"
                "R1# show ip ospf interface Gi0/1\n"
                "GigabitEthernet0/1 is up, line protocol is up\n"
                "  Internet Address 10.1.12.1/30, Area 0\n"
                "  Process ID 1, Router ID 1.1.1.1, Network Type BROADCAST, Cost: 1\n"
                "  Timer intervals configured, Hello 10, Dead 40, Wait 40, Retransmit 5\n\n"
                "R2# show ip ospf interface Gi0/1\n"
                "GigabitEthernet0/1 is up, line protocol is up\n"
                "  Internet Address 10.1.12.2/30, Area 10\n"
                "  Process ID 1, Router ID 2.2.2.2, Network Type BROADCAST, Cost: 1\n"
                "  Timer intervals configured, Hello 10, Dead 40, Wait 40, Retransmit 5\n"
            ),
            "expected_fault": "OSPF Area mismatch (Area 0 on R1 vs Area 10 on R2) prevents forming a neighbor adjacency.",
            "osi_layer": "Layer 3",
            "concept_tag": "ospf-area-mismatch",
            "severity": "High"
        },
        {
            "case_id": "RT-002",
            "category": "Routing",
            "symptom": "Branch office LAN cannot reach the HQ LAN, but can ping the headquarters gateway router public IP.",
            "topology_note": "Branch LAN (192.168.10.0/24) connected to BranchRouter. HQ LAN (10.0.0.0/8) connected to HQRouter.",
            "show_output": (
                "BranchRouter# show ip route static\n"
                "Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP\n"
                "Gateway of last resort is not set\n"
                "S    172.16.1.0/24 [1/0] via 203.0.113.2\n"
                "  (No route to HQ subnet 10.0.0.0/8 exists)\n"
            ),
            "expected_fault": "Missing static route to the remote HQ network (10.0.0.0/8) on the Branch Router.",
            "osi_layer": "Layer 3",
            "concept_tag": "missing-static-route",
            "severity": "High"
        },
        {
            "case_id": "RT-003",
            "category": "Routing",
            "symptom": "OSPF neighbor adjacency is stuck in EXSTART/EXCHANGE state and never transitions to FULL.",
            "topology_note": "R1 and R2 are cabled over a WAN link. Layer 2 is working.",
            "show_output": (
                "R1# show ip ospf neighbor\n"
                "Neighbor ID     Pri   State           Dead Time   Address         Interface\n"
                "2.2.2.2           1   EXSTART/  -     00:00:34    192.168.12.2    Gi0/1\n\n"
                "R1# show ip interface Gi0/1 | include MTU\n"
                "  MTU is 1500 bytes\n\n"
                "R2# show ip interface Gi0/1 | include MTU\n"
                "  MTU is 1450 bytes\n"
            ),
            "expected_fault": "Interface MTU mismatch (1500 bytes on R1 vs 1450 bytes on R2) prevents OSPF database exchange completion.",
            "osi_layer": "Layer 3",
            "concept_tag": "ospf-mtu-mismatch",
            "severity": "High"
        },
        {
            "case_id": "RT-004",
            "category": "Routing",
            "symptom": "Routing loop occurs between R1 and R2; traceroute bounces back and forth indefinitely.",
            "topology_note": "Both routers have static routes pointing to each other for specific subnets.",
            "show_output": (
                "R1# show ip route 10.200.1.0\n"
                "Routing entry for 10.200.1.0/24\n"
                "  Known via \"static\", distance 1, metric 0\n"
                "  Routing Descriptor Blocks:\n"
                "  * 192.168.12.2, via GigabitEthernet0/0\n\n"
                "R2# show ip route 10.200.1.0\n"
                "Routing entry for 10.200.1.0/24\n"
                "  Known via \"static\", distance 1, metric 0\n"
                "  Routing Descriptor Blocks:\n"
                "  * 192.168.12.1, via GigabitEthernet0/0\n"
            ),
            "expected_fault": "Routing loop caused by mutually recursive static routes pointing back and forth between R1 and R2.",
            "osi_layer": "Layer 3",
            "concept_tag": "routing-loop-static",
            "severity": "Critical"
        },

        # --- ACL CATEGORY ---
        {
            "case_id": "ACL-001",
            "category": "ACL",
            "symptom": "Web developer cannot access the HTTPS page on Server 1, but normal HTTP access works fine.",
            "topology_note": "Router 1 has an inbound Access Control List applied on GigabitEthernet0/0.",
            "show_output": (
                "R1# show access-lists\n"
                "Extended IP access list BLOCK_WEB\n"
                "    10 deny tcp any any eq 443\n"
                "    20 permit tcp any any eq 80\n"
                "    30 permit ip any any\n\n"
                "R1# show running-config interface Gi0/0\n"
                "interface GigabitEthernet0/0\n"
                " ip address 192.168.1.1 255.255.255.0\n"
                " ip access-group BLOCK_WEB in\n"
            ),
            "expected_fault": "ACL rule (sequence 10) explicitly denies HTTPS (port 443) traffic.",
            "osi_layer": "Layer 4",
            "concept_tag": "acl-blocking-needed-port",
            "severity": "High"
        },
        {
            "case_id": "ACL-002",
            "category": "ACL",
            "symptom": "Network administrators are locked out of SSH access to the router, despite physical links being up.",
            "topology_note": "VTY lines are secured with an access class.",
            "show_output": (
                "R1# show running-config | section line vty\n"
                "line vty 0 4\n"
                " access-class ADMIN_ONLY in\n"
                " transport input ssh\n\n"
                "R1# show access-lists ADMIN_ONLY\n"
                "Standard IP access list ADMIN_ONLY\n"
                "    10 permit 10.99.1.0 0.0.0.255\n"
                "    (Implicit deny active. Admin is connecting from IP 192.168.1.50)\n"
            ),
            "expected_fault": "The implicit deny of the VTY access-class ACL blocks admin connections coming from the management host subnet (192.168.1.50).",
            "osi_layer": "Layer 4",
            "concept_tag": "vty-acl-implicit-deny",
            "severity": "Critical"
        },
        {
            "case_id": "ACL-003",
            "category": "ACL",
            "symptom": "All inbound traffic to the DMZ servers is blocked, even though rules look correct.",
            "topology_note": "Access list is applied to Router 1 Gi0/1 interface.",
            "show_output": (
                "R1# show access-lists DMZ_INBOUND\n"
                "Extended IP access list DMZ_INBOUND\n"
                "    10 permit tcp any host 172.16.10.10 eq 80\n"
                "    20 permit tcp any host 172.16.10.10 eq 443\n\n"
                "R1# show running-config interface Gi0/1\n"
                "interface GigabitEthernet0/1\n"
                " ip address 172.16.10.1 255.255.255.0\n"
                " ip access-group DMZ_INBOUND out\n"
                "   (Note: ACL applied OUTBOUND on LAN-facing interface instead of INBOUND on WAN interface)\n"
            ),
            "expected_fault": "ACL direction error: ACL is applied outbound blocking return traffic/packets exiting the router interface to DMZ.",
            "osi_layer": "Layer 4",
            "concept_tag": "acl-wrong-direction",
            "severity": "High"
        },
        {
            "case_id": "ACL-004",
            "category": "ACL",
            "symptom": "Traffic from Host A is completely blocked, even though there's a permit rule for its subnet.",
            "topology_note": "An ACL is applied on the core switch or router interface.",
            "show_output": (
                "R1# show access-lists FILTER\n"
                "Extended IP access list FILTER\n"
                "    10 deny ip 192.168.10.0 0.0.0.255 any\n"
                "    20 permit ip 192.168.10.50 0.0.0.0 any (Host A is 192.168.10.50)\n"
            ),
            "expected_fault": "ACL rule order error: The deny statement for the entire subnet (192.168.10.0/24) precedes the specific permit statement for Host A (192.168.10.50).",
            "osi_layer": "Layer 4",
            "concept_tag": "acl-rule-order",
            "severity": "Medium"
        },

        # --- NAT CATEGORY ---
        {
            "case_id": "NAT-001",
            "category": "NAT",
            "symptom": "Hosts inside the office cannot browse the internet, and no NAT translations are seen.",
            "topology_note": "Router 1 is the NAT border router. LAN interface is Gi0/0, WAN interface is Serial0/0/0.",
            "show_output": (
                "R1# show ip nat translations\n"
                "   (Output is empty)\n\n"
                "R1# show running-config interface Gi0/0\n"
                "interface GigabitEthernet0/0\n"
                " ip address 192.168.1.1 255.255.255.0\n"
                " ip nat outside\n\n"
                "R1# show running-config interface Serial0/0/0\n"
                "interface Serial0/0/0\n"
                " ip address 203.0.113.1 255.255.255.252\n"
                " ip nat inside\n"
            ),
            "expected_fault": "NAT inside/outside interface designations are swapped (Gi0/0 is configured as outside, Serial0/0/0 as inside).",
            "osi_layer": "Layer 3",
            "concept_tag": "nat-interfaces-swapped",
            "severity": "High"
        },
        {
            "case_id": "NAT-002",
            "category": "NAT",
            "symptom": "Only the first user to access the web gets through. All other users fail to load pages.",
            "topology_note": "A single public IP is bound to the WAN interface. PAT (NAT Overload) should be configured.",
            "show_output": (
                "R1# show running-config | include ip nat\n"
                "ip nat inside source list 1 interface GigabitEthernet0/1\n"
                "  (Note: the word 'overload' is missing at the end of the command)\n\n"
                "R1# show ip nat translations\n"
                "Pro Inside global      Inside local       Outside local      Outside global\n"
                "--- 203.0.113.1        192.168.1.5        ---                ---\n"
            ),
            "expected_fault": "Missing 'overload' keyword in the NAT configuration statement, preventing Port Address Translation (PAT).",
            "osi_layer": "Layer 3",
            "concept_tag": "missing-nat-overload",
            "severity": "Critical"
        },
        {
            "case_id": "NAT-003",
            "category": "NAT",
            "symptom": "Devices in the Sales department can access the web, but Marketing department devices fail to connect.",
            "topology_note": "Sales subnet is 192.168.10.0/24. Marketing subnet is 192.168.20.0/24.",
            "show_output": (
                "R1# show running-config | include ip nat inside source\n"
                "ip nat inside source list NAT_ACL interface Gi0/1 overload\n\n"
                "R1# show access-lists NAT_ACL\n"
                "Standard IP access list NAT_ACL\n"
                "    10 permit 192.168.10.0 0.0.0.255\n"
                "    (No rule exists for Marketing subnet 192.168.20.0/24)\n"
            ),
            "expected_fault": "The NAT access control list (NAT_ACL) does not permit/include the Marketing department subnet (192.168.20.0/24).",
            "osi_layer": "Layer 3",
            "concept_tag": "nat-acl-missing-subnet",
            "severity": "High"
        },
        {
            "case_id": "NAT-004",
            "category": "NAT",
            "symptom": "Static NAT mapping does not work for the internal web server. External users get connection refused.",
            "topology_note": "Web server static IP is 192.168.1.10. Public IP is 203.0.113.10.",
            "show_output": (
                "R1# show running-config | include ip nat\n"
                "ip nat inside source static 192.168.1.100 203.0.113.10\n\n"
                "R1# show ip interface brief | include 192.168.1.\n"
                "  (Actual web server is configured with 192.168.1.10, not 192.168.1.100)\n"
            ),
            "expected_fault": "Static NAT configuration error: Mismatched host IP (mapped 192.168.1.100 instead of server's actual IP 192.168.1.10).",
            "osi_layer": "Layer 3",
            "concept_tag": "static-nat-wrong-ip",
            "severity": "Medium"
        },

        # --- WIRELESS CATEGORY ---
        {
            "case_id": "WLAN-001",
            "category": "Wireless",
            "symptom": "Smartphones and laptops fail to connect to the 'Office-WiFi' SSID. Shows 'Authentication failed' error.",
            "topology_note": "The SSID is configured with WPA2-Personal security on a standalone Access Point.",
            "show_output": (
                "AP# show dot11 ssid Office-WiFi\n"
                "SSID: Office-WiFi\n"
                "VLAN: 10\n"
                "Security: WPA2-PSK\n"
                "Pre-Shared Key: CompPass123!   (Admin note: AP configured key is CompPass123!)\n\n"
                "Host_Device# show wireless profile\n"
                "SSID: Office-WiFi\n"
                "Security: WPA2-PSK\n"
                "Pre-Shared Key: CompPass123    (User typed key is missing exclamation mark)\n"
            ),
            "expected_fault": "WPA2 Pre-Shared Key (PSK) password mismatch on client configuration.",
            "osi_layer": "Layer 2",
            "concept_tag": "wifi-psk-mismatch",
            "severity": "High"
        },
        {
            "case_id": "WLAN-002",
            "category": "Wireless",
            "symptom": "Laptops scan for networks but cannot find the 'Guest-WiFi' network in the list.",
            "topology_note": "A corporate lightweight AP is configured for Guest Wi-Fi access.",
            "show_output": (
                "WLC# show wlan 2\n"
                "WLAN ID.......................................... 2\n"
                "Profile Name..................................... Guest-WiFi\n"
                "Network Name (SSID).............................. Guest-WiFi\n"
                "Status........................................... Enabled\n"
                "Broadcast SSID................................... Disabled\n"
            ),
            "expected_fault": "SSID broadcasting is disabled on the WLC for the Guest-WiFi profile.",
            "osi_layer": "Layer 2",
            "concept_tag": "ssid-broadcast-disabled",
            "severity": "Medium"
        },
        {
            "case_id": "WLAN-003",
            "category": "Wireless",
            "symptom": "Wireless users connect to AP but get an IP address from VLAN 1 (Management) instead of VLAN 80 (Wireless Users).",
            "topology_note": "The AP port is connected to Switch 1 interface FastEthernet 0/12. VLAN 80 is configured on the network.",
            "show_output": (
                "Switch1# show interface Fa0/12 switchport\n"
                "Name: Fa0/12\n"
                "Switchport: Enabled\n"
                "Administrative Mode: static access\n"
                "Operational Mode: static access\n"
                "Administrative Access VLAN: 1 (default)\n"
                "Operational Access VLAN: 1 (default)\n"
            ),
            "expected_fault": "Switch access port Fa0/12 connected to the AP is assigned to VLAN 1 instead of being configured as a trunk port to pass VLAN 80.",
            "osi_layer": "Layer 2",
            "concept_tag": "ap-switchport-access-vlan",
            "severity": "High"
        },
        {
            "case_id": "WLAN-004",
            "category": "Wireless",
            "symptom": "Wireless clients connect to AP and get IP address, but cannot ping the local gateway.",
            "topology_note": "Wireless LAN Router handles local dhcp and gateway.",
            "show_output": (
                "Wireless_Router# show ip interface brief\n"
                "Interface              IP-Address      OK? Method Status                Protocol\n"
                "Vlan80                 192.168.80.1    YES manual down                  down\n"
                "FastEthernet0/1        unassigned      YES unset  up                    up\n"
            ),
            "expected_fault": "The gateway SVl interface Vlan80 on the wireless router/switch is down.",
            "osi_layer": "Layer 1",
            "concept_tag": "wireless-gateway-interface-down",
            "severity": "High"
        }
    ]

    # Fill up to 32 cases. We have 4 per category, 8 categories. Total 32. Let's make sure.
    assert len(cases) == 32, f"Expected 32 cases, got {len(cases)}"

    # Ensure directories exist
    os.makedirs("data", exist_ok=True)

    # Write to cases.csv
    csv_file = "data/cases.csv"
    fieldnames = ["case_id", "category", "symptom", "topology_note", "show_output", "expected_fault", "osi_layer", "concept_tag", "severity"]
    
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow(case)
            
    print(f"Successfully generated {len(cases)} cases at {csv_file}")

if __name__ == "__main__":
    generate()
