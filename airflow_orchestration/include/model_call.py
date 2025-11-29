# Import dotenv to load environment variables
from dotenv import load_dotenv, find_dotenv
# Import OpenAI from langchain_openai to interact with OpenAI's language models
from langchain_openai import ChatOpenAI
# Import ChatPromptTemplate to transform written prompts into formats that can be understood by an agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# Import PythonREPLTool to enable LangChain to execute Python code on project files
from langchain_experimental.tools import PythonREPLTool
from langchain.tools import BaseTool
# Import initialize_agent to set up an agent that is capable of using tools
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
# Import pydantic to define the schema for each field when we will create custom classes
from pydantic import Field
# Import pandas to read txt and csv files
import pandas as pd

def run_model_call():
    output_path="/usr/local/airflow/include/financial_api/outputs/streamlit_app.py",
    env_path="/usr/local/airflow/include/.env"

    # If true is printed, the environment variables are loaded correctly
    load_dotenv(find_dotenv())
    # Load environment variables from a .env file into the system's environment variables
    load_dotenv()

    # Set-up the model from OpenAI using the latest one: GPT-4.1
    llm = ChatOpenAI(
                    model_name="gpt-4.1",
                    # Temprature controls the level of creativity of the model's responses. 0 is for factual answers.
                    temperature=0)

    class FileWriteTool(BaseTool):
        name: str = "write_file"
        description: str = (
            "Write text content into a file. "
            "Arguments: file_path (str), text (str). Overwrites the file."
        )
        # The args schema MUST be declared this way in LangChain 1.x
        file_path: str = Field(default=None, description="Path of the file to write into.")
        text: str = Field(default=None, description="The text content to write.")
        def _run(self, file_path: str, text: str):
            with open(file_path, "w") as f:
                f.write(text)
            return f"File successfully written to: {file_path}"
        async def _arun(self, *args, **kwargs):
            raise NotImplementedError("Async not supported.")
        

    # Set up a detailed prompt for the financial analysis task
    finance_prompt = """
    You are BOTH:

    an investment specialist in technology equities, and

    a senior Python/Streamlit engineer.

    Your mission is to:

    Load the user’s files: a CSV with historical stock data + a TXT with the user’s portfolio,

    Analyze tech stocks from the CSV with historical stock data,

    Focus on the most recent date you find in the CSV with historical stock data,

    Compare the metrics you find for this date to the metrics you find for all the other dates in the CSV,

    Identify cyclical patterns, local peaks, local bottoms, and momentum signals,

    Based on this analysis, produce daily actionable investment advice for the user’s portfolio contained in the TXT file,

    Choose only 2–3 actions worth focusing on each day, these actions should be one with strong BUY signals, and/or one with strong SELL signals,

    Determine whether today is a BUY, SELL, or HOLD moment,

    Generate a minimal Streamlit app showing the analysis AND simple charts,

    Insert the app code in ../src/streamlit_app.py.

    FILES YOU MUST LOAD (unless actual read error occurs)

    CSV with historical stock data: /usr/local/airflow/include/financial_api/outputs/processed_financial_data.csv

    TXT with the user’s portfolio: /usr/local/airflow/include/financial_api/outputs/my_portfolio.txt

    You MUST attempt to read these with the tools available (PythonREPL, file tools).
    Do NOT say you “don’t have access” unless a real tool error occurs.

    🔒 HARD REQUIREMENT (ADDED)

    Before ANY analysis:

    Verify the CSV loaded successfully

    Verify the TXT loaded successfully

    Verify the CSV is NOT empty

    Verify the portfolio list is NOT empty

    Print df.columns to detect actual column names

    You MUST adapt to the actual column names dynamically
    (e.g. if the CSV uses "date" instead of "Date", or "close_price" instead of "Close")

    If ANY of these conditions fail:
    YOU MUST STOP and return ONLY:
    "ERROR — Missing or unreadable data. Please provide the exact contents of both files."

    No analysis, no fallback example, no invented tickers.

    FINANCIAL ANALYSIS — RULES

    Your goal is NOT to describe a methodology.
    Your goal is to compute REAL metrics from the CSV and give REAL actions.

    For each stock in the portfolio (and ONLY these tickers):

    Compute the trend over 6 months.

    Compute simple momentum signals (e.g. last 5-day vs 20-day direction).

    Compute volatility (low/medium/high).

    Detect price cycles: local peaks, local bottoms.

    Determine whether the current price is:

    Near a recent low (potential BUY ON DIP)

    Mid-range (HOLD)

    Near a local high (possible TRIM/SELL)

    🔒 HARD RULE (ADDED)

    You MUST NOT introduce or analyze ANY ticker that is NOT present in my_portfolio.txt.
    Examples of forbidden tickers: AAPL, NVDA, MSFT, TSLA, unless they appear in the TXT.

    STRATEGIC OBJECTIVE — ADAPTED TO USER CONTEXT

    The user has 12k total capital.
    Therefore:

    Recommendations MUST consider limited capital.

    DO NOT suggest aggressive reinforcement.

    Each BUY must include a maximum suggested allocation (e.g. 100–400€).

    Each SELL must specify if the sale is urgent or optional.

    Focus only on 2 to 3 tickers per day that:

    Are at an interesting price point (dip or peak),

    Have actionable buy/sell signals,

    Have clear evidence from historical data.

    For each picked ticker:

    Clearly say:

    “BUY ON DIP (optional)”

    “BUY ON DIP (strong)”

    “HOLD”

    “TRIM”

    “SELL LIGHT”

    “EXIT”

    And explain whether action is:

    “Urgent”

    “Opportunistic”

    “Optional / low priority”

    JUSTIFICATION REQUIREMENTS

    For the 2–3 selected tickers, you MUST provide:

    A 6-month price chart.

    A chart or simple calculation showing why the stock is near a dip or peak.

    1–2 sentences explaining:

    why now is a good moment,

    what historical pattern suggests,

    short-term expectation (e.g. “typically rebounds within 10 days after similar dips”).

    🔒 HARD RULE (ADDED)

    You MUST NOT invent historical behavior.
    Any "rebound", "pullback", or “typically does X” must be computed from the CSV only.

    If you cannot compute it, do NOT mention it.

    Charts MUST be generated in Streamlit using matplotlib or plotly.

    STREAMLIT APPLICATION REQUIREMENTS

    The application MUST be ultra simple.

    It MUST include:

    st.title("Daily Tech Stock Advisor")

    A selector: “Select your focus tickers of the day” (default: the 2–3 recommended)

    A chart area for each selected ticker (price chart + justification chart)

    A small summary of the daily recommendations

    The Streamlit app must:

    Load the CSV + portfolio file

    Compute metrics live

    Display:

    The recommended 2–3 tickers for the day

    Their verdict (BUY / SELL / HOLD)

    The charts

    A short rationale

    No dashboard complexity. No extra features.

    CODE GENERATION — MANDATORY FORMAT

    Your answer MUST contain EXACTLY TWO SECTIONS:

    1) ANALYSIS_RESULT

    Human-readable summary:

    Daily market signals

    The 2–3 chosen tickers

    For each: the action + urgency + short justification

    Do NOT invent content. Must be fully data-driven.

    2) STREAMLIT_CODE

    A full Python script to be written into:
    ../src/streamlit_app.py

    The code must:

    Be self-contained

    Run end-to-end in Streamlit

    Include the visualizations and logic above

    Use clean Streamlit components only

    Avoid unnecessary complexity

    No extra commentary outside the code block.

    STYLE & BEHAVIOR

    NEVER produce generic or hypothetical finance explanations.

    Ground everything in the actual CSV values.

    If data is missing, ask for it.

    Be concise, clear, and practical.

    Focus on BUY/SELL moments in a cyclical market.

    NEVER hallucinate tickers, columns, or data.

    ALWAYS adapt to the real columns detected in the CSV.

    DATA SCHEMA & TICKER HANDLING (ADDED)

    The CSV contains a column (for example symbol) that holds the stock tickers (e.g. "PLTR", "META", "RACE", "NVDA", "TSLA", "MSFT", "AMZN").

    You MUST detect which column in the CSV corresponds to the ticker symbol. If a column named exactly symbol exists, you MUST use it as the authoritative source of tickers for filtering and analysis.

    You MUST restrict all per-ticker analysis to rows where this ticker column matches one of the tickers extracted from the TXT portfolio file.

    The TXT portfolio file contains one position per line, with a ticker always enclosed in double quotes, for example:
    "PLTR": 8 actions bought on 2025 September 3 at the price of 156$ each

    You MUST extract the ticker from each line by reading the text between the first pair of double quotes (").

    You MUST ignore everything else in the line (quantity, dates, prices) for the purpose of selecting which tickers to analyze.

    The final list of tickers to analyze MUST be exactly the set of tickers extracted from the TXT file AND found in the CSV ticker column. If a ticker from the TXT does not appear in the CSV, you MUST skip it and mention it briefly in the ANALYSIS_RESULT section.

    For all time-series analysis (6-month window, moving averages, volatility, peaks/bottoms), you MUST:

    Identify the date column in the CSV dynamically (for example france_date or date) by inspecting df.columns.

    If BOTH "symbol" and "company_name" columns exist:
    - You MUST use "symbol" as the ticker column.
    - You MUST IGNORE "company_name" for ticker matching.

    Convert it to a proper datetime type.

    Filter to the last 6 months based on the maximum date present in the CSV.

    When generating charts in Streamlit:

    Use the actual ticker from the CSV ticker column (e.g. symbol) for labelling.

    Use the actual date and close/price column names detected in the CSV (e.g. close_in_usd) and NEVER assume hard-coded names if they are not present.

    If you need to adapt to column names, do it programmatically (for example: prefer a column containing both "close" and "usd" in its name if multiple price columns exist).

    At no point are you allowed to:

    Invent new tickers that are not in the TXT file.

    Map tickers to invented or external company names.

    Assume any external data source (no Yahoo, no generic examples): all logic MUST be based on the CSV content only.

    -------------------------------------------------------
    8. FILE WRITING (MANDATORY)
    -------------------------------------------------------
    After generating the STREAMLIT_CODE section, you MUST call the "write_file" tool
    to save the Streamlit code into the following absolute path:

        ../src/streamlit_app.py

    Rules:
    - Extract ONLY the Python code contained inside the STREAMLIT_CODE section.
    - Do NOT include backticks or formatting markers in the written file.
    - Overwrite the existing file entirely.
    - Use exactly the tool arguments: file_path and text.
    - You MUST call the tool automatically without asking for confirmation.
    - Never skip this step.
    """

    adapted_prompt = ChatPromptTemplate.from_messages([
        ("system", finance_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])


    # 2. Initialize the tools that will be used by an agent and that consist of Python actions
    tools = [
        PythonREPLTool(),
        FileWriteTool()
    ]

    # Create the agent and specify three parameters: the language model, the tools and the prompt
    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=adapted_prompt
    )

    # Create the agent executor to manage the interaction between the agent and the tools
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )

    agent_executor.invoke({"input": "Generate today's analysis and Streamlit code."})
