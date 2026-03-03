"Tests for the SchemaProvider class in xmlvalidator.py"
import pytest
from gamslib.validation.xmlvalidator import SchemaProvider


@pytest.mark.parametrize(
    "schema_uri, method_to_test",
    [
        # --- xsd ---
        ("simple.xsd", "get_xsd"),
        # relaxng
        ("simple.rng", "get_relaxng"),
        ("simple.rnc", "get_relaxng_compact"),
        # --- dtd ---
        ("simple.dtd", "get_dtd"),
        # schematron files with different query bindings
        ("simple_exslt.sch", "get_schematron"),
        ("simple_stx.sch", "get_schematron"),
        # TODO: these are not supported by lxml, switch to saxon?
        #("simple.xpath2.sch", "get_schematron"),
        #("simple.xpath3.sch", "get_schematron"),
        #("simple.xslt.sch", "get_schematron"),
        #("simple.xslt2.sch", "get_schematron"),
        #("simple.xslt3.sch", "get_schematron"),
    ],
)
def test_get_simple_valid_schema(schema_uri, method_to_test, lazy_shared_datadir):
    """Test the passed function with a simple valid schema.

    Every schema is fetched twice to test the caching mechanism.
    """
    # if uri is a path to a file we convert it to a file URI
    # all filenames are relative to the schemas directory in the shared datadir
    if not (schema_uri.startswith("file:") or schema_uri.startswith("http")):
        schema_uri = (lazy_shared_datadir / "schemas" / schema_uri).resolve().as_uri()
    get_schema_method = getattr(SchemaProvider, method_to_test)

    # Clear cache to ensure the test is not affected by previous tests
    get_schema_method.cache_clear()

    schema = get_schema_method(schema_uri)
    assert schema is not None

    # Second call should return the cached schema (same object)
    schema2 = get_schema_method(schema_uri)
    assert schema2 is schema


# TODO: Implement tests for real documents
# @pytest.mark.parametrize("filename, method", [

# ]
# def test_get_realistic_valid_schema(filename, method, shared_datadir):
#     """Test the passed function with a realistic valid schema."""
#     schema_file = shared_datadir / "schemas" / filename
#     get_schema = getattr(SchemaProvider, method)
#     uri = schema_file.resolve().as_uri()
#     schema = get_schema(uri)
#     assert schema is not None
#     # Second call should return the cached schema (same object)
#     schema2 = get_schema(uri)
#     assert schema2 is schema

