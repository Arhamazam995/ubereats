# UberEats Scraper

A simple web scraper built with Scrapy to extract restaurant data and product details from UberEats using location and restaurant URLs.

## Features

- Scrape menu items with prices and descriptions
- Handle product customizations and options
- Accepts dynamic input for location and restaurant URL

## Getting Started

### Prerequisites

- Python version(3.13) "https://www.python.org/downloads/"
- pip version(25.1.1) "https://packaging.python.org/tutorials/installing-packages/"
- Git "https://github.com/"

### Installation

1. Install required dependencies:
 
- pip install -r requirements.txt (scrapy 2.13.2)
- create virtual environment
- setup your virtual environment
- active your virtual environment

2. Usage

- (run command)
scrapy crawl ubereates -a location="New York, NY" -a restaurant_url="https://www.ubereats.com/store/example-restaurant-id"

3. Output example

{
  "Title": "Caffè Latte",
  "Price": "$5.10, 151 Cal.",
  "Image url": "image_url",
  "Uuid" : "234567889966"
  "Item Description": "Our dark, rich espresso is balanced with steamed milk...",
  "Customizations": [...],
}

4. Folder stucture:
 
ubereats-scraper/
│
├── ubereats/
│   ├── spiders/
│   │   └── ubereats_spider.py
│   ├── items.py
│   ├── pipelines.py
│   └── settings.py
│
├── requirements.txt
├── scrapy.cfg
└── README.md 

5. Clone the repository:

```bash
git clone https://github.com/yourusername/ubereats-scraper.git
cd ubereats-scraper
