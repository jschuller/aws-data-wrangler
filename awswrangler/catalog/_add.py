"""AWS Glue Catalog Delete Module."""

from __future__ import annotations

import logging
from typing import Any

import boto3

from awswrangler import _utils, exceptions, typing
from awswrangler._config import apply_configs
from awswrangler.catalog._definitions import (
    _check_column_type,
    _csv_partition_definition,
    _json_partition_definition,
    _orc_partition_definition,
    _parquet_partition_definition,
    _update_table_definition,
)
from awswrangler.catalog._utils import _catalog_id, sanitize_table_name

_logger: logging.Logger = logging.getLogger(__name__)


def _add_partitions(
    database: str,
    table: str,
    boto3_session: boto3.Session | None,
    inputs: list[dict[str, Any]],
    catalog_id: str | None = None,
) -> None:
    chunks: list[list[dict[str, Any]]] = _utils.chunkify(lst=inputs, max_length=100)
    client_glue = _utils.client(service_name="glue", session=boto3_session)
    for chunk in chunks:
        res = client_glue.batch_create_partition(
            **_catalog_id(catalog_id=catalog_id, DatabaseName=database, TableName=table, PartitionInputList=chunk)
        )
        if ("Errors" in res) and res["Errors"]:
            for error in res["Errors"]:
                if "ErrorDetail" in error:
                    if "ErrorCode" in error["ErrorDetail"]:
                        if error["ErrorDetail"]["ErrorCode"] != "AlreadyExistsException":
                            raise exceptions.ServiceApiError(str(res["Errors"]))


@apply_configs
def add_csv_partitions(
    database: str,
    table: str,
    partitions_values: dict[str, list[str]],
    bucketing_info: typing.BucketingInfoTuple | None = None,
    catalog_id: str | None = None,
    compression: str | None = None,
    sep: str = ",",
    serde_library: str | None = None,
    serde_parameters: dict[str, str] | None = None,
    boto3_session: boto3.Session | None = None,
    columns_types: dict[str, str] | None = None,
    partitions_parameters: dict[str, str] | None = None,
) -> None:
    r"""Add partitions (metadata) to a CSV Table in the AWS Glue Catalog.

    Parameters
    ----------
    database
        Database name.
    table
        Table name.
    partitions_values
        Dictionary with keys as S3 path locations and values as a list of partitions values as str
        (e.g. {'s3://bucket/prefix/y=2020/m=10/': ['2020', '10']}).
    bucketing_info
        Tuple consisting of the column names used for bucketing as the first element and the number of buckets as the
        second element.
        Only `str`, `int` and `bool` are supported as column data types for bucketing.
    catalog_id
        The ID of the Data Catalog from which to retrieve Databases.
        If none is provided, the AWS account ID is used by default.
    compression
        Compression style (``None``, ``gzip``, etc).
    sep
        String of length 1. Field delimiter for the output file.
    serde_library
        Specifies the SerDe Serialization library which will be used. You need to provide the Class library name
        as a string.
        If no library is provided the default is `org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe`.
    serde_parameters
        Dictionary of initialization parameters for the SerDe.
        The default is `{"field.delim": sep, "escape.delim": "\\"}`.
    boto3_session
        The default boto3 session will be used if boto3_session receive None.
    columns_types
        Only required for Hive compability.
        Dictionary with keys as column names and values as data types (e.g. {'col0': 'bigint', 'col1': 'double'}).
        P.S. Only materialized columns please, not partition columns.
    partitions_parameters
        Dictionary with key-value pairs defining partition parameters.

    Examples
    --------
    >>> import awswrangler as wr
    >>> wr.catalog.add_csv_partitions(
    ...     database='default',
    ...     table='my_table',
    ...     partitions_values={
    ...         's3://bucket/prefix/y=2020/m=10/': ['2020', '10'],
    ...         's3://bucket/prefix/y=2020/m=11/': ['2020', '11'],
    ...         's3://bucket/prefix/y=2020/m=12/': ['2020', '12']
    ...     }
    ... )

    """
    table = sanitize_table_name(table=table)
    inputs: list[dict[str, Any]] = [
        _csv_partition_definition(
            location=k,
            values=v,
            bucketing_info=bucketing_info,
            compression=compression,
            sep=sep,
            columns_types=columns_types,
            serde_library=serde_library,
            serde_parameters=serde_parameters,
            partitions_parameters=partitions_parameters,
        )
        for k, v in partitions_values.items()
    ]
    _add_partitions(database=database, table=table, boto3_session=boto3_session, inputs=inputs, catalog_id=catalog_id)


