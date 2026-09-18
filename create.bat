echo streamlit > requirements.txt
echo supabase >> requirements.txt
echo pandas >> requirements.txt
echo python-dotenv >> requirements.txt

echo __pycache__/ > .gitignore
echo *.py[cod] >> .gitignore
echo .env >> .gitignore

echo SUPABASE_URL=https://dzirkiytixfmqspzxdvq.supabase.co > .env
echo SUPABASE_KEY=your_anon_publishable_key_here >> .env