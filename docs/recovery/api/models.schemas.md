# `models.schemas` — recovered API surface

## Module-level names

- `Dict` (_SpecialGenericAlias)
- `List` (_SpecialGenericAlias)
- `Optional` (_SpecialForm)
- `annotations` (_Feature)

## class `BaseModel(object)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `CheckpointData(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `checkpoint_type: <class 'str'>`, `step_name: <class 'str'>`, `data: typing.Dict`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `CheckpointResponse(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `action: <class 'str'>`, `data: typing.Dict`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `Enum(object)`


## class `LogEntry(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `step_name: typing.Optional[str]`, `level: <class 'str'>`, `message: <class 'str'>`, `created_at: typing.Optional[datetime.datetime]`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `StepInfo(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `skill_name: <class 'str'>`, `display_name: <class 'str'>`, `step_order: <class 'int'>`, `status: <enum 'StepStatus'>`, `has_checkpoint: <class 'bool'>`, `checkpoint_type: typing.Optional[str]`, `output_files: typing.List[str]`, `started_at: typing.Optional[datetime.datetime]`, `completed_at: typing.Optional[datetime.datetime]`, `error_message: typing.Optional[str]`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `StepStatus(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## class `TemplateType(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## class `WorkflowCreate(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `template: <enum 'TemplateType'>`, `title: <class 'str'>`, `params: typing.Dict`, `enable_checkpoints: <class 'bool'>`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `WorkflowInfo(BaseModel)`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: A dictionary containing metadata about generic Pydantic models.
        The `origin` and `args` items map to the [`__origin__`][genericalias.__origin__]
        and [`__args__`][genericalias.__args__] attributes of [generic aliases][types-genericalias],
        and the `parameter` item maps to the `__parameter__` attribute of generic classes.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

Fields: `id: <class 'str'>`, `template: <enum 'TemplateType'>`, `title: <class 'str'>`, `params: typing.Dict`, `status: <enum 'WorkflowStatus'>`, `current_step: typing.Optional[str]`, `steps: typing.List[models.schemas.StepInfo]`, `created_at: typing.Optional[datetime.datetime]`, `updated_at: typing.Optional[datetime.datetime]`

- `__init__(self, /, **data: 'Any') -> 'None'` — Create a new model by parsing and validating input data from keyword arguments.
- `construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — 
- `copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — Returns a copy of the model.
- `dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'` — 
- `from_orm(obj: 'Any') -> 'Self'` — 
- `json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'` — 
- `model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'` — Creates a new instance of the `Model` class with validated data.
- `model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'dict[str, Any]'` — !!! abstract "Usage Documentation"
- `model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, polymorphic_serialization: 'bool | None' = None) -> 'str'` — !!! abstract "Usage Documentation"
- `model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'` — Generates a JSON schema for a model class.
- `model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'` — Compute the class name for parametrizations of generic classes.
- `model_post_init(self, context: 'Any', /) -> 'None'` — Override this method to perform additional initialization after `__init__` and `model_construct`.
- `model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'` — Try to rebuild the pydantic-core schema for the model.
- `model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate a pydantic model instance.
- `model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — !!! abstract "Usage Documentation"
- `model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'` — Validate the given object with string data against the Pydantic model.
- `parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `parse_obj(obj: 'Any') -> 'Self'` — 
- `parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'` — 
- `schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'` — 
- `schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'` — 
- `update_forward_refs(**localns: 'Any') -> 'None'` — 
- `validate(value: 'Any') -> 'Self'` — 

## class `WorkflowStatus(str, Enum)`

str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

