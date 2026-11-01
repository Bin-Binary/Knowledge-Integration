import os

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict, Annotated
from operator import add
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
load_dotenv()

model = ChatOpenAI(
    model="qwen3.8-max",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL"),
    temperature=0.7,
)
class State(TypedDict):
    messages: Annotated[list[str], add]

def node_chat(state: State) -> State:
    return {
        'messages': [model.invoke(state['messages'][-1])]
    }

graph = StateGraph(State)
graph.add_node(node_chat)

graph.add_edge(START, 'node_chat')
graph.add_edge('node_chat', END)

checkpointer = InMemorySaver()
agent = graph.compile(checkpointer=checkpointer)
my_message = str(input("User: "))
# 这里[Schemata@Remembering_information:Debug]的Retieve Keyword 需要显示配置，否则会报错。侧面验证了需要Keyword来检索
## response = agent.invoke({'messages': [human]})
response = agent.invoke(
    {'messages': [HumanMessage(my_message)]},
    {"configurable": {"thread_id": "thread-1"}}
)
for message in response['messages']:
    message.pretty_print()

