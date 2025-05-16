from typing import Optional
from marko import inline

from .schemas import BatchUpdateRequest
from .indentation import INITIAL_FIRST_LINE_INDENT


def insert_text(start: int, text: str) -> BatchUpdateRequest:
    return {
        "insertText": {
            "text": text,
            "location": {"index": start},
        }
    }


# text styles
def make_bold(start, end) -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True},
            "fields": "bold",
        }
    }


def make_italic(start, end) -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"italic": True},
            "fields": "italic",
        }
    }


def make_strikethrough(start, end) -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"strikethrough": True},
            "fields": "strikethrough",
        }
    }


def make_link(start, end, url) -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"link": {"url": url}},
            "fields": "link",
        }
    }


def make_codespan(start, end, font_family="Courier New") -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"weightedFontFamily": {"fontFamily": font_family}},
            "fields": "weightedFontFamily",
        }
    }


def get_codeblock_text_style(start, end) -> BatchUpdateRequest:
    return {
        "updateTextStyle": {
            "range": {
                "startIndex": start,
                "endIndex": end,
            },
            "textStyle": {
                "weightedFontFamily": {"fontFamily": "Consolas", "weight": 400},
                "fontSize": {"magnitude": 9, "unit": "PT"},
            },
            "fields": "weightedFontFamily,fontSize",
        }
    }


def get_appropriate_inline_text_style(
    element: inline.InlineElement, start: int, end: int
) -> Optional[BatchUpdateRequest]:
    if isinstance(element, inline.StrongEmphasis):
        return make_bold(start, end)
    elif isinstance(element, inline.Emphasis):
        return make_italic(start, end)
    elif isinstance(element, inline.Link):
        return make_link(start, end, element.dest)
    elif isinstance(element, inline.CodeSpan):
        return make_codespan(start, end)
    return None


# paragraph styles
def get_quoto_paragraph_style(start, end):
    return {
        "updateParagraphStyle": {
            "range": {
                "startIndex": start,
                "endIndex": end,
            },
            "paragraphStyle": {
                "indentFirstLine": {"magnitude": 6, "unit": "PT"},
                "indentStart": {"magnitude": 6, "unit": "PT"},
                # dark grey for left border and light grey for background
                "borderLeft": {
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "color": {
                        "color": {"rgbColor": {"red": 0.7, "green": 0.7, "blue": 0.7}}
                    },
                    "dashStyle": "SOLID",
                },
                "borderTop": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "borderBottom": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "borderRight": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "shading": {
                    "backgroundColor": {
                        "color": {
                            "rgbColor": {
                                "red": 0.93,
                                "green": 0.93,
                                "blue": 0.93,
                            }
                        }
                    },
                },
                "spaceAbove": {"magnitude": 8, "unit": "PT"},
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "indentFirstLine,indentStart,borderLeft,borderTop,borderBottom,borderRight,shading,spaceAbove,spaceBelow",
        }
    }


def get_code_block_paragraph_style(start, end):
    return {
        "updateParagraphStyle": {
            "range": {
                "startIndex": start,
                "endIndex": end,
            },
            "paragraphStyle": {
                # dark green for left border and light green for background
                "shading": {
                    "backgroundColor": {
                        "color": {
                            "rgbColor": {
                                "red": 0.87,
                                "green": 0.93,
                                "blue": 0.87,
                            }
                        }
                    }
                },
                "borderLeft": {
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "color": {
                        "color": {"rgbColor": {"red": 0.64, "green": 0.7, "blue": 0.64}}
                    },
                    "dashStyle": "SOLID",
                },
                "borderTop": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "borderBottom": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "borderRight": {
                    "width": {"magnitude": 0, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "indentFirstLine": {"magnitude": 6, "unit": "PT"},
                "indentStart": {"magnitude": 6, "unit": "PT"},
                "spaceAbove": {"magnitude": 8, "unit": "PT"},
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "shading,borderLeft,borderTop,borderBottom,borderRight,indentFirstLine,indentStart,spaceAbove,spaceBelow",
        }
    }
