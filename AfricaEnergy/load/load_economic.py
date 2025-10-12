import os 
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client.get_database("africa_energy")
collection = db.get_collection("social_collection")

def load_social_data(collection):
    try:
        df = pd.read_csv("/home/deecodes/internship/AfricaEnergy/staging_data/africa_social_and_economic_data.csv")
        df = df.drop(columns=["Unnamed: 0"], errors="ignore")
        df = df.dropna(axis=1, how='all')
        data_dict = df.to_dict("records")

        if data_dict:
            collection.insert_many(data_dict)
            print(f"Loaded {collection.count_documents({})} documents into {collection.name} successfully!")
    except Exception as e:
        print(f"Error loading data to collection: {e}")

if __name__ == "__main__":
    load_social_data(collection)
