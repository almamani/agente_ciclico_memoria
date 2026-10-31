import asyncio
from pathlib import Path
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import construir_grafo


RUTA_MEMORIA = Path(__file__).resolve().parent / "memoria.sqlite"


async def main() -> None:
    # Cada ejecución comienza con conversaciones nuevas.
    identificador = uuid4().hex[:12]
    hilo_comercial = f"comercial_{identificador}"
    hilo_error = f"sin_coincidencias_{identificador}"

    demostraciones = [
        (
            "1. Consulta con dos herramientas",
            hilo_comercial,
            "¿Cuántos pedidos tiene Repuestos del Centro "
            "y cuál es el importe total?",
        ),
        (
            "2. Seguimiento con memoria",
            hilo_comercial,
            "¿Y cuál fue el último pedido?",
        ),
        (
            "3. Cliente no encontrado",
            hilo_error,
            "¿Cuántos pedidos tiene Ferretería Luna "
            "y cuál es el importe total?",
        ),
    ]

    # Permite mostrar solo los mensajes nuevos de cada turno.
    mensajes_mostrados: dict[str, int] = {}

    async with AsyncSqliteSaver.from_conn_string(
        str(RUTA_MEMORIA)
    ) as memoria:
        app = construir_grafo(memoria)

        for titulo, thread_id, pregunta in demostraciones:
            configuracion: RunnableConfig = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 10,
            }

            print(f"\n--- {titulo} ---")
            print(f"thread_id: {thread_id}")

            resultado = await app.ainvoke(
                {"messages": [HumanMessage(content=pregunta)]},
                config=configuracion,
            )

            mensajes = resultado["messages"]
            desde = mensajes_mostrados.get(thread_id, 0)

            for mensaje in mensajes[desde:]:
                mensaje.pretty_print()

            mensajes_mostrados[thread_id] = len(mensajes)

    print("\nHilos guardados en SQLite:")
    print(f"Comercial y seguimiento: {hilo_comercial}")
    print(f"Pedido de aclaración: {hilo_error}")


if __name__ == "__main__":
    asyncio.run(main())
