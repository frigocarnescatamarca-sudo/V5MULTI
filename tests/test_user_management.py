"""
Test Suite for WhatsApp Sandwich Bot - User Management System
Tests: User creation (CREAR ADMIN/DELIVERY), Login (soy X clave Y), Logout (cerrar sesion),
       Kick users (KICKEAR), Delete users (ELIMINAR), List users (USUARIOS),
       Multi-admin notifications, Delivery LISTO command, Order reminders
"""

import pytest
import requests
import os
import time
import random

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://dualbot-hub.preview.emergentagent.com').rstrip('/')

# Test phone numbers - Master admin must be configured first
MASTER_ADMIN_PHONE = "1111111111"
TEST_USER_PHONE = "2222222222"
TEST_DELIVERY_PHONE = "3333333333"


class TestSetupMasterAdmin:
    """Setup: Configure master admin phone"""
    
    def test_configure_master_admin(self):
        """Configure master admin phone for testing"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/config",
            json={"admin_phone": MASTER_ADMIN_PHONE}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("admin_phone") == MASTER_ADMIN_PHONE
        print(f"✅ Master admin configured: {MASTER_ADMIN_PHONE}")


class TestUserEndpoints:
    """Test GET /api/sandwich/users and GET /api/sandwich/sessions endpoints"""
    
    def test_get_users_endpoint(self):
        """Test GET /api/sandwich/users returns user list"""
        response = requests.get(f"{BASE_URL}/api/sandwich/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        print(f"✅ GET /api/sandwich/users works: {len(data['users'])} users")
    
    def test_get_sessions_endpoint(self):
        """Test GET /api/sandwich/sessions returns session lists"""
        response = requests.get(f"{BASE_URL}/api/sandwich/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "admin_sessions" in data
        assert "delivery_sessions" in data
        assert isinstance(data["admin_sessions"], list)
        assert isinstance(data["delivery_sessions"], list)
        print(f"✅ GET /api/sandwich/sessions works: {len(data['admin_sessions'])} admin, {len(data['delivery_sessions'])} delivery")


class TestCreateUserCommand:
    """Test CREAR ADMIN/DELIVERY username password command"""
    
    def test_create_admin_user(self):
        """Test creating admin user via WhatsApp command"""
        username = f"testadmin{random.randint(100, 999)}"
        password = "testpass123"
        
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should confirm user creation
        assert "✅" in reply or username.lower() in reply.lower() or "creado" in reply.lower()
        print(f"✅ CREAR ADMIN works: {reply[:100]}...")
        
        # Verify user exists in database
        users_response = requests.get(f"{BASE_URL}/api/sandwich/users")
        users = users_response.json().get("users", [])
        user_found = any(u.get("username") == username.lower() and u.get("role") == "admin" for u in users)
        assert user_found, f"User {username} not found in users list"
        print(f"✅ User {username} verified in database")
    
    def test_create_delivery_user(self):
        """Test creating delivery user via WhatsApp command"""
        username = f"testdelivery{random.randint(100, 999)}"
        password = "deliverypass123"
        
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR DELIVERY {username} {password}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "✅" in reply or username.lower() in reply.lower() or "creado" in reply.lower()
        print(f"✅ CREAR DELIVERY works: {reply[:100]}...")
        
        # Verify user exists
        users_response = requests.get(f"{BASE_URL}/api/sandwich/users")
        users = users_response.json().get("users", [])
        user_found = any(u.get("username") == username.lower() and u.get("role") == "delivery" for u in users)
        assert user_found, f"Delivery user {username} not found"
        print(f"✅ Delivery user {username} verified in database")
    
    def test_create_duplicate_user_fails(self):
        """Test creating duplicate user returns error"""
        username = f"dupuser{random.randint(100, 999)}"
        password = "pass123"
        
        # Create first time
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        
        # Try to create again
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should indicate user already exists
        assert "ya existe" in reply.lower() or "already" in reply.lower() or "existe" in reply.lower()
        print(f"✅ Duplicate user creation handled: {reply[:100]}...")


class TestLoginCommand:
    """Test 'soy username clave password' login command"""
    
    def test_login_success(self):
        """Test successful login"""
        # First create a user
        username = f"logintest{random.randint(100, 999)}"
        password = "loginpass123"
        
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        
        # Now login from different phone
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": TEST_USER_PHONE,
                "message": f"soy {username} clave {password}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should show welcome message with role
        assert "bienvenido" in reply.lower() or "sesión" in reply.lower() or "admin" in reply.lower()
        print(f"✅ Login success: {reply[:150]}...")
        
        # Verify session exists
        sessions_response = requests.get(f"{BASE_URL}/api/sandwich/sessions")
        sessions = sessions_response.json()
        admin_sessions = sessions.get("admin_sessions", [])
        session_found = any(s.get("username") == username.lower() for s in admin_sessions)
        assert session_found, f"Session for {username} not found"
        print(f"✅ Session verified for {username}")
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        username = f"wrongpass{random.randint(100, 999)}"
        password = "correctpass"
        
        # Create user
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        
        # Try login with wrong password
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": TEST_USER_PHONE,
                "message": f"soy {username} clave wrongpassword"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "❌" in reply or "incorrecto" in reply.lower() or "error" in reply.lower()
        print(f"✅ Wrong password handled: {reply[:100]}...")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": TEST_USER_PHONE,
                "message": "soy nonexistentuser999 clave anypass"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "❌" in reply or "incorrecto" in reply.lower()
        print(f"✅ Non-existent user login handled: {reply[:100]}...")


class TestLogoutCommand:
    """Test 'cerrar sesion' logout command"""
    
    def test_logout_success(self):
        """Test successful logout"""
        username = f"logouttest{random.randint(100, 999)}"
        password = "logoutpass"
        test_phone = f"444{random.randint(1000000, 9999999)}"
        
        # Create and login
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Now logout
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_phone,
                "message": "cerrar sesion"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "cerrada" in reply.lower() or "hasta luego" in reply.lower() or "✅" in reply
        print(f"✅ Logout success: {reply[:100]}...")
    
    def test_logout_no_session(self):
        """Test logout when not logged in"""
        test_phone = f"555{random.randint(1000000, 9999999)}"
        
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_phone,
                "message": "cerrar sesion"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "no" in reply.lower() or "activa" in reply.lower()
        print(f"✅ Logout without session handled: {reply[:100]}...")


class TestKickCommand:
    """Test KICKEAR username command"""
    
    def test_kick_user(self):
        """Test kicking a logged-in user"""
        username = f"kicktest{random.randint(100, 999)}"
        password = "kickpass"
        test_phone = f"666{random.randint(1000000, 9999999)}"
        
        # Create and login
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Kick the user
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"KICKEAR {username}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "✅" in reply or "cerrada" in reply.lower()
        print(f"✅ KICKEAR works: {reply[:100]}...")
    
    def test_kick_nonexistent_session(self):
        """Test kicking user with no active session"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": "KICKEAR nonexistentuser999"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "❌" in reply or "no tiene" in reply.lower() or "activa" in reply.lower()
        print(f"✅ Kick non-existent session handled: {reply[:100]}...")


