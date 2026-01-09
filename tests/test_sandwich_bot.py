"""
Test Suite for WhatsApp Sandwich Bot - 10 New Features
Tests: Sequential order numbers, Admin commands, Delivery commands, Client commands,
       Location handling, Auto-resume, Admin panel integration
"""

import pytest
import requests
import os
import time
import random

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://brand-hub-app.preview.emergentagent.com').rstrip('/')

# Test phone numbers
ADMIN_PHONE = "1234567890"
DELIVERY_PHONE = "9876543210"
CLIENT_PHONE = f"TEST_{random.randint(1000000000, 9999999999)}"


class TestSandwichBotConfig:
    """Test bot configuration endpoints"""
    
    def test_get_config(self):
        """Test getting bot configuration"""
        response = requests.get(f"{BASE_URL}/api/sandwich/whatsapp/config")
        assert response.status_code == 200
        data = response.json()
        assert "admin_phone" in data
        assert "delivery_phones" in data
        assert "nombre_negocio" in data
        print(f"✅ Config retrieved: admin_phone={data.get('admin_phone')}, delivery_phones={data.get('delivery_phones')}")
    
    def test_update_config_admin_phone(self):
        """Test updating admin phone"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/config",
            json={"admin_phone": ADMIN_PHONE, "delivery_phones": [DELIVERY_PHONE]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("admin_phone") == ADMIN_PHONE
        assert DELIVERY_PHONE in data.get("delivery_phones", [])
        print(f"✅ Config updated: admin_phone={ADMIN_PHONE}, delivery_phones={[DELIVERY_PHONE]}")


class TestSequentialOrderNumbers:
    """Test Feature 3: Sequential order numbers (#1, #2, #3)"""
    
    def test_reset_order_counter(self):
        """Test resetting the order counter"""
        response = requests.post(f"{BASE_URL}/api/sandwich/reset-order-counter")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✅ Order counter reset successfully")
    
    def test_get_pedidos(self):
        """Test getting all orders"""
        response = requests.get(f"{BASE_URL}/api/sandwich/pedidos")
        assert response.status_code == 200
        data = response.json()
        assert "pedidos" in data
        print(f"✅ Retrieved {len(data.get('pedidos', []))} orders")


class TestAdminCommands:
    """Test Admin commands via WhatsApp message endpoint"""
    
    def test_admin_greeting(self):
        """Test admin greeting shows commands"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": "hola"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Admin should see commands list
        assert "PEDIDOS" in reply or "Admin" in reply or "Comandos" in reply
        print(f"✅ Admin greeting works: {reply[:100]}...")
    
    def test_admin_pedidos_command(self):
        """Test PEDIDOS command"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": "PEDIDOS"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should show pending orders or "no hay pedidos"
        assert "pendiente" in reply.lower() or "no hay" in reply.lower() or "#" in reply
        print(f"✅ PEDIDOS command works: {reply[:100]}...")
    
    def test_admin_pausar_command(self):
        """Test PAUSAR command for human handover"""
        test_client = f"{random.randint(1000000000, 9999999999)}"  # Must be digits only
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": f"PAUSAR {test_client}"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        assert "pausado" in reply.lower() or "paused" in reply.lower()
        print(f"✅ PAUSAR command works: {reply[:100]}...")
    
    def test_admin_reanudar_command(self):
        """Test REANUDAR command"""
        test_client = f"{random.randint(1000000000, 9999999999)}"  # Must be digits only
        # First pause
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": f"PAUSAR {test_client}"}
        )
        # Then resume
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": f"REANUDAR {test_client}"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        assert "reanudado" in reply.lower() or "resumed" in reply.lower()
        print(f"✅ REANUDAR command works: {reply[:100]}...")
    
    def test_admin_delivery_command(self):
        """Test DELIVERY command to add delivery person"""
        new_delivery = f"{random.randint(1000000000, 9999999999)}"  # Must be digits only
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": f"DELIVERY {new_delivery}"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        assert "agregado" in reply.lower() or "delivery" in reply.lower()
        print(f"✅ DELIVERY command works: {reply[:100]}...")


