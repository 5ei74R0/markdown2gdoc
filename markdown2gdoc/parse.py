import warnings
from typing import NewType, Protocol, Self, runtime_checkable

from marko import block, element, inline
from marko import parse as md2ast
from pydantic import BaseModel
from structured_google_apis import google_docs

from .styles import (
    DEFAULT_PARAGRAPH_STYLE_HEADING_1,
    DEFAULT_PARAGRAPH_STYLE_HEADING_2,
    DEFAULT_PARAGRAPH_STYLE_HEADING_3,
    DEFAULT_PARAGRAPH_STYLE_HEADING_4,
    DEFAULT_PARAGRAPH_STYLE_HEADING_5,
    DEFAULT_PARAGRAPH_STYLE_HEADING_6,
    DEFAULT_TEXT_STYLE_HEADING_1,
    DEFAULT_TEXT_STYLE_HEADING_2,
    DEFAULT_TEXT_STYLE_HEADING_3,
    DEFAULT_TEXT_STYLE_HEADING_4,
    DEFAULT_TEXT_STYLE_HEADING_5,
    DEFAULT_TEXT_STYLE_HEADING_6,
)
from .update_requests import (
    get_bold_text_style,
    get_code_block_paragraph_style,
    get_codeblock_text_style,
    get_codespan_text_style,
    get_italic_text_style,
    get_link_text_style,
    get_list_paragraph_style,
    get_quoto_paragraph_style,
    get_specified_paragraph_style,
    get_specified_text_style,
    insert_text,
)

TabCount = NewType("TabCount", int)
CurrentIndex = NewType("CurrentIndex", int)


@runtime_checkable
class HasChildren(Protocol):
    children: list


class Requests(BaseModel):
    text_insertions: list[google_docs.Request] = []
    update_styles: list[google_docs.Request] = []

    def extend(self, other: Self):
        self.text_insertions.extend(other.text_insertions)
        self.update_styles.extend(other.update_styles)

    def append_text(self, text_insertion: google_docs.Request):
        self.text_insertions.append(text_insertion)

    def append_style(self, update_style: google_docs.Request):
        self.update_styles.append(update_style)


def get_text_from_marko_element(element: inline.InlineElement) -> str:
    if isinstance(element, inline.RawText):
        return element.children
    elif isinstance(
        element,
        (
            inline.StrongEmphasis,
            inline.Emphasis,
            inline.Link,
            inline.CodeSpan,
            inline.Literal,
        ),
    ):
        if hasattr(element, "children"):
            if isinstance(element.children, list) and element.children:
                if isinstance(element.children[0], inline.RawText):
                    return element.children[0].children
                elif isinstance(element.children[0], str):
                    return element.children[0]
            elif isinstance(element.children, str):
                return element.children
        return ""
    elif hasattr(element, "children") and isinstance(element.children, list):
        return "".join(get_text_from_marko_element(child) for child in element.children)
    elif isinstance(element, str):
        return element
    return ""


