# Movie Night Watchlist

This is a flask web application that helps you manage your movie watchlist and randomly picks what to watch next.

# Tech Stack

backend - Flask
API - OMDB 
frontend - just html css 

# screenshots

# why I made this?

I made this for ysws called slushies in hackclub, this was a lowkey cool project, it was fun to make

# note

This project is not scalable, It has ratelimits enforced tho

# Installation

1. Clone the repository

```bash
git clone https://github.com/kusuta012/mvwl.git
cd mvwl
```

2. create a virtual environment

```bash
pip install uv
uv venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
uv pip install -r requirements.txt
```

4. Set up environment variables
```bash
export OMDB_API_KEY='your_api_key_here'
export SECRET_KEY='your_secret_key_here'
```

5. Get your api key from https://www.omdbapi.com/apikey.aspx

6. Run app.py

```bash
python app.py
```

Yayy!!, ENjoy

