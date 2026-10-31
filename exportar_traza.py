import asyncio
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import messages_to_dict
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import construir_grafo


RUTA_PROYECTO = Path(__file__).resolve().parent
RUTA_MEMORIA = RUTA_PROYECTO / "memoria.sqlite"


async def main() -> None:
    parser = argparse.ArgumentParser(
      description="Exporta a JSON la conversación de un hilo."
    )
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--salida", required=True)
    parser.add_argument("--descripcion", required=True)
    argumentos = parser.parse_args()

    thread_id = argumentos.thread_id
    ruta_salida = RUTA_PROYECTO / argumentos.salida

    
    if not RUTA_MEMORIA.is_file():
        raise FileNotFoundError("No se encontró memoria.sqlite.")

    configuracion: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
    }

    async with AsyncSqliteSaver.from_conn_string(
        str(RUTA_MEMORIA)
    ) as memoria:
        app = construir_grafo(memoria)
        estado = await app.aget_state(configuracion)
        mensajes = estado.values.get("messages", [])

    if not mensajes:
        raise ValueError(
            f"No hay mensajes guardados para el hilo {thread_id}."
        )

    traza = {
        "thread_id": thread_id,
        "exportado_en": datetime.now(timezone.utc).isoformat(),
        "descripcion": argumentos.descripcion,
        "messages": messages_to_dict(mensajes),
    }

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    ruta_salida.write_text(
        json.dumps(traza, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Traza exportada: {ruta_salida}")
    print(f"Mensajes incluidos: {len(mensajes)}")


if __name__ == "__main__":
    asyncio.run(main())