import csv
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from sift_py.grpc.transport import SiftChannelConfig, use_sift_channel
from sift_py.ingestion.channel import ChannelConfig, ChannelDataType, double_value
from sift_py.ingestion.config.telemetry import TelemetryConfig
from sift_py.ingestion.flow import FlowConfig, FlowOrderedChannelValues
from sift_py.ingestion.service import IngestionService

def parse_csv(
        path_to_csv: Path, telemetry_config: TelemetryConfig
) -> List[FlowOrderedChannelValues]:
    flows: List[FlowOrderedChannelValues] = []

    flow = telemetry_config.flows[0] # we have one csv, and one flow to consume the csv

    with open(path_to_csv, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader) #skip header
        
        for row in reader:
            timestamp_str, values = row[0], row[1:]
            
            assert len(values) == len(flow.channels), "number of channels don't match number of features in row"
            flows.append(
                    {
                        "flow_name": flow.name,
                        "timestamp": 
                           pd.Timestamp.utcfromtimestamp(float(timestamp_str)), 
                        "channel_values": 
                            [double_value(float(raw_value)) for raw_value in values]
                    }
            )

    return flows

def load_telemetry_config(
        path_to_csv: Path, asset_name: str, ingestion_client_key: str
) -> TelemetryConfig:
    channels = []

    with open(path_to_csv, "r") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader) #only need headers to load telemetry

        channel_names = header[1:] #skip time series column

        for name in channel_names:
            channels.append(
                    ChannelConfig(
                        name=name,
                        data_type = ChannelDataType.DOUBLE
                    )
            )

    return TelemetryConfig(
           asset_name=asset_name, 
           ingestion_client_key = ingestion_client_key, 
           flows=[FlowConfig(name="data", channels=channels)] # one flow for one csv?
    )

def main(filename, runname):
    load_dotenv()

    sift_uri = os.getenv("SIFT_API_URI")
    assert sift_uri, "expected 'SIFT_API_URI' environment variable to be set"

    apikey = os.getenv("SIFT_API_KEY")
    assert apikey, "expected 'SIFT_API_KEY' environment variable to be set"

    asset_name = os.getenv("ASSET_NAME")
    assert asset_name, "expected 'ASSET_NAME' environment variable to be set"

    ingestion_client_key = os.getenv("INGESTION_CLIENT_KEY")
    assert ingestion_client_key, "expected 'INGESTION_CLIENT_KEY' environment variable to be set"

    lidar_data_csv = Path("../", "lidar_files", "filename")

    telemetry_config = load_telemetry_config(
            lidar_data_csv, asset_name, ingestion_client_key
    )
    flows_data = parse_csv(lidar_data_csv, telemetry_config)

    sift_channel_conf = SiftChannelConfig(uri = sift_uri, apikey = apikey)

    with use_sift_channel(sift_channel_conf) as channel:
        ingestion_service = IngestionService(
                channel = channel,
                config = telemetry_config
        )

        run_name = f"{runname}-{datetime.now()}"
        ingestion_service.attach_run(channel, run_name, "test csv ingestion")

        with ingestion_service.buffered_ingestion() as buffered_ingestion:
            buffered_ingestion.ingest_flows(*flows_data)
