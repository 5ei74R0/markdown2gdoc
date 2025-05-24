from typing import Optional

from marko import inline
from structured_google_apis.google_docs import (
    Color,
    DashStyle,
    Dimension,
    InsertTextRequest,
    Link,
    Location,
    OptionalColor,
    ParagraphBorder,
    ParagraphStyle,
    Range,
    Request,
    RgbColor,
    Shading,
    TextStyle,
    Unit,
    UpdateParagraphStyleRequest,
    UpdateTextStyleRequest,
    WeightedFontFamily,
    utils,
)


def insert_text(start: int, text: str) -> Request:
    return Request(
        insert_text=InsertTextRequest(
            text=text,
            location=Location(index=start),
        )
    )


def get_bold_text_style(start: int, end: int) -> Request:
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=TextStyle(bold=True),
            fields="bold",
        )
    )


def get_italic_text_style(start: int, end: int) -> Request:
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=TextStyle(italic=True),
            fields="italic",
        )
    )


def get_link_text_style(start: int, end: int, url: str) -> Request:
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=TextStyle(link=Link(url=url)),
            fields="link",
        )
    )


def get_codespan_text_style(start: int, end: int, font_family="Roboto Mono") -> Request:
    t_style = TextStyle(
        font_size=Dimension(magnitude=10, unit=Unit.PT),
        weighted_font_family=WeightedFontFamily(font_family=font_family),
        foreground_color=OptionalColor(
            color=Color(rgb_color=RgbColor(red=0.24, green=0.5, blue=0.24))
        ),
    )
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=t_style,
            fields=utils.get_fields(t_style),
        )
    )


def get_codeblock_text_style(
    start: int, end: int, font_family="Roboto Mono"
) -> Request:
    t_style = TextStyle(
        weighted_font_family=WeightedFontFamily(font_family=font_family),
        font_size=Dimension(magnitude=9, unit=Unit.PT),
    )
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=t_style,
            fields=utils.get_fields(t_style),
        )
    )


def get_specified_text_style(start: int, end: int, text_style: TextStyle) -> Request:
    return Request(
        update_text_style=UpdateTextStyleRequest(
            range=Range(start_index=start, end_index=end),
            text_style=text_style,
            fields=utils.get_fields(text_style),
        )
    )


def get_appropriate_inline_text_style(
    element: inline.InlineElement, start: int, end: int
) -> Optional[Request]:
    if isinstance(element, inline.StrongEmphasis):
        return get_bold_text_style(start, end)
    elif isinstance(element, inline.Emphasis):
        return get_italic_text_style(start, end)
    elif isinstance(element, inline.Link):
        return get_link_text_style(start, end, element.dest)
    elif isinstance(element, inline.CodeSpan):
        return get_codespan_text_style(start, end)
    else:
        return None


def get_specified_paragraph_style(
    start: int, end: int, paragraph_style: ParagraphStyle
) -> Request:
    return Request(
        update_paragraph_style=UpdateParagraphStyleRequest(
            range=Range(start_index=start, end_index=end),
            paragraph_style=paragraph_style,
            fields=utils.get_fields(paragraph_style),
        )
    )


def get_quoto_paragraph_style(start: int, end: int) -> Request:
    p_style = ParagraphStyle(
        indent_first_line=Dimension(magnitude=6, unit=Unit.PT),
        indent_start=Dimension(magnitude=6, unit=Unit.PT),
        # dark grey for left border and light grey for background
        border_left=ParagraphBorder(
            width=Dimension(magnitude=3, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            color=OptionalColor(
                color=Color(rgb_color=RgbColor(red=0.7, green=0.7, blue=0.7))
            ),
            dash_style=DashStyle.SOLID,
        ),
        border_top=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        border_bottom=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        border_right=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        shading=Shading(
            background_color=OptionalColor(
                color=Color(rgb_color=RgbColor(red=0.93, green=0.93, blue=0.93))
            )
        ),
        space_above=Dimension(magnitude=8, unit=Unit.PT),
        space_below=Dimension(magnitude=8, unit=Unit.PT),
    )
    return Request(
        update_paragraph_style=UpdateParagraphStyleRequest(
            range=Range(start_index=start, end_index=end),
            paragraph_style=p_style,
            fields=utils.get_fields(p_style),
        )
    )


def get_code_block_paragraph_style(start: int, end: int) -> Request:
    p_style = ParagraphStyle(
        # dark green for left border and light green for background
        shading=Shading(
            background_color=OptionalColor(
                color=Color(rgb_color=RgbColor(red=0.87, green=0.93, blue=0.87))
            )
        ),
        border_left=ParagraphBorder(
            width=Dimension(magnitude=3, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            color=OptionalColor(
                color=Color(rgb_color=RgbColor(red=0.64, green=0.7, blue=0.64))
            ),
            dash_style=DashStyle.SOLID,
        ),
        border_top=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        border_bottom=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        border_right=ParagraphBorder(
            width=Dimension(magnitude=0, unit=Unit.PT),
            padding=Dimension(magnitude=6, unit=Unit.PT),
            dash_style=DashStyle.SOLID,
        ),
        indent_first_line=Dimension(magnitude=6, unit=Unit.PT),
        indent_start=Dimension(magnitude=6, unit=Unit.PT),
        space_above=Dimension(magnitude=8, unit=Unit.PT),
        space_below=Dimension(magnitude=8, unit=Unit.PT),
    )
    return Request(
        update_paragraph_style=UpdateParagraphStyleRequest(
            range=Range(start_index=start, end_index=end),
            paragraph_style=p_style,
            fields=utils.get_fields(p_style),
        )
    )


def get_list_paragraph_style(start: int, end: int, is_ordered: bool) -> Request:
    return Request.model_validate(
        {
            "createParagraphBullets": {
                "range": {
                    "startIndex": start,
                    "endIndex": end,
                },
                "bulletPreset": "NUMBERED_DECIMAL_ALPHA_ROMAN"
                if is_ordered
                else "BULLET_DISC_CIRCLE_SQUARE",
            }
        }
    )
