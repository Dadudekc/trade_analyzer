import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to perform sentiment analysis using TextBlob and VADER
def analyze_sentiment(data):
    analyzer = SentimentIntensityAnalyzer()
    data['textblob_sentiment'] = data['content'].apply(lambda x: TextBlob(x).sentiment.polarity)
    data['vader_sentiment'] = data['content'].apply(lambda x: analyzer.polarity_scores(x)['compound'])
    return data

# Sample data
messages = [
    {'timestamp': '2024-06-04 23:01:50', 'content': '$TSLA hurry up 6/13, this stock will be $120 Bearish'},
    {'timestamp': '2024-06-04 22:38:23', 'content': '$TSLA Baron Capital CEO Ron Baron will appear on @SquawkCNBC tomorrow, June 5 at 7:30 a.m. ET.'}
]

# Convert to DataFrame
sentiment_data = pd.DataFrame(messages)

# Perform sentiment analysis
sentiment_data = analyze_sentiment(sentiment_data)

# Generate HTML
html_content = f"""
<html>
<head>
    <title>Stock Data and News Headlines</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .stock-table, .news-headlines, .sentiment-table {{ margin: 20px; }}
        .stock-table th, .stock-table td, .sentiment-table th, .sentiment-table td {{ padding: 10px; border: 1px solid #ccc; }}
        .news-headlines h2 {{ font-size: 1.2em; }}
    </style>
    <script>
        function sortTable(n, tableName) {{
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.getElementById(tableName);
            switching = true;
            dir = "asc"; 
            while (switching) {{
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    if (dir == "asc") {{
                        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }} else if (dir == "desc") {{
                        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                            shouldSwitch = true;
                            break;
                        }}
                    }}
                }}
                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++; 
                }} else {{
                    if (switchcount == 0 && dir == "asc") {{
                        dir = "desc";
                        switching = true;
                    }}
                }}
            }}
        }}
    </script>
</head>
<body>
    <h1>Stock Data</h1>
    <table id="stockTable" class="stock-table">
        <tr><th onclick="sortTable(0, 'stockTable')">Stock Name</th><th onclick="sortTable(1, 'stockTable')">Stock Price</th></tr>
    </table>
    <h1>News Headlines</h1>
    <div class="news-headlines">
    </div>
    <h1>Sentiment Analysis</h1>
    <table id="sentimentTable" class="sentiment-table">
        <tr><th onclick="sortTable(0, 'sentimentTable')">Timestamp</th><th onclick="sortTable(1, 'sentimentTable')">Content</th><th onclick="sortTable(2, 'sentimentTable')">TextBlob Sentiment</th><th onclick="sortTable(3, 'sentimentTable')">VADER Sentiment</th></tr>
        {''.join([f"<tr><td>{row['timestamp']}</td><td>{row['content']}</td><td>{row['textblob_sentiment']}</td><td>{row['vader_sentiment']}</td></tr>" for _, row in sentiment_data.iterrows()])}
    </table>
</body>
</html>
"""

with open('stock_data_output.html', 'w') as file:
    file.write(html_content)
    
print("HTML output saved to stock_data_output.html")
