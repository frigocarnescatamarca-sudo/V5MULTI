#!/usr/bin/env python3
"""
Backend API Testing for Estonia Cobertura Colaborativa
Tests admin panel, agent system, and document viewer functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://cobertura-express.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "Estonia2025!"}

class TestRunner:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.created_agent_id = None
        self.created_premio_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_admin_login(self):
        """Test admin login functionality"""
        try:
            response = requests.post(f"{BACKEND_URL}/admin/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.admin_token = data["token"]
                    self.log_result("Admin Login", True, "Admin login successful")
                    return True
                else:
                    self.log_result("Admin Login", False, "Login response missing token", data)
                    return False
            else:
                self.log_result("Admin Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_create_agent(self):
        """Test creating a new agent"""
        if not self.admin_token:
            self.log_result("Create Agent", False, "No admin token available")
            return False
            
        agent_data = {
            "nombre": "Agente Test",
            "email": "agente@test.com", 
            "telefono": "1122334455",
            "username": "agentetest",
            "password": "test123",
            "comision_porcentaje": 15,
            "activo": True
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/admin/agentes", json=agent_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("agente"):
                    self.created_agent_id = data["agente"]["id"]
                    self.log_result("Create Agent", True, f"Agent created with ID: {self.created_agent_id}")
                    return True
                else:
                    self.log_result("Create Agent", False, "Response missing success/agente", data)
                    return False
            else:
                self.log_result("Create Agent", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Agent", False, f"Exception: {str(e)}")
            return False
    
    def test_list_agents(self):
        """Test listing agents"""
        try:
            response = requests.get(f"{BACKEND_URL}/admin/agentes")
            
            if response.status_code == 200:
                data = response.json()
                if "agentes" in data:
                    agents = data["agentes"]
                    # Check if our created agent is in the list
                    found_agent = None
                    for agent in agents:
                        if agent.get("username") == "agentetest":
                            found_agent = agent
                            break
                    
                    if found_agent:
                        self.log_result("List Agents", True, f"Found {len(agents)} agents, including created test agent")
                        return True
                    else:
                        self.log_result("List Agents", False, f"Created agent not found in list of {len(agents)} agents")
                        return False
                else:
                    self.log_result("List Agents", False, "Response missing 'agentes' field", data)
                    return False
            else:
                self.log_result("List Agents", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List Agents", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_login(self):
        """Test agent login with created agent"""
        agent_credentials = {"username": "agentetest", "password": "test123"}
        
        try:
            response = requests.post(f"{BACKEND_URL}/agente/login", json=agent_credentials)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("token"):
                    self.agent_token = data["token"]
                    agent_info = data.get("agente", {})
                    self.log_result("Agent Login", True, f"Agent login successful for {agent_info.get('nombre', 'Unknown')}")
                    return True
                else:
                    self.log_result("Agent Login", False, "Login response missing token", data)
                    return False
            else:
                self.log_result("Agent Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Agent Login", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_dashboard(self):
        """Test agent dashboard data retrieval"""
        if not self.agent_token:
            self.log_result("Agent Dashboard", False, "No agent token available")
            return False
            
        try:
            response = requests.get(f"{BACKEND_URL}/agente/mis-seguros", params={"token": self.agent_token})
            
            if response.status_code == 200:
                data = response.json()
                if "seguros" in data and "estadisticas" in data:
                    stats = data["estadisticas"]
                    self.log_result("Agent Dashboard", True, 
                                  f"Dashboard loaded - Total seguros: {stats.get('total_seguros', 0)}, "
                                  f"Pagados: {stats.get('seguros_pagados', 0)}")
                    return True
                else:
                    self.log_result("Agent Dashboard", False, "Response missing seguros/estadisticas", data)
                    return False
            else:
                self.log_result("Agent Dashboard", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Agent Dashboard", False, f"Exception: {str(e)}")
            return False
    
    def test_create_premio(self):
        """Test creating a new premio"""
        if not self.admin_token:
            self.log_result("Create Premio", False, "No admin token available")
            return False
            
        premio_data = {
            "nombre": "Premio 10 Ventas",
            "cantidad_seguros": 10,
            "monto_premio": 5000,
            "activo": True
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/admin/premios", json=premio_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("premio"):
                    self.created_premio_id = data["premio"]["id"]
                    self.log_result("Create Premio", True, f"Premio created with ID: {self.created_premio_id}")
                    return True
                else:
                    self.log_result("Create Premio", False, "Response missing success/premio", data)
                    return False
            else:
                self.log_result("Create Premio", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Create Premio", False, f"Exception: {str(e)}")
            return False
    
    def test_list_premios(self):
        """Test listing premios"""
        try:
            response = requests.get(f"{BACKEND_URL}/admin/premios")
            
            if response.status_code == 200:
                data = response.json()
                if "premios" in data:
                    premios = data["premios"]
                    # Check if our created premio is in the list
                    found_premio = None
                    for premio in premios:
                        if premio.get("nombre") == "Premio 10 Ventas":
                            found_premio = premio
                            break
                    
                    if found_premio:
                        self.log_result("List Premios", True, f"Found {len(premios)} premios, including created test premio")
                        return True
                    else:
                        self.log_result("List Premios", False, f"Created premio not found in list of {len(premios)} premios")
                        return False
                else:
                    self.log_result("List Premios", False, "Response missing 'premios' field", data)
                    return False
            else:
                self.log_result("List Premios", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("List Premios", False, f"Exception: {str(e)}")
            return False
    
    def test_agent_vencimientos(self):
        """Test agent vencimientos endpoint"""
        if not self.agent_token:
            self.log_result("Agent Vencimientos", False, "No agent token available")
            return False
            
        try:
            response = requests.get(f"{BACKEND_URL}/agente/vencimientos", params={"token": self.agent_token})
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["vencidos", "proximos_7_dias", "proximos_15_dias", "proximos_30_dias", "vigentes"]
                if all(key in data for key in expected_keys):
                    total_vencimientos = sum(len(data[key]) for key in expected_keys)
                    self.log_result("Agent Vencimientos", True, f"Vencimientos loaded with {total_vencimientos} total items")
                    return True
                else:
                    missing_keys = [key for key in expected_keys if key not in data]
                    self.log_result("Agent Vencimientos", False, f"Response missing keys: {missing_keys}", data)
                    return False
            else:
                self.log_result("Agent Vencimientos", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Agent Vencimientos", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_seguros_list(self):
        """Test admin seguros listing"""
        try:
            response = requests.get(f"{BACKEND_URL}/admin/seguros")
            
            if response.status_code == 200:
                data = response.json()
                if "seguros" in data and "total" in data:
                    seguros_count = len(data["seguros"])
                    total_count = data["total"]
                    self.log_result("Admin Seguros List", True, f"Listed {seguros_count} seguros out of {total_count} total")
                    return True
                else:
                    self.log_result("Admin Seguros List", False, "Response missing seguros/total fields", data)
                    return False
            else:
                self.log_result("Admin Seguros List", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Admin Seguros List", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Estonia Cobertura Colaborativa Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test sequence based on dependencies
        tests = [
            self.test_admin_login,
            self.test_create_agent,
            self.test_list_agents,
            self.test_agent_login,
            self.test_agent_dashboard,
            self.test_agent_vencimientos,
            self.test_create_premio,
            self.test_list_premios,
            self.test_admin_seguros_list
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
            print()  # Add spacing between tests
        
        print("=" * 60)
        print(f"📊 Test Summary: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

def main():
    """Main test execution"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Save detailed results
    with open("/app/test_results_backend.json", "w") as f:
        json.dump(runner.test_results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/test_results_backend.json")
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()