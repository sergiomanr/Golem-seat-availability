from playwright.sync_api import sync_playwright
import re
import json
import http.server
import socketserver
import webbrowser

def start_server():
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    # Use allow_reuse_address to prevent "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\nDashboard ready at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        webbrowser.open(f"http://localhost:{PORT}")
        httpd.serve_forever()

def run_scraper():
    with sync_playwright() as p:
        all_movies_data = {}
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Loading the main page...")
        # Open the main page
        page.goto("https://www.golem.es/golem/golem-madrid", wait_until="networkidle")
        # page.wait_for_timeout(2000) # Give dynamic content time to load

        # --- THE COOKIE DESTROYER ---
        print("\n--- CHECKING FOR COOKIES ---")
        try:
            # Search for the div with id "cookiescript_accept"
            accept_btn = page.locator("#cookiescript_accept")
            
            if accept_btn.count() > 0 and accept_btn.is_visible():
                print("Cookie banner detected! Clicking 'ACEPTAR'...")
                accept_btn.click()
                page.wait_for_timeout(1500) # Give it time to fade away
            else:
                print("No cookie banner visible. Proceeding...")
        except Exception as e:
            print(f"Could not click cookie banner: {e}")
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
                        # full_url = href if href.startswith("http") else f"https://entradasfilmoteca.sacatuentrada.es{href}"
                        movie_urls.add(href)

        # print("\n--- HARVESTING LINKS PAGE 2---")
        # page.goto("https://entradasfilmoteca.sacatuentrada.es/es/busqueda?&pagina=2", wait_until="networkidle")
        # links_2 = page.locator("a").all()

        # for link in links_2:
        #     raw_href = link.get_attribute("href")
        #     if raw_href:
        #         href = raw_href.strip()
        #         if "/es/entradas/" in href:
        #             if len(href.strip("/").split("/")) >= 3: 
        #                 full_url = href if href.startswith("http") else f"https://entradasfilmoteca.sacatuentrada.es{href}"
        #                 movie_urls.add(full_url)

        print(f"Found {len(movie_urls)} unique, clean movie pages!")
        # print(movie_urls)

        print("\n--- VISITING EACH MOVIE ---")
        movie_urls_2 = []
        for url in movie_urls:
            movie_plus_date =[]
            movie_plus_date.append(url.split("/")[-1])
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            links_4 = page.locator("a").all()
            for link in links_4:
                raw_href = link.get_attribute("href")
                if raw_href:
                    href = raw_href.strip()
                    if "/numeradas/" in href:
                        movie_plus_date.append(href)
                        movie_plus_date.append(page.locator("div.calendario_reserva.row").first.inner_text().strip())
                        movie_urls_2.append(movie_plus_date)

        # for url in movie_urls_2:
        #         good_url = url[1]
        #         date = url[0]
        #         Room = url[2]
        #         time = Room[:5]
                
        #         if Room[13] == "1":
        #             room = "Sala 1"
        #         else:
        #             room = "Sala 2"
        #         print(f"\nLoading: {good_url}")
        #         page.goto(good_url, wait_until="networkidle")
                
        #         try:
        #             movie_title = page.locator("h1").first.inner_text().strip()
        #         except:
        #             movie_title = "Unknown Movie - " + good_url.split("/")[-2]

        #         print(f"   -> Scraping seats for: {movie_title}")
                
        #         try:
        #             page.wait_for_selector("span.butaca", timeout=5000)
        #         except:
        #             print("   -> No seats found. Might be general admission or sold out.")
        #             continue

        #         movie_seats = {
        #             "available_seats": [],
        #             "occupied_seats": []
        #         }

        #         seats = page.locator("span.butaca").all()
        #         for seat in seats:
        #             seat_class = seat.get_attribute("class") or ""
        #             seat_id = seat.get_attribute("id")
                    
        #             if "green" in seat_class:
        #                 movie_seats["available_seats"].append({
        #                     "id": seat_id,
        #                     "status": "green (available)",
        #                     "puerta": seat.get_attribute("name-puerta"),
        #                     "row": seat.get_attribute("data-option-fila"),
        #                     "number": seat.get_attribute("data-option-numero"),
        #                 })
        #             elif "grey" in seat_class:
        #                 movie_seats["occupied_seats"].append({
        #                     "id": seat_id,
        #                     "status": "grey (occupied)",
        #                     "puerta": "Unknown (Data hidden by website)"
        #                 })
        #             movie_seats["Date"] = date
        #             movie_seats["Time"] = time
        #             movie_seats["Room"] = room
        #         print(f"   -> Found {len(movie_seats['available_seats'])} available and {len(movie_seats['occupied_seats'])} occupied seats.")
        #         all_movies_data[movie_title] = movie_seats

        # browser.close()

        # --- SAVE TO JSON ---
        print("\n--- SAVING DATA ---")
        with open("movies_data.json", "w", encoding="utf-8") as json_file:
            json.dump(all_movies_data, json_file, indent=4, ensure_ascii=False)
        
        print("Success! Data saved to 'movies_data.json'.")

if __name__ == "__main__":
    run_scraper()
    # start_server()
