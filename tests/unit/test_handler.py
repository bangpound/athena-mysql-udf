import unittest
import base64
from typing import List

import pyarrow as pa
import copy
import uuid
import datetime

from athena_mysql_udf import app


class TestAthenaUDFHandler(unittest.TestCase):
    REQUEST_TEMPLATE = {
        "@type": "UserDefinedFunctionRequest",
        "identity": {
            "arn": "UNKNOWN_ARN",
            "account": "12345",
            "principalTags": {},
            "iamGroups": [],
        },
        "inputRecords": {
            "aId": "9af9372c-1d73-49ed-9e26-c47fc7c91615",
            "schema": "sss",
            "records": "sss",
        },
        "outputSchema": {"schema": "sss"},
        "methodName": "my_udf",
        "functionType": "SCALAR",
    }

    def test_ping_request(self):
        ping_request = {
            "@type": "PingRequest",
            "identity": {
                "id": "UNKNOWN",
                "principal": "UNKNOWN",
                "account": "12345",
                "arn": "UNKNOWN_ARN",
                "tags": {},
                "groups": [],
            },
            "catalogName": "my_udf",
            "queryId": "6c59fb04-9bb4-48ea-9afb-971fe1edd2c2",
        }

        resp = app.lambda_handler(ping_request, None)
        self.assertEqual(
            resp,
            {
                "@type": "PingResponse",
                "catalogName": "event",
                "queryId": "6c59fb04-9bb4-48ea-9afb-971fe1edd2c2",
                "sourceType": "athena_udf",
                "capabilities": 23,
            },
        )

    def test_distill(self):
        request = copy.copy(self.REQUEST_TEMPLATE)
        schema = pa.schema([pa.field("0", pa.string())])
        request["inputRecords"]["schema"] = base64.b64encode(schema.serialize())
        request["outputSchema"]["schema"] = base64.b64encode(schema.serialize())

        inputs: list[str] = [
            "SELECT * FROM table_one WHERE id = 1",
            "SELECT * FROM table_one, table_two WHERE id = 1",
        ]
        records: str = base64.b64encode(
            pa.RecordBatch.from_arrays([inputs], schema=schema).serialize()
        ).decode()
        request["inputRecords"]["records"] = records
        resp = app.lambda_handler(request, None)
        uuid.UUID(resp["records"]["aId"])

        assert resp["methodName"] == "my_udf"
        assert resp["@type"] == "UserDefinedFunctionResponse"
        output_schema = pa.ipc.read_schema(
            pa.BufferReader(base64.b64decode(resp["records"]["schema"]))
        )
        record_batch = pa.ipc.read_record_batch(
            pa.BufferReader(base64.b64decode(resp["records"]["records"])),
            output_schema,
        )
        record_batch_list = [x["0"] for x in record_batch.to_pylist()]
        assert record_batch_list == ["SELECT table_one", "SELECT table_one table_two"]

    ping_request = {
        "@type": "PingRequest",
        "identity": {
            "id": "UNKNOWN",
            "principal": "UNKNOWN",
            "account": "12345",
            "arn": "UNKNOWN_ARN",
            "tags": {},
            "groups": [],
        },
        "catalogName": "my_udf",
        "queryId": "6c59fb04-9bb4-48ea-9afb-971fe1edd2c2",
    }
