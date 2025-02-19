# Transfermarkt Scraper - 2010 to 2024

This project contains a scraper designed to extract data from the 5 major European football leagues:
- **Premier League**
- **Bundesliga**
- **Serie A**
- **La Liga**
- **Ligue 1**

The scraper operates for each season from 2010 to 2024 and collects information for every player from clubs that have participated in these leagues during this period. The extracted details include:
- **Market Value**
- **Age**
- **Team**
- **Role**
- **Nationality**
- **Shirt Number**

## Features

- **Season Iteration:** Loops through each league and season from 2010 to 2024.
- **Club Data Extraction:** For every club, the scraper gathers player data.
- **S3 Upload:** Extracted data is saved to Amazon S3 (requires proper AWS configuration).

## Requirements

- Python 3.x
- The following Python libraries (installable via `pip`):
  - `requests`
  - `beautifulsoup4`
  - `boto3`
  - `pandas`

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/FrancyToschi/scraper-transfermarkt.git
# scraper-transfermarkt
