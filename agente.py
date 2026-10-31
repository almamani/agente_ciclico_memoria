import os
from pathlib import Path

from dotenv import load_dotenv
from typing import TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_openai import ChatOpenAI

from herramientas import buscar_cliente, consultar_pedidos

class EstadoAgente(MessagesState):
    pass

class ActualizacionMensajes(TypedDict):
    messages: list[BaseMessage]


RUTA_PROYECTO = Path(__file__).resolve().parent
load_dotenv(RUTA_PROYECTO / ".env")

api_key = os.getenv("OPENAI_API_KEY", "").strip()

if not api_key:
    raise ValueError(
        "Falta OPENAI_API_KEY. Configurala en el archivo .env."
    )

nombre_modelo = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

if not nombre_modelo:
    raise ValueError("OPENAI_MODEL no puede estar vacío.")

herramientas = [buscar_cliente, consultar_pedidos]

llm = ChatOpenAI(
    model=nombre_modelo,
    api_key=api_key,
    temperature=0,
    timeout=30,
    max_retries=2,
)

modelo_con_herramientas = llm.bind_tools(herramientas)

INSTRUCCIONES = """
Sos un asistente comercial que consulta clientes y pedidos
mediante las herramientas disponibles. Los datos son simulados.

Reglas:
- Para consultar pedidos por nombre de cliente, primero usá
  buscar_cliente y después consultar_pedidos con el identificador obtenido.
- No inventes clientes, identificadores, pedidos ni importes.
- Si hay varios clientes posibles, pedí al usuario que elija uno.
- Si no encontrás al cliente o faltan datos, pedí una aclaración.
- Distinguí un cliente inexistente de uno existente sin pedidos.
- Si una herramienta informa un fallo técnico, no lo interpretes
  como ausencia de pedidos. Reintentá una vez si corresponde;
  si el problema continúa, explicalo sin inventar resultados.
- Para identificar el último pedido, compará las fechas.
- Aprovechá el historial para entender preguntas de seguimiento.
- Respondé en español, de forma clara, indicando los importes en pesos.
"""

async def llamar_modelo(
    estado: EstadoAgente,
) -> ActualizacionMensajes:
    mensajes: list[BaseMessage] = [
        SystemMessage(content=INSTRUCCIONES),
        *estado["messages"],
    ]

    respuesta = await modelo_con_herramientas.ainvoke(mensajes)

    return {"messages": [respuesta]}


def construir_grafo(
    checkpointer: BaseCheckpointSaver,
):
    grafo = StateGraph(EstadoAgente)

    grafo.add_node("agent", llamar_modelo)
    grafo.add_node("tools", ToolNode(herramientas))

    grafo.add_edge(START, "agent")

    grafo.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    grafo.add_edge("tools", "agent")

    return grafo.compile(checkpointer=checkpointer)