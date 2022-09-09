from collections import defaultdict

import libcst as cst
from libcst import matchers as m
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.metadata.parent_node_provider import ParentNodeProvider
from libcst.metadata.scope_provider import ScopeProvider

CLIENT_METHODS = {"get", "post", "delete", "put", "patch", "head", "options", "request"}
NO_BODY_METHODS = {"get", "delete", "head", "options"}
NO_BODY_PARAMS = {"content", "data", "json", "files"}


class BumpTestClientCommand(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ScopeProvider, ParentNodeProvider)

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self._assignments = {}  # type: ignore[var-annotated]

    @m.call_if_inside(
        m.Call(
            func=m.Attribute(
                attr=m.OneOf(*[m.Name(method) for method in CLIENT_METHODS])
            )
        )
    )
    @m.leave(m.Name("allow_redirects"))
    def replace_redirects(
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.Name:
        # NOTE: Do we need to ensure caller is a TestClient? If yes, then we cannot
        # match a Name node. We need to match a Call node.
        return updated_node.with_changes(value="follow_redirects")

    @m.leave(
        m.Call(
            func=m.Attribute(
                attr=m.OneOf(*[m.Name(method) for method in NO_BODY_METHODS]),
            ),
            args=[
                m.ZeroOrMore(),
                m.OneOf(*[m.Arg(keyword=m.Name(param)) for param in NO_BODY_PARAMS]),
                m.ZeroOrMore(),
            ],
        )
    )
    def replace_methods_by_request(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        method_node = cst.ensure_type(updated_node.func, cst.Attribute).attr
        method = cst.ensure_type(method_node, cst.Name).value.upper()
        return updated_node.with_changes(
            func=updated_node.func.with_changes(attr=cst.Name("request")),
            args=[cst.Arg(value=cst.SimpleString(f'"{method}"')), *updated_node.args],
        )

    @m.call_if_inside(m.FunctionDef())
    @m.leave(m.Assign())
    def save_data_assignment(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign:
        for target in updated_node.targets:
            if isinstance(target.target, cst.Name):
                self._assignments[target.target.value] = updated_node.value
        return updated_node

    @m.leave(m.FunctionDef())
    def reset_assignments_after_function(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        self._assignments = {}
        return updated_node

    @m.leave(
        m.Call(
            func=m.Attribute(
                attr=m.OneOf(*[m.Name(method) for method in CLIENT_METHODS])
            ),
            args=[m.ZeroOrMore(), m.Arg(keyword=m.Name("data")), m.ZeroOrMore()],
        )
    )
    def replace_data_by_content(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        args = []
        for arg in updated_node.args:
            if m.matches(arg, m.Arg(keyword=m.Name("data"))):
                if isinstance(arg.value, cst.Name):
                    value = self._assignments.get(arg.value.value)
                else:
                    value = arg.value
                if isinstance(value, cst.BaseString):
                    args.append(arg.with_changes(keyword=cst.Name("content")))
                    continue
            args.append(arg)
        return updated_node.with_changes(args=args)

    @m.leave(
        m.Call(
            func=m.Attribute(
                attr=m.OneOf(*[m.Name(method) for method in CLIENT_METHODS])
            ),
            args=[m.ZeroOrMore(), m.Arg(keyword=m.Name("data")), m.ZeroOrMore()],
        )
    )
    def replace_data_payload(
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        args = []
        data = defaultdict(list)
        for arg in updated_node.args:
            if m.matches(arg, m.Arg(keyword=m.Name("data"))):
                if m.matches(
                    arg.value,
                    m.List(
                        elements=[
                            m.ZeroOrMore(),
                            m.Element(value=m.Tuple()),
                            m.ZeroOrMore(),
                        ]
                    ),
                ):
                    for element in cst.ensure_type(arg.value, cst.List).elements:
                        element = cst.ensure_type(element, cst.Element)
                        elements = cst.ensure_type(element.value, cst.Tuple).elements
                        key_tuple, value_tuple = elements
                        key = key_tuple.value.value
                        value = value_tuple.value.value
                        data[key].append(value)
            if data:
                args.append(arg)
                continue
            args.append(arg)

        return updated_node.with_changes(args=args)