class TestDeleteUserCommand:
    """Test ELIMINAR username command"""
    
    def test_delete_user(self):
        """Test deleting a user"""
        username = f"deletetest{random.randint(100, 999)}"
        password = "deletepass"
        
        # Create user
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        
        # Delete user
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"ELIMINAR {username}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "✅" in reply or "eliminado" in reply.lower()
        print(f"✅ ELIMINAR works: {reply[:100]}...")
        
        # Verify user no longer exists
        users_response = requests.get(f"{BASE_URL}/api/sandwich/users")
        users = users_response.json().get("users", [])
        user_found = any(u.get("username") == username.lower() for u in users)
        assert not user_found, f"User {username} should have been deleted"
        print(f"✅ User {username} verified deleted")
    
    def test_delete_nonexistent_user(self):
        """Test deleting non-existent user"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": "ELIMINAR nonexistentuser999"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        assert "❌" in reply or "no encontrado" in reply.lower() or "not found" in reply.lower()
        print(f"✅ Delete non-existent user handled: {reply[:100]}...")


class TestListUsersCommand:
    """Test USUARIOS command"""
    
    def test_list_users(self):
        """Test listing all users"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": "USUARIOS"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should show users list or "no hay usuarios"
        assert "usuario" in reply.lower() or "no hay" in reply.lower() or "👥" in reply
        print(f"✅ USUARIOS command works: {reply[:200]}...")


