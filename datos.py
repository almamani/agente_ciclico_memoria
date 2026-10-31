from typing import TypedDict

class Cliente(TypedDict):
    cliente_id: int
    nombre: str

class Pedido(TypedDict):
    pedido_id: int
    cliente_id: int
    fecha: str
    total: int  # Importe en pesos enteros para esta simulación.


CLIENTES: list[Cliente] = [
    {"cliente_id": 102, "nombre": "Repuestos del Centro"},
    {"cliente_id": 103, "nombre": "Taller Norte"},
]

PEDIDOS: list[Pedido] = [
    {
        "pedido_id": 1001,
        "cliente_id": 102,
        "fecha": "2026-10-01",
        "total": 4500,
    },
    {
        "pedido_id": 1002,
        "cliente_id": 102,
        "fecha": "2026-10-10",
        "total": 6000,
    },
    {
        "pedido_id": 1003,
        "cliente_id": 102,
        "fecha": "2026-10-20",
        "total": 4000,
    },
]