- `__init__(self, *args, **kwds)` — Initialize self.  See help(type(self)) for accurate signature.
- `capitalize(self, /)` — Return a capitalized version of the string.
- `casefold(self, /)` — Return a version of the string suitable for caseless comparisons.
- `center(self, width, fillchar=' ', /)` — Return a centered string of length width.
- `count()` — S.count(sub[, start[, end]]) -> int
- `encode(self, /, encoding='utf-8', errors='strict')` — Encode the string using the codec registered for encoding.
- `endswith()` — S.endswith(suffix[, start[, end]]) -> bool
- `expandtabs(self, /, tabsize=8)` — Return a copy where all tab characters are expanded using spaces.
- `find()` — S.find(sub[, start[, end]]) -> int
- `format()` — S.format(*args, **kwargs) -> str
- `format_map()` — S.format_map(mapping) -> str
- `index()` — S.index(sub[, start[, end]]) -> int
- `isalnum(self, /)` — Return True if the string is an alpha-numeric string, False otherwise.
- `isalpha(self, /)` — Return True if the string is an alphabetic string, False otherwise.
- `isascii(self, /)` — Return True if all characters in the string are ASCII, False otherwise.
- `isdecimal(self, /)` — Return True if the string is a decimal string, False otherwise.
- `isdigit(self, /)` — Return True if the string is a digit string, False otherwise.
- `isidentifier(self, /)` — Return True if the string is a valid Python identifier, False otherwise.
- `islower(self, /)` — Return True if the string is a lowercase string, False otherwise.
- `isnumeric(self, /)` — Return True if the string is a numeric string, False otherwise.
- `isprintable(self, /)` — Return True if the string is printable, False otherwise.
- `isspace(self, /)` — Return True if the string is a whitespace string, False otherwise.
- `istitle(self, /)` — Return True if the string is a title-cased string, False otherwise.
- `isupper(self, /)` — Return True if the string is an uppercase string, False otherwise.
- `join(self, iterable, /)` — Concatenate any number of strings.
- `ljust(self, width, fillchar=' ', /)` — Return a left-justified string of length width.
- `lower(self, /)` — Return a copy of the string converted to lowercase.
- `lstrip(self, chars=None, /)` — Return a copy of the string with leading whitespace removed.
- `maketrans(x, y=<unrepresentable>, z=<unrepresentable>, /)` — Return a translation table usable for str.translate().
- `partition(self, sep, /)` — Partition the string into three parts using the given separator.
- `removeprefix(self, prefix, /)` — Return a str with the given prefix string removed if present.
- `removesuffix(self, suffix, /)` — Return a str with the given suffix string removed if present.
- `replace(self, old, new, count=-1, /)` — Return a copy with all occurrences of substring old replaced by new.
- `rfind()` — S.rfind(sub[, start[, end]]) -> int
- `rindex()` — S.rindex(sub[, start[, end]]) -> int
- `rjust(self, width, fillchar=' ', /)` — Return a right-justified string of length width.
- `rpartition(self, sep, /)` — Partition the string into three parts using the given separator.
- `rsplit(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `rstrip(self, chars=None, /)` — Return a copy of the string with trailing whitespace removed.
- `split(self, /, sep=None, maxsplit=-1)` — Return a list of the substrings in the string, using sep as the separator string.
- `splitlines(self, /, keepends=False)` — Return a list of the lines in the string, breaking at line boundaries.
- `startswith()` — S.startswith(prefix[, start[, end]]) -> bool
- `strip(self, chars=None, /)` — Return a copy of the string with leading and trailing whitespace removed.
- `swapcase(self, /)` — Convert uppercase characters to lowercase and lowercase characters to uppercase.
- `title(self, /)` — Return a version of the string where each word is titlecased.
- `translate(self, table, /)` — Replace each character in the string using the given translation table.
- `upper(self, /)` — Return a copy of the string converted to uppercase.
- `zfill(self, width, /)` — Pad a numeric string with zeros on the left, to fill a field of the given width.

## class `datetime(date)`

datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])

The year, month and day arguments are required. tzinfo may be None, or an
instance of a tzinfo subclass. The remaining arguments may be ints.

- `__init__(self, /, *args, **kwargs)` — Initialize self.  See help(type(self)) for accurate signature.
- `astimezone()` — tz -> convert to local time in new timezone tz
- `combine()` — date, time -> datetime with same date and time fields
- `ctime()` — Return ctime() style string.
- `date()` — Return date object with same year, month and day.
- `dst()` — Return self.tzinfo.dst(self).
- `fromisocalendar()` — int, int, int -> Construct a date from the ISO year, week number and weekday.
- `fromisoformat()` — string -> datetime from a string in most ISO 8601 formats
- `fromordinal()` — int -> date corresponding to a proleptic Gregorian ordinal.
- `fromtimestamp()` — timestamp[, tz] -> tz's local time from POSIX timestamp.
- `isocalendar()` — Return a named tuple containing ISO year, week number, and weekday.
- `isoformat()` — [sep] -> string in ISO 8601 format, YYYY-MM-DDT[HH[:MM[:SS[.mmm[uuu]]]]][+HH:MM].
- `isoweekday()` — Return the day of the week represented by the date.
- `now(tz=None)` — Returns new datetime object representing current time local to tz.
- `replace()` — Return datetime with new specified fields.
- `strftime()` — format -> strftime() style string.
- `strptime()` — string, format -> new datetime parsed from a string (like time.strptime()).
- `time()` — Return time object with same time but with tzinfo=None.
- `timestamp()` — Return POSIX timestamp as float.
- `timetuple()` — Return time tuple, compatible with time.localtime().
- `timetz()` — Return time object with same time and tzinfo.
- `today()` — Current date or datetime:  same as self.__class__.fromtimestamp(time.time()).
- `toordinal()` — Return proleptic Gregorian ordinal.  January 1 of year 1 is day 1.
- `tzname()` — Return self.tzinfo.tzname(self).
- `utcfromtimestamp()` — Construct a naive UTC datetime from a POSIX timestamp.
- `utcnow()` — Return a new datetime representing UTC day and time.
- `utcoffset()` — Return self.tzinfo.utcoffset(self).
- `utctimetuple()` — Return UTC time tuple, compatible with time.localtime().
- `weekday()` — Return the day of the week represented by the date.

## Functions

- `Field(default: 'Any' = PydanticUndefined, *, default_factory: 'Callable[[], Any] | Callable[[dict[str, Any]], Any] | None' = PydanticUndefined, alias: 'str | None' = PydanticUndefined, alias_priority: 'int | None' = PydanticUndefined, validation_alias: 'str | AliasPath | AliasChoices | None' = PydanticUndefined, serialization_alias: 'str | None' = PydanticUndefined, title: 'str | None' = PydanticUndefined, field_title_generator: 'Callable[[str, FieldInfo], str] | None' = PydanticUndefined, description: 'str | None' = PydanticUndefined, examples: 'list[Any] | None' = PydanticUndefined, exclude: 'bool | None' = PydanticUndefined, exclude_if: 'Callable[[Any], bool] | None' = PydanticUndefined, discriminator: 'str | types.Discriminator | None' = PydanticUndefined, deprecated: 'Deprecated | str | bool | None' = PydanticUndefined, json_schema_extra: 'JsonDict | Callable[[JsonDict], None] | None' = PydanticUndefined, frozen: 'bool | None' = PydanticUndefined, validate_default: 'bool | None' = PydanticUndefined, repr: 'bool' = PydanticUndefined, init: 'bool | None' = PydanticUndefined, init_var: 'bool | None' = PydanticUndefined, kw_only: 'bool | None' = PydanticUndefined, pattern: 'str | re.Pattern[str] | None' = PydanticUndefined, strict: 'bool | None' = PydanticUndefined, coerce_numbers_to_str: 'bool | None' = PydanticUndefined, gt: 'annotated_types.SupportsGt | None' = PydanticUndefined, ge: 'annotated_types.SupportsGe | None' = PydanticUndefined, lt: 'annotated_types.SupportsLt | None' = PydanticUndefined, le: 'annotated_types.SupportsLe | None' = PydanticUndefined, multiple_of: 'float | None' = PydanticUndefined, allow_inf_nan: 'bool | None' = PydanticUndefined, max_digits: 'int | None' = PydanticUndefined, decimal_places: 'int | None' = PydanticUndefined, min_length: 'int | None' = PydanticUndefined, max_length: 'int | None' = PydanticUndefined, union_mode: "Literal['smart', 'left_to_right']" = PydanticUndefined, fail_fast: 'bool | None' = PydanticUndefined, **extra: 'Unpack[_EmptyKwargs]') -> 'Any'` — !!! abstract "Usage Documentation"