@apply_configs
def add_json_partitions(
    database: str,
    table: str,
    partitions_values: dict[str, list[str]],
    bucketing_info: typing.BucketingInfoTuple | None = None,
    catalog_id: str | None = None,
    compression: str | None = None,
    serde_library: str | None = None,
    serde_parameters: dict[str, str] | None = None,
    boto3_session: boto3.Session | None = None,
    columns_types: dict[str, str] | None = None,
    partitions_parameters: dict[str, str] | None = None,
) -> None:
    r"""Add partitions (metadata) to a JSON Table in the AWS Glue Catalog.

    Parameters
    ----------
    database
        Database name.
    table
        Table name.
    partitions_values
        Dictionary with keys as S3 path locations and values as a list of partitions values as str
        (e.g. {'s3://bucket/prefix/y=2020/m=10/': ['2020', '10']}).
    bucketing_info
        Tuple consisting of the column names used for bucketing as the first element and the number of buckets as the
        second element.
        Only `str`, `int` and `bool` are supported as column data types for bucketing.
    catalog_id
        The ID of the Data Catalog from which to retrieve Databases.
        If none is provided, the AWS account ID is used by default.
    compression
        Compression style (``None``, ``gzip``, etc).
    serde_library
        Specifies the SerDe Serialization library which will be used. You need to provide the Class library name
        as a string.
        If no library is provided the default is `org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe`.
    serde_parameters
        Dictionary of initialization parameters for the SerDe.
        The default is `{"field.delim": sep, "escape.delim": "\\"}`.
    boto3_session
        Boto3 Session. The default boto3 session will be used if boto3_session receive None.
    columns_types
        Only required for Hive compability.
        Dictionary with keys as column names and values as data types (e.g. {'col0': 'bigint', 'col1': 'double'}).
        P.S. Only materialized columns please, not partition columns.
    partitions_parameters
        Dictionary with key-value pairs defining partition parameters.

    Examples
    --------
    >>> import awswrangler as wr
    >>> wr.catalog.add_json_partitions(
    ...     database='default',
    ...     table='my_table',
    ...     partitions_values={
    ...         's3://bucket/prefix/y=2020/m=10/': ['2020', '10'],
    ...         's3://bucket/prefix/y=2020/m=11/': ['2020', '11'],
    ...         's3://bucket/prefix/y=2020/m=12/': ['2020', '12']
    ...     }
    ... )

    """
    table = sanitize_table_name(table=table)
    inputs: list[dict[str, Any]] = [
        _json_partition_definition(
            location=k,
            values=v,
            bucketing_info=bucketing_info,
            compression=compression,
            columns_types=columns_types,
            serde_library=serde_library,
            serde_parameters=serde_parameters,
            partitions_parameters=partitions_parameters,
        )
        for k, v in partitions_values.items()
    ]
    _add_partitions(database=database, table=table, boto3_session=boto3_session, inputs=inputs, catalog_id=catalog_id)


@apply_configs
def add_parquet_partitions(
    database: str,
    table: str,
    partitions_values: dict[str, list[str]],
    bucketing_info: typing.BucketingInfoTuple | None = None,
    catalog_id: str | None = None,
    compression: str | None = None,
    boto3_session: boto3.Session | None = None,
    columns_types: dict[str, str] | None = None,
    partitions_parameters: dict[str, str] | None = None,
) -> None:
    """Add partitions (metadata) to a Parquet Table in the AWS Glue Catalog.

    Parameters
    ----------
    database
        Database name.
    table
        Table name.
    partitions_values
        Dictionary with keys as S3 path locations and values as a list of partitions values as str
        (e.g. {'s3://bucket/prefix/y=2020/m=10/': ['2020', '10']}).
    bucketing_info
        Tuple consisting of the column names used for bucketing as the first element and the number of buckets as the
        second element.
        Only `str`, `int` and `bool` are supported as column data types for bucketing.
    catalog_id
        The ID of the Data Catalog from which to retrieve Databases.
        If none is provided, the AWS account ID is used by default.
    compression
        Compression style (``None``, ``snappy``, ``gzip``, etc).
    boto3_session
        Boto3 Session. The default boto3 session will be used if boto3_session receive None.
    columns_types
        Only required for Hive compability.
        Dictionary with keys as column names and values as data types (e.g. {'col0': 'bigint', 'col1': 'double'}).
        P.S. Only materialized columns please, not partition columns.
    partitions_parameters
        Dictionary with key-value pairs defining partition parameters.

    Examples
    --------
    >>> import awswrangler as wr
    >>> wr.catalog.add_parquet_partitions(
    ...     database='default',
    ...     table='my_table',
    ...     partitions_values={
    ...         's3://bucket/prefix/y=2020/m=10/': ['2020', '10'],
    ...         's3://bucket/prefix/y=2020/m=11/': ['2020', '11'],
    ...         's3://bucket/prefix/y=2020/m=12/': ['2020', '12']
    ...     }
    ... )

    """
    table = sanitize_table_name(table=table)
    if partitions_values:
        inputs: list[dict[str, Any]] = [
            _parquet_partition_definition(
                location=k,
                values=v,
                bucketing_info=bucketing_info,
                compression=compression,
                columns_types=columns_types,
                partitions_parameters=partitions_parameters,
            )
            for k, v in partitions_values.items()
        ]
        _add_partitions(
            database=database, table=table, boto3_session=boto3_session, inputs=inputs, catalog_id=catalog_id
        )


