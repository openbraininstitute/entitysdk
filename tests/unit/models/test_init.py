import inspect

from entitysdk import models


def test_models_all():
    """Ensure that the models imported in enttysdk.models.__init__.py are consistent with __all__"""
    imported_names = sorted(
        name for name, element in inspect.getmembers(models) if inspect.isclass(element)
    )
    all_dict_names = sorted(models.__all__)

    assert imported_names == all_dict_names, (
        "Imported classes and __all__ in entitysdk.models.__init__.py are not consistent.\n"
        f"Imported models : {imported_names}\n"
        f"Names in __all__:"
    )
