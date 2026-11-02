# electricity-usage-realtime-billing
Realtime data usage pipeline for Swedish households using ENTSO-E day ahead pricing

## Motivation
This project is about solving the business scenario where customers are billed on the basis of electricity usage. This data pipeline does solve the problem of pricing in real time energy usage.

### Business Scenario
A global utility provider tracks millions of smart meters transmitting electricity usage events every 10 seconds. Simultaneously, an energy market trading desk pushes localized electricity pricing tariffs every minute. The system must join these two independent real-time streams to calculate an accurate, billing-ready cost metric per household, flagging sudden spikes or missing data intervals instantly.

## Data pipeline system architecture
<img width="1024" height="572" alt="electricity_telemetery_diagram" src="https://github.com/user-attachments/assets/841547c2-4b2b-4c30-8233-5ce04b0c3a58" />

Azure container instance for the daily pricing job runs once by calling the entso-e api of Swedish 4 zones and this data is published to azure event hub. I simulated the meter telemetry data by running real time python streaming application on ACI and it is published to another event hub stream. I merged these 2 streams into my Databricks pipeline allowing me to calculate real time electricity real time billing usage per household.

### Medallion architecture
I designed the data pipeline based on the medallion architecture. Where first bronze layer is the RAW ingestion of 2 data streams in real time from event hubs. In silver layer I cleaned up and transform the raw data by schema design and filtering of the data (i.e. pricing per zone only, telemetry usage per household). In gold layer, cleaned data is aggregated based on the business use case(what is the aggregated current day usage / billing period usage per household).

## Results
<img width="898" height="557" alt="image" src="https://github.com/user-attachments/assets/4cafd47f-deef-4315-92de-f3c7b6ad05ad" />

This is an example of the pipeline running for a 1hr 48-minute time period. We can see the cumulative electricity usage given each smart meter telemetry reading coming from each household every 10 seconds.
