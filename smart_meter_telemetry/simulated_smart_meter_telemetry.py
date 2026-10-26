import os
import json
import time
import random
from datetime import datetime, timezone
from azure.eventhub import EventHubProducerClient, EventData
from azure.identity import DefaultAzureCredential

# 1. INITIALIZATION: Setup your configuration

EVENTHUB_FQDN = os.environ.get(
    "EVENTHUB_FQDN",
    "entsoeelectricityusagepricing.servicebus.windows.net"
)
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "smart-meter-telemetry")

NUM_HOUSEHOLDS = 2000  # Scales perfectly to thousands
GRID_SECTORS = ["SE1", "SE2", "SE3", "SE4"]

# Generate our household registry metadata once at startup
print(f"📋 Generating registry for {NUM_HOUSEHOLDS} smart meters...")
HOUSEHOLD_REGISTRY = [
    {
        "meter_id": f"MTR-{i:06d}",
        "tariff_grid_id": random.choice(GRID_SECTORS),
        "base_load": random.uniform(0.2, 0.7)  # unique baseline footprint per house
    }
    for i in range(1, NUM_HOUSEHOLDS + 1)
]


def simulate_metrics(household, current_hour):
    """Calculates the payload for a single household scaled to a 10-second reporting window."""
    is_peak = 17 <= current_hour <= 21
    # multiplier represents instant kW power draw boost
    multiplier = random.uniform(2.0, 3.5) if is_peak else random.uniform(0.8, 1.2)

    # Base load in kW (e.g., 0.5 kW to 3.0 kW power draw)
    power_draw_kw = household["base_load"] * multiplier * random.uniform(0.9, 1.1)

    # Convert kW power draw to actual kWh consumed over 10 seconds (10s = 10/3600 hours)
    interval_seconds = 10
    kwh_consumed = power_draw_kw * (interval_seconds / 3600.0)

    return {
        "meter_id": household["meter_id"],
        "tariff_grid_id": household["tariff_grid_id"],
        "kwh_consumed": round(kwh_consumed, 6), # Increase decimal precision for small 10s intervals
        "voltage": round(random.uniform(220.0, 240.0), 1),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 2. RUNTIME CORE: Continuous Batch Execution
def run_generator():
    credential = DefaultAzureCredential()
    producer = EventHubProducerClient(
        fully_qualified_namespace=EVENTHUB_FQDN,
        eventhub_name=EVENT_HUB_NAME,
        credential=credential
    )

    try:
        while True:
            start_time = time.time()
            current_hour = datetime.now().hour

            # Initialize an empty optimized Azure Event Hub batch network payload
            event_batch = producer.create_batch()
            print(f"⏳ Generating interval payload for {NUM_HOUSEHOLDS} households...")

            for household in HOUSEHOLD_REGISTRY:
                payload = simulate_metrics(household, current_hour)
                event_json = json.dumps(payload)

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

            elapsed = time.time() - start_time
            print(f"🚀 Batch successfully sent in {elapsed:.2f} seconds.")

            # Smart meters report every 10 seconds.
            # Sleep for the remaining balance of the 10-second interval window.
            sleep_time = max(0, 10 - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopping generator safely.")
    finally:
        producer.close()


if __name__ == "__main__":
    run_generator()