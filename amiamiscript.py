import amiami
import os
from curl_cffi import requests
from pymongo import MongoClient
from bson import ObjectId

# Discord webhook URL
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# MongoDB connection string
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

# Connect to MongoDB
client = MongoClient(MONGO_CONNECTION_STRING)
db = client['amiami_database']
collection = db['item_availability']

# Function to send a message to Discord
def send_discord_message(item):
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL environment variable is not set.")
        return
    
    embed = {
        "title": item.productName,
        "url": f"{item.productURL}",
        "thumbnail": {"url": f"{item.imageURL}"},
        "fields": [
            {"name": "Price", "value": f"¥{item.price}", "inline": True},
            {"name": "Product Code", "value": f"{item.productCode}", "inline": True},
            {"name": "Availability", "value": f"{item.availability}", "inline": True}
        ]
    }
    
    data = {
        "embeds": [embed]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
        print(f"Sent update for: {item.productName}")
    except Exception as e:
        print(f"Failed to send Discord message: {str(e)}")

def amiami_search():
    lines = get_search_terms()
    for line in lines:
        if line:  # Skip empty lines
            try:
                results = amiami.search(line,
                        s_st_list_preorder_available=1,
                        s_st_list_backorder_available=1,
                        s_st_list_newitem_available=1,
                        s_st_condition_flg=1,
                        s_cate_tag=37,
                        s_maker_id=97)
                
                for item in results.items:
                    item_id = item.productCode
                    is_available = item.availability
                    
                    # Check if the item exists in the database
                    existing_item = collection.find_one({"productCode": item_id})
                    
                    if existing_item:
                        if existing_item['availability'] != is_available:
                            send_discord_message(item)
                            # Update the availability in the database
                            collection.update_one(
                                {"productCode": item_id},
                                {"$set": {"availability": is_available}}
                            )
                    else:
                        if is_available:
                            send_discord_message(item)
                            # Insert the new item into the database
                            collection.insert_one({
                                "productCode": item_id,
                                "availability": is_available
                            })
                
                print("\n")
            except Exception as e:
                print(f"Error searching for '{line}': {str(e)}")

def get_search_terms():
    search_terms = os.getenv('AMIAMI_SEARCH_TERMS')
    if not search_terms:
        print("Error: AMIAMI_SEARCH_TERMS environment variable is not set.")
        return []
    return [term.strip() for term in search_terms.split(',')]

if __name__ == "__main__":
    amiami_search()