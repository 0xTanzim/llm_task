from graph_app import create_app
from langchain_core.messages import AIMessage, HumanMessage


def main():
    # Test with different queries
    test_queries = [
        # "What is the latest in artificial intelligence?",
        # "Write a Python function that sums even numbers",
        "Give me the highest ordered products from the database",
    ]

    app = create_app()

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)

        result = app.invoke(
            {
                "messages": [HumanMessage(content=query)],
                "selected_model": None,
                "selected_tools": [],
                "llm_calls": 0,
                "errors": [],
            },
              {"configurable": {"thread_id": "1"}},  
        )

        print("\n" + "=" * 50)
        print("=" * 50)

        # Extract final response
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                print(f"\nFinal Response: {msg.content}")
                break


if __name__ == "__main__":
    main()