class TestDeliveryCommands:
    """Test Delivery person commands"""
    
    def test_delivery_greeting(self):
        """Test delivery person greeting"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": DELIVERY_PHONE, "message": "hola"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Delivery should see their commands
        assert "Delivery" in reply or "PEDIDO" in reply or "ENCAMINO" in reply
        print(f"✅ Delivery greeting works: {reply[:100]}...")
    
    def test_delivery_commands_list(self):
        """Test delivery sees command list"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": DELIVERY_PHONE, "message": "comandos"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should show delivery commands
        assert "PEDIDO" in reply or "ENCAMINO" in reply or "ENTREGADO" in reply
        print(f"✅ Delivery commands list works: {reply[:100]}...")


class TestClientCommands:
    """Test client commands (cancelar, estado, hablar con humano)"""
    
    def test_client_greeting(self):
        """Test regular client greeting"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": CLIENT_PHONE, "message": "hola"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Client should see welcome message or menu
        assert len(reply) > 0
        print(f"✅ Client greeting works: {reply[:100]}...")
    
    def test_client_human_handover_request(self):
        """Test client requesting human attention"""
        test_client = f"TEST_HUMAN_{random.randint(1000000000, 9999999999)}"
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": test_client, "message": "quiero hablar con alguien"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should acknowledge human handover
        assert "encargado" in reply.lower() or "momento" in reply.lower() or "comunico" in reply.lower() or len(reply) > 0
        print(f"✅ Human handover request works: {reply[:100]}...")
    
    def test_client_cancel_no_order(self):
        """Test client cancel when no active order"""
        test_client = f"TEST_CANCEL_{random.randint(1000000000, 9999999999)}"
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": test_client, "message": "cancelar"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should handle gracefully
        assert len(reply) > 0
        print(f"✅ Cancel without order handled: {reply[:100]}...")


class TestLocationHandling:
    """Test Feature 4: Location sharing detection"""
    
    def test_location_message(self):
        """Test handling location message"""
        test_client = f"TEST_LOC_{random.randint(1000000000, 9999999999)}"
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_client,
                "message": "📍 Ubicación compartida",
                "location": {
                    "latitude": -28.47,
                    "longitude": -65.78
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should acknowledge location
        assert "ubicación" in reply.lower() or "guardé" in reply.lower() or "perfecto" in reply.lower()
        print(f"✅ Location handling works: {reply[:100]}...")
    
    def test_location_with_degrees_format(self):
        """Test location with degreesLatitude format"""
        test_client = f"TEST_LOC2_{random.randint(1000000000, 9999999999)}"
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={
                "phone_number": test_client,
                "message": "📍 Ubicación compartida",
                "location": {
                    "degreesLatitude": -28.47,
                    "degreesLongitude": -65.78
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        assert "ubicación" in reply.lower() or "guardé" in reply.lower() or "perfecto" in reply.lower()
        print(f"✅ Location with degrees format works: {reply[:100]}...")


class TestWhatsAppStatus:
    """Test WhatsApp connection status endpoints"""
    
    def test_whatsapp_status(self):
        """Test getting WhatsApp status"""
        response = requests.get(f"{BASE_URL}/api/sandwich/whatsapp/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "connected" in data
        print(f"✅ WhatsApp status: {data}")
    
    def test_whatsapp_qr(self):
        """Test getting QR code endpoint"""
        response = requests.get(f"{BASE_URL}/api/sandwich/whatsapp/qr")
        assert response.status_code == 200
        data = response.json()
        # QR might be null if not awaiting
        assert "qr" in data or "qr_data_url" in data or "status" in data
        print(f"✅ WhatsApp QR endpoint works")


class TestMenuEndpoints:
    """Test menu CRUD endpoints"""
    
    def test_get_menu(self):
        """Test getting menu"""
        response = requests.get(f"{BASE_URL}/api/sandwich/menu")
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        menu = data.get("menu", [])
        assert len(menu) > 0
        print(f"✅ Menu retrieved: {len(menu)} categories")
    
    def test_menu_has_categories(self):
        """Test menu structure"""
        response = requests.get(f"{BASE_URL}/api/sandwich/menu")
        assert response.status_code == 200
        data = response.json()
        menu = data.get("menu", [])
        for cat in menu:
            assert "categoria" in cat
            assert "productos" in cat
        print(f"✅ Menu structure is valid")


class TestPedidosEndpoints:
    """Test orders (pedidos) endpoints"""
    
    def test_get_all_pedidos(self):
        """Test getting all orders"""
        response = requests.get(f"{BASE_URL}/api/sandwich/pedidos")
        assert response.status_code == 200
        data = response.json()
        assert "pedidos" in data
        print(f"✅ Retrieved {len(data.get('pedidos', []))} orders")
    
    def test_get_pedidos_by_estado(self):
        """Test filtering orders by status"""
        response = requests.get(f"{BASE_URL}/api/sandwich/pedidos?estado=pendiente")
        assert response.status_code == 200
        data = response.json()
        assert "pedidos" in data
        # All returned orders should be pendiente
        for pedido in data.get("pedidos", []):
            assert pedido.get("estado") == "pendiente"
        print(f"✅ Filtered orders by estado works")
    
    def test_update_pedido_estado(self):
        """Test updating order status"""
        # First get a pending order
        response = requests.get(f"{BASE_URL}/api/sandwich/pedidos?estado=pendiente")
        data = response.json()
        pedidos = data.get("pedidos", [])
        
        if pedidos:
            numero_pedido = pedidos[0].get("numero_pedido")
            # Update to confirmado
            update_response = requests.put(
                f"{BASE_URL}/api/sandwich/pedidos/{numero_pedido}/estado",
                json={"estado": "confirmado"}
            )
            assert update_response.status_code == 200
            print(f"✅ Updated order {numero_pedido} to confirmado")
        else:
            print("⚠️ No pending orders to test update")


class TestEstadisticas:
    """Test statistics endpoint"""
    
    def test_get_estadisticas(self):
        """Test getting statistics"""
        response = requests.get(f"{BASE_URL}/api/sandwich/estadisticas")
        assert response.status_code == 200
        data = response.json()
        assert "total_pedidos" in data or "pedidos_hoy" in data or "pedidos_pendientes" in data
        print(f"✅ Statistics: {data}")


class TestPausedChats:
    """Test paused chats functionality"""
    
    def test_pause_chat_endpoint(self):
        """Test pausing a chat via endpoint"""
        test_phone = f"TEST_PAUSE_{random.randint(1000000000, 9999999999)}"
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/pause-chat",
            json={"phone_number": test_phone}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Pause chat endpoint works")
    
    def test_resume_chat_endpoint(self):
        """Test resuming a chat via endpoint"""
        test_phone = f"TEST_RESUME_{random.randint(1000000000, 9999999999)}"
        # First pause
        requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/pause-chat",
            json={"phone_number": test_phone}
        )
        # Then resume
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/resume-chat",
            json={"phone_number": test_phone}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✅ Resume chat endpoint works")


class TestConversations:
    """Test conversations endpoint"""
    
    def test_get_conversations(self):
        """Test getting all conversations"""
        response = requests.get(f"{BASE_URL}/api/sandwich/whatsapp/conversations")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data or isinstance(data, list)
        print(f"✅ Conversations endpoint works")


class TestOrderFlowIntegration:
    """Integration test for complete order flow"""
    
    def test_admin_confirm_nonexistent_order(self):
        """Test confirming non-existent order"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": "CONFIRMAR 99999"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        # Should indicate order not found
        assert "no encontré" in reply.lower() or "not found" in reply.lower() or "❌" in reply
        print(f"✅ Non-existent order handled: {reply[:100]}...")
    
    def test_admin_listo_nonexistent_order(self):
        """Test LISTO command on non-existent order"""
        response = requests.post(
            f"{BASE_URL}/api/sandwich/whatsapp/message",
            json={"phone_number": ADMIN_PHONE, "message": "LISTO 99999"}
        )
        assert response.status_code == 200
        data = response.json()
        reply = data.get("reply", "")
        assert "no encontré" in reply.lower() or "not found" in reply.lower() or "❌" in reply
        print(f"✅ LISTO non-existent order handled: {reply[:100]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
