from src.tests.test_registry import iter_specs, modules


def test_registry_filters_by_category():
    specs = list(iter_specs(category="audio"))
    assert specs
    assert all(spec.category == "audio" for spec in specs)


def test_registry_filters_by_name():
    specs = list(iter_specs(name_filter="Ringer Mode"))
    assert len(specs) == 1
    assert specs[0].name == "Ringer Mode Tests"


def test_registry_filters_by_document_module():
    specs = list(iter_specs(module="AUDIO"))
    assert specs
    assert all(spec.document_module == "AUDIO" for spec in specs)


def test_registry_exposes_document_modules():
    assert "AUDIO" in modules()
