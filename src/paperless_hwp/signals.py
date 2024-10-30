def get_hwp_parser(*args, **kwargs):
    from paperless_hwp.parser import HwpDocumentParser

    return HwpDocumentParser(*args, **kwargs)

def hwp_consumer_declaration(sender, **kwargs):
    return {
        "parser": get_hwp_parser,
        "weight": 0,
        "mime_types": {
            "application/vnd.hancom.hwp": ".hwp",
            "application/haansofthwp": ".hwp",
            "application/x-hwp": ".hwp",
        },
    }
