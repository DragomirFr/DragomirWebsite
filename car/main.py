from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import uvicorn


app = FastAPI(
    title="Vehicle Lookup API",
    description="Vehicle data scraper using FullCarChecks",
    version="1.0"
)


async def scrape_vehicle(registration: str):

    registration = registration.upper().replace(" ", "")

    url = f"https://fullcarchecks.co.uk/freecheck?reg={registration}"


    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()


        try:

            await page.goto(
                url,
                wait_until="networkidle",
                timeout=60000
            )


            # Allow JS content to fully render
            await page.wait_for_timeout(3000)


            html = await page.content()


            soup = BeautifulSoup(
                html,
                "lxml"
            )


            text = soup.get_text(
                "\n",
                strip=True
            )


            print(f"\nFull check results for {registration}\n")


            vehicle = {
                "registration": registration,
                "make": None,
                "model": None,
                "year": None,
                "motExpiry": None,
                "colour": None,
                "fuelType": None,
                "engineSize": None
            }


            # -------------------------
            # Get Vehicle Description
            # -------------------------

            if "Vehicle Description" in text:

                description = text.split(
                    "Vehicle Description",
                    1
                )[1]

            else:

                description = text



            # -------------------------
            # Manufacturer
            # -------------------------

            make = re.search(
                r"Manufacturer\s*\n(.+)",
                description
            )

            if make:

                vehicle["make"] = make.group(1).strip()



            # -------------------------
            # Model
            # -------------------------

            model = re.search(
                r"Model\s*\n(.+)",
                description
            )

            if model:

                vehicle["model"] = model.group(1).strip()



            # -------------------------
            # Year
            # -------------------------

            year = re.search(
                r"Year\s*\n(\d{4})",
                description
            )

            if year:

                vehicle["year"] = year.group(1)



            # -------------------------
            # Colour
            # -------------------------

            colour = re.search(
                r"Colour\s*\n(.+)",
                description
            )

            if colour:

                vehicle["colour"] = colour.group(1).strip()



            # -------------------------
            # Fuel Type
            # -------------------------

            fuel = re.search(
                r"Fuel Type\s*\n(.+)",
                description
            )

            if fuel:

                vehicle["fuelType"] = fuel.group(1).strip()



            # -------------------------
            # Engine Size
            # -------------------------

            engine = re.search(
                r"Engine Size\s*\n(.+)",
                description
            )

            if engine:

                vehicle["engineSize"] = engine.group(1).strip()



            # -------------------------
            # MOT Expiry
            # -------------------------

            mot = re.search(
                r"MOT Expiry\s*\n(.+)",
                text
            )

            if mot:

                vehicle["motExpiry"] = mot.group(1).strip()



            await browser.close()


            return vehicle



        except Exception as e:


            await browser.close()


            raise Exception(
                f"Scraping failed: {str(e)}"
            )





@app.get("/car")
async def get_car(reg: str):


    if not reg:

        raise HTTPException(
            status_code=400,
            detail="Registration number required"
        )


    try:

        vehicle = await scrape_vehicle(
            reg
        )


        return {

            "success": True,
            "vehicle": vehicle

        }


    except Exception as e:


        return {

            "success": False,
            "error": str(e)

        }





@app.get("/")
async def home():

    return {

        "status": "online",
        "message": "Vehicle API running"

    }





if __name__ == "__main__":

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000

    )
