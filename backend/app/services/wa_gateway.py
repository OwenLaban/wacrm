"""
Abstraksi WA Gateway - ganti provider tanpa ubah logic bisnis
Support: fonnte, wablas, mock (untuk dev & testing)
"""
import os
import httpx
import asyncio
import random

class WAGateway:
    def __init__(self):
        self.provider = os.getenv("WA_GATEWAY_PROVIDER", "mock").lower()
        self.fonnte_token = os.getenv("FONNTE_TOKEN", "")
        self.wablas_token = os.getenv("WABLAS_TOKEN", "")

    async def send_message(self, phone: str, message: str) -> dict:
        """
        Kirim pesan WA
        phone: 628123456789 (tanpa + dan tanpa spasi)
        return: {"success": bool, "id": str, "error": str}
        """
        # Normalisasi phone
        phone = self._normalize_phone(phone)

        if self.provider == "mock":
            return await self._mock_send(phone, message)
        elif self.provider == "fonnte":
            return await self._fonnte_send(phone, message)
        elif self.provider == "wablas":
            return await self._wablas_send(phone, message)
        else:
            return {"success": False, "error": f"Provider {self.provider} tidak dikenal"}

    def _normalize_phone(self, phone: str) -> str:
        phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = "62" + phone[1:]
        return phone

    async def _mock_send(self, phone: str, message: str) -> dict:
        # Simulasi delay network 300ms
        await asyncio.sleep(0.3)
        print(f"[MOCK WA] -> {phone}: {message[:80]}...")
        # Simulasi 95% sukses
        if random.random() < 0.95:
            return {"success": True, "id": f"mock_{random.randint(10000,99999)}"}
        return {"success": False, "error": "Mock simulasi gagal"}

    async def _fonnte_send(self, phone: str, message: str) -> dict:
        """Docs: https://fonnte.com/docs"""
        if not self.fonnte_token:
            return {"success": False, "error": "FONNTE_TOKEN kosong"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.fonnte.com/send",
                    headers={"Authorization": self.fonnte_token},
                    data={"target": phone, "message": message, "delay": "2"}
                )
                data = resp.json()
                # Fonnte return {"status": true/false}
                if data.get("status"):
                    return {"success": True, "id": str(data.get("id", ""))}
                return {"success": False, "error": str(data.get("reason", data))}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _wablas_send(self, phone: str, message: str) -> dict:
        """Docs: https://wablas.com/docs"""
        if not self.wablas_token:
            return {"success": False, "error": "WABLAS_TOKEN kosong"}
        try:
            # Wablas butuh domain, simpan di env WABLAS_DOMAIN
            domain = os.getenv("WABLAS_DOMAIN", "https://console.wablas.com")
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{domain}/api/send-message",
                    headers={"Authorization": self.wablas_token},
                    json={"phone": phone, "message": message}
                )
                data = resp.json()
                if data.get("status") == "success":
                    return {"success": True, "id": str(data.get("data", {}).get("id", ""))}
                return {"success": False, "error": str(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton
wa_gateway = WAGateway()
