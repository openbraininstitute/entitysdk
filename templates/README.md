

This directory stores custom templates that are used by datamodel-code-generator to auto-generate the server schemas.

Default templates: https://github.com/koxudaxi/datamodel-code-generator/tree/main/src/datamodel_code_generator/model/template

Custom templates:

Enum.jinja2
-----------

Replace enum base class from (str, Enum) to StrEnum.

Note that --use-subclass-enum in datamodel-codegen command is required to convert Enum to the correct subclass of (str, Enum) and --additional-imports "enum.StrEnum" to include the dependency.

There is also an issue with importing the dependency at the top of the generated file which conflicts with __future__ that needs to be at the top.
