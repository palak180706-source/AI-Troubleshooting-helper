import json
import ipaddress

def check_duplicate_ips(state):
    findings = []
    ip_to_devices = {}
    
    for dev_name, dev_info in state.get("devices", {}).items():
        for intf_name, intf_info in dev_info.get("interfaces", {}).items():
            ip = intf_info.get("ip_address")
            if ip and ip != "unassigned":
                # Clean IP (remove subnet notation if present)
                clean_ip = ip.split("/")[0].strip()
                if clean_ip not in ip_to_devices:
                    ip_to_devices[clean_ip] = []
                ip_to_devices[clean_ip].append((dev_name, intf_name))
                
    for ip, locs in ip_to_devices.items():
        if len(locs) > 1:
            devices_str = ", ".join([f"{dev} ({intf})" for dev, intf in locs])
            findings.append({
                "check": "duplicate_ip",
                "severity": "Critical",
                "detail": f"Duplicate IP address '{ip}' configured on multiple interfaces: {devices_str}",
                "devices": [dev for dev, _ in locs]
            })
            
    return findings

def check_wrong_masks(state):
    findings = []
    interfaces_with_ip = []
    
    for dev_name, dev_info in state.get("devices", {}).items():
        for intf_name, intf_info in dev_info.get("interfaces", {}).items():
            ip = intf_info.get("ip_address")
            mask = intf_info.get("subnet_mask")
            if ip and mask and ip != "unassigned" and mask != "unassigned":
                try:
                    if "/" in ip:
                        ip_val = ip.split("/")[0]
                    else:
                        ip_val = ip
                    # Check if subnet mask is valid
                    ipaddress.IPv4Network(f"0.0.0.0/{mask}")
                    iface = ipaddress.IPv4Interface(f"{ip_val}/{mask}")
                    interfaces_with_ip.append({
                        "device": dev_name,
                        "interface": intf_name,
                        "ip": ip_val,
                        "mask": mask,
                        "iface_obj": iface
                    })
                except Exception as e:
                    findings.append({
                        "check": "wrong_mask",
                        "severity": "High",
                        "detail": f"Invalid subnet mask '{mask}' on {dev_name} {intf_name}: {str(e)}",
                        "devices": [dev_name]
                    })
                    
    # Compare each pair of interfaces to check if they overlap but have different masks
    for i in range(len(interfaces_with_ip)):
        for j in range(i + 1, len(interfaces_with_ip)):
            if1 = interfaces_with_ip[i]
            if2 = interfaces_with_ip[j]
            
            # Check if they are in overlapping/same subnets
            # We can define them as sharing the same network if their networks overlap
            net1 = if1["iface_obj"].network
            net2 = if2["iface_obj"].network
            
            if net1.overlaps(net2):
                if if1["mask"] != if2["mask"]:
                    findings.append({
                        "check": "wrong_mask",
                        "severity": "High",
                        "detail": (
                            f"Subnet mask mismatch on overlapping subnet. "
                            f"{if1['device']} {if1['interface']} has {if1['ip']}/{if1['mask']} "
                            f"but {if2['device']} {if2['interface']} has {if2['ip']}/{if2['mask']}."
                        ),
                        "devices": [if1["device"], if2["device"]]
                    })
                    
    return findings

def check_gateway_mismatch(state):
    findings = []
    # Collect all configured IPs on all devices to verify gateway existence
    all_ips = set()
    for dev_name, dev_info in state.get("devices", {}).items():
        for intf_name, intf_info in dev_info.get("interfaces", {}).items():
            ip = intf_info.get("ip_address")
            if ip and ip != "unassigned":
                all_ips.add(ip.split("/")[0].strip())
                
    for dev_name, dev_info in state.get("devices", {}).items():
        # Check only hosts or devices configured with a default gateway
        for intf_name, intf_info in dev_info.get("interfaces", {}).items():
            gateway = intf_info.get("gateway")
            ip = intf_info.get("ip_address")
            mask = intf_info.get("subnet_mask")
            
            if gateway and gateway != "unassigned":
                # Check if gateway is in same subnet
                if ip and mask and ip != "unassigned" and mask != "unassigned":
                    try:
                        iface = ipaddress.IPv4Interface(f"{ip}/{mask}")
                        gw_ip = ipaddress.IPv4Address(gateway)
                        if gw_ip not in iface.network:
                            findings.append({
                                "check": "gateway_mismatch",
                                "severity": "High",
                                "detail": (
                                    f"Default gateway '{gateway}' on {dev_name} {intf_name} "
                                    f"is not in the configured subnet {iface.network} (IP: {ip}/{mask})."
                                ),
                                "devices": [dev_name]
                            })
                    except Exception as e:
                        # Mask error is handled elsewhere
                        pass
                
                # Check if gateway IP exists in the network state
                if gateway not in all_ips:
                    findings.append({
                        "check": "gateway_mismatch",
                        "severity": "Medium",
                        "detail": (
                            f"Default gateway '{gateway}' on {dev_name} {intf_name} "
                            f"does not correspond to any active interface IP in the network state."
                        ),
                        "devices": [dev_name]
                    })
                    
    return findings

