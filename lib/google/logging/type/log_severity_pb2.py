# -*- coding: utf-8 -*-

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: google/logging/type/log_severity.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b"\n&google/logging/type/log_severity.proto\x12\x13google.logging.type*\x82\x01\n\x0bLogSeverity\x12\x0b\n\x07\x44\x45\x46\x41ULT\x10\x00\x12\t\n\x05\x44\x45\x42UG\x10\x64\x12\t\n\x04INFO\x10\xc8\x01\x12\x0b\n\x06NOTICE\x10\xac\x02\x12\x0c\n\x07WARNING\x10\x90\x03\x12\n\n\x05\x45RROR\x10\xf4\x03\x12\r\n\x08\x43RITICAL\x10\xd8\x04\x12\n\n\x05\x41LERT\x10\xbc\x05\x12\x0e\n\tEMERGENCY\x10\xa0\x06\x42\xc5\x01\n\x17\x63om.google.logging.typeB\x10LogSeverityProtoP\x01Z8google.golang.org/genproto/googleapis/logging/type;ltype\xa2\x02\x04GLOG\xaa\x02\x19Google.Cloud.Logging.Type\xca\x02\x19Google\\Cloud\\Logging\\Type\xea\x02\x1cGoogle::Cloud::Logging::Typeb\x06proto3"
)

_LOGSEVERITY = DESCRIPTOR.enum_types_by_name["LogSeverity"]
LogSeverity = enum_type_wrapper.EnumTypeWrapper(_LOGSEVERITY)
DEFAULT = 0
DEBUG = 100
INFO = 200
NOTICE = 300
WARNING = 400
ERROR = 500
CRITICAL = 600
ALERT = 700
EMERGENCY = 800


if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n\027com.google.logging.typeB\020LogSeverityProtoP\001Z8google.golang.org/genproto/googleapis/logging/type;ltype\242\002\004GLOG\252\002\031Google.Cloud.Logging.Type\312\002\031Google\\Cloud\\Logging\\Type\352\002\034Google::Cloud::Logging::Type"
    _LOGSEVERITY._serialized_start = 64
    _LOGSEVERITY._serialized_end = 194
# @@protoc_insertion_point(module_scope)
