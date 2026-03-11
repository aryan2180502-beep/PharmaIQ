import unittest
from mcp_servers.iot_mcp import get_temperature, trigger_alert
from mcp_servers.erp_mcp import get_inventory, raise_po
from mcp_servers.idsp_mcp import get_disease_signals
from mcp_servers.inventory_mcp import get_expiry_risk_items

class TestPharmaIQ_MCP(unittest.TestCase):

    def test_iot_mcp(self):
        # Test basic temp retrieval
        res = get_temperature(1)
        self.assertIn("temperature", res)
        self.assertIsInstance(res["temperature"], (int, float))
        
        # Test alert trigger
        res = trigger_alert(1, "Test Alert")
        self.assertEqual(res["status"], "success")

    def test_erp_mcp(self):
        # Test inventory retrieval
        res = get_inventory(1)
        self.assertIsInstance(res, list)
        
        # Test PO placement
        res = raise_po(1, "SKU-001", 50, agent="TEST_AGENT")
        self.assertEqual(res["status"], "success")

    def test_idsp_mcp(self):
        # Test signals retrieval
        res = get_disease_signals("Mumbai")
        self.assertIsInstance(res, list)

    def test_inventory_mcp(self):
        # Test expiry risk scanning
        res = get_expiry_risk_items(days_threshold=90)
        self.assertIsInstance(res, list)

if __name__ == "__main__":
    unittest.main()
