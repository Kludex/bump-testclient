import libcst as cst
from libcst import matchers as m
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.metadata.scope_provider import ScopeProvider

CLIENT_METHODS = {"get", "post", "delete", "put", "patch", "head", "options", "request"}
NO_BODY_METHODS = {"get", "delete", "head", "options"}
NO_BODY_PARAMS = {"content", "data", "json", "files"}


class BumpTestClientCommand(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ScopeProvider,)

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
        return updated_node.with_changes(
            func=updated_node.func.with_changes(attr=cst.Name("request")),
            args=[cst.Arg(value=cst.SimpleString('"GET"')), *updated_node.args],
        )

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
        # TODO: Need to retrieve the value of the data argument. Only if it's bytes/text
        # a replacement should be made.
        args = []
        for arg in updated_node.args:
            if m.matches(arg, m.Arg(keyword=m.Name("data"))):
                args.append(arg.with_changes(keyword=cst.Name("content")))
            else:
                args.append(arg)
        return updated_node.with_changes(args=args)