@apply_configs
def add_orc_partitions(
    database: str,
    table: str,
    partitions_values: dict[str, list[str]],
    bucketing_info: typing.BucketingInfoTuple | None = None,
    catalog_id: str | None = None,
    compression: str | None = None,
    boto3_session: boto3.Session | None = None,
    columns_types: dict[str, str] | None = None,
    partitions_parameters: dict[str, str] | None = None,
) -> None:
    """Add partitions (metadata) to a ORC Table in the AWS Glue Catalog.

    Parameters
    ----------
    database
        Database name.
    table
        Table name.
    partitions_values
        Dictionary with keys as S3 path locations and values as a list of partitions values as str
        (e.g. {'s3://bucket/prefix/y=2020/m=10/': ['2020', '10']}).
    bucketing_info
        Tuple consisting of the column names used for bucketing as the first element and the number of buckets as the
        second element.
        Only `str`, `int` and `bool` are supported as column data types for bucketing.
    catalog_id
        The ID of the Data Catalog from which to retrieve Databases.
        If none is provided, the AWS account ID is used by default.
    compression
        Compression style (``None``, ``snappy``, ``zlib``, etc).
    boto3_session
        Boto3 Session. The default boto3 session will be used if boto3_session receive None.
    columns_types
        Only required for Hive compability.
        Dictionary with keys as column names and values as data types (e.g. {'col0': 'bigint', 'col1': 'double'}).
        P.S. Only materialized columns please, not partition columns.
    partitions_parameters
        Dictionary with key-value pairs defining partition parameters.

    Examples
    --------
    >>> import awswrangler as wr
    >>> wr.catalog.add_orc_partitions(
    ...     database='default',
    ...     table='my_table',
    ...     partitions_values={
    ...         's3://bucket/prefix/y=2020/m=10/': ['2020', '10'],
    ...         's3://bucket/prefix/y=2020/m=11/': ['2020', '11'],
    ...         's3://bucket/prefix/y=2020/m=12/': ['2020', '12']
    ...     }
    ... )

    """
    table = sanitize_table_name(table=table)
    if partitions_values:
        inputs: list[dict[str, Any]] = [
            _orc_partition_definition(
                location=k,
                values=v,
                bucketing_info=bucketing_info,
                compression=compression,
                columns_types=columns_types,
                partitions_parameters=partitions_parameters,
            )
            for k, v in partitions_values.items()
        ]
        _add_partitions(
            database=database, table=table, boto3_session=boto3_session, inputs=inputs, catalog_id=catalog_id
        )


@apply_configs
def add_column(
    database: str,
    table: str,
    column_name: str,
    column_type: str = "string",
    column_comment: str | None = None,
    boto3_session: boto3.Session | None = None,
    catalog_id: str | None = None,
) -> None:
    """Add a column in a AWS Glue Catalog table.

    Parameters
    ----------
    database
        Database name.
    table
        Table name.
    column_name
        Column name
    column_type
        Column type.
    column_comment
        Column Comment
    boto3_session
        The default boto3 session will be used if **boto3_session** is ``None``.
    catalog_id
        The ID of the Data Catalog from which to retrieve Databases.
        If none is provided, the AWS account ID is used by default.

    Examples
    --------
    >>> import awswrangler as wr
    >>> wr.catalog.add_column(
    ...     database='my_db',
    ...     table='my_table',
    ...     column_name='my_col',
    ...     column_type='int'
    ... )
    """
    if _check_column_type(column_type):
        client_glue = _utils.client(service_name="glue", session=boto3_session)
        table_res = client_glue.get_table(**_catalog_id(catalog_id=catalog_id, DatabaseName=database, Name=table))
        table_input: dict[str, Any] = _update_table_definition(table_res)
        table_input["StorageDescriptor"]["Columns"].append(
            {"Name": column_name, "Type": column_type, "Comment": column_comment}
        )
        res: dict[str, Any] = client_glue.update_table(
            **_catalog_id(catalog_id=catalog_id, DatabaseName=database, TableInput=table_input)
        )
        if ("Errors" in res) and res["Errors"]:
            for error in res["Errors"]:
                if "ErrorDetail" in error:
                    if "ErrorCode" in error["ErrorDetail"]:
                        raise exceptions.ServiceApiError(str(res["Errors"]))
