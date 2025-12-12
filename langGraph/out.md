(lang-chain) ➜  lang_chain git:(dev) ✗ /home/tanzim/Learning/Task/lang_chain/.venv/bin/python /home/tanzim/Learning/Task/lang_chain/langGraph/learnGraph.py
/home/tanzim/Learning/Task/lang_chain/.venv/lib64/python3.14/site-packages/langchain_core/_api/deprecation.py:26: UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
  from pydantic.v1.fields import FieldInfo as FieldInfoV1

============================================================
Query: What is the latest in artificial intelligence?
============================================================
🟢 Selected: Default Model + General Tools

==================================================
==================================================

Final Response: Artificial intelligence is a rapidly evolving field. Based on the latest search results, here are some key areas of recent development:

1.  **Generative AI Advancements:** Chatbots are reaching new heights, suggesting continued development in large language models (LLMs) and content generation capabilities.
2.  **AI Assistants and Copilots:** There is a focus on how these tools are transforming various work workflows.
3.  **Robotics and Physical AI:** Companies like Tesla are unveiling significant updates to their humanoid robots (like Optimus), emphasizing advances in dexterity and perception.
4.  **General Industry News:** Major news outlets like the WSJ and Reuters are covering breakthroughs, technology trends, business applications, and the ongoing discussions around AI regulation and ethics.

To get the most *current* breaking news or very specific details on any of these topics, you could ask me to narrow the search (e.g., "What is the latest on generative AI in drug discovery?").

============================================================
Query: Write a Python function that sums even numbers
============================================================
🔴 Selected: Claude (Anthropic) + Code Tools

==================================================
==================================================

Final Response: The key steps are:

1. Define a function `sum_even_numbers` that takes a list of numbers as input.
2. Initialize a `total` variable to 0.
3. Loop through the list of numbers, and for each even number, add it to the `total`.
4. Return the final `total` sum of even numbers.

The function can be called with any list of numbers, and it will return the sum of the even numbers in that list.

============================================================
Query: Give me the highest ordered products from the database
============================================================
🔵 Selected: OpenAI + Database Tools
[RealDictRow({'table_name': 'customers'}), RealDictRow({'table_name': 'orders'}), RealDictRow({'table_name': 'order_items'}), RealDictRow({'table_name': 'products'})]

==================================================
==================================================

Final Response: The query to retrieve the highest ordered products has been executed successfully. Here are the results for the top ordered products based on the quantity sold:

1. **USB-C Cable**
   - Total Ordered Quantity: 210
2. **Phone Stand**
   - Total Ordered Quantity: 6
3. **Monitor 4K**
   - Total Ordered Quantity: 3
4. **Keyboard Mechanical**
   - Total Ordered Quantity: 2
5. **Desk Lamp**
   - Total Ordered Quantity: 2

Additionally, there are 3 more products listed in the results. In total, 8 products were found but only the top 5 are displayed here.

If you would like to see all the results or need further analysis, please let me know!
(lang-chain) ➜  lang_chain git:(dev) ✗ 