def check_interface_down(state):
    findings = []
    for dev_name, dev_info in state.get("devices", {}).items():
        for intf_name, intf_info in dev_info.get("interfaces", {}).items():
            status = intf_info.get("status", "up").lower()
            protocol = intf_info.get("protocol", "up").lower()
            
            if "down" in status or "down" in protocol:
                severity = "High" if dev_info.get("type") == "router" else "Medium"
                findings.append({
                    "check": "interface_down",
                    "severity": severity,
                    "detail": f"Interface {dev_name} {intf_name} is down/down. Status: '{status}', Protocol: '{protocol}'.",
                    "devices": [dev_name]
                })
    return findings

def check_missing_vlan(state):
    findings = []
    for dev_name, dev_info in state.get("devices", {}).items():
        if dev_info.get("type") == "switch":
            vlans = dev_info.get("vlans", [])
            # Make sure it's a list of ints
            vlans = [int(v) for v in vlans]
            for intf_name, intf_info in dev_info.get("interfaces", {}).items():
                mode = intf_info.get("mode", "access")
                if mode == "access":
                    vlan_assigned = intf_info.get("access_vlan")
                    if vlan_assigned is not None:
                        vlan_val = int(vlan_assigned)
                        if vlan_val not in vlans:
                            findings.append({
                                "check": "missing_vlan",
                                "severity": "High",
                                "detail": (
                                    f"Switchport {dev_name} {intf_name} is assigned to VLAN {vlan_val}, "
                                    f"but VLAN {vlan_val} is missing from the switch's VLAN database ({vlans})."
                                ),
                                "devices": [dev_name]
                            })
    return findings

def check_missing_route(state):
    findings = []
    expected_routes = state.get("expected_routes", [])
    
    for req in expected_routes:
        router_name = req.get("router")
        target_net = req.get("network")
        
        if not router_name or not target_net:
            continue
            
        router_info = state.get("devices", {}).get(router_name)
        if not router_info:
            continue
            
        routes = router_info.get("routes", [])
        
        try:
            target_net_obj = ipaddress.IPv4Network(target_net)
            
            # Check if there is a route that matches or encompasses the target network
            has_route = False
            for route in routes:
                dest = route.get("destination")
                if not dest:
                    continue
                try:
                    if dest == "0.0.0.0/0":
                        has_route = True
                        break
                    dest_net_obj = ipaddress.IPv4Network(dest)
                    # A route matches if it is equal or if it's a supernet of the target
                    if dest_net_obj == target_net_obj or target_net_obj.subnet_of(dest_net_obj):
                        has_route = True
                        break
                except Exception:
                    pass
                    
            if not has_route:
                findings.append({
                    "check": "missing_route",
                    "severity": "High",
                    "detail": f"Router {router_name} is missing a route to expected network {target_net} (and has no default route).",
                    "devices": [router_name]
                })
        except Exception as e:
            findings.append({
                "check": "missing_route",
                "severity": "Medium",
                "detail": f"Error parsing expected route network '{target_net}': {str(e)}",
                "devices": [router_name]
            })
            
    return findings

def run_all_checks(state_json_or_dict):
    if isinstance(state_json_or_dict, str):
        try:
            state = json.loads(state_json_or_dict)
        except Exception as e:
            return [{
                "check": "json_parse_error",
                "severity": "Critical",
                "detail": f"Failed to parse network state JSON: {str(e)}",
                "devices": []
            }]
    else:
        state = state_json_or_dict
        
    findings = []
    findings.extend(check_duplicate_ips(state))
    findings.extend(check_wrong_masks(state))
    findings.extend(check_gateway_mismatch(state))
    findings.extend(check_interface_down(state))
    findings.extend(check_missing_vlan(state))
    findings.extend(check_missing_route(state))
    
    return findings

if __name__ == "__main__":
    # Test execution
    import sys
    state_path = "data/sample_network_state.json"
    if len(sys.argv) > 1:
        state_path = sys.argv[1]
        
    try:
        with open(state_path, "r") as f:
            state_data = json.load(f)
        findings = run_all_checks(state_data)
        print(f"Deterministic Rule Checker execution on {state_path}:")
        print(json.dumps(findings, indent=2))
    except Exception as e:
        print(f"Error running rule checker: {str(e)}")
