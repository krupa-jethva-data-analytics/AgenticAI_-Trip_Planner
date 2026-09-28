from utils.model_loader import ModelLoader
from prompt.prompt import SYSTEM_PROMPT
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool
from langgraph.graph import StateGraph, MessagesState, END, START
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage



REJECT_MESSAGE = (
    "I'm a trip planning assistant, so I can only help with "
    "travel-related questions. Where would you like to travel?"
)


class GraphBuilder():
    def __init__(self, model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()

        self.tools = []

        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConverterTool()

        self.tools.extend([*self.weather_tools.weather_tool_list,
                           *self.place_search_tools.place_search_tool_list,
                           *self.calculator_tools.calculator_tool_list,
                           *self.currency_converter_tools.currency_converter_tool_list])

        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)

        self.graph = None

        self.system_prompt = SYSTEM_PROMPT

    # ---------- NEW: guardrail ----------
    def guardrail_check(self, state: MessagesState):
        """Decides where to go next: 'agent' (travel) or 'reject' (not travel)."""
        user_text = state["messages"][-1].content

        classifier_prompt = [
            SystemMessage(content=(
                "You are a strict classifier. Reply with ONLY one word.\n"
                "Reply 'YES' if the message is about travel: trip planning, "
                "destinations, itineraries, hotels, flights, local places, "
                "weather for a trip, or trip budget/currency.\n"
                "Reply 'NO' for anything else."
            )),
            HumanMessage(content=user_text),
        ]

        # Use the plain LLM (without tools) so it only classifies
        verdict = self.llm.invoke(classifier_prompt).content.strip().upper()

        if verdict.startswith("NO"):
            return "reject"
        return "agent"

    # ---------- NEW: fixed reply for off-topic questions ----------
    def reject_function(self, state: MessagesState):
        return {"messages": [AIMessage(content=REJECT_MESSAGE)]}

    def agent_function(self, state: MessagesState):
        """Main agent function"""
        user_question = state["messages"]
        input_question = [self.system_prompt] + user_question
        response = self.llm_with_tools.invoke(input_question)
        return {"messages": [response]}

    def build_graph(self):
        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("reject", self.reject_function)   # NEW

        # CHANGED: START now goes through the guardrail instead of straight to agent
        graph_builder.add_conditional_edges(
            START,
            self.guardrail_check,
            {"agent": "agent", "reject": "reject"},
        )

        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("reject", END)                    # NEW
        # REMOVED: graph_builder.add_edge("agent", END)

        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.build_graph()

    