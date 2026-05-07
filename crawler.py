from playwright.sync_api import sync_playwright
import re
import json
import http.server
import socketserver
import webbrowser

def start_server():
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\nDashboard ready at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()

free = 0
occupied = 0
def run_scraper():
    global free, occupied
    with sync_playwright() as p:
        all_movies_data = {}
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading the main page...")
        # Open the main page
        page.goto("https://www.golem.es/golem/golem-madrid", wait_until="domcontentloaded")
        # page.wait_for_timeout(2000) # Give dynamic content time to load

        # --- THE COOKIE DESTROYER ---
        # print("\n--- CHECKING FOR COOKIES ---")
        # try:
        #     # Search for the div with id "cookiescript_accept"
        #     accept_btn = page.locator("#cookiescript_accept")
            
        #     if accept_btn.count() > 0 and accept_btn.is_visible():
        #         print("Cookie banner detected! Clicking 'ACEPTAR'...")
        #         accept_btn.click()
        #         page.wait_for_timeout(1500) # Give it time to fade away
        #     else:
        #         print("No cookie banner visible. Proceeding...")
        # except Exception as e:
        #     print(f"Could not click cookie banner: {e}")
        # ----------------------------

        print("\n--- HARVESTING LINKS ---")
        links = page.locator("a").all()
        movie_urls = set() 
        
        for link in links:
            raw_href = link.get_attribute("href")
            
            if raw_href:
                href = raw_href.strip()
                if "/golem/pelicula/" in href:
                    if len(href.strip("/").split("/")) >= 3: 
                        full_url = href if href.startswith("http") else f"https://www.golem.es{href}"
                        movie_urls.add(full_url)

        print(f"Found {len(movie_urls)} unique, clean movie pages!")

        print("\n--- VISITING EACH MOVIE ---")
        movie_urls_2 = []
        for url in movie_urls:

            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            links_4 = page.locator("a").all()
            for link in links_4:
                raw_href = link.get_attribute("href")
                if raw_href:
                    href = raw_href.strip()
                    if "madrid.admit-one.eu" in href:
                        movie_urls_2.append(href)


        final_screening_urls = []
        for url in movie_urls_2:
            print(f"\nVisiting ticket page: {url}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            screenings_per_movie = []
            try:
                screening_links = page.locator("div.my-4").first.locator("a").all()
                for link in screening_links:
                    href = link.get_attribute("href")
                    if href:
                        screenings_per_movie.append(href)
            except Exception as e:
                print(f"Could not extract screening links: {e}")
            final_screening_urls.append(screenings_per_movie)
            

        for movie in final_screening_urls:
            all_seats_per_screening = {}
            for screening in movie:
                page.goto(screening, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)


                seats = page.locator("span.as_1, span.us_1, span.us_1_res").all()
                movie_seats_for_screening = {
                    "available_seats": [],
                    "occupied_seats": [],
                    "reserved_seats":[]
                }

                try:
                    page.wait_for_selector("span.as_1", timeout=5000)
                except:
                    print("   -> No seats found. Might be general admission or sold out.")
                    continue
                
                try:
                    movie_title = page.locator("h3").nth(6).inner_text().strip()
                except:
                    movie_title = "Unknown Movie"
                
                try:
                    performance_html = page.locator('div[id^="a1web-cart-performance-detailed-"]').first.inner_html()
                    room = f'Sala {performance_html.split(">")[1].split(" ")[4][:2]}'
                    date = ' '.join(performance_html.split(">")[3].split(" ")[:3])
                    time = str(performance_html.split(">")[3].split(" ")[5][:-3])
                except:
                    performance_html = "Not found"
                    room = "Unknown Room"
                    date = "Unknown Date"
                    time = "Unknown Time"

                # For the occupied seats
                last_known_id = 0

                for seat in seats:
                    seat_class = seat.get_attribute("class")
                    
                    try:
                        seat_id = seat.get_attribute("id")
                    except:
                            seat_id = 0


                    if "as_1" in seat_class:
                        last_known_id = int(seat_id[1:])
                        movie_seats_for_screening["available_seats"].append({
                            "id": seat_id,
                            "status": "green (available)"
                        })
                    elif "us_1" == seat_class:
                        last_known_id +=1
                        movie_seats_for_screening["occupied_seats"].append({
                            "id": "s"+str(last_known_id),
                            "status": "grey (occupied)"
                        })
                    elif "us_1_res" == seat_class:
                        movie_seats_for_screening["reserved_seats"].append({
                            "id": "s"+str(last_known_id),
                            "status": "grey (occupied)"
                        })
                    
                    movie_seats_for_screening["Date"] = date
                    movie_seats_for_screening["Room"] = room
                # print(f"   -> Found {len(movie_seats_for_screening['available_seats'])} available and {len(movie_seats_for_screening['occupied_seats'])} occupied seats and {len(movie_seats_for_screening['reserved_seats'])} reserved seats.")
                all_seats_per_screening[time] = movie_seats_for_screening
                free += len(movie_seats_for_screening['available_seats'])
                occupied += len(movie_seats_for_screening['occupied_seats'])

            all_movies_data[movie_title] = all_seats_per_screening
                

        # browser.close()

        # --- SAVE TO JSON ---
        print("\n--- SAVING DATA ---")
        all_movies_data["total_free"] = free
        all_movies_data["total_occupied"] = occupied
        with open("movies_data.json", "w", encoding="utf-8") as json_file:
            json.dump(all_movies_data, json_file, indent=4, ensure_ascii=False)
        
        print("Success! Data saved to 'movies_data.json'.")

if __name__ == "__main__":
    run_scraper()
    start_server()
