import asyncio
import json
import websockets
from typing import Set
from datetime import datetime

class WebSocketManager:
    """Менеджер WebSocket соединений"""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.loop = None
        
    async def handler(self, websocket, path):
        """Обработчик WebSocket соединений"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        print(f"🔌 Клиент подключился: {client_ip} (всего: {len(self.clients)})")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📨 Сообщение от {client_ip}: {data.get('type', 'unknown')}")
                    
                    # Обработка команд от клиента
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'timestamp': datetime.now().isoformat()
                        }))
                        
                except json.JSONDecodeError:
                    print(f"⚠️ Неверный JSON от {client_ip}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Соединение закрыто: {client_ip}")
        finally:
            self.clients.remove(websocket)
            print(f"🔌 Клиент отключился: {client_ip} (всего: {len(self.clients)})")
    
    async def broadcast(self, data: dict):
        """Отправить данные всем подключенным клиентам"""
        if not self.clients:
            return
            
        message = json.dumps(data, ensure_ascii=False)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                print(f"❌ Ошибка отправки клиенту: {e}")
                disconnected.add(client)
        
        # Удаляем отключенных клиентов
        self.clients -= disconnected
        
    async def start_server(self):
        """Запустить WebSocket сервер"""
        print(f"🌐 WebSocket сервер запускается на ws://{self.host}:{self.port}")
        self.server = await websockets.serve(
            self.handler, 
            self.host, 
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        print(f"✅ WebSocket сервер готов к подключениям")
        
    async def stop_server(self):
        """Остановить WebSocket сервер"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("🛑 WebSocket сервер остановлен")