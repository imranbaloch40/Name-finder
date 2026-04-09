import streamlit as st
from curl_cffi import requests # Upgraded for TLS fingerprinting
from bs4 import BeautifulSoup

def fetch_sim_data_stealth(query):
    # 'impersonate' makes the request look exactly like a real Chrome browser
    session = requests.Session()
    base_url = "https://paksiminfo.org/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": base_url,
    }

    try:
        # 1. Warm up the session (GET)
        response = session.get(base_url, headers=headers, impersonate="chrome120")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Extract CSRF token
        csrf_tag = soup.find('meta', {'name': 'csrf-token'})
        csrf_token = csrf_tag['content'] if csrf_tag else None

        if not csrf_token:
            return "Error: Could not find CSRF token. The site might be blocking you."

        # 3. Perform Search (POST)
        payload = {'csrf_token': csrf_token, 'query': query}
        post_response = session.post(base_url, data=payload, headers=headers, impersonate="chrome120")
        
        # --- DEBUG CHECK ---
        if "Verify you are human" in post_response.text or "Cloudflare" in post_response.text:
            return "BLOCKED: The website is asking for a CAPTCHA. Try again later or solve one in your browser first."

        # 4. Parse Results
        result_soup = BeautifulSoup(post_response.text, 'html.parser')
        table = result_soup.find('table', {'id': 'resultsTable'})
        
        if not table:
            return "No records found. The site might have returned an empty page."

        # Extract all rows from the table directly (handles missing tbody safely)
        rows = table.find_all('tr')
        results = []
        for row in rows:
            cols = row.find_all(['td', 'th']) # some tables might use th for data by mistake, but we focus on columns
            
            # Usually the first row is headers. We can check if it's actual data by the number of cols
            # Only process if we have enough columns and it is not a header row
            if len(cols) >= 4 and cols[0].name == 'td':
                results.append({
                    "Mobile": cols[0].text.strip(),
                    "Name": cols[1].text.strip(),
                    "CNIC": cols[2].text.strip(),
                    "Address": cols[3].text.strip()
                })
        return results

    except Exception as e:
        return f"System Error: {str(e)}"

# --- Streamlit UI ---
st.title("🔍 Pak SIM Stealth Lookup")

target = st.text_input("Enter Number", value="03-------")

if st.button("Search"):
    with st.spinner("Bypassing security..."):
        data = fetch_sim_data_stealth(target)
        if isinstance(data, list):
            st.success("Data Retrieved!")
            st.table(data)
        else:
            st.error(data)
            # Show a snippet of what the site actually sent back
            with st.expander("See Raw Debug Info"):
                st.write("This is what the server sent instead of data:")
                st.code(data[:500])