import athena_udf
import mysql_distill
from functools import cache


@cache()
def cached_distill(digest_text: str):
    if digest_text:
        return mysql_distill.distill(digest_text)
    return ""


class MysqlUDFHandler(athena_udf.BaseAthenaUDF):
    @staticmethod
    def handle_athena_record(input_schema, output_schema, arguments):
        digest_text = arguments[0]
        return cached_distill(digest_text)


lambda_handler = MysqlUDFHandler().lambda_handler
