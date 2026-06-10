import pandas as pd

# Load raw dataset
df = pd.read_csv("D:/paradise/backend/data/NIFTY 50.csv")

# Convert Date column
df["Date"] = pd.to_datetime(df["Date"])

# Sort by Date
df = df.sort_values("Date")

# Calculate daily return
df["Return"] = df["Close"].pct_change()

# Remove first NA
df = df.dropna()

# Convert to annual returns
df["Year"] = df["Date"].dt.year
annual_returns = df.groupby("Year")["Return"].sum()

# Save processed dataset
annual_returns.to_csv("nifty_annual_returns.csv")

print("Annual returns file created successfully.")