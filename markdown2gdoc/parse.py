from marko import block, element, inline
from marko import parse as md2ast
from structured_google_apis import google_docs

from .indentation import (
    INITIAL_FIRST_LINE_INDENT,
    INITIAL_START_INDENT,
    LEVEL_INDENT_STEP,
)
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
    get_appropriate_inline_text_style,
    get_code_block_paragraph_style,
    get_codeblock_text_style,
    get_quoto_paragraph_style,
    insert_text,
)


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
        self.PRAGRAPH_STYLES: dict[int, google_docs.ParagraphStyle] = {
            1: DEFAULT_PARAGRAPH_STYLE_HEADING_1,
            2: DEFAULT_PARAGRAPH_STYLE_HEADING_2,
            3: DEFAULT_PARAGRAPH_STYLE_HEADING_3,
            4: DEFAULT_PARAGRAPH_STYLE_HEADING_4,
            5: DEFAULT_PARAGRAPH_STYLE_HEADING_5,
            6: DEFAULT_PARAGRAPH_STYLE_HEADING_6,
        }
        self.TEXT_STYLES: dict[int, google_docs.ParagraphStyle] = {
            1: DEFAULT_TEXT_STYLE_HEADING_1,
            2: DEFAULT_TEXT_STYLE_HEADING_2,
            3: DEFAULT_TEXT_STYLE_HEADING_3,
            4: DEFAULT_TEXT_STYLE_HEADING_4,
            5: DEFAULT_TEXT_STYLE_HEADING_5,
            6: DEFAULT_TEXT_STYLE_HEADING_6,
        }

    def convert(self, markdown_content: str) -> list[google_docs.Request]:
        ast = md2ast(markdown_content)
        requests, _ = self.markdown_ast_to_google_docs_requests(ast)
        return requests

    def process_list_item_children(
        self,
        children: element.Element,
        current_index: int,
        nesting_level: int,
        is_ordered_list: bool,
    ) -> tuple[list[google_docs.Request], int]:
        requests = []
        first_paragraph_processed = False

        for child_node in children:
            if (
                isinstance(child_node, block.Paragraph)
                and not first_paragraph_processed
            ):
                paragraph_text = ""
                inline_formatting_requests = []
                temp_inline_start_index = current_index

                for inline_child in child_node.children:
                    text_segment = get_text_from_marko_element(inline_child)
                    paragraph_text += text_segment
                    inline_text_style = get_appropriate_inline_text_style(
                        inline_child,
                        temp_inline_start_index,
                        temp_inline_start_index + len(text_segment),
                    )
                    if inline_text_style is not None:
                        inline_formatting_requests.append(inline_text_style)
                    temp_inline_start_index += len(text_segment)

                paragraph_text_with_newline = paragraph_text + "\n"

                # 1. Insert the paragraph text with a newline
                requests.append(insert_text(current_index, paragraph_text_with_newline))

                # 2. Apply the bullet style (set the type of marker)
                requests.append(
                    google_docs.Request.model_validate(
                        {
                            "createParagraphBullets": {
                                "range": {
                                    "startIndex": current_index,
                                    "endIndex": current_index
                                    + len(paragraph_text_with_newline),
                                },
                                "bulletPreset": "NUMBERED_DECIMAL_ALPHA_ROMAN"
                                if is_ordered_list
                                else "BULLET_DISC_CIRCLE_SQUARE",
                            }
                        }
                    )
                )

                # 3. set the indentation explicitly
                target_indent_first_line = INITIAL_FIRST_LINE_INDENT + (
                    nesting_level * LEVEL_INDENT_STEP
                )
                target_indent_start = INITIAL_START_INDENT + (
                    nesting_level * LEVEL_INDENT_STEP
                )

                # indentStart must be greater than or equal to indentFirstLine
                target_indent_start = max(target_indent_start, target_indent_first_line)

                requests.append(
                    google_docs.Request.model_validate(
                        {
                            "updateParagraphStyle": {
                                "range": {
                                    "startIndex": current_index,
                                    "endIndex": current_index
                                    + len(paragraph_text_with_newline),
                                },
                                "paragraphStyle": {
                                    "indentFirstLine": {
                                        "magnitude": target_indent_first_line,
                                        "unit": "PT",
                                    },
                                    "indentStart": {
                                        "magnitude": target_indent_start,
                                        "unit": "PT",
                                    },
                                },
                                "fields": "indentFirstLine,indentStart",
                            }
                        }
                    )
                )

                # 4. Apply the inline styles
                requests.extend(inline_formatting_requests)

                current_index += len(paragraph_text_with_newline)
                first_paragraph_processed = True

            elif isinstance(child_node, block.List):
                nested_list_requests, current_index = (
                    self.markdown_ast_to_google_docs_requests(
                        child_node, current_index, nesting_level + 1
                    )
                )
                requests.extend(nested_list_requests)
            else:
                other_block_requests, current_index = (
                    self.markdown_ast_to_google_docs_requests(
                        child_node, current_index, nesting_level
                    )
                )
                requests.extend(other_block_requests)
        return requests, current_index

    def markdown_ast_to_google_docs_requests(
        self,
        ast_node: element.Element,
        current_index: int = 1,
        current_nesting_level: int = 0,
    ) -> tuple[list[google_docs.Request], int]:
        requests = []

        if isinstance(ast_node, block.Document):
            for child in ast_node.children:
                child_requests, current_index = (
                    self.markdown_ast_to_google_docs_requests(child, current_index, 0)
                )
                requests.extend(child_requests)
        elif isinstance(ast_node, block.Heading):
            text_content = (
                "".join(
                    get_text_from_marko_element(child) for child in ast_node.children
                )
                + "\n"
            )
            requests.append(insert_text(current_index, text_content))
            heading_level = ast_node.level
            requests.append(
                google_docs.Request(
                    update_paragraph_style=google_docs.UpdateParagraphStyleRequest(
                        range=google_docs.Range(
                            start_index=current_index,
                            end_index=current_index + len(text_content),
                        ),
                        paragraph_style=self.PRAGRAPH_STYLES[heading_level],
                        fields=google_docs.utils.get_fields(
                            self.PRAGRAPH_STYLES[heading_level]
                        ),
                    )
                )
            )
            requests.append(
                google_docs.Request(
                    update_text_style=google_docs.UpdateTextStyleRequest(
                        range=google_docs.Range(
                            start_index=current_index,
                            end_index=current_index + len(text_content),
                        ),
                        text_style=self.TEXT_STYLES[heading_level],
                        fields=google_docs.utils.get_fields(
                            self.TEXT_STYLES[heading_level]
                        ),
                    )
                )
            )
            current_index += len(text_content)
        elif isinstance(ast_node, block.Paragraph):
            paragraph_text = ""
            inline_reqs = []
            temp_idx = current_index
            for child in ast_node.children:
                text = get_text_from_marko_element(child)
                paragraph_text += text
                inline_text_style = get_appropriate_inline_text_style(
                    child, temp_idx, temp_idx + len(text)
                )
                if inline_text_style is not None:
                    inline_reqs.append(inline_text_style)
                temp_idx += len(text)
            paragraph_text_with_newline = paragraph_text + "\n"
            requests.append(insert_text(current_index, paragraph_text_with_newline))
            requests.extend(inline_reqs)
            current_index += len(paragraph_text_with_newline)
        elif isinstance(ast_node, block.List):
            for item_node in ast_node.children:
                if isinstance(item_node, block.ListItem):
                    item_requests, current_index = self.process_list_item_children(
                        item_node.children,
                        current_index,
                        current_nesting_level,
                        ast_node.ordered,
                    )
                    requests.extend(item_requests)
        elif isinstance(ast_node, block.Quote):
            temp_child_requests: list[google_docs.Request] = []
            temp_current_index_for_children = current_index
            processed_quote_text_len = 0

            for child in ast_node.children:
                child_reqs, temp_current_index_for_children = (
                    self.markdown_ast_to_google_docs_requests(
                        child, temp_current_index_for_children, current_nesting_level
                    )
                )
                temp_child_requests.extend(child_reqs)

            for req in temp_child_requests:
                requests.append(req)
                if req.insert_text is not None:
                    requests.append(
                        get_quoto_paragraph_style(
                            req.insert_text.location.index,
                            req.insert_text.location.index + len(req.insert_text.text),
                        )
                    )
                    processed_quote_text_len += len(req.insert_text.text)
            current_index = temp_current_index_for_children

        elif isinstance(ast_node, (block.FencedCode, block.CodeBlock)):
            code_content = (
                get_text_from_marko_element(ast_node.children[0])
                if ast_node.children
                else ""
            )
            code_content_with_newline = (
                code_content.rstrip("\n") + "\n" if code_content else "\n"
            )
            requests.append(insert_text(current_index, code_content_with_newline))
            requests.append(
                get_code_block_paragraph_style(
                    current_index, current_index + len(code_content_with_newline)
                )
            )
            requests.append(
                get_codeblock_text_style(
                    current_index, current_index + len(code_content_with_newline)
                )
            )
            current_index += len(code_content_with_newline)
        elif isinstance(ast_node, block.ThematicBreak):
            hr_text = "\n"
            requests.append(insert_text(current_index, hr_text))
            requests.append(
                google_docs.Request.model_validate(
                    {
                        "updateParagraphStyle": {
                            "range": {
                                "startIndex": current_index,
                                "endIndex": current_index + len(hr_text),
                            },
                            "paragraphStyle": {
                                "borderBottom": {
                                    "width": {"magnitude": 1, "unit": "PT"},
                                    "padding": {"magnitude": 3, "unit": "PT"},
                                    "dashStyle": "SOLID",
                                    "color": {
                                        "color": {
                                            "rgbColor": {
                                                "red": 0.7,
                                                "green": 0.7,
                                                "blue": 0.7,
                                            }
                                        }
                                    },
                                },
                                "spaceAbove": {"magnitude": 6, "unit": "PT"},
                                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                            },
                            "fields": "borderBottom,spaceAbove,spaceBelow",
                        }
                    }
                )
            )
            current_index += len(hr_text)

        return requests, current_index