class MarkdownToGoogleDocsConverter:
    def __init__(self):
        self.PARAGRAPH_STYLES: dict[int, google_docs.ParagraphStyle] = {
            1: DEFAULT_PARAGRAPH_STYLE_HEADING_1,
            2: DEFAULT_PARAGRAPH_STYLE_HEADING_2,
            3: DEFAULT_PARAGRAPH_STYLE_HEADING_3,
            4: DEFAULT_PARAGRAPH_STYLE_HEADING_4,
            5: DEFAULT_PARAGRAPH_STYLE_HEADING_5,
            6: DEFAULT_PARAGRAPH_STYLE_HEADING_6,
        }
        self.TEXT_STYLES: dict[int, google_docs.TextStyle] = {
            1: DEFAULT_TEXT_STYLE_HEADING_1,
            2: DEFAULT_TEXT_STYLE_HEADING_2,
            3: DEFAULT_TEXT_STYLE_HEADING_3,
            4: DEFAULT_TEXT_STYLE_HEADING_4,
            5: DEFAULT_TEXT_STYLE_HEADING_5,
            6: DEFAULT_TEXT_STYLE_HEADING_6,
        }

    def convert(self, markdown_content: str) -> list[google_docs.Request]:
        ast = md2ast(markdown_content)
        requests = self.ast_to_google_docs_requests(ast)
        return requests

    def ast_to_google_docs_requests(
        self, ast_node: element.Element
    ) -> list[google_docs.Request]:
        insertions_and_styles, _, _ = self._dfs(ast_node)
        reqs = []
        reqs.extend(insertions_and_styles.text_insertions)
        reqs.extend(insertions_and_styles.update_styles)
        return reqs

    def _dfs(
        self,
        node: element.Element,
        start_idx: int = 1,
        indentation: int = 0,
        break_char: str = "\n",
        tabs: TabCount = 0,
    ) -> tuple[Requests, CurrentIndex, TabCount]:
        # leaf node operation
        if isinstance(node, inline.LineBreak):
            return (
                Requests(text_insertions=[insert_text(start_idx, "\v")]),
                start_idx + 1,
                tabs,
            )
        if isinstance(node, inline.RawText):
            content: str = node.children.replace("\n", break_char)
            return (
                Requests(text_insertions=[insert_text(start_idx, content)]),
                start_idx + len(content),
                tabs,
            )
        if isinstance(node, str):
            content: str = node.replace("\n", break_char)
            return (
                Requests(text_insertions=[insert_text(start_idx, content)]),
                start_idx + len(content),
                tabs,
            )
        if not isinstance(node, HasChildren):
            warnings.warn(
                f"I don't validate this condition. {node} do not have children and it's not str."
            )
            return Requests(), start_idx, tabs

        # 1. insert all the texts in the node, update the current_idx, and collect child requests
        assert isinstance(node, HasChildren), f"node {node} does not have children"
        child_requests = Requests()
        child_start_idx = start_idx
        for child in node.children:
            if isinstance(child, block.Paragraph):
                # make a indentation for the paragraph
                child_requests.append_text(
                    insert_text(child_start_idx, "\t" * indentation + " ")
                )  # a following space is required for the tab to work properly
                child_start_idx += indentation
                tabs += indentation
            child_indentation = (
                indentation + 1 if isinstance(node, block.ListItem) else indentation
            )
            break_char = (
                "\v"
                if isinstance(node, (block.FencedCode, block.CodeBlock))
                else break_char
            )
            reqs, current_idx, tabs = self._dfs(
                child, child_start_idx, child_indentation, break_char, tabs
            )
            child_requests.extend(reqs)
            child_start_idx = current_idx
        current_idx = child_start_idx
        if isinstance(
            node, (block.Heading, block.Paragraph, block.FencedCode, block.CodeBlock)
        ):
            child_requests.extend(
                Requests(text_insertions=[insert_text(current_idx, "\n")])
            )
            current_idx += 1

        # 2. apply styles to the text
        requests = Requests()

        # purify the start and end index of the text that was affected by the tabs
        pure_start = start_idx - tabs
        pure_end = current_idx - tabs

        # update paragraph/text style
        if isinstance(node, inline.Link):
            requests.extend(child_requests)
            requests.append_style(
                get_link_text_style(pure_start, pure_end, node.dest)
            )  # should overwrite the children's style not to disable the link
        elif isinstance(node, inline.CodeSpan):
            requests.extend(child_requests)
            requests.append_style(get_codespan_text_style(pure_start, pure_end))
        elif isinstance(node, inline.Emphasis):
            requests.append_style(get_italic_text_style(pure_start, pure_end))
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, inline.StrongEmphasis):
            requests.append_style(get_bold_text_style(pure_start, pure_end))
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, block.Heading):
            requests.append_style(
                get_specified_paragraph_style(
                    pure_start, pure_end, self.PARAGRAPH_STYLES[node.level]
                )
            )
            requests.append_style(
                get_specified_text_style(
                    pure_start, pure_end, self.TEXT_STYLES[node.level]
                )
            )
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, block.Quote):
            requests.append_style(get_quoto_paragraph_style(pure_start, pure_end))
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, (block.FencedCode, block.CodeBlock)):
            requests.append_style(get_code_block_paragraph_style(pure_start, pure_end))
            requests.append_style(get_codeblock_text_style(pure_start, pure_end))
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, block.List):
            if indentation == 0:
                # if the node is the root of list (not nested), apply the list style
                requests.append_style(
                    get_list_paragraph_style(pure_start, pure_end, node.ordered)
                )
            requests.extend(child_requests)  # overwrite styles by its children
        elif isinstance(node, block.ListItem):
            requests.extend(child_requests)
        elif isinstance(node, block.Paragraph):
            requests.extend(child_requests)
        else:
            requests.extend(child_requests)

        return requests, current_idx, tabs