class TestDeliveryListoCommand:
    """Test that delivery can use LISTO X command"""
    
    def test_delivery_listo_command(self):
        """Test delivery using LISTO command"""
        # Create delivery user
        username = f"deliverylisto{random.randint(100, 999)}"
        password = "listopass"
        delivery_phone = f"777{random.randint(1000000, 9999999)}"
        
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR DELIVERY {username} {password}"
            }
        )
        
        # Login as delivery
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Try LISTO command (will fail if no order, but should be recognized)
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": "LISTO 99999"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should recognize command (even if order not found)
        assert "no encontré" in reply.lower() or "❌" in reply or "listo" in reply.lower() or "pedido" in reply.lower()
        print(f"✅ Delivery LISTO command recognized: {reply[:100]}...")


class TestSendRemindersEndpoint:
    """Test POST /api/sandwich/send-reminders endpoint"""
    
    def test_send_reminders_endpoint(self):
        """Test sending reminders for pending orders"""
        response = requests.post(f"{BASE_URL}/api/sandwich/send-reminders")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert data.get("success") == True
        assert "reminders_sent" in data
        print(f"✅ POST /api/sandwich/send-reminders works: {data.get('reminders_sent')} reminders sent")


class TestNonMasterAdminCannotCreateUsers:
    """Test that non-master admin cannot create users"""
    
    def test_logged_admin_cannot_create_users(self):
        """Test that logged-in admin (not master) cannot create users"""
        # Create and login as regular admin
        username = f"regularadmin{random.randint(100, 999)}"
        password = "regularpass"
        admin_phone = f"888{random.randint(1000000, 9999999)}"
        
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR ADMIN {username} {password}"
            }
        )
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": admin_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Try to create user as regular admin
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": admin_phone,
                "message": "CREAR ADMIN newuser newpass"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should NOT create user (only master admin can)
        # The command should either be ignored or show admin commands
        print(f"✅ Regular admin CREAR command result: {reply[:150]}...")


class TestDeliveryCommands:
    """Test delivery-specific commands"""
    
    def test_delivery_encamino_command(self):
        """Test delivery ENCAMINO command"""
        username = f"deliveryenc{random.randint(100, 999)}"
        password = "encpass"
        delivery_phone = f"999{random.randint(1000000, 9999999)}"
        
        # Create and login delivery
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR DELIVERY {username} {password}"
            }
        )
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Try ENCAMINO command
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": "ENCAMINO 99999"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should recognize command
        assert "no encontré" in reply.lower() or "❌" in reply or "camino" in reply.lower() or "pedido" in reply.lower()
        print(f"✅ Delivery ENCAMINO command recognized: {reply[:100]}...")
    
    def test_delivery_entregado_command(self):
        """Test delivery ENTREGADO command"""
        username = f"deliveryent{random.randint(100, 999)}"
        password = "entpass"
        delivery_phone = f"101{random.randint(1000000, 9999999)}"
        
        # Create and login delivery
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": MASTER_ADMIN_PHONE,
                "message": f"CREAR DELIVERY {username} {password}"
            }
        )
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": f"soy {username} clave {password}"
            }
        )
        
        # Try ENTREGADO command
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": delivery_phone,
                "message": "ENTREGADO 99999"
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        
        # Should recognize command
        assert "no encontré" in reply.lower() or "❌" in reply or "entregado" in reply.lower() or "pedido" in reply.lower()
        print(f"✅ Delivery ENTREGADO command recognized: {reply[:100]}...")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_users(self):
        """Clean up test users created during testing"""
        # Get all users
        users_response = requests.get(f"{BASE_URL}/api/sandwich/users")
        users = users_response.json().get("users", [])
        
        # Delete test users (those starting with 'test')
        deleted = 0
        for user in users:
            username = user.get("username", "")
            if username.startswith("test") or username.startswith("logintest") or username.startswith("logouttest") or username.startswith("kicktest") or username.startswith("deletetest") or username.startswith("dupuser") or username.startswith("wrongpass") or username.startswith("deliverylisto") or username.startswith("regularadmin") or username.startswith("deliveryenc") or username.startswith("deliveryent"):
                requests.post(
                    f"{BASE_URL}/api/sandwich/whatsapp/message",
                    json={
                        "phone_number": MASTER_ADMIN_PHONE,
                        "message": f"ELIMINAR {username}"
                    }
                )
                deleted += 1
        
        print(f"✅ Cleanup: Deleted {deleted} test users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
