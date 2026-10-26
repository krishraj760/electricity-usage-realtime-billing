sweden_eic_bidding_zones = {"SE_1": 'SE1', "SE_2":'SE2', "SE_3":'SE3', "SE_4":'SE4'}

import os
from azure.identity import DefaultAzureCredential
import pandas as pd
from entsoe import Client
import json

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from azure.eventhub import EventHubProducerClient, EventData

# 1. INITIALIZATION: Setup your configuration
EVENTHUB_FQDN = os.environ.get("EVENTHUB_FQDN", "entsoeelectricityusagepricing.servicebus.windows.net")
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "day-ahead-pricing")


# 1. Define your target time zone
tz = ZoneInfo("Europe/Stockholm")

# 2. Get the current date/time in that specific time zone
current_time_in_tz = datetime.now(tz)

# 3. Add 1 day to calculate the next calendar date

current_date = current_time_in_tz.date()
previous_date = (current_time_in_tz - timedelta(days=1)).date()
next_date = (current_time_in_tz + timedelta(days=1)).date()
day_after_next_date = (current_time_in_tz + timedelta(days=2)).date()

print("Current Date in TZ:", current_date)
print("Next Calendar Date:", next_date)
print("Day After Next Day Calendar Date:", day_after_next_date)

# # Initialize client with your token
client = Client(api_key=os.environ["ENTSOE_API_KEY"])

# Define timestamps
get_pricing_for_current_day = True

start = pd.Timestamp(current_date if get_pricing_for_current_day else next_date, tz="Europe/Stockholm")
end = pd.Timestamp(next_date if get_pricing_for_current_day else day_after_next_date, tz="Europe/Stockholm")

credential = DefaultAzureCredential()
producer = EventHubProducerClient(
    fully_qualified_namespace=EVENTHUB_FQDN,
    eventhub_name=EVENT_HUB_NAME,
    credential=credential
)
# Initialize an empty optimized Azure Event Hub batch network payload
event_batch = producer.create_batch()


for SE_code in sweden_eic_bidding_zones:
    df = client.prices.day_ahead(start, end, country = SE_code)
    list_of_json = df.to_dict(orient="records")

    for pricing_record in list_of_json:
        pricing_record["eic_bidding_zone"] = sweden_eic_bidding_zones[SE_code]
        event_json = json.dumps(pricing_record, default=str)
        print(event_json)

        try:
            # Attempt to pack the string into the network batch
            event_batch.add(EventData(event_json))
        except ValueError:
            # The network batch reached its maximum size limit (typically 1MB or 256KB)
            # Flush the current batch to Azure immediately and start a fresh batch
            producer.send_batch(event_batch)
            event_batch = producer.create_batch()
            event_batch.add(EventData(event_json))

# Send whatever remains in the batch out to Azure Event Hub
producer.send_batch(event_batch)


