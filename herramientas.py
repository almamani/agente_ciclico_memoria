from typing import Literal, TypedDict
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator

from datos import CLIENTES, PEDIDOS, Cliente, Pedido

class BuscarClienteInput(BaseModel):
  nombre: str = Field(
        description="Nombre completo o parte del nombre del cliente."
  )

  @field_validator("nombre")
  @classmethod
  def validar_nombre(cls, valor: str) -> str:
        valor = valor.strip()

        if not valor:
            raise ValueError("El nombre del cliente no puede estar vacío.")

        return valor


class ResultadoBusquedaCliente(TypedDict):
    estado: Literal["encontrado", "sin_coincidencias", "ambiguo"]
    clientes: list[Cliente]
    mensaje: str

@tool(args_schema=BuscarClienteInput)
async def buscar_cliente(nombre: str) -> ResultadoBusquedaCliente:
    """Busca clientes por su nombre completo o por una parte del nombre.

    Usá esta herramienta para obtener el cliente_id antes de consultar
    pedidos de un cliente identificado por nombre. No distingue mayúsculas
    de minúsculas. Si devuelve varios clientes, pedí al usuario que precise
    cuál desea consultar. Si no encuentra coincidencias, solicitá que revise
    el nombre; no inventes identificadores.
    """
    coincidencias = [
        cliente.copy()
        for cliente in CLIENTES
        if nombre.casefold() in cliente["nombre"].casefold()
    ]

    if not coincidencias:
        return {
            "estado": "sin_coincidencias",
            "clientes": [],
            "mensaje": "No se encontraron clientes. Solicitá un nombre más preciso.",
        }

    if len(coincidencias) > 1:
        return {
            "estado": "ambiguo",
            "clientes": coincidencias,
            "mensaje": "Hay varios clientes. Pedí al usuario que elija uno.",
        }

    return {
        "estado": "encontrado",
        "clientes": coincidencias,
        "mensaje": "Cliente identificado correctamente.",
    }  


class ConsultarPedidosInput(BaseModel):
    cliente_id: int = Field(
        gt=0,
        description=(
            "Identificador del cliente cuyos pedidos se quieren consultar. "
            "Debe obtenerse mediante buscar_cliente o haber sido "
            "proporcionado explícitamente por el usuario."
        ),
    )

class ResultadoPedidos(TypedDict):
    estado: Literal["ok", "cliente_inexistente"]
    cliente_id: int
    pedidos: list[Pedido]
    cantidad: int
    total: int
    mensaje: str


@tool(args_schema=ConsultarPedidosInput)
async def consultar_pedidos(cliente_id: int) -> ResultadoPedidos:
    """Consulta todos los pedidos de un cliente mediante su identificador.

    Devuelve los pedidos con sus fechas e importes, la cantidad y el total
    acumulado en pesos. Permite responder también cuál fue el último pedido.
    Si solo conocés el nombre del cliente, usá primero buscar_cliente para
    obtener su identificador. Un cliente existente sin pedidos devuelve
    estado 'ok', una lista vacía y totales en cero. Si el cliente no existe,
    solicitá revisar su identificación; no interpretes ese caso como ausencia
    de pedidos.
    """
    existe = any(
        cliente["cliente_id"] == cliente_id
        for cliente in CLIENTES
    )

    if not existe:
        return {
            "estado": "cliente_inexistente",
            "cliente_id": cliente_id,
            "pedidos": [],
            "cantidad": 0,
            "total": 0,
            "mensaje": "El cliente no existe. Revisá su identificación.",
        }

    pedidos_cliente = [
        pedido.copy()
        for pedido in PEDIDOS
        if pedido["cliente_id"] == cliente_id
    ]

    return {
        "estado": "ok",
        "cliente_id": cliente_id,
        "pedidos": pedidos_cliente,
        "cantidad": len(pedidos_cliente),
        "total": sum(pedido["total"] for pedido in pedidos_cliente),
        "mensaje": (
            "Consulta realizada correctamente."
            if pedidos_cliente
            else "El cliente existe, pero no tiene pedidos."
        ),
    }    