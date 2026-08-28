import pytest
from src.rule_checker import (
    check_duplicate_ips,
    check_wrong_masks,
    check_gateway_mismatch,
    check_interface_down,
    check_missing_vlan,
    check_missing_route
)

# Test duplicate IP
def test_duplicate_ip_positive():
    # Seeding duplicate IP issue
    state = {
        "devices": {
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"}}},
            "HostB": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"}}}
        }
    }
    findings = check_duplicate_ips(state)
    assert len(findings) == 1
    assert findings[0]["check"] == "duplicate_ip"
    assert "HostA" in findings[0]["devices"]
    assert "HostB" in findings[0]["devices"]

def test_duplicate_ip_negative():
    # Healthy IP assignment
    state = {
        "devices": {
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"}}},
            "HostB": {"interfaces": {"Fa0": {"ip_address": "192.168.1.11", "subnet_mask": "255.255.255.0"}}}
        }
    }
    findings = check_duplicate_ips(state)
    assert len(findings) == 0

# Test wrong masks
def test_wrong_masks_positive():
    # Subnet mask mismatch on overlapping subnet
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}}},
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.128"}}}
        }
    }
    findings = check_wrong_masks(state)
    assert len(findings) == 1
    assert findings[0]["check"] == "wrong_mask"

def test_wrong_masks_negative():
    # Matching masks
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}}},
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0"}}}
        }
    }
    findings = check_wrong_masks(state)
    assert len(findings) == 0

# Test gateway mismatch
def test_gateway_mismatch_positive():
    # Host gateway does not match host subnet
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}}},
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0", "gateway": "192.168.2.1"}}}
        }
    }
    findings = check_gateway_mismatch(state)
    assert len(findings) >= 1
    assert any(f["check"] == "gateway_mismatch" for f in findings)

def test_gateway_mismatch_negative():
    # Host gateway matches router interface in local subnet
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}}},
            "HostA": {"interfaces": {"Fa0": {"ip_address": "192.168.1.10", "subnet_mask": "255.255.255.0", "gateway": "192.168.1.1"}}}
        }
    }
    findings = check_gateway_mismatch(state)
    # Filter only mismatch checks
    mismatch_findings = [f for f in findings if f["check"] == "gateway_mismatch"]
    assert len(mismatch_findings) == 0

# Test interface down
def test_interface_down_positive():
    # Interface is shut down
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0", "status": "administratively down", "protocol": "down"}}}
        }
    }
    findings = check_interface_down(state)
    assert len(findings) == 1
    assert findings[0]["check"] == "interface_down"

def test_interface_down_negative():
    # Interface is up
    state = {
        "devices": {
            "R1": {"interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0", "status": "up", "protocol": "up"}}}
        }
    }
    findings = check_interface_down(state)
    assert len(findings) == 0

# Test missing VLAN
def test_missing_vlan_positive():
    # Switch port VLAN not in switch VLAN list
    state = {
        "devices": {
            "SW1": {
                "type": "switch",
                "vlans": [1, 10],
                "interfaces": {
                    "Fa0/1": {"mode": "access", "access_vlan": 99}
                }
            }
        }
    }
    findings = check_missing_vlan(state)
    assert len(findings) == 1
    assert findings[0]["check"] == "missing_vlan"

def test_missing_vlan_negative():
    # Switch port VLAN is in switch VLAN list
    state = {
        "devices": {
            "SW1": {
                "type": "switch",
                "vlans": [1, 10, 99],
                "interfaces": {
                    "Fa0/1": {"mode": "access", "access_vlan": 99}
                }
            }
        }
    }
    findings = check_missing_vlan(state)
    assert len(findings) == 0

# Test missing route
def test_missing_route_positive():
    # Router missing static route to expected subnet
    state = {
        "devices": {
            "R1": {
                "type": "router",
                "interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}},
                "routes": [
                    {"destination": "192.168.1.0/24", "type": "connected"}
                ]
            }
        },
        "expected_routes": [
            {"router": "R1", "network": "10.0.0.0/24"}
        ]
    }
    findings = check_missing_route(state)
    assert len(findings) == 1
    assert findings[0]["check"] == "missing_route"

def test_missing_route_negative():
    # Router has static route or default route covering destination
    state = {
        "devices": {
            "R1": {
                "type": "router",
                "interfaces": {"Gi0/0": {"ip_address": "192.168.1.1", "subnet_mask": "255.255.255.0"}},
                "routes": [
                    {"destination": "192.168.1.0/24", "type": "connected"},
                    {"destination": "10.0.0.0/8", "type": "static"} # Covers 10.0.0.0/24
                ]
            }
        },
        "expected_routes": [
            {"router": "R1", "network": "10.0.0.0/24"}
        ]
    }
    findings = check_missing_route(state)
    assert len(findings) == 0
