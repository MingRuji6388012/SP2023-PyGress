#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests

from .database import Database, OrderCondition, WhereCondition
from . import errors

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

FIRESTORE_URI = "https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"

###############################################################################


class WhereOperators:
    eq: str = "=="
    contains: str = "array_contains"
    gt: str = ">"
    lt: str = "<"
    gteq: str = ">="
    lteq: str = "<="


class OrderOperators:
    desc: str = "DESCENDING"
    asce: str = "ASCENDING"


class NoCredResponseTypes:
    boolean: str = "booleanValue"
    double: str = "doubleValue"
    dt: str = "timestampValue"
    integer: str = "integerValue"
    null: str = "nullValue"
    string: str = "stringValue"


class CloudFirestoreDatabase(Database):

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        # With credentials:
        if credentials_path:
            # Resolve credentials
            credentials_path = Path(credentials_path).resolve(strict=True)

            # Initialize database reference
            cred = credentials.Certificate(str(credentials_path))

            # Check name
            # This is done as if the name is None we just want to initialize the main connection
            if name:
                firebase_admin.initialize_app(cred, name=name)
            else:
                firebase_admin.initialize_app(cred)

            # Store configuration
            self._credentials_path = credentials_path
            self._root = firestore.client()
        elif project_id:
            self._credentials_path = None
            self._project_id = project_id
            self._db_uri = FIRESTORE_URI.format(project_id=project_id)
        else:
            raise errors.MissingParameterError(["project_id", "credentials_path"])

    @staticmethod
    def _jsonify_firestore_response(fields: Dict) -> Dict:
        formatted = {}

        # Cast or parse values from returned
        for k, type_and_value in fields.items():
            if NoCredResponseTypes.boolean in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.boolean]
            elif NoCredResponseTypes.null in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.null]
            elif NoCredResponseTypes.string in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.string]
            elif NoCredResponseTypes.double in type_and_value:
                formatted[k] = float(type_and_value[NoCredResponseTypes.double])
            elif NoCredResponseTypes.integer in type_and_value:
                formatted[k] = int(type_and_value[NoCredResponseTypes.integer])
            elif NoCredResponseTypes.dt in type_and_value:
                formatted[k] = datetime.strptime(
                    type_and_value[NoCredResponseTypes.dt],
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                )

        return formatted

    def get_row(self, table: str, id: str) -> Dict:
        # With credentials
        if self._credentials_path:
            # Get result
            result = self._root.collection(table).document(id).get().to_dict()

            # Found, return expansion
            if result:
                return {"id": id, **result}

            # Not found, return None
            return None

        # Fill target uri
        target_uri = f"{self._db_uri}/{table}/{id}"
        response = requests.get(target_uri).json()

        # Check for error
        if "fields" in response:
            # Format response
            return {"id": id, **self._jsonify_firestore_response(response["fields"])}

        raise KeyError(f"No row with id: {id} exists.")

    @staticmethod
    def _construct_where_condition(filt: Union[WhereCondition, List, Tuple]):
        if isinstance(filt, WhereCondition):
            return filt
        elif isinstance(filt, (list, tuple)):
            # Assume equal
            if len(filt) == 2:
                return WhereCondition(filt[0], WhereOperators.eq, filt[1])
            elif len(filt) == 3:
                return WhereCondition(*filt)
            else:
                raise errors.UnstructuredWhereConditionError(filt)
        else:
            raise errors.UnknownTypeWhereConditionError(filt)

    @staticmethod
    def _construct_orderby_condition(by: Union[List, OrderCondition, str, Tuple]):
        if isinstance(by, OrderCondition):
            return by
        if isinstance(by, str):
            # Assume descending
            return OrderCondition(by, OrderOperators.desc)
        elif isinstance(by, (list, tuple)):
            # Assume descending
            if len(by) == 1:
                return OrderCondition(by[0], OrderOperators.desc)
            elif len(by) == 2:
                return OrderCondition(*by)
            else:
                raise errors.UnstructuredOrderConditionError(by)
        else:
            raise errors.UnknownTypeOrderConditionError(by)

    def get_rows(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        # With credentials
        if self._credentials_path:
            # Create base table ref
            ref = self._root.collection(table)

            # Apply filters
            if filters:
                for f in filters:
                    # Construct WhereCondition
                    f = self._construct_where_condition(f)
                    # Apply
                    ref = ref.where(f.column_name, f.operator, f.value)

            # Apply order by
            if order_by:
                order_by = self._construct_orderby_condition(order_by)
                ref = ref.order_by(order_by.column_name, order_by.operator)

            # Apply limit
            if limit:
                ref = ref.limit(limit)

            # Get and expand
            return [{"id": i.id, **i.to_dict()} for i in ref.stream()]

        target_uri = f"{self._db_uri}/{table}"
        response = requests.get(target_uri).json()

        # Check for error
        if "documents" in response:
            return [
                {
                    "id": d["name"].split("/")[-1],  # Get last item in the uri
                    **self._jsonify_firestore_response(d["fields"])
                } for d in response["documents"]
            ]
            return [{"id": d["name"], **self._jsonify_firestore_response(d["fields"])} for d in response["documents"]]

        raise KeyError(f"No table with name: {table} exits.")

    def _get_rows_with_max_results_expectation(
        self,
        table: str,
        pks: List[Union[WhereCondition, List, Tuple]],
        expected_max_rows: int
    ):
        # Find matching
        pks = [self._construct_where_condition(pk) for pk in pks]
        matching = self.get_rows(table=table, filters=pks)

        # Handle expectation
        if len(matching) > expected_max_rows:
            raise errors.UniquenessError(table, [pk.column_name for pk in pks], matching)
        elif len(matching) == 0:
            return None
        else:
            return matching[0]

    def _get_or_upload_row(self, table: str, pks: List[Union[WhereCondition, List, Tuple]], values: Dict) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise errors.MissingCredentialsError()

        # Fast return for already stored
        found = self._get_rows_with_max_results_expectation(
            table=table,
            pks=pks,
            expected_max_rows=1
        )
        # Return or upload
        if found:
            return found
        else:
            # Create id
            id = str(uuid4())
            # Store the row
            self._root.collection(table).document(id).set(values)

            # Return row
            return {"id": id, **values}

    def get_or_upload_body(self, name: str, description: Optional[str] = None) -> Dict:
        return self._get_or_upload_row(
            table="body",
            pks=[("name", name)],
            values={
                "name": name,
                "description": description,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_event(
        self,
        body_id: int,
        event_datetime: datetime,
        source_uri: str,
        thumbnail_uri: str,
        video_uri: str
    ) -> Dict:
        return self._get_or_upload_row(
            table="event",
            pks=[("video_uri", video_uri)],
            values={
                "body_id": body_id,
                "event_datetime": event_datetime,
                "source_uri": source_uri,
                "thumbnail_uri": thumbnail_uri,
                "video_uri": video_uri,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_algorithm(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="algorithm",
            pks=[("name", name), ("version", version)],
            values={
                "name": name,
                "version": version,
                "description": description,
                "source": source,
                "created": datetime.utcnow()
            }
        )

    def __str__(self):
        if self._credentials_path:
            return f"<FirebaseDatabase [{self._credentials_path}]>"

        return f"<FirebaseDatabase [{self._project_id}]"

    def __repr__(self):
        return str(self)