import textwrap

import libcst as cst
import pytest
from libcst.codemod import CodemodContext
from libcst.metadata import MetadataWrapper

from bump_testclient.command import BumpTestClientCommand


@pytest.mark.parametrize(
    "input,expected",
    (
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.get("/", allow_redirects=False)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.get("/", follow_redirects=False)
            """
            ),
            id="successful redirects",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client):
                response = client.potato("/", allow_redirects=False)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client):
                response = client.potato("/", allow_redirects=False)
            """
            ),
            id="not method redirects",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.get("/", json={{}})
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.request("GET", "/", json={{}})
            """
            ),
            id="no body methods replacement successful",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.get("/", json={{}}, allow_redirects=True)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.request("GET", "/", json={{}}, follow_redirects=True)
            """
            ),
            id="no body methods with redirects",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.delete("/", json={{}})
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.request("DELETE", "/", json={{}})
            """
            ),
            id="no body delete replacement successful",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", data='potato')
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", content='potato')
            """
            ),
            id="replace data by content text",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", data=b'potato')
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", content=b'potato')
            """
            ),
            id="replace data by content bytes",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", data={{}})
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                response = client.post("/", data={{}})
            """
            ),
            id="not replace data by content",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = b"potato"
                response = client.post("/", data=data)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = b"potato"
                response = client.post("/", content=data)
            """
            ),
            id="replace data by content with variable",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = {{}}
                response = client.post("/", data=data)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = {{}}
                response = client.post("/", data=data)
            """
            ),
            id="not replace data by content with variable",
        ),
        pytest.param(
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = b"potato"
                response = client.post("/", data=data)

            def test_another(client: TestClient):
                data = {{}}
                response = client.post("/", data=data)
            """
            ),
            textwrap.dedent(
                """
            from starlette.testclient import TestClient

            def test(client: TestClient):
                data = b"potato"
                response = client.post("/", content=data)

            def test_another(client: TestClient):
                data = {{}}
                response = client.post("/", data=data)
            """
            ),
            id="two test functions",
        ),
    ),
)
def test_transformer(input: str, expected: str) -> None:
    wrapper = MetadataWrapper(cst.parse_module(input))
    transformer = BumpTestClientCommand(CodemodContext())
    modified_tree = wrapper.visit(transformer)
    assert modified_tree.code == expected
