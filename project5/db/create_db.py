import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

engine = create_engine(
    "postgresql+psycopg2://openpg:openpgpwd@localhost:5432/energy_ml"
)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "2016_Building_Energy_Benchmarking.csv"

df = pd.read_csv(DATA_PATH)

df = df[[
    "OSEBuildingID",
    "PrimaryPropertyType",
    "PropertyGFATotal",
    "YearBuilt",
    "SiteEnergyUse(kBtu)"
]]

df.columns = [
    "building_id",
    "primary_property_type",
    "gross_floor_area",
    "year_built",
    "site_energy_use"
]

df.to_sql("buildings", engine, if_exists="append", index=False)

print("Dataset inséré en base avec succès")
