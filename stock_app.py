import streamlit as st
import os
import yfinance as yf
import requests
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
from sqlite_backend import init_db, save_to_sqlite, retrieve_from_sqlite, check_table_exists

# Load environment variables
load_dotenv()

# Set OpenAI API key and NewsAPI key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY") # Make sure to add your NewsAPI key in the .env file

# Ensure the SQLite database is initialized
init_db()

# Verify that the table exists
if not check_table_exists():
    st.error("Table 'analysis_data' could not be created. Please check your database setup.")
else:
    print("Table 'analysis_data' is confirmed to exist.")

# Streamlit configuration
st.set_page_config(page_title="Stock Market Analysis & Investment (India)", page_icon="💹")
st.title("Stock Market Analysis & Investment (India)")

# Initialize session state for storing analysis content
if "analysis_content" not in st.session_state:
    st.session_state.analysis_content = ""

# Input fields for trading inputs
stock_symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE)")
initial_capital = st.number_input("Enter Initial Capital in ₹ (e.g., 100000)", min_value=0)
risk_tolerance = st.selectbox("Select Risk Tolerance", ["Low", "Moderate", "High"])
trading_strategy = st.text_input("Enter Trading Strategy (e.g., Value Investing, Momentum)")
investment_horizon = st.selectbox("Investment Horizon", ["Short-term", "Long-term"])
portfolio_diversification = st.number_input("Portfolio Diversification Percentage", min_value=0, max_value=100)
period = st.selectbox("Select Data Period", ["1mo", "3mo", "6mo", "1y", "5y", "10y"])

# Display the initial capital and other inputs using the rupee symbol in output (if applicable)
st.write(f"Initial Capital: ₹{initial_capital}")

# Define a function to fetch stock data with technical indicators using yfinance
def fetch_stock_data(symbol, period="1y"):
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)

    # Technical Indicators
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Upper_BB'] = data['Close'].rolling(window=20).mean() + (data['Close'].rolling(window=20).std() * 2)
    data['Lower_BB'] = data['Close'].rolling(window=20).mean() - (data['Close'].rolling(window=20).std() * 2)

    return data

# Fetch fundamental data
def fetch_fundamental_data(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    return {
        "Market Cap": info.get("marketCap"),
        "P/E Ratio": info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "Debt/Equity Ratio": info.get("debtToEquity")
    }

# Fetch real-time news using NewsAPI
def fetch_realtime_news(stock_symbol):
    url = f"https://newsapi.ai/api/v1/news?apikey={NEWSAPI_KEY}&q={stock_symbol}&language=en"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()
            news_articles = [
                {"title": article["title"], "description": article["description"]}
                for article in news_data["articles"][:5]  # Limit to the top 5 articles
            ]
            return news_articles
        else:
            print("Error fetching news:", response.status_code, response.text)
            return []
    except Exception as e:
        print("Error fetching news:", e)
        return []

# Display stock data with indicators
if stock_symbol:
    stock_data = fetch_stock_data(stock_symbol, period)
    st.write(f"Stock Data with Indicators for {stock_symbol}")
    st.line_chart(stock_data[['Close', 'MA50', 'MA200', 'Upper_BB', 'Lower_BB']])
    st.line_chart(stock_data['RSI'])

# Display fundamental data and economic indicators
fundamentals = fetch_fundamental_data(stock_symbol) if stock_symbol else {}
st.write("Fundamental Analysis")
st.json(fundamentals)

st.write("Real-Time News")
news_articles = fetch_realtime_news(stock_symbol)
for article in news_articles:
    st.write(f"{article['title']}\n{article['description']}")

# Define Stock Analyst and Investment Advisor Agents
stock_analyst = Agent(
    role='Stock Analyst',
    goal=f'Analyze market trends, price patterns, and performance indicators for {stock_symbol}.',
    verbose=True,
    memory=True,
    backstory="Expert in stock market analysis, providing key insights on price patterns, trends, and potential risks.",
    allow_delegation=True
)

# Pass the latest news as part of the goal for investment advice
investment_advisor = Agent(
    role='Investment Advisor',
    goal=(
        f"Provide investment advice for {stock_symbol}, based on an initial capital of ₹{initial_capital}, "
        f"a {risk_tolerance} risk tolerance, and a {trading_strategy} strategy. Consider a {investment_horizon} horizon, "
        f"{portfolio_diversification}% diversification, technical indicators, fundamentals, and recent news updates. "
        f"The latest news includes the following: {news_articles}."
    ),
    verbose=True,
    memory=True,
    backstory="Knowledgeable in finance and investment, offers insights into optimizing capital allocation and managing risks.",
    allow_delegation=False
)

# Define Tasks for Analysis and Investment Advice
analysis_task = Task(
    description=f"Analyze stock {stock_symbol} using technical indicators and fundamentals over {period} with a {investment_horizon} perspective.",
    expected_output="Summary of stock trends, key indicators, and risk factors relevant to {stock_symbol}.",
    agent=stock_analyst
)

advice_task = Task(
    description=f"Recommend an investment strategy for {stock_symbol} with an initial capital of ₹{initial_capital}, "
                f"considering {risk_tolerance} risk, a {investment_horizon} horizon, and {portfolio_diversification}% diversification.",
    expected_output="Investment strategy with risk management techniques and capital allocation tips, incorporating recent news updates.",
    agent=investment_advisor,
    async_execution=False,
    output_file='investment-advice.md'
)

# Button to Generate Analysis and Investment Advice
if st.button("Generate Analysis & Advice"):
    if stock_symbol and initial_capital > 0:
        crew = Crew(
            agents=[stock_analyst, investment_advisor],
            tasks=[analysis_task, advice_task],
            process=Process.sequential,
            memory=True,
            cache=True,
            max_rpm=100,
            share_crew=True
        )

        result = crew.kickoff(inputs={
            'stock_symbol': stock_symbol,
            'initial_capital': initial_capital,
            'risk_tolerance': risk_tolerance,
            'trading_strategy': trading_strategy,
            'investment_horizon': investment_horizon,
            'portfolio_diversification': portfolio_diversification
        })

        if os.path.exists("investment-advice.md"):
            with open("investment-advice.md", "r") as file:
                st.session_state.analysis_content = file.read()
                st.markdown(st.session_state.analysis_content)
        else:
            st.error("Failed to generate analysis and advice. Please try again.")
    else:
        st.error("Please enter all required trading inputs.")

# Button to Save Analysis and Advice
if st.button("Save"):
    if st.session_state.analysis_content:
        parameters = f"₹{initial_capital}-{risk_tolerance}-{trading_strategy}"
        save_to_sqlite(stock_symbol, parameters, st.session_state.analysis_content)
        st.success("Analysis and advice saved successfully!")
    else:
        st.error("Please generate the analysis and advice first before saving.")

# Button to Retrieve Analysis and Advice
if st.button("Retrieve Previous Analysis"):
    if stock_symbol and initial_capital > 0:
        parameters = f"₹{initial_capital}-{risk_tolerance}-{trading_strategy}"
        previous_content = retrieve_from_sqlite(stock_symbol, parameters)
        if previous_content:
            st.markdown(previous_content)
        else:
            st.error("No previous analysis found for these parameters.")
    else:
        st.error("Please enter the required inputs to retrieve previous analysis.")
