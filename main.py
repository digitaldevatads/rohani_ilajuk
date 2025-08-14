from fastapi import FastAPI, Query
from typing import List, Optional
import requests
import os

app = FastAPI()

# Read API key from environment variable set in Render
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

def get_business_count(zip_code: str) -> Optional[int]:
    url = (
        f"https://api.census.gov/data/2022/cbp"
        f"?get=ESTAB"
        f"&for=zip%20code%20tabulation%20area:{zip_code}"
        f"&key={CENSUS_API_KEY}"
    )
    try:
        r = requests.get(url)
        data = r.json()
        if len(data) > 1:
            return int(data[1][0])
    except:
        pass
    return None

@app.get("/api/housing-data/")
def get_housing_data(
    zip_codes: List[str] = Query(..., description="List of ZIP codes"),
    min_owner_occupied: Optional[float] = Query(None, description="Min % owner-occupied filter")
):
    results = []

    for zip_code in zip_codes:
        try:
            url = (
                f"https://api.census.gov/data/2022/acs/acs5"
                f"?get=B25001_001E,B25003_002E,B25003_003E,B25024_002E,B25032_010E"
                f"&for=zip%20code%20tabulation%20area:{zip_code}"
                f"&key={CENSUS_API_KEY}"
            )
            res = requests.get(url)
            data = res.json()

            if len(data) < 2:
                results.append({"zip_code": zip_code, "error": "No data found"})
                continue

            headers, values = data
            total_units = int(values[0])
            owner_occupied = int(values[1])
            renter_occupied = int(values[2])
            single_family_detached = int(values[3])
            apartments = int(values[4])

            percent_owner_occupied = round(owner_occupied / total_units * 100, 2) if total_units else 0
            business_count = get_business_count(zip_code)

            if min_owner_occupied is not None and percent_owner_occupied < min_owner_occupied:
                continue

            results.append({
                "zip_code": zip_code,
                "total_units": total_units,
                "owner_occupied_units": owner_occupied,
                "renter_occupied_units": renter_occupied,
                "single_family_detached_units": single_family_detached,
                "apartments_units": apartments,
                "business_establishments": business_count if business_count is not None else "data_unavailable",
                "percent_owner_occupied": percent_owner_occupied,
            })

        except Exception as e:
            results.append({"zip_code": zip_code, "error": str(e)})

    return {"results": results}